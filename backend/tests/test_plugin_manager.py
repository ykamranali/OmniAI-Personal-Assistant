import pytest
from app.agents.base import agent_manager
from app.plugins.manager import plugin_manager

def test_plugin_loading():
    # Clear agents first to make test independent of other tests
    agent_manager._agents.clear()
    
    # Verify that initially there are no registered agents
    agents_before = agent_manager.get_all_agents()
    assert len(agents_before) == 0, f"Expected 0 agents initially, found {len(agents_before)}"
    
    # Load plugins
    plugin_manager.load_plugins()
    
    # Verify that the agents were registered
    agents_after = agent_manager.get_all_agents()
    assert len(agents_after) == 2, f"Expected 2 agents after loading plugins, found {len(agents_after)}"
    
    # Verify we can retrieve them by name
    browser_agent = agent_manager.get_agent("BrowserAgent")
    assert browser_agent is not None
    assert browser_agent.name == "BrowserAgent"
    
    os_agent = agent_manager.get_agent("OSAutomationAgent")
    assert os_agent is not None
    assert os_agent.name == "OSAutomationAgent"
