from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import asyncio
import psutil
from app.plugins.manager import plugin_manager
from app.agents.base import agent_manager
from app.agents.os_agent import OSAutomationAgent
from app.agents.browser_agent import BrowserAgent
from app.agents.memory_agent import MemoryAgent
from app.core.runtime_config import runtime_config
from app.services.voice_loop import voice_loop_service

from app.api.routers import chat, memory, models, system, voice

async def system_stats_task():
    while True:
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            ram_percent = mem.percent
            ram_used = round(mem.used / (1024**3), 1)
            ram_total = round(mem.total / (1024**3), 1)
            
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = round(disk.free / (1024**3), 1)
            
            agents_count = len(agent_manager.get_all_agents())
            
            stats = {
                "type": "system_stats",
                "cpu": cpu,
                "ram_percent": ram_percent,
                "ram_used": ram_used,
                "ram_total": ram_total,
                "disk_percent": disk_percent,
                "disk_free": disk_free,
                "active_agents": agents_count
            }
            await manager.broadcast(json.dumps(stats))
        except Exception as e:
            print(f"Error in stats task: {e}")
        await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("Starting OmniAI Personal Assistant Backend...")
    plugin_manager.load_plugins()
    # Register core agents
    agent_manager.register_agent(OSAutomationAgent())
    agent_manager.register_agent(BrowserAgent())
    agent_manager.register_agent(MemoryAgent())
    # Start the system stats broadcast task
    task = asyncio.create_task(system_stats_task())

    # Wire the always-on local voice loop to this event loop + the WS broadcaster,
    # and auto-start it only if the user previously enabled it (default: off).
    voice_loop_service.configure(asyncio.get_running_loop(), manager.broadcast)
    if runtime_config.get("voice_loop_enabled", False):
        err = voice_loop_service.start()
        if err:
            print(f"Could not auto-start voice loop: {err}")

    yield
    # Shutdown actions
    task.cancel()
    voice_loop_service.stop()
    print("Shutting down OmniAI Personal Assistant Backend...")

app = FastAPI(
    title="OmniAI Personal Assistant API",
    description="Backend API for OmniAI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to OmniAI Personal Assistant API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    os_control_allowed = False
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WebSocket message: {data}")
            
            # Parse request
            request_text = data
            try:
                msg_json = json.loads(data)
                if msg_json.get("type") == "config":
                    if "os_control_allowed" in msg_json:
                        os_control_allowed = msg_json["os_control_allowed"]
                        runtime_config.set("os_control_allowed", os_control_allowed)
                        print(f"OS control allowed: {os_control_allowed}")
                    continue
                if msg_json.get("type") == "confirm_action":
                    # A confirmation reply arrived with nothing waiting on it
                    # (e.g. stale/duplicate click) — nothing to do, ignore it.
                    continue
                request_text = msg_json.get("request", data)
            except Exception:
                pass
            
            # Route to registered agents
            response = None
            context = {"os_control_allowed": os_control_allowed, "websocket": websocket}
            for agent in agent_manager.get_all_agents():
                res = await agent.process_request(request_text, context=context)
                if res.status != "unknown":
                    response = res
                    break
            
            if response:
                await websocket.send_text(response.model_dump_json())
            else:
                # Fallback to general conversational AI
                from app.services.llm import llm_service
                print("No specialized agent claimed request, falling back to LLM...")
                
                await websocket.send_text(json.dumps({"type": "stream_start"}))
                
                full_response = ""
                try:
                    import os
                    prompt_path = os.path.join(os.path.dirname(__file__), "core", "system_prompt.txt")
                    try:
                        with open(prompt_path, "r", encoding="utf-8") as f:
                            sys_prompt = f.read()
                    except Exception:
                        sys_prompt = "You are Omni Jarvis."
                    
                    messages = [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": request_text}
                    ]
                    async for chunk in llm_service.chat_stream(messages):
                        if chunk:
                            full_response += chunk
                            await websocket.send_text(json.dumps({
                                "type": "stream_chunk",
                                "chunk": chunk
                            }))
                except Exception as e:
                    print(f"Streaming error: {e}")
                
                await websocket.send_text(json.dumps({
                    "type": "stream_end",
                    "full_response": full_response
                }))
    except Exception as e:
        if websocket in manager.active_connections:
            manager.disconnect(websocket)
        print(f"Client disconnected from WebSocket: {e}")

