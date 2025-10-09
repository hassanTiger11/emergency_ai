"""
API Routes
All FastAPI endpoints for the application
"""
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session

from endpoints.config import OUTPUT_DIR, ENABLE_AUTH
from ai_model.transcription import transcribe_with_whisper
from ai_model.analysis import analyze_transcript
from ai_model.utils import timestamp_yyyymmddhhmm, save_outputs
from endpoints.pdf_generator import create_professional_report_pdf
from database.auth import get_optional_current_user
from database.models import Paramedic, Conversation as ConversationModel
from database.connection import get_db


async def root():
    """Serve the main HTML page"""
    html_file = Path("static/index.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
    return {"message": "Paramedic Assistant API is running"}


async def upload_audio(
    session_id: str,
    audio_file: UploadFile,
    current_user: Optional[Paramedic] = None,
    db: Optional[Session] = None
):
    """
    Accept audio file from browser and process it.
    Browser records audio using MediaRecorder API and uploads it here.
    
    If authentication is enabled and user is logged in, saves conversation to database.
    
    Args:
        session_id: Unique session identifier
        audio_file: Uploaded audio file
        current_user: Authenticated user (if logged in)
        db: Database session (if available)
    """
    try:
        # Generate timestamp
        ts = timestamp_yyyymmddhhmm()
        short_session = session_id[:8]
        
        # Save uploaded audio file
        wav_path = OUTPUT_DIR / f"{short_session}_{ts}_recording.wav"
        with wav_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        print(f"💾 Saved audio: {wav_path.name}")
        
        # Transcribe
        print(f"🔄 Transcribing audio for session: {short_session}...")
        transcript = transcribe_with_whisper(wav_path)
        
        # Analyze
        print(f"🧠 Analyzing transcript for session: {short_session}...")
        analysis = analyze_transcript(transcript)
        
        # Save outputs to file system
        save_outputs(transcript, analysis, session_id, ts)
        
        # Save to database if auth is enabled and user is logged in
        conversation_id = None
        if ENABLE_AUTH and current_user and db:
            try:
                # Check if conversation already exists (idempotent operation)
                conversation = db.query(ConversationModel).filter_by(
                    session_id=session_id
                ).first()
                
                if conversation:
                    # Update existing conversation
                    conversation.transcript = transcript
                    conversation.analysis = analysis
                    conversation_id = conversation.id
                    print(f"🔄 Updated existing conversation (ID: {conversation_id}) for session: {short_session}")
                else:
                    # Create new conversation
                    conversation = ConversationModel(
                        session_id=session_id,
                        paramedic_id=current_user.id,
                        transcript=transcript,
                        analysis=analysis
                    )
                    db.add(conversation)
                    print(f"💾 Created new conversation for session: {short_session}")
                
                db.commit()
                db.refresh(conversation)
                conversation_id = conversation.id
                
            except Exception as db_error:
                print(f"⚠️  Failed to save to database: {str(db_error)}")
                db.rollback()
                # Continue anyway - file system backup exists
        elif ENABLE_AUTH:
            print("🔓 Auth enabled but user not logged in - skipping database save")
        
        print(f"✅ Completed processing for session: {short_session}")
        
        response_data = {
            "status": "completed",
            "session_id": session_id,
            "timestamp": ts,
            "transcript": transcript,
            "analysis": analysis
        }
        
        if conversation_id:
            response_data["conversation_id"] = conversation_id
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        print(f"❌ Error processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Paramedic Assistant API"}


async def generate_pdf_report(analysis_data: dict):
    """
    Generate and return a professional PDF report
    """
    try:
        # Generate timestamp for filename
        ts = timestamp_yyyymmddhhmm()
        session_id = analysis_data.get('session_id', 'unknown')[:8]
        
        # Create PDF filename
        pdf_filename = f"{session_id}_{ts}_medical_report.pdf"
        pdf_path = OUTPUT_DIR / pdf_filename
        
        # Generate PDF
        create_professional_report_pdf(analysis_data, str(pdf_path))
        
        print(f"📄 Generated PDF report: {pdf_filename}")
        
        # Return the PDF file for download
        return FileResponse(
            path=str(pdf_path),
            filename=pdf_filename,
            media_type='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

