"""
User Management Routes
Endpoints for user profile management and conversation history
"""
import os
import shutil
import base64
import io
from pathlib import Path
from typing import List
from fastapi import Depends, HTTPException, status, APIRouter, UploadFile, File
from sqlalchemy.orm import Session
from PIL import Image

from endpoints.config import PROFILE_PICS_DIR
from database.connection import get_db
from database.models import Paramedic, Conversation
from database.schemas import (
    ParamedicResponse,
    ParamedicUpdate,
    ConversationResponse,
    ConversationSummary,
    ConversationListResponse,
    PaginationMeta
)
from database.auth import get_current_user, get_password_hash

router = APIRouter(prefix="/api/user", tags=["user"])


def compress_profile_picture(file_content: bytes, max_size: int = 300) -> bytes:
    """
    Compress and resize profile picture for optimal storage and loading.
    
    Args:
        file_content: Raw image file bytes
        max_size: Maximum width/height in pixels (default 300)
    
    Returns:
        Compressed JPEG image bytes
    """
    img = Image.open(io.BytesIO(file_content))
    
    # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img)
        img = background
    
    # Resize maintaining aspect ratio
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # Compress to JPEG with 80% quality
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=80, optimize=True)
    return output.getvalue()


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
        # Read file content
        file_content = await file.read()
        
        # Compress and resize the image (300x300px, 80% quality JPEG)
        compressed_content = compress_profile_picture(file_content, max_size=300)
        
        # Encode compressed image as base64
        base64_data = base64.b64encode(compressed_content).decode('utf-8')
        
        # Always use JPEG MIME type since we compress to JPEG
        mime_type = "image/jpeg"
        
        # Create data URL
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        # Log the compression savings
        original_size = len(file_content)
        compressed_size = len(compressed_content)
        reduction = ((original_size - compressed_size) / original_size) * 100
        print(f"📸 Compressed profile picture: {original_size:,} → {compressed_size:,} bytes ({reduction:.1f}% smaller)")
        
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


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    current_user: Paramedic = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 10
):
    """
    Get paginated conversations for the current user
    
    Parameters:
    - page: Page number (default: 1)
    - limit: Number of conversations per page (default: 10, max: 50)
    
    Returns a summary of conversations with pagination metadata.
    """
    # Validate and cap limit
    limit = min(limit, 50)  # Max 50 per page
    page = max(page, 1)  # Minimum page 1
    
    # Calculate offset
    offset = (page - 1) * limit
    
    # Get total count
    total = db.query(Conversation).filter(
        Conversation.paramedic_id == current_user.id
    ).count()
    
    # Get paginated conversations
    conversations = db.query(Conversation).filter(
        Conversation.paramedic_id == current_user.id
    ).order_by(Conversation.created_at.desc()).offset(offset).limit(limit).all()
    
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
    
    # Create pagination metadata
    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        has_more=offset + limit < total
    )
    
    return ConversationListResponse(
        conversations=summaries,
        pagination=pagination
    )


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


