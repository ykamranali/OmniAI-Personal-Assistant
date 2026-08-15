"""
Always-on local voice loop for OmniAI.

Pipeline: wake word -> record until silence -> transcribe (faster-whisper) ->
route through the same agent/LLM stack used by chat -> synthesize speech
(edge-tts) -> play back, interruptibly (barge-in).

Everything in this module runs on-device: audio capture/playback and wake-word
detection happen on a dedicated background thread (they're blocking I/O), and
hop back into the FastAPI asyncio event loop only for the LLM/agent call and
TTS synthesis, which are already async elsewhere in the app.

This is intentionally best-effort and defensive: if optional dependencies
(sounddevice, openwakeword, soundfile) aren't installed or no microphone is
available, `start()` reports a clear error instead of crashing the backend.
"""
import asyncio
import io
import json
import queue
import threading
import time
from typing import Optional

import numpy as np

from app.core.runtime_config import runtime_config

SAMPLE_RATE = 16000
FRAME_SAMPLES = 1280  # 80ms frames — required chunk size for openWakeWord
SILENCE_TIMEOUT_S = 1.2       # trailing silence that ends an utterance
MIN_UTTERANCE_S = 0.3         # ignore blips shorter than this
MAX_UTTERANCE_S = 20.0        # hard cap per utterance, so a stuck mic can't loop forever


