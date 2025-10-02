import os
import wave
import json
import queue
import threading
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============ CONFIG ============
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL_TRANSCRIBE = "whisper-1"
MODEL_CHAT = "gpt-4o-mini"
# ===============================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Paramedic Assistant API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Audio Recording Class ----------
class Recorder:
    """Thread-safe audio recorder for a single session"""
    def __init__(self, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self._q = queue.Queue()
        self._frames = []
        self._stream = None
        self._recording = False
        self._thread = None

    def _callback(self, indata, frames, time_, status):
        if status:
            pass
        self._q.put(indata.copy())

    def _record_loop(self):
        while self._recording:
            try:
                data = self._q.get(timeout=0.1)
                self._frames.append(data)
            except queue.Empty:
                pass

    def start(self):
        if self._recording:
            return
        self._frames = []
        self._recording = True
        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype=self.dtype,
            callback=self._callback,
            blocksize=0
        )
        self._stream.start()
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._recording:
            return
        self._recording = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._stream:
            self._stream.stop()
            self._stream.close()

    def is_recording(self):
        return self._recording

    def get_audio(self) -> np.ndarray:
        if not self._frames:
            return np.zeros((0, self.channels), dtype=self.dtype)
        audio = np.concatenate(self._frames, axis=0)
        if audio.ndim == 2 and audio.shape[1] == 1:
            audio = audio.reshape(-1)
        return audio


# ---------- Session Management ----------
class SessionManager:
    """Manages multiple recording sessions (one per device/browser)"""
    def __init__(self):
        self.sessions: Dict[str, Recorder] = {}
        self._lock = threading.Lock()
    
    def get_or_create_recorder(self, session_id: str) -> Recorder:
        """Get existing recorder for session or create new one"""
        with self._lock:
            if session_id not in self.sessions:
                print(f"📱 Creating new session: {session_id}")
                self.sessions[session_id] = Recorder()
            return self.sessions[session_id]
    
    def get_recorder(self, session_id: str) -> Optional[Recorder]:
        """Get existing recorder for session (or None)"""
        return self.sessions.get(session_id)
    
    def cleanup_session(self, session_id: str):
        """Remove a session and its recorder"""
        with self._lock:
            if session_id in self.sessions:
                recorder = self.sessions[session_id]
                if recorder.is_recording():
                    recorder.stop()
                del self.sessions[session_id]
                print(f"🗑️  Cleaned up session: {session_id}")
    
    def get_active_sessions(self) -> list:
        """Get list of active session IDs"""
        return list(self.sessions.keys())
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self.sessions)

# Global session manager (handles all devices)
session_manager = SessionManager()


# ---------- Request/Response Models ----------
class SessionRequest(BaseModel):
    session_id: str


# ---------- Helper Functions ----------
def write_wav(path: Path, audio: np.ndarray, samplerate=SAMPLE_RATE):
    path = Path(path)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())


def transcribe_with_whisper(wav_path: Path) -> str:
    with open(wav_path, "rb") as f:
        resp = client.audio.translations.create(
            model=MODEL_TRANSCRIBE,
            file=f
        )
    return resp.text or ""


def strip_json_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.lstrip("`")
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.rstrip("`").strip()
    return t


def extract_json_loose(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text


def build_prompt(transcript: str) -> str:
    return f"""
You are a paramedic assistant for field triage in Makkah.
Read the conversation transcript (English).
Extract structured data to fill the official EMS report and provide triage severity + action.

Return ONLY valid JSON with this schema:

{{
  "patient": {{
    "name": "string|null",
    "gender": "Male|Female|null",
    "age": "string|null",
    "nationality": "Saudi|Non-Saudi|null",
    "ID": "string|null"
  }},
  "scene": {{
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "caller_phone": "string|null",
    "location": "string|null",
    "case_code": "string|null",
    "case_type": "Medical|Trauma|null",
    "mechanism": "Fall|Traffic Accident|Stab|Burn|Choking|Other|null"
  }},
  "chief_complaint": "string",
  "history": {{
    "onset": "string|null",
    "duration": "string|null",
    "associated_symptoms": ["string", "..."],
    "allergies": "string|null",
    "medications": "string|null",
    "past_history": "string|null",
    "last_meal": "string|null",
    "events": "string|null"
  }},
  "vitals": {{
    "bp_systolic": "number|null",
    "bp_diastolic": "number|null",
    "hr": "number|null",
    "rr": "number|null",
    "spo2": "number|null",
    "temp": "number|null",
    "gcs": "number|null",
    "pain_scale_0_10": "number|null"
  }},
  "exam": "string|null",
  "interventions": ["string", "..."],
  "severity": "Very High|High|Medium|Low|Very Low",
  "recommendation": "Transfer to hospital|Treat on site",
  "reasoning": "Short rationale in English",
  "form_en": "A structured, sectioned, aligned English report as plain text. Use the exact section headers below."
}}

When constructing "form_en", use EXACTLY these section headers and colon-aligned fields:

==== PATIENT INFO ====
Name              : <value or N/A>
Gender            : <value or N/A>
Age               : <value or N/A>
Nationality       : <value or N/A>
ID                : <value or N/A>

==== SCENE DETAILS ====
Date              : <YYYY-MM-DD or N/A>
Time              : <HH:MM or N/A>
Caller Phone      : <value or N/A>
Location          : <value or N/A>
Case Code         : <value or N/A>
Case Type         : <Medical|Trauma or N/A>
Mechanism         : <value or N/A>

==== CHIEF COMPLAINT ====
<one concise line>

==== HISTORY (SAMPLE) ====
Onset             : <value or N/A>
Duration          : <value or N/A>
Associated Sx     : <comma-separated or N/A>
Allergies         : <value or N/A>
Medications       : <value or N/A>
Past History      : <value or N/A>
Last Meal         : <value or N/A>
Events            : <value or N/A>

==== VITALS ====
BP (Sys/Dia)      : <120/80 or N/A>
Heart Rate        : <value or N/A>
Resp Rate         : <value or N/A>
SpO2              : <value% or N/A>
Temperature       : <value°C or N/A>
GCS               : <value or N/A>
Pain (0-10)       : <value or N/A>

==== EXAM FINDINGS ====
<concise bullet-like text or N/A>

==== INTERVENTIONS ====
- <item or N/A>

==== SEVERITY & ACTION ====
Severity          : <Very High|High|Medium|Low|Very Low>
Recommendation    : <Transfer to hospital|Treat on site>
Reasoning         : <one concise English line>

Rules:
- If data is missing, use N/A or null (in JSON), but do not invent facts.
- High-risk red flags ⇒ Very High/High & Transfer.
- Stable minor issues ⇒ Treat on site if safe.

Transcript:
\"\"\"{transcript}\"\"\"
"""


def analyze_transcript(transcript: str) -> dict:
    prompt = build_prompt(transcript)
    resp = client.chat.completions.create(
        model=MODEL_CHAT,
        temperature=0,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON. No prose."},
            {"role": "user", "content": prompt}
        ]
    )
    raw = resp.choices[0].message.content or ""
    text = strip_json_fences(raw)

    try:
        return json.loads(text)
    except Exception:
        try_text = extract_json_loose(text)
        try:
            return json.loads(try_text)
        except Exception:
            return {"error": "Could not parse JSON", "raw": raw}


