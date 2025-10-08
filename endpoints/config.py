"""
API Configuration
Contains all configuration constants for the application
"""
from pathlib import Path

# Directory configuration
OUTPUT_DIR = Path(".output")
OUTPUT_DIR.mkdir(exist_ok=True)

# OpenAI Model configuration
MODEL_TRANSCRIBE = "whisper-1"
MODEL_CHAT = "gpt-4o-mini"

# CORS settings
CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