class VoiceLoopService:
    """Singleton controlling the always-on wake-word listener."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._broadcast = None  # async callable(str) -> None, wired up by main.py
        self._ww_model = None

    @property
    def is_running(self) -> bool:
        return self._running

    def configure(self, loop: asyncio.AbstractEventLoop, broadcast):
        """Wire the service to the running FastAPI event loop + WS broadcaster."""
        self._loop = loop
        self._broadcast = broadcast

    def start(self) -> Optional[str]:
        """Start the background listener thread. Returns an error string on failure, else None."""
        if self._running:
            return None
        try:
            import sounddevice as sd  # noqa: F401  (import check — fail fast with a clear error)
        except Exception as e:
            return (f"sounddevice is not available ({e}). Install it with "
                    f"'pip install sounddevice' (requires PortAudio) and restart the backend.")
        try:
            import openwakeword  # noqa: F401
        except Exception as e:
            return f"openwakeword is not available ({e}). Install it with 'pip install openwakeword'."

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="omni-voice-loop", daemon=True)
        self._thread.start()
        self._running = True
        return None

    def stop(self):
        if not self._running:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._running = False

    # ── internals ────────────────────────────────────────────────────────────

    def _emit(self, event_type: str, **fields):
        """Broadcast a status/event message to every connected WS client."""
        if not self._loop or not self._broadcast:
            return
        payload = json.dumps({"type": event_type, **fields})
        try:
            asyncio.run_coroutine_threadsafe(self._broadcast(payload), self._loop)
        except Exception as e:
            print(f"[VoiceLoop] Failed to broadcast event: {e}")

    def _vad_threshold(self) -> float:
        try:
            return float(runtime_config.get("voice_vad_energy_threshold", 0.02) or 0.02)
        except (TypeError, ValueError):
            return 0.02

    def _has_speech(self, audio_f32: np.ndarray) -> bool:
        """Simple RMS-energy voice activity detector. Tune via the
        'voice_vad_energy_threshold' runtime setting if it's too sensitive or not
        sensitive enough for your mic/room."""
        if audio_f32.size == 0:
            return False
        rms = float(np.sqrt(np.mean(np.square(audio_f32))))
        return rms > self._vad_threshold()

    def _load_wake_word_model(self):
        from openwakeword.model import Model
        from openwakeword import utils as oww_utils
        try:
            oww_utils.download_models()
        except Exception as e:
            print(f"[VoiceLoop] Could not auto-download openWakeWord models ({e}); "
                  f"continuing in case they're already cached.")
        wake_word = runtime_config.get("wake_word", "hey_jarvis")
        try:
            return Model(wakeword_models=[wake_word])
        except Exception as e:
            print(f"[VoiceLoop] Could not load wake word '{wake_word}' ({e}); "
                  f"falling back to all bundled default wake-word models.")
            return Model()

    def _run(self):
        import sounddevice as sd

        try:
            self._ww_model = self._load_wake_word_model()
        except Exception as e:
            self._emit("voice_loop_error", message=f"Failed to load wake word model: {e}")
            self._running = False
            return

        audio_q: "queue.Queue[np.ndarray]" = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[VoiceLoop] audio status: {status}")
            audio_q.put(indata.copy())

        self._emit("voice_loop_state", state="idle")

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=FRAME_SAMPLES,
                callback=callback,
            ):
                frame_buf = np.zeros((0,), dtype=np.int16)
                while not self._stop_event.is_set():
                    try:
                        chunk = audio_q.get(timeout=0.5).reshape(-1)
                    except queue.Empty:
                        continue
                    frame_buf = np.concatenate([frame_buf, chunk])

                    while len(frame_buf) >= FRAME_SAMPLES:
                        frame = frame_buf[:FRAME_SAMPLES]
                        frame_buf = frame_buf[FRAME_SAMPLES:]

                        scores = self._ww_model.predict(frame)
                        if any(score > 0.5 for score in scores.values()):
                            self._ww_model.reset()
                            self._handle_wake(audio_q)
                            frame_buf = np.zeros((0,), dtype=np.int16)
        except Exception as e:
            self._emit("voice_loop_error", message=str(e))
        finally:
            self._emit("voice_loop_state", state="stopped")
            self._running = False

    def _handle_wake(self, audio_q: "queue.Queue[np.ndarray]"):
        self._emit("voice_loop_state", state="listening")
        utterance = np.zeros((0,), dtype=np.int16)
        last_speech_time = time.monotonic()
        start_time = time.monotonic()

        while True:
            if self._stop_event.is_set():
                return
            if time.monotonic() - start_time > MAX_UTTERANCE_S:
                break
            try:
                chunk = audio_q.get(timeout=0.2).reshape(-1)
            except queue.Empty:
                if utterance.size > SAMPLE_RATE * MIN_UTTERANCE_S and \
                        time.monotonic() - last_speech_time > SILENCE_TIMEOUT_S:
                    break
                continue

            utterance = np.concatenate([utterance, chunk])
            if self._has_speech(chunk.astype(np.float32) / 32768.0):
                last_speech_time = time.monotonic()
            elif utterance.size > SAMPLE_RATE * MIN_UTTERANCE_S and \
                    time.monotonic() - last_speech_time > SILENCE_TIMEOUT_S:
                break

        if utterance.size < SAMPLE_RATE * MIN_UTTERANCE_S:
            self._emit("voice_loop_state", state="idle")
            return

        self._emit("voice_loop_state", state="thinking")

        transcript = self._transcribe(utterance)
        if not transcript.strip():
            self._emit("voice_loop_state", state="idle")
            return
        self._emit("voice_loop_transcript", text=transcript)

        if not self._loop:
            self._emit("voice_loop_state", state="idle")
            return

        future = asyncio.run_coroutine_threadsafe(self._respond(transcript), self._loop)
        try:
            reply_text, audio_bytes = future.result(timeout=120)
        except Exception as e:
            self._emit("voice_loop_error", message=f"Failed to get a response: {e}")
            self._emit("voice_loop_state", state="idle")
            return

        if reply_text:
            self._emit("voice_loop_reply", text=reply_text)
        if audio_bytes:
            self._emit("voice_loop_state", state="speaking")
            self._speak(audio_bytes, audio_q)

        self._emit("voice_loop_state", state="idle")

    def _transcribe(self, pcm_int16: np.ndarray) -> str:
        from app.services.audio import audio_service
        audio_f32 = pcm_int16.astype(np.float32) / 32768.0
        try:
            segments, _info = audio_service.whisper_model.transcribe(audio_f32, beam_size=5)
            return "".join(seg.text for seg in segments).strip()
        except Exception as e:
            print(f"[VoiceLoop] Transcription failed: {e}")
            return ""

    async def _respond(self, transcript: str):
        """Runs on the FastAPI event loop: route through agents/LLM, then synthesize speech."""
        from app.agents.base import agent_manager
        from app.services.llm import llm_service
        from app.services.audio import audio_service

        # Note: no "websocket" key here, so if this turns out to be a risky OS
        # automation request, OSAutomationAgent's confirmation gate will safely
        # decline it rather than trying to negotiate approval over voice.
        context = {"os_control_allowed": runtime_config.get("os_control_allowed", False)}

        reply_text = ""
        for agent in agent_manager.get_all_agents():
            res = await agent.process_request(transcript, context=context)
            if res.status != "unknown":
                reply_text = res.message
                break

        if not reply_text:
            import os
            try:
                prompt_path = os.path.join(os.path.dirname(__file__), "..", "core", "system_prompt.txt")
                with open(prompt_path, "r", encoding="utf-8") as f:
                    sys_prompt = f.read()
            except Exception:
                sys_prompt = "You are Omni Jarvis."
            
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": transcript}
            ]
            reply_text = await llm_service.generate_chat_response(messages)

        audio_bytes = b""
        if runtime_config.get("voice_enabled", True) and reply_text:
            voice = runtime_config.get("tts_voice", "en-US-AriaNeural")
            path = await audio_service.synthesize(reply_text, voice)
            if path:
                import os as _os
                try:
                    with open(path, "rb") as f:
                        audio_bytes = f.read()
                finally:
                    try:
                        _os.remove(path)
                    except OSError:
                        pass

        return reply_text, audio_bytes

    def _speak(self, mp3_bytes: bytes, audio_q: "queue.Queue[np.ndarray]") -> None:
        """Play synthesized speech, interruptible: if the user starts talking again
        (barge-in), stop playback immediately and hand control back to the listener."""
        import sounddevice as sd
        try:
            import soundfile as sf
        except Exception as e:
            print(f"[VoiceLoop] 'soundfile' is not available ({e}); cannot play back speech locally.")
            return

        barge_in = runtime_config.get("voice_barge_in_enabled", True)

        try:
            data, samplerate = sf.read(io.BytesIO(mp3_bytes), dtype="float32")
        except Exception as e:
            print(f"[VoiceLoop] Could not decode TTS audio for playback ({e}). "
                  f"Make sure 'soundfile' is a recent version with libsndfile MP3 support "
                  f"(pip install --upgrade soundfile).")
            return

        # Drop anything queued up while we were synthesizing, so barge-in checks
        # below react to fresh audio, not stale audio from before we started talking.
        while not audio_q.empty():
            try:
                audio_q.get_nowait()
            except queue.Empty:
                break

        channels = data.shape[1] if data.ndim == 2 else 1
        block = max(int(samplerate * 0.1), 1)
        pos = 0
        try:
            with sd.OutputStream(samplerate=samplerate, channels=channels) as stream:
                while pos < len(data):
                    if self._stop_event.is_set():
                        return
                    if barge_in:
                        try:
                            live_chunk = audio_q.get_nowait().reshape(-1).astype(np.float32) / 32768.0
                            if self._has_speech(live_chunk):
                                break  # user is talking over the assistant — stop and listen
                        except queue.Empty:
                            pass
                    stream.write(data[pos:pos + block])
                    pos += block
        except Exception as e:
            print(f"[VoiceLoop] Playback failed: {e}")


voice_loop_service = VoiceLoopService()
