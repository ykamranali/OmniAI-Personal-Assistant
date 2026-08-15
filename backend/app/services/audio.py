import os
import edge_tts
from faster_whisper import WhisperModel
import uuid

# Configuration
MODEL_SIZE = "tiny.en"  # Using tiny.en for speed; can be configurable
TTS_VOICE = "en-US-AriaNeural"  # Default edge-tts voice
TEMP_AUDIO_DIR = "temp_audio"

os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

class AudioService:
    def __init__(self):
        print(f"Loading faster-whisper model '{MODEL_SIZE}'...")
        # device="cpu" is safer on generic Windows setups without CUDA configured
        # Change to device="cuda" if available
        self.whisper_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        
    def transcribe(self, audio_file_path: str) -> str:
        """Transcribe an audio file using faster-whisper."""
        try:
            segments, info = self.whisper_model.transcribe(audio_file_path, beam_size=5)
            text = "".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            print(f"Transcription failed: {e}")
            return ""

    async def synthesize(self, text: str, voice: str = TTS_VOICE) -> str:
        """Synthesize text to speech using edge-tts and save to a temporary file."""
        if not text:
            return ""
            
        file_name = f"{uuid.uuid4()}.mp3"
        file_path = os.path.join(TEMP_AUDIO_DIR, file_name)
        
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(file_path)
            return file_path
        except Exception as e:
            print(f"TTS Synthesis failed: {e}")
            return ""

audio_service = AudioService()
