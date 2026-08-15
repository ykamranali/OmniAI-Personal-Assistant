import asyncio
import os
import re
import json
import time
import base64
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent, AgentResponse
from app.services.llm import llm_service
from app.core.runtime_config import runtime_config
from PIL import Image

SYSTEM_PROMPT = """You are an Autonomous Computer Use OS Agent.
Your job is to complete the user's request by observing the screen and taking actions step by step.
You will be provided with a screenshot of the current screen state at each step.

Available actions you can output as a single JSON object:
1. Click (provide x, y relative coordinates from 0.0 to 1.0):
   {"action": "click", "x": 0.5, "y": 0.5}
2. Double Click:
   {"action": "double_click", "x": 0.5, "y": 0.5}
3. Type text on the keyboard:
   {"action": "type", "text": "hello world"}
4. Press a specific key (e.g., enter, tab, win):
   {"action": "press", "key": "enter"}
5. Scroll (positive for up, negative for down):
   {"action": "scroll", "amount": -500}
6. Finish the task:
   {"action": "done", "message": "I have completed the task."}

IMPORTANT:
- Every time files are created or saved, they MUST be located in the user's Downloads folder (`%USERPROFILE%\\Downloads`).
- Output ONLY a valid JSON object and absolutely no other text. Example: {"action": "click", "x": 0.1, "y": 0.9}
- Do NOT include markdown formatting like ```json. Do NOT include conversational text.
- If you are done, output the "done" action.

User request: """

# Only claim a request as desktop automation if it actually sounds like one.
# Without this, OSAutomationAgent (registered first) would swallow every
# single chat message — including plain conversation like "hello" — the
# moment OS Control is toggled on, sending it through the screenshot/vision
# loop and failing to parse a JSON action out of a conversational reply.
AUTOMATION_TRIGGERS = re.compile(
    r"\b("
    r"open|close|launch|start|run|quit|exit|"
    r"click|double.click|type|write|press|scroll|drag|"
    r"screenshot|take a screenshot|capture (the )?screen|"
    r"minimize|maximize|resize|move (the )?(mouse|window)|"
    r"switch (to|tab)|focus (on )?|"
    r"save (it|this|the file)|download|install|uninstall|"
    r"take (a )?picture|record (the )?screen"
    r")\b",
    re.IGNORECASE,
)

# Keywords that flag a request or an individual typed action as risky enough to
# require an explicit human confirmation before OmniAI is allowed to proceed.
# This is a best-effort heuristic, not a security boundary.
RISKY_PATTERN = re.compile(
    r"\b("
    r"delete|remove|uninstall|format|wipe|factory reset|"
    r"shutdown|restart|reboot|"
    r"send (the )?email|send (the )?message|send (the )?dm|"
    r"pay|purchase|buy|checkout|order|"
    r"transfer|wire|venmo|paypal|bank|routing number|account number|"
    r"credit card|debit card|cvv|password|passcode|"
    r"sudo|rm -rf"
    r")\b",
    re.IGNORECASE,
)

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
LOG_PATH = os.path.join(LOG_DIR, "os_agent_actions.log")


