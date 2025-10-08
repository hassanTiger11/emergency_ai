# Use Python 3.11 slim image (UV works best with 3.11)
FROM python:3.11-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Install system dependencies for audio and PDF generation
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    libsndfile1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgstreamer1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy UV configuration files first for better caching
COPY pyproject.toml uv.lock* ./

# Install dependencies using UV (much faster than pip)
RUN uv sync --frozen --no-dev

# Copy application files
COPY api.py .
COPY endpoints/ ./endpoints/
COPY ai_model/ ./ai_model/
COPY static/ ./static/
COPY .env* ./

# Create output directory
RUN mkdir -p .output

# Expose port
EXPOSE 8000

# Use UV to run the application
CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]