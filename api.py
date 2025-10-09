"""
Paramedic Assistant API
Main FastAPI application with restructured imports
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from endpoints.config import (
    CORS_ORIGINS, 
    CORS_ALLOW_CREDENTIALS, 
    CORS_ALLOW_METHODS, 
    CORS_ALLOW_HEADERS,
    ENABLE_AUTH,
    UPLOADS_DIR
)
from endpoints.routes import root, upload_audio, health_check, generate_pdf_report

# Import database dependencies (always available, but only used if auth enabled)
from database.models import Paramedic
from database.auth import get_optional_current_user
from database.connection import get_db, is_db_connected, get_db_error

# Initialize database if auth is enabled
if ENABLE_AUTH:
    from database.connection import init_db
    init_db()
    if is_db_connected():
        print("🔐 Authentication enabled")
    else:
        print("⚠️  Authentication enabled but database connection failed")
        print(f"⚠️  Error: {get_db_error()}")
else:
    print("⚠️  Authentication disabled - running in development mode")

# Import auth routes if enabled
if ENABLE_AUTH:
    from endpoints.auth_routes import router as auth_router
    from endpoints.user_routes import router as user_router

# Initialize FastAPI app
app = FastAPI(title="Paramedic Assistant API")

# Request model for PDF generation
class AnalysisData(BaseModel):
    session_id: str
    analysis: dict

# Mount static files
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Include authentication routes if enabled
if ENABLE_AUTH:
    app.include_router(auth_router)
    app.include_router(user_router)


# ---------- API Endpoints ----------
@app.get("/")
async def get_root():
    """Serve the main HTML page or database error page"""
    # Check if database connection failed
    if ENABLE_AUTH and not is_db_connected():
        db_error_file = Path("static/db_error.html")
        if db_error_file.exists():
            return HTMLResponse(content=db_error_file.read_text(encoding='utf-8'))
    return await root()


@app.get("/db-error")
async def get_db_error_page():
    """Serve the database error page"""
    db_error_file = Path("static/db_error.html")
    if db_error_file.exists():
        return HTMLResponse(content=db_error_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Error page not found")


@app.post("/api/upload-audio")
async def post_upload_audio(
    session_id: str = Form(...),
    audio_file: UploadFile = File(...),
    current_user: Optional[Paramedic] = Depends(get_optional_current_user),
    db: Optional[Session] = Depends(get_db)
):
    """
    Accept audio file from browser and process it.
    Browser records audio using MediaRecorder API and uploads it here.
    Saves conversation to database if user is authenticated.
    """
    return await upload_audio(
        session_id=session_id,
        audio_file=audio_file,
        current_user=current_user,
        db=db
    )


@app.post("/api/save-analysis")
async def post_save_analysis(
    session_id: str = Form(...),
    transcript: str = Form(...),
    analysis: str = Form(...),
    current_user: Optional[Paramedic] = Depends(get_optional_current_user),
    db: Optional[Session] = Depends(get_db)
):
    """
    Save or update analysis results to database for authenticated users.
    Idempotent: safe to call multiple times with same session_id.
    """
    from database.models import Conversation as ConversationModel
    import json
    
    try:
        # Parse the analysis JSON string
        analysis_data = json.loads(analysis)
        
        # Save to database if user is authenticated
        conversation_id = None
        if current_user and db:
            try:
                # Check if conversation already exists (idempotent operation)
                conversation = db.query(ConversationModel).filter_by(
                    session_id=session_id
                ).first()
                
                if conversation:
                    # Update existing conversation
                    conversation.transcript = transcript
                    conversation.analysis = analysis_data
                    conversation_id = conversation.id
                    print(f"🔄 Updated existing conversation (ID: {conversation_id}) for session: {session_id[:8]}")
                else:
                    # Create new conversation
                    conversation = ConversationModel(
                        session_id=session_id,
                        paramedic_id=current_user.id,
                        transcript=transcript,
                        analysis=analysis_data
                    )
                    db.add(conversation)
                    print(f"💾 Created new conversation for session: {session_id[:8]}")
                
                db.commit()
                db.refresh(conversation)
                conversation_id = conversation.id
                
            except Exception as db_error:
                print(f"⚠️  Failed to save to database: {str(db_error)}")
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Database save failed: {str(db_error)}")
        
        return {
            "status": "saved",
            "session_id": session_id,
            "conversation_id": conversation_id
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid analysis JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save analysis: {str(e)}")


@app.get("/api/health")
async def get_health_check():
    """Health check endpoint with database status"""
    db_status = is_db_connected() if ENABLE_AUTH else True
    health_data = await health_check()
    
    if isinstance(health_data, dict):
        health_data["database_connected"] = db_status
        health_data["database_error"] = get_db_error() if not db_status else None
    
    return health_data


@app.post("/api/generate-pdf")
async def post_generate_pdf(data: AnalysisData):
    """
    Generate and download a professional PDF report
    """
    return await generate_pdf_report(data.dict())


# ---------- Static HTML Routes ----------
@app.get("/login")
async def get_login():
    """Serve the login HTML page"""
    html_file = Path("static/login.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Login page not found")


@app.get("/login.html")
async def get_login_html():
    """Serve the login HTML page (alternative route)"""
    return await get_login()


@app.get("/settings")
async def get_settings():
    """Serve the settings HTML page"""
    html_file = Path("static/settings.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Settings page not found")


@app.get("/settings.html")
async def get_settings_html():
    """Serve the settings HTML page (alternative route)"""
    return await get_settings()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