def timestamp_yyyymmddhhmm() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def save_outputs(transcript: str, analysis: dict, session_id: str, ts: str):
    """Save outputs with session ID prefix for tracking"""
    # Shorten session ID to first 8 chars for filename
    short_session = session_id[:8]
    
    (OUTPUT_DIR / f"{short_session}_{ts}_transcript.txt").write_text(transcript, encoding="utf-8")
    (OUTPUT_DIR / f"{short_session}_{ts}_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if isinstance(analysis, dict) and analysis.get("form_en"):
        (OUTPUT_DIR / f"{short_session}_{ts}_report.txt").write_text(analysis["form_en"], encoding="utf-8")


# ---------- API Endpoints ----------
@app.get("/")
async def root():
    """Serve the main HTML page"""
    html_file = Path("static/index.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
    return {"message": "Paramedic Assistant API is running"}


@app.post("/api/start-recording")
async def start_recording(request: SessionRequest):
    """Start audio recording for a specific session"""
    session_id = request.session_id
    
    # Get or create recorder for this session
    recorder = session_manager.get_or_create_recorder(session_id)
    
    if recorder.is_recording():
        raise HTTPException(status_code=400, detail="Recording already in progress for this session")
    
    try:
        recorder.start()
        print(f"🎙️  Started recording for session: {session_id[:8]}...")
        return {
            "status": "recording",
            "message": "Recording started",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")


@app.post("/api/stop-recording")
async def stop_recording(request: SessionRequest):
    """Stop recording and process the audio for a specific session"""
    session_id = request.session_id
    
    # Get recorder for this session
    recorder = session_manager.get_recorder(session_id)
    
    if not recorder:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not recorder.is_recording():
        raise HTTPException(status_code=400, detail="No recording in progress for this session")
    
    try:
        # Stop recording
        recorder.stop()
        audio = recorder.get_audio()
        
        if audio.size == 0:
            raise HTTPException(status_code=400, detail="No audio captured")
        
        # Generate timestamp
        ts = timestamp_yyyymmddhhmm()
        short_session = session_id[:8]
        
        # Save audio with session prefix
        wav_path = OUTPUT_DIR / f"{short_session}_{ts}_recording.wav"
        write_wav(wav_path, audio, SAMPLE_RATE)
        print(f"💾 Saved audio: {wav_path.name}")
        
        # Transcribe
        print(f"🔄 Transcribing audio for session: {short_session}...")
        transcript = transcribe_with_whisper(wav_path)
        
        # Analyze
        print(f"🧠 Analyzing transcript for session: {short_session}...")
        analysis = analyze_transcript(transcript)
        
        # Save outputs
        save_outputs(transcript, analysis, session_id, ts)
        print(f"✅ Completed processing for session: {short_session}")
        
        return JSONResponse(content={
            "status": "completed",
            "session_id": session_id,
            "timestamp": ts,
            "transcript": transcript,
            "analysis": analysis
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing session {session_id[:8]}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/api/status")
async def get_status(request: SessionRequest):
    """Get current recording status for a specific session"""
    session_id = request.session_id
    recorder = session_manager.get_recorder(session_id)
    
    return {
        "session_id": session_id,
        "recording": recorder.is_recording() if recorder else False,
        "session_exists": recorder is not None
    }


@app.get("/api/sessions")
async def get_sessions():
    """Get info about all active sessions (admin/debug endpoint)"""
    sessions = session_manager.get_active_sessions()
    return {
        "active_sessions": len(sessions),
        "session_ids": [s[:8] + "..." for s in sessions]  # Show first 8 chars
    }


@app.post("/api/cleanup-session")
async def cleanup_session(request: SessionRequest):
    """Manually cleanup a session (optional)"""
    session_id = request.session_id
    session_manager.cleanup_session(session_id)
    return {"status": "cleaned", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

