"""
Utility Functions
Helper functions for AI model operations
"""
import json
from pathlib import Path
from datetime import datetime

from endpoints.config import OUTPUT_DIR


def strip_json_fences(text: str) -> str:
    """
    Remove markdown code fences from JSON text
    
    Args:
        text: Text that may contain markdown code fences
        
    Returns:
        Clean text without fences
    """
    t = text.strip()
    if t.startswith("```"):
        t = t.lstrip("`")
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.rstrip("`").strip()
    return t


def extract_json_loose(text: str) -> str:
    """
    Extract JSON object from text by finding first { and last }
    
    Args:
        text: Text containing a JSON object
        
    Returns:
        Extracted JSON string
    """
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text


def timestamp_yyyymmddhhmm() -> str:
    """
    Generate timestamp string in YYYYMMDDHHMMSS format
    
    Returns:
        Timestamp string
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


def save_outputs(transcript: str, analysis: dict, session_id: str, ts: str):
    """
    Save outputs with session ID prefix for tracking
    
    Args:
        transcript: The transcribed text
        analysis: The analysis results
        session_id: Session identifier
        ts: Timestamp string
    """
    short_session = session_id[:8]
    
    (OUTPUT_DIR / f"{short_session}_{ts}_transcript.txt").write_text(
        transcript, encoding="utf-8"
    )
    (OUTPUT_DIR / f"{short_session}_{ts}_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if isinstance(analysis, dict) and analysis.get("form_en"):
        (OUTPUT_DIR / f"{short_session}_{ts}_report.txt").write_text(
            analysis["form_en"], encoding="utf-8"
        )

