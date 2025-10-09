"""
API Configuration
Contains all configuration constants for the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Directory configuration
OUTPUT_DIR = Path(".output")
OUTPUT_DIR.mkdir(exist_ok=True)

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

PROFILE_PICS_DIR = UPLOADS_DIR / "profile_pics"
PROFILE_PICS_DIR.mkdir(exist_ok=True)

# OpenAI Model configuration
MODEL_TRANSCRIBE = "whisper-1"
MODEL_CHAT = "gpt-4o-mini"

# CORS settings
CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Authentication configuration
# Set ENABLE_AUTH=true in .env to enable authentication
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Database configuration (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/emergency_ai")
# Handle Render's postgres:// to postgresql:// conversion
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

