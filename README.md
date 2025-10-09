# 🚑 Paramedic Assistant - Makkah EMS

An AI-powered web application that helps paramedics create medical reports through voice recording. The system transcribes conversations using OpenAI Whisper and analyzes them with GPT-4 to generate structured EMS reports.

## Features

- 🎙️ **One-Click Recording**: Simple web interface with start/stop recording button
- 🗣️ **Multi-Language Support**: Automatically translates Arabic and other languages to English
- 🤖 **AI-Powered Analysis**: Uses GPT-4 to extract structured medical data
- 📋 **Structured Reports**: Generates standardized EMS reports with all relevant fields
- 🎨 **Modern UI**: Beautiful, responsive interface optimized for field use
- 📊 **Severity Assessment**: Automatic triage severity and recommendation
- 🔐 **User Authentication** (Optional): Complete user management system with login, profiles, and conversation history
- 💾 **Database Storage** (Optional): PostgreSQL integration for persistent conversation storage
- 📱 **ChatGPT-Style Sidebar**: Collapsible sidebar for accessing previous sessions (when auth enabled)

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Microphone access

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd emergency_AI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional: Enable authentication (default: false)
   ENABLE_AUTH=false
   
   # If ENABLE_AUTH=true, also configure:
   # JWT_SECRET_KEY=your-secure-secret-key
   # DATABASE_URL=postgresql://user:password@localhost:5432/emergency_ai
   ```
   
   **Note**: For detailed authentication setup, see [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md)

### Running the Application

#### Option 1: Local Python

1. **Start the server**
   ```bash
   python api.py
   ```

   Or with uvicorn:
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the web interface**
   
   Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

#### Option 2: Docker

1. **Build the Docker image:**
   ```bash
   docker build -t paramedic-assistant .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 -e OPENAI_API_KEY=your_api_key_here paramedic-assistant
   ```

3. **Access the application:**
   ```
   http://localhost:8000
   ```

#### Using the Application

- Click the **"Start Recording"** button to begin recording
- Speak naturally about the emergency case
- Click the button again to **stop recording**
- The system will automatically transcribe and analyze
- View the generated report on the screen

## API Endpoints

### `POST /api/start-recording`
Starts audio recording from the microphone.

**Response:**
```json
{
  "status": "recording",
  "message": "Recording started"
}
```

### `POST /api/stop-recording`
Stops recording and processes the audio (transcribe + analyze).

**Response:**
```json
{
  "status": "completed",
  "timestamp": "202510021430",
  "transcript": "Patient is a 45-year-old male...",
  "analysis": {
    "patient": {...},
    "scene": {...},
    "chief_complaint": "Chest pain",
    "severity": "High",
    "recommendation": "Transfer to hospital",
    "form_en": "Complete formatted report..."
  }
}
```

### `GET /api/status`
Returns current recording status.

**Response:**
```json
{
  "recording": true
}
```

## Project Structure

```
emergency_AI/
├── api.py                  # FastAPI backend server
├── transcribe.py           # Original CLI version
├── static/
│   └── index.html         # Web interface
├── output/                # Generated reports and recordings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
└── README.md             # This file
```

## Report Fields

The system extracts and structures the following information:

- **Patient Info**: Name, gender, age, nationality, ID
- **Scene Details**: Date, time, location, case type, mechanism
- **Chief Complaint**: Primary reason for call
- **History (SAMPLE)**: Signs, allergies, medications, past history, last meal, events
- **Vitals**: BP, HR, RR, SpO2, temperature, GCS, pain scale
- **Exam Findings**: Physical examination results
- **Interventions**: Actions taken
- **Severity & Action**: Triage level and recommendations

## Output Files

All recordings and reports are saved in the `output/` directory:

- `recording_YYYYMMDDHHMM.wav` - Audio recording
- `transcript_YYYYMMDDHHMM.txt` - Transcribed text
- `analysis_YYYYMMDDHHMM.json` - Full structured data
- `report_en_YYYYMMDDHHMM.txt` - Formatted English report

## Technologies Used

- **FastAPI**: Modern Python web framework
- **OpenAI Whisper**: Speech-to-text transcription
- **GPT-4o-mini**: Natural language analysis
- **sounddevice**: Audio recording
- **NumPy**: Audio processing

## Command Line Version

The original command-line version is still available in `transcribe.py`:

```bash
python transcribe.py
```

Press Ctrl+C to stop recording in CLI mode.

## Troubleshooting

### Microphone not working
- Ensure microphone permissions are granted
- Check default audio input device in system settings

### OpenAI API errors
- Verify your API key is correct in `.env`
- Check your OpenAI account has sufficient credits
- Ensure you have access to Whisper and GPT-4 models

### Port already in use
Change the port in `api.py` or use:
```bash
uvicorn api:app --port 8080
```

## 🔐 Authentication System

The application includes an **optional authentication system** that can be enabled/disabled via configuration:

### Quick Start (No Authentication)
```bash
ENABLE_AUTH=false  # Default - runs without authentication
```

### With Authentication
```bash
ENABLE_AUTH=true
JWT_SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/emergency_ai
```

When authentication is enabled, the application provides:
- User signup and login
- Secure password hashing
- JWT token authentication
- User profile management with profile pictures
- Conversation history stored in PostgreSQL
- ChatGPT-style sidebar for accessing previous sessions
- Settings page for managing account

**For complete setup instructions**, see [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md)

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Use HTTPS in production environments
- Use strong JWT secret keys (minimum 32 characters) when auth is enabled
- Enable authentication (`ENABLE_AUTH=true`) for production deployments
- Ensure HIPAA compliance when handling patient data

## License

This project is for educational and professional use in emergency medical services.

## 🚀 Deploying to Render

### Quick Deploy

1. **Push your code to GitHub** (make sure `.env` is in `.gitignore`)

2. **Create a new Web Service on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will automatically detect the Dockerfile

3. **Configure Environment Variables:**
   - Add `OPENAI_API_KEY` in the Environment section
   - Paste your actual OpenAI API key

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for the build and deployment to complete
   - Your app will be live at: `https://your-app-name.onrender.com`

### Using render.yaml (Blueprint)

Alternatively, Render can auto-configure using the included `render.yaml`:

1. In Render Dashboard, go to "Blueprints"
2. Click "New Blueprint Instance"
3. Connect your repository
4. Render will read `render.yaml` and set everything up
5. Just add your `OPENAI_API_KEY` in the environment variables

### Important Notes for Render Deployment

- **Free Tier**: Render's free tier spins down after inactivity. First request may be slow.
- **Microphone Access**: The web app requires HTTPS for microphone access (Render provides this automatically)
- **Persistent Storage**: On Render, the `output/` directory is ephemeral. Files are lost on restart. Consider adding cloud storage (S3, etc.) for production.

## Support

For issues or questions, please contact your system administrator or refer to the OpenAI API documentation.

