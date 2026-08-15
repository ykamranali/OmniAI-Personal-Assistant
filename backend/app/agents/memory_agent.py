from typing import Any, Dict
from app.agents.base import BaseAgent, AgentResponse
from app.services.memory import memory_service
import re

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Memory Agent",
            description="Manages long-term semantic memory and requests permissions to store new memories."
        )

    async def process_request(self, request: str, context: Dict[str, Any] = None) -> AgentResponse:
        request_lower = request.lower()
        
        # Check if user explicitly wants to remember something
        if request_lower.startswith("remember that ") or request_lower.startswith("remember:"):
            # Extract what needs to be remembered
            fact = re.sub(r'^(remember that |remember:)\s*', '', request, flags=re.IGNORECASE).strip()
            
            return AgentResponse(
                status="memory_confirmation_required",
                message="Would you like me to store this in long-term memory?",
                data={"fact": fact, "collection": "general"}
            )
            
        # Check if user is querying memory explicitly
        if "what is my" in request_lower or "do you remember" in request_lower:
            # We can perform a similarity search to find relevant facts
            results = memory_service.search_memory("general", request)
            if results:
                facts = "\n".join([f"- {r['text']}" for r in results])
                return AgentResponse(
                    status="success",
                    message=f"I found the following in your memory:\n{facts}",
                    data={"results": results}
                )

        return AgentResponse(status="unknown", message="Not handled by memory agent")

    async def get_capabilities(self) -> list[str]:
        return ["Store memories", "Retrieve memories", "Delete memories"]
