"""
Voice API router for OmniAI Personal Assistant.
Provides endpoints for speech-to-text (STT) transcription and text-to-speech (TTS) synthesis.
"""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/voice", tags=["voice"])

TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accept an audio file upload and transcribe it using faster-whisper.
    Returns the transcribed text.
    """
    try:
        # Save uploaded file to a temp path
        temp_path = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}_{file.filename}")
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        # Lazy import to avoid loading Whisper unless this endpoint is actually called
        try:
            from app.services.audio import audio_service
            text = audio_service.transcribe(temp_path)
        except Exception as model_error:
            raise HTTPException(
                status_code=503,
                detail=f"Whisper model unavailable: {str(model_error)}"
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return {"status": "success", "text": text}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest):
    """
    Convert text to speech using edge-tts.
    Returns the path to the synthesized audio file.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        from app.services.audio import audio_service
        file_path = await audio_service.synthesize(request.text, request.voice)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="TTS synthesis produced no output")

        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=os.path.basename(file_path),
            background=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.get("/loop/status")
async def voice_loop_status():
    """Report whether the always-on local wake-word voice loop is currently running."""
    from app.services.voice_loop import voice_loop_service
    return {"status": "success", "data": {"running": voice_loop_service.is_running}}


@router.get("/voices")
async def list_voices():
    """Return a curated list of available edge-tts voices."""
    voices = [
        {"id": "en-US-AriaNeural", "name": "Aria (US Female)", "language": "en-US"},
        {"id": "en-US-GuyNeural", "name": "Guy (US Male)", "language": "en-US"},
        {"id": "en-US-JennyNeural", "name": "Jenny (US Female)", "language": "en-US"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia (UK Female)", "language": "en-GB"},
        {"id": "en-GB-RyanNeural", "name": "Ryan (UK Male)", "language": "en-GB"},
        {"id": "en-AU-NatashaNeural", "name": "Natasha (AU Female)", "language": "en-AU"},
        {"id": "en-IN-NeerjaNeural", "name": "Neerja (IN Female)", "language": "en-IN"},
    ]
    return {"status": "success", "data": voices}
