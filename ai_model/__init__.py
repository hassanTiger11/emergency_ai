"""
AI Model Package
Contains all AI model supporting functions for transcription and analysis
"""
from ai_model.openai_client import client
from ai_model.transcription import transcribe_with_whisper
from ai_model.analysis import analyze_transcript
from ai_model.prompts import build_prompt
from ai_model.utils import (
    strip_json_fences,
    extract_json_loose,
    timestamp_yyyymmddhhmm,
    save_outputs,
)

__all__ = [
    "client",
    "transcribe_with_whisper",
    "analyze_transcript",
    "build_prompt",
    "strip_json_fences",
    "extract_json_loose",
    "timestamp_yyyymmddhhmm",
    "save_outputs",
]

