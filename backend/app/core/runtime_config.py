"""
Runtime configuration store for OmniAI Personal Assistant.
Holds settings that can be changed at runtime via the /system/settings API.
"""
from typing import Any, Dict
from app.core.config import settings


class RuntimeConfig:
    """
    A simple in-memory key/value store for runtime-changeable settings.
    Defaults are seeded from the static `settings` object.
    """

    def __init__(self):
        self._config: Dict[str, Any] = {
            "default_model": settings.DEFAULT_MODEL,
            "ollama_host": settings.OLLAMA_HOST,
            "voice_enabled": True,
            "tts_voice": "en-US-AriaNeural",
            "os_control_allowed": True,
            "chroma_path": settings.CHROMA_PATH,
            # OS automation (vision-loop) hardening
            "os_agent_vision_model": "llama3.2-vision",
            "os_agent_max_steps": 25,
            "os_agent_timeout_seconds": 240,
            # Always-on local voice assistant (wake word + streaming STT/TTS)
            "voice_loop_enabled": True,
            "wake_word": "hey_jarvis",
            "voice_barge_in_enabled": True,
            "voice_vad_energy_threshold": 0.02,
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        return dict(self._config)

    def update(self, updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            if key in self._config:
                self._config[key] = value


# Global singleton
runtime_config = RuntimeConfig()
