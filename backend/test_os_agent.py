import asyncio
from app.agents.os_agent import OSAutomationAgent
from app.services.llm import llm_service

async def main():
    agent = OSAutomationAgent()
    prompt = agent.SYSTEM_PROMPT if hasattr(agent, 'SYSTEM_PROMPT') else """You are an Autonomous OS Agent.
Your job is to convert the user's request into precise OS tool commands.
If the user's request is a general question or conversational and does NOT require OS action, you must output exactly: {}

Otherwise, output ONLY a single JSON object representing the action to take.
Available actions:
1. Launch an application:
   {"action": "launch", "app": "notepad"}
2. Type text on the keyboard:
   {"action": "type", "text": "hello world"}
3. Press a specific key (e.g., enter, tab, win):
   {"action": "press", "key": "enter"}
4. Take a screenshot:
   {"action": "screenshot"}

Output ONLY valid JSON and absolutely no other text.
User request: """
    
    prompt += "open notepad and type hello world"
    llm_output = await llm_service.generate_response(prompt)
    print("--- RAW LLM OUTPUT ---")
    print(llm_output)
    print("----------------------")

if __name__ == "__main__":
    asyncio.run(main())
