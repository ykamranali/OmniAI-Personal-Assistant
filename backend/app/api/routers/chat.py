from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.llm import llm_service
from app.agents.base import agent_manager
import json

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
    last_user_message = next((m.content for m in reversed(request.messages) if m.role == "user"), None)
    
    # 1. First see if an Agent wants to intercept (e.g. MemoryAgent)
    if last_user_message:
        from app.core.runtime_config import runtime_config
        for agent in agent_manager.get_all_agents():
            # Pass a context if needed
            res = await agent.process_request(last_user_message, context={"os_control_allowed": runtime_config.get("os_control_allowed")})
            if res.status != "unknown":
                # The agent intercepted the request (e.g. asking for memory confirmation)
                return {
                    "type": "agent_response",
                    "agent": agent.name,
                    "status": res.status,
                    "message": res.message,
                    "data": res.data
                }
                
    # 2. If no agent intercepts, stream the LLM response
    messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
    
    import os
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "core", "system_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            sys_prompt = f.read()
    except Exception:
        sys_prompt = "You are Omni Jarvis."
        
    if not any(m["role"] == "system" for m in messages_dict):
        messages_dict.insert(0, {"role": "system", "content": sys_prompt})

    async def event_generator():
        try:
            async for chunk in llm_service.chat_stream(messages_dict, request.model):
                # Yield SSE format
                if chunk:
                    # Escape newlines for SSE data payload
                    data_payload = json.dumps({"chunk": chunk})
                    yield f"data: {data_payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
