import httpx
import json
from typing import AsyncGenerator, List, Dict, Any
from app.core.config import settings

class OllamaService:
    """
    Service for interacting with local Ollama models.
    """
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.default_model = settings.DEFAULT_MODEL

    async def get_models(self) -> List[Dict[str, Any]]:
        """
        Fetch available models from the local Ollama instance.
        """
        url = f"{self.host}/api/tags"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                return response.json().get("models", [])
            except Exception as e:
                print(f"Failed to fetch Ollama models: {e}")
                return []

    async def generate_response(self, prompt: str, model: str = None) -> str:
        """
        Generate a complete response from the local LLM.
        """
        target_model = model or self.default_model
        url = f"{self.host}/api/generate"
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=300.0)
                response.raise_for_status()
                return response.json().get("response", "")
            except Exception as e:
                print(f"Ollama generation failed: {e}")
                return f"Error communicating with local AI model: {e}"

    async def generate_stream(self, prompt: str, model: str = None) -> AsyncGenerator[str, None]:
        """
        Stream response from local LLM using simple prompt.
        """
        target_model = model or self.default_model
        url = f"{self.host}/api/generate"
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": True
        }
        
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("POST", url, json=payload, timeout=300.0) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            yield data.get("response", "")
            except Exception as e:
                print(f"Ollama streaming failed: {e}")
                yield f"Error: {e}"

    async def generate_chat_response(self, messages: List[Dict[str, Any]], model: str = None) -> str:
        """
        Generate a complete response from the local LLM using the chat API.
        """
        target_model = model or self.default_model
        url = f"{self.host}/api/chat"
        
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg.get("role"),
                "content": msg.get("content", "")
            }
            if "images" in msg and msg["images"]:
                formatted_msg["images"] = msg["images"]
            formatted_messages.append(formatted_msg)
            
        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=300.0)
                response.raise_for_status()
                return response.json().get("message", {}).get("content", "")
            except Exception as e:
                print(f"Ollama chat generation failed: {e}")
                return ""

    async def chat_stream(self, messages: List[Dict[str, str]], model: str = None) -> AsyncGenerator[str, None]:
        """
        Stream response using the chat API (supports history).
        """
        target_model = model or self.default_model
        url = f"{self.host}/api/chat"
        # Ensure messages conform to Ollama's format (role, content, and optionally images)
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg.get("role"),
                "content": msg.get("content", "")
            }
            if "images" in msg and msg["images"]:
                formatted_msg["images"] = msg["images"]
            formatted_messages.append(formatted_msg)

        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "stream": True
        }
        
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("POST", url, json=payload, timeout=300.0) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
            except Exception as e:
                print(f"Ollama chat streaming failed: {e}")
                yield f"Error: {e}"

llm_service = OllamaService()
