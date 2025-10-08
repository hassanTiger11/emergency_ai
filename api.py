"""
Paramedic Assistant API
Main FastAPI application with restructured imports
"""
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from endpoints.config import CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, CORS_ALLOW_METHODS, CORS_ALLOW_HEADERS
from endpoints.routes import root, upload_audio, health_check, generate_pdf_report

# Initialize FastAPI app
app = FastAPI(title="Paramedic Assistant API")

# Request model for PDF generation
class AnalysisData(BaseModel):
    session_id: str
    analysis: dict

# Mount static files
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)


# ---------- API Endpoints ----------
@app.get("/")
async def get_root():
    """Serve the main HTML page"""
    return await root()


@app.post("/api/upload-audio")
async def post_upload_audio(
    session_id: str = Form(...),
    audio_file: UploadFile = File(...)
):
    """
    Accept audio file from browser and process it.
    Browser records audio using MediaRecorder API and uploads it here.
    """
    return await upload_audio(session_id=session_id, audio_file=audio_file)


@app.get("/api/health")
async def get_health_check():
    """Health check endpoint"""
    return await health_check()


@app.post("/api/generate-pdf")
async def post_generate_pdf(data: AnalysisData):
    """
    Generate and download a professional PDF report
    """
    return await generate_pdf_report(data.dict())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
