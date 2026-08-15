from app.agents.browser_agent import BrowserAgent
from app.agents.base import agent_manager

def register_plugin():
    agent = BrowserAgent()
    agent_manager.register_agent(agent)
    return agent
