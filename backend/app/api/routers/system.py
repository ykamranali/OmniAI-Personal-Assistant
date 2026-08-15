"""
System router for OmniAI Personal Assistant.
Provides endpoints for system tasks, registered agents, and runtime settings.
"""
from fastapi import APIRouter, HTTPException
import psutil
import time
from typing import Any, Dict
from pydantic import BaseModel
from app.agents.base import agent_manager
from app.core.runtime_config import runtime_config

router = APIRouter(prefix="/system", tags=["system"])


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    default_model: str | None = None
    voice_enabled: bool | None = None
    tts_voice: str | None = None
    os_control_allowed: bool | None = None
    # OS automation (vision-loop) hardening
    os_agent_vision_model: str | None = None
    os_agent_max_steps: int | None = None
    os_agent_timeout_seconds: int | None = None
    # Always-on local voice assistant
    voice_loop_enabled: bool | None = None
    wake_word: str | None = None
    voice_barge_in_enabled: bool | None = None
    voice_vad_energy_threshold: float | None = None


class OSAgentExecuteRequest(BaseModel):
    request: str


# ─────────────────────────────────────────────
# System Tasks
# ─────────────────────────────────────────────

@router.get("/tasks")
async def get_system_tasks():
    """Return the top 5 processes by memory usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'create_time']):
        try:
            pinfo = proc.info
            pinfo['memory_mb'] = pinfo['memory_info'].rss / (1024 * 1024)
            uptime_seconds = time.time() - pinfo['create_time']
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            pinfo['duration'] = (
                f"{int(hours)}h {int(minutes)}m" if hours > 0
                else f"{int(minutes)}m {int(seconds)}s"
            )
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    top_processes = sorted(processes, key=lambda p: p['memory_mb'], reverse=True)[:5]
    formatted_tasks = [
        {
            "id": p['pid'],
            "name": p['name'],
            "status": "Running",
            "duration": p['duration'],
            "memory": f"{p['memory_mb']:.1f} MB",
        }
        for p in top_processes
    ]
    return {"status": "success", "data": formatted_tasks}


# ─────────────────────────────────────────────
# Agents
# ─────────────────────────────────────────────

@router.get("/agents")
async def get_active_agents():
    """Return all registered agents."""
    agents = agent_manager.get_all_agents()
    agent_data = [{"name": a.name, "description": a.description} for a in agents]
    return {"status": "success", "data": agent_data}


# ─────────────────────────────────────────────
# Runtime Settings
# ─────────────────────────────────────────────

@router.get("/settings")
async def get_settings():
    """Return current runtime settings."""
    return {"status": "success", "data": runtime_config.get_all()}


@router.post("/settings")
async def update_settings(update: SettingsUpdate):
    """Update one or more runtime settings."""
    changes: Dict[str, Any] = {
        k: v for k, v in update.model_dump().items() if v is not None
    }

    # Starting/stopping the always-on voice loop is a side effect, not just a
    # stored flag — start/stop the background listener thread to match.
    voice_loop_toggle = changes.get("voice_loop_enabled")

    runtime_config.update(changes)

    if voice_loop_toggle is not None:
        from app.services.voice_loop import voice_loop_service
        if voice_loop_toggle:
            err = voice_loop_service.start()
            if err:
                runtime_config.set("voice_loop_enabled", False)
                return {"status": "error", "message": err, "data": runtime_config.get_all()}
        else:
            voice_loop_service.stop()

    return {"status": "success", "data": runtime_config.get_all()}


# ─────────────────────────────────────────────
# OS Agent execution (post-confirmation)
# ─────────────────────────────────────────────

@router.post("/os-agent/execute")
async def execute_os_agent(payload: OSAgentExecuteRequest):
    """
    Re-invoke the OS automation agent for a request it previously flagged as
    sensitive and returned as status="confirmation_required" over the REST
    chat endpoint. The frontend calls this only after the user clicks Approve.
    """
    agent = agent_manager.get_agent("OSAutomationAgent")
    if not agent:
        raise HTTPException(status_code=500, detail="OSAutomationAgent is not registered")

    context = {
        "os_control_allowed": runtime_config.get("os_control_allowed", False),
        "confirmed": True,
    }
    res = await agent.process_request(payload.request, context=context)
    return {
        "type": "agent_response",
        "agent": "OSAutomationAgent",
        "status": res.status,
        "message": res.message,
        "data": res.data,
    }
