"""
AI Analysis
Handles transcript analysis using GPT
"""
import json

from ai_model.openai_client import client
from ai_model.prompts import build_prompt
from ai_model.utils import strip_json_fences, extract_json_loose
from endpoints.config import MODEL_CHAT


def analyze_transcript(transcript: str) -> dict:
    """
    Analyze transcript using GPT and extract structured data
    
    Args:
        transcript: The transcribed text to analyze
        
    Returns:
        Dictionary containing structured analysis data
    """
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

