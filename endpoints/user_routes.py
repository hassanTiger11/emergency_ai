"""
User Management Routes
Endpoints for user profile management and conversation history
"""
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import Depends, HTTPException, status, APIRouter, UploadFile, File
from sqlalchemy.orm import Session

from endpoints.config import PROFILE_PICS_DIR
from database.connection import get_db
from database.models import Paramedic, Conversation
from database.schemas import (
    ParamedicResponse,
    ParamedicUpdate,
    ConversationResponse,
    ConversationSummary
)
from database.auth import get_current_user, get_password_hash

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile", response_model=ParamedicResponse)
async def get_profile(current_user: Paramedic = Depends(get_current_user)):
    """
    Get current user's profile information
    """
    return ParamedicResponse.model_validate(current_user)


@router.put("/profile", response_model=ParamedicResponse)
async def update_profile(
    profile_data: ParamedicUpdate,
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information
    
    Allows updating name, email, age, and password.
    Only provided fields will be updated.
    """
    # Update fields if provided
    if profile_data.name is not None:
        current_user.name = profile_data.name
    
    if profile_data.email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(Paramedic).filter(
            Paramedic.email == profile_data.email,
            Paramedic.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        current_user.email = profile_data.email
    
    if profile_data.age is not None:
        current_user.age = profile_data.age
    
    if profile_data.password is not None:
        current_user.hashed_password = get_password_hash(profile_data.password)
    
    try:
        db.commit()
        db.refresh(current_user)
        return ParamedicResponse.model_validate(current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/profile-picture", response_model=ParamedicResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a profile picture for the current user
    
    Accepts image files (jpg, jpeg, png, gif) up to 5MB.
    """
    # Validate file type
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (5MB max)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()  # Get position (file size)
    file.file.seek(0)  # Reset to beginning
    
    max_size = 5 * 1024 * 1024  # 5MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is 5MB"
        )
    
    try:
        # Read file content and encode as base64
        file_content = await file.read()
        import base64
        base64_data = base64.b64encode(file_content).decode('utf-8')
        
        # Determine MIME type for data URL
        mime_type = "image/jpeg"  # default
        if file_ext in ['.png']:
            mime_type = "image/png"
        elif file_ext in ['.gif']:
            mime_type = "image/gif"
        elif file_ext in ['.webp']:
            mime_type = "image/webp"
        
        # Create data URL
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        # Update user profile with base64 data
        current_user.profile_pic_data = data_url
        # Keep the old URL field for backward compatibility (set to None)
        current_user.profile_pic_url = None
        db.commit()
        db.refresh(current_user)
        
        print(f"💾 Saved profile picture to database for user: {current_user.name}")
        return ParamedicResponse.model_validate(current_user)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


@router.delete("/profile-picture", response_model=ParamedicResponse)
async def delete_profile_picture(
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's profile picture
    """
    # Clear both URL and base64 data
    current_user.profile_pic_url = None
    current_user.profile_pic_data = None
    db.commit()
    db.refresh(current_user)
    
    return ParamedicResponse.model_validate(current_user)


@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for the current user
    
    Returns a summary of all conversations, sorted by most recent first.
    """
    conversations = db.query(Conversation).filter(
        Conversation.paramedic_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()
    
    # Convert to summary format
    summaries = []
    for conv in conversations:
        summary = ConversationSummary(
            id=conv.id,
            session_id=conv.session_id,
            created_at=conv.created_at
        )
        
        # Extract patient name and chief complaint from analysis
        if isinstance(conv.analysis, dict):
            summary.patient_name = conv.analysis.get('patient_name')
            summary.chief_complaint = conv.analysis.get('chief_complaint')
        
        summaries.append(summary)
    
    return summaries


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation by ID
    
    Only returns conversations that belong to the current user.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.paramedic_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse.model_validate(conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific conversation
    
    Only allows deleting conversations that belong to the current user.
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.paramedic_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"status": "success", "message": "Conversation deleted"}