def image_to_base64(img: Image.Image) -> str:
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def _log_action(request: str, entry: Dict[str, Any]) -> None:
    """Append a JSON-lines audit record of what the OS agent actually did."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": request,
            **entry,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[OSAutomationAgent] Failed to write action log: {e}")


class OSAutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="OSAutomationAgent",
            description="Automates OS tasks autonomously using a Vision LLM to see the screen and control the mouse/keyboard.",
        )

    async def _request_confirmation(self, websocket, prompt: str, timeout: float = 60.0) -> bool:
        """
        Ask the connected client to approve a risky step before it executes.
        Returns False (deny) on missing websocket, timeout, malformed reply, or explicit denial —
        i.e. the safe default is always "do not proceed".
        """
        if websocket is None:
            return False
        try:
            await websocket.send_text(json.dumps({
                "type": "confirmation_required",
                "message": prompt,
            }))
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=timeout)
            data = json.loads(raw)
            return data.get("type") == "confirm_action" and bool(data.get("approved", False))
        except Exception as e:
            print(f"[OSAutomationAgent] Confirmation step failed/timed out: {e}")
            return False

    async def process_request(self, request: str, context: Dict[str, Any] = None) -> AgentResponse:
        context = context or {}

        if not context.get("os_control_allowed", False):
            return AgentResponse(status="unknown", message="OS Control is not allowed by the user. Please enable it in the toolbar.")

        if not AUTOMATION_TRIGGERS.search(request):
            # Doesn't sound like a desktop-automation command — let it fall
            # through to normal conversation instead of screenshotting.
            return AgentResponse(status="unknown", message="Not a recognized OS automation command.")

        websocket = context.get("websocket")
        already_confirmed = context.get("confirmed", False)

        # ── Upfront safety gate ────────────────────────────────────────────
        # If the instruction itself looks risky (deleting things, sending
        # messages/emails, spending money, touching credentials, etc.) ask
        # the user to explicitly approve before any screen automation starts.
        #
        # Two transports are supported:
        #  - Over the raw `/ws` socket, `websocket` is available so we can do
        #    a live round-trip confirmation and continue in the same call.
        #  - Over the REST chat endpoint (the path the desktop UI actually
        #    uses today) there's no open channel to ask mid-request, so we
        #    return early with status="confirmation_required" — the same
        #    pattern MemoryAgent already uses — and the caller re-invokes us
        #    with context["confirmed"]=True once the user approves in the UI.
        if RISKY_PATTERN.search(request) and not already_confirmed:
            prompt = (
                f"This request looks like it may take a sensitive action "
                f"(delete data, send a message, spend money, or handle credentials):\n\n"
                f"\"{request}\"\n\nProceed?"
            )
            if websocket is not None:
                approved = await self._request_confirmation(websocket, prompt)
                _log_action(request, {"event": "upfront_risk_check", "approved": approved})
                if not approved:
                    return AgentResponse(
                        status="error",
                        message="This request looked potentially sensitive, so I paused for confirmation and didn't receive an approval. Nothing was done.",
                    )
            else:
                _log_action(request, {"event": "upfront_risk_check", "approved": None, "transport": "rest"})
                return AgentResponse(
                    status="confirmation_required",
                    message=prompt,
                    data={"agent": "OSAutomationAgent", "request": request},
                )

        import pyautogui
        pyautogui.FAILSAFE = False
        screen_width, screen_height = pyautogui.size()

        vision_model = runtime_config.get("os_agent_vision_model", "llama3.2-vision")
        max_iterations = int(runtime_config.get("os_agent_max_steps", 25) or 25)
        timeout_seconds = float(runtime_config.get("os_agent_timeout_seconds", 240) or 240)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + request}
        ]

        executed_actions: List[str] = []
        start_time = time.monotonic()

        async def run_loop() -> Optional[AgentResponse]:
            for iteration in range(max_iterations):
                if time.monotonic() - start_time > timeout_seconds:
                    executed_actions.append(f"Stopped: exceeded {int(timeout_seconds)}s time budget.")
                    break

                await asyncio.sleep(1)  # Wait for screen to settle
                screenshot = await asyncio.to_thread(pyautogui.screenshot)
                img_b64 = image_to_base64(screenshot)

                current_step_msg = {
                    "role": "user",
                    "content": f"Step {iteration + 1}. Please provide the next action JSON based on this screen.",
                    "images": [img_b64],
                }
                messages.append(current_step_msg)

                if not hasattr(llm_service, "generate_chat_response"):
                    return AgentResponse(status="error", message="Vision loop requires generate_chat_response capability.")

                # IMPORTANT: use the dedicated vision-capable model for this loop.
                # The general chat/default model (e.g. a text-only model like
                # llama3.1) cannot see the screenshots and will effectively be
                # guessing blind, so we never fall back to it here.
                llm_output = await llm_service.generate_chat_response(messages, model=vision_model)

                print(f"OS_AGENT RAW OUTPUT (Step {iteration + 1}):", repr(llm_output))
                llm_output = (llm_output or "").strip()

                match = re.search(r'\{.*\}', llm_output, re.DOTALL)
                if match:
                    llm_output = match.group(0)

                try:
                    command = json.loads(llm_output)
                except json.JSONDecodeError:
                    return AgentResponse(status="error", message=f"Failed to parse LLM output as JSON: {llm_output}")

                messages.append({"role": "assistant", "content": json.dumps(command)})

                action = command.get("action")

                if action == "done":
                    msg = command.get("message", "Task finished.")
                    executed_actions.append(f"Done: {msg}")
                    _log_action(request, {"event": "action", "step": iteration + 1, "action": "done", "message": msg})
                    break

                elif action in ["click", "double_click"]:
                    x_rel = command.get("x", 0.5)
                    y_rel = command.get("y", 0.5)
                    x_abs = int(x_rel * screen_width)
                    y_abs = int(y_rel * screen_height)

                    if action == "click":
                        await asyncio.to_thread(pyautogui.click, x=x_abs, y=y_abs)
                        executed_actions.append(f"Clicked at ({x_abs}, {y_abs})")
                    else:
                        await asyncio.to_thread(pyautogui.doubleClick, x=x_abs, y=y_abs)
                        executed_actions.append(f"Double-clicked at ({x_abs}, {y_abs})")
                    _log_action(request, {"event": "action", "step": iteration + 1, "action": action, "x": x_abs, "y": y_abs})

                elif action == "type":
                    text = command.get("text", "")
                    # Per-action safety gate: even if the original request wasn't
                    # flagged, don't blindly type something that looks like a
                    # credential or a risky phrase without a fresh confirmation.
                    if RISKY_PATTERN.search(text):
                        approved = await self._request_confirmation(
                            websocket,
                            f"OmniAI is about to type text that looks sensitive:\n\n\"{text}\"\n\nProceed?",
                        )
                        _log_action(request, {"event": "type_risk_check", "step": iteration + 1, "text_preview": text[:40], "approved": approved})
                        if not approved:
                            executed_actions.append("Skipped a risky 'type' action — not approved.")
                            continue
                    await asyncio.to_thread(pyautogui.write, text, interval=0.05)
                    executed_actions.append(f"Typed text: {text}")
                    _log_action(request, {"event": "action", "step": iteration + 1, "action": "type", "text_preview": text[:80]})

                elif action == "press":
                    key = command.get("key", "")
                    await asyncio.to_thread(pyautogui.press, key)
                    executed_actions.append(f"Pressed {key}")
                    _log_action(request, {"event": "action", "step": iteration + 1, "action": "press", "key": key})

                elif action == "scroll":
                    amount = command.get("amount", 0)
                    await asyncio.to_thread(pyautogui.scroll, amount)
                    executed_actions.append(f"Scrolled {amount}")
                    _log_action(request, {"event": "action", "step": iteration + 1, "action": "scroll", "amount": amount})

                else:
                    executed_actions.append(f"Unknown action: {action}")
                    _log_action(request, {"event": "unknown_action", "step": iteration + 1, "raw": command})
            else:
                executed_actions.append(f"Stopped: reached the {max_iterations}-step limit.")
            return None

        try:
            early_result = await run_loop()
            if early_result is not None:
                return early_result
        except Exception as e:
            _log_action(request, {"event": "error", "error": str(e)})
            return AgentResponse(status="error", message=f"Failed during OS action loop: {str(e)}")

        summary = "Executed sequence: " + " -> ".join(executed_actions) if executed_actions else "No actions were executed."
        return AgentResponse(status="success", message=summary)
