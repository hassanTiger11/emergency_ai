# Project Architecture

This document describes the refactored architecture of the Emergency AI Paramedic Assistant application.

## Project Structure

```
emergency_AI/
├── endpoints/                # API layer
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration constants
│   └── routes.py            # FastAPI route handlers
│
├── ai_model/                 # AI Model layer
│   ├── __init__.py          # Package initialization
│   ├── openai_client.py     # OpenAI client initialization
│   ├── transcription.py     # Whisper transcription functions
│   ├── analysis.py          # GPT analysis functions
│   ├── prompts.py           # Prompt templates
│   └── utils.py             # Helper utilities
│
├── static/                   # Frontend files
│   └── index.html           # Web interface
│
├── .output/                  # Generated outputs (hidden folder)
│   ├── *_transcript.txt     # Transcription files
│   ├── *_analysis.json      # Analysis results
│   └── *_report.txt         # Formatted reports
│
├── api.py                    # Main FastAPI application
├── transcribe.py            # CLI transcription tool
├── requirements.txt         # Python dependencies
└── Dockerfile               # Container configuration
```

## Module Descriptions

### `/endpoints` - API Layer

Contains all FastAPI-related code for the web API:

- **`config.py`**: Application configuration constants
  - Output directory paths
  - OpenAI model names
  - CORS settings
  
- **`routes.py`**: API endpoint handlers
  - `root()`: Serves the main HTML interface
  - `upload_audio()`: Handles audio file uploads and processing
  - `health_check()`: Health check endpoint

### `/ai_model` - AI Model Layer

Contains all AI-related functionality:

- **`openai_client.py`**: OpenAI client initialization
  - Loads environment variables
  - Creates authenticated OpenAI client
  
- **`transcription.py`**: Audio transcription
  - `transcribe_with_whisper()`: Converts audio to English text
  
- **`analysis.py`**: Transcript analysis
  - `analyze_transcript()`: Extracts structured data from transcripts
  
- **`prompts.py`**: Prompt engineering
  - `build_prompt()`: Creates GPT prompts for analysis
  
- **`utils.py`**: Helper functions
  - `strip_json_fences()`: Cleans JSON from markdown
  - `extract_json_loose()`: Extracts JSON from text
  - `timestamp_yyyymmddhhmm()`: Generates timestamps
  - `save_outputs()`: Saves processing results

## Data Flow

```
1. Browser → POST /api/upload-audio
   ├─ Audio file (WAV)
   └─ Session ID

2. endpoints/routes.py → upload_audio()
   ├─ Save audio file
   └─ Call AI pipeline

3. ai_model/transcription.py
   ├─ Send to Whisper API
   └─ Return English transcript

4. ai_model/analysis.py
   ├─ Build prompt (ai_model/prompts.py)
   ├─ Send to GPT API
   └─ Parse JSON response

5. ai_model/utils.py → save_outputs()
   ├─ Save transcript.txt
   ├─ Save analysis.json
   └─ Save report.txt

6. endpoints/routes.py → Return JSON response
   └─ Browser receives results
```

## Benefits of This Architecture

1. **Separation of Concerns**
   - API logic separate from AI logic
   - Each module has a single responsibility

2. **Scalability**
   - Easy to add new endpoints in `endpoints/routes.py`
   - Easy to add new AI functions in `ai_model/`
   - Configuration centralized in `endpoints/config.py`

3. **Maintainability**
   - Clear module boundaries
   - Easy to locate specific functionality
   - Easier to test individual components

4. **Reusability**
   - AI functions can be used by other tools (e.g., `transcribe.py`)
   - Configuration shared across modules
   - Utils can be imported anywhere

## Usage

### Running the API Server

```bash
python api.py
```

Or with uvicorn directly:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Using AI Functions Programmatically

```python
from ai_model import transcribe_with_whisper, analyze_transcript
from pathlib import Path

# Transcribe audio
audio_path = Path("recording.wav")
transcript = transcribe_with_whisper(audio_path)

# Analyze transcript
analysis = analyze_transcript(transcript)
print(analysis["severity"])
```

### Importing Configuration

```python
from endpoints.config import OUTPUT_DIR, MODEL_CHAT

print(f"Outputs saved to: {OUTPUT_DIR}")
print(f"Using model: {MODEL_CHAT}")
```

## Environment Variables

Required in `.env` file:

```
OPENAI_API_KEY=sk-...
```

## Next Steps for Scaling

1. **Database Layer**: Add `database/` module for persistent storage
2. **Authentication**: Add `auth/` module for user authentication
3. **Background Tasks**: Use Celery for async processing
4. **Caching**: Add Redis for response caching
5. **Testing**: Add `tests/` directory with unit tests
6. **Logging**: Add structured logging with log levels
7. **Monitoring**: Add health metrics and monitoring endpoints

