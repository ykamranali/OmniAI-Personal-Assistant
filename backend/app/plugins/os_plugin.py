from app.agents.os_agent import OSAutomationAgent
from app.agents.base import agent_manager

def register_plugin():
    agent = OSAutomationAgent()
    agent_manager.register_agent(agent)
    return agent
