import os
import wave
import json
import queue
import signal
import threading
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI

# ============ CONFIG ============
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL_TRANSCRIBE = "whisper-1"   # OpenAI Whisper (API)
MODEL_CHAT = "gpt-4o-mini"       # Analysis / form filling
# ===============================

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------- Audio: record-until-stop (Ctrl+C) ----------
class Recorder:
    def __init__(self, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self._q = queue.Queue()
        self._frames = []
        self._stream = None
        self._stop_event = threading.Event()

    def _callback(self, indata, frames, time_, status):
        if status:
            pass
        self._q.put(indata.copy())

    def start(self):
        self._frames = []
        self._stop_event.clear()
        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype=self.dtype,
            callback=self._callback,
            blocksize=0
        )
        self._stream.start()
        print("🎙️  Recording... Press Ctrl+C to stop.")
        try:
            while not self._stop_event.is_set():
                try:
                    data = self._q.get(timeout=0.1)
                    self._frames.append(data)
                except queue.Empty:
                    pass
        finally:
            self._stream.stop()
            self._stream.close()

    def stop(self):
        self._stop_event.set()

    def get_audio(self) -> np.ndarray:
        if not self._frames:
            return np.zeros((0, self.channels), dtype=self.dtype)
        return np.concatenate(self._frames, axis=0)


def record_until_ctrl_c() -> np.ndarray:
    rec = Recorder()
    def handle_sigint(signum, frame):
        rec.stop()
    prev = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handle_sigint)
    try:
        rec.start()
    finally:
        signal.signal(signal.SIGINT, prev)
    audio = rec.get_audio()
    if audio.ndim == 2 and audio.shape[1] == 1:
        audio = audio.reshape(-1)
    return audio


def write_wav(path: Path, audio: np.ndarray, samplerate=SAMPLE_RATE):
    path = Path(path)
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())


# ---------- Whisper Translation (to English) ----------
def transcribe_with_whisper(wav_path: Path) -> str:
    print("🔁 Sending audio to OpenAI Whisper (English output)...")
    with open(wav_path, "rb") as f:
        resp = client.audio.translations.create(
            model=MODEL_TRANSCRIBE,
            file=f
        )
    return resp.text or ""


# ---------- GPT JSON helpers ----------
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


# ---------- Analysis with ChatGPT ----------
def build_prompt(transcript: str) -> str:
    # Ask for a STRICT JSON and a STRUCTURED English report with fixed section headers and aligned fields.
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


# ---------- Output helpers ----------
def timestamp_yyyymmddhhmm() -> str:
    # YYYYMMDDHHMM (year, month, day, hour, minute)
    return datetime.now().strftime("%Y%m%d%H%M")

def save_outputs(transcript: str, analysis: dict, ts: str):
    (OUTPUT_DIR / f"transcript_{ts}.txt").write_text(transcript, encoding="utf-8")
    (OUTPUT_DIR / f"analysis_{ts}.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    if isinstance(analysis, dict) and analysis.get("form_en"):
        (OUTPUT_DIR / f"report_en_{ts}.txt").write_text(analysis["form_en"], encoding="utf-8")

def print_summary(analysis: dict):
    print("\n" + "="*60)
    if "error" in analysis:
        print("[ChatGPT] JSON parsing failed. Raw output kept in analysis file.")
        return
    print(f"Chief Complaint: {analysis.get('chief_complaint')}")
    print(f"Severity: {analysis.get('severity')}")
    print(f"Recommendation: {analysis.get('recommendation')}")
    reason = analysis.get("reasoning")
    if reason:
        print(f"Reasoning: {reason}")
    print("="*60)
    if analysis.get("form_en"):
        print("\n📋 Structured English Report (preview):\n")
        print(analysis["form_en"][:1500])
        print("\n(Full report saved in output/)\n")


# ---------- Main ----------
def main():
    print("\nParamedic Assistant (Makkah) — Whisper (English) + GPT-4o\n")
    print("Start speaking. Press Ctrl+C when you want to stop.\n")

    # Record until user stops
    audio = record_until_ctrl_c()
    if audio.size == 0:
        print("No audio captured.")
        return

    ts = timestamp_yyyymmddhhmm()
    wav_path = OUTPUT_DIR / f"recording_{ts}.wav"
    write_wav(wav_path, audio, SAMPLE_RATE)
    print(f"✅ Saved WAV: {wav_path}")

    # Transcribe (English)
    transcript = transcribe_with_whisper(wav_path)
    print("\n📝 Transcript (English):\n", transcript)

    # Analyze & produce structured report
    print("\n🧠 Analyzing with ChatGPT...")
    analysis = analyze_transcript(transcript)

    # Save + summarize
    save_outputs(transcript, analysis, ts)
    print_summary(analysis)


if __name__ == "__main__":
    main()
