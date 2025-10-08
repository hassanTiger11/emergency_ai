"""
Audio Transcription
Handles audio transcription using OpenAI Whisper
"""
from pathlib import Path

from ai_model.openai_client import client
from endpoints.config import MODEL_TRANSCRIBE


def transcribe_with_whisper(wav_path: Path) -> str:
    """
    Transcribe audio file using OpenAI Whisper
    
    Args:
        wav_path: Path to the WAV audio file
        
    Returns:
        Transcribed text in English
    """
    with open(wav_path, "rb") as f:
        resp = client.audio.translations.create(
            model=MODEL_TRANSCRIBE,
            file=f
        )
    return resp.text or ""

