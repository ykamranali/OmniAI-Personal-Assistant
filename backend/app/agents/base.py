from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class AgentResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """
    Base class for all OmniAI Agents.
    Every specialized agent (Voice, Memory, Calendar, etc.) must inherit from this.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def process_request(self, request: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Process a user request and return an AgentResponse.
        """
        pass
    
    async def get_capabilities(self) -> List[str]:
        """
        Return a list of capabilities this agent supports.
        """
        return []

class AgentManager:
    """
    Manages the registration and routing of requests to appropriate agents.
    """
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        self._agents[agent.name] = agent
        print(f"Registered agent: {agent.name}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def get_all_agents(self) -> List[BaseAgent]:
        return list(self._agents.values())

# Global agent manager
agent_manager = AgentManager()
