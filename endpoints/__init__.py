"""
Endpoints Package
Contains API routes and configuration
"""
from endpoints.config import OUTPUT_DIR, MODEL_TRANSCRIBE, MODEL_CHAT
from endpoints.routes import root, upload_audio, health_check

__all__ = [
    "OUTPUT_DIR",
    "MODEL_TRANSCRIBE",
    "MODEL_CHAT",
    "root",
    "upload_audio",
    "health_check",
]

