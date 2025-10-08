# Use Python 3.11 slim image (UV works best with 3.11)
FROM python:3.11-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# No system dependencies needed for basic PDF generation

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using UV (much faster than pip)
RUN uv pip install --system --no-cache -r requirements.txt

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

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]