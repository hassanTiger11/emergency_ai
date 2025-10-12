"""
Pydantic Schemas
Request/Response models for API validation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ============ Paramedic Schemas ============

class ParamedicBase(BaseModel):
    """Base paramedic schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    medical_id: Optional[str] = Field(None, max_length=50)
    national_id: Optional[str] = Field(None, max_length=50)
    age: Optional[int] = Field(None, ge=18, le=100)


class ParamedicCreate(ParamedicBase):
    """Schema for creating a new paramedic"""
    password: str = Field(..., min_length=8)


class ParamedicUpdate(BaseModel):
    """Schema for updating paramedic profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, ge=18, le=100)
    password: Optional[str] = Field(None, min_length=8)


class ParamedicResponse(ParamedicBase):
    """Schema for paramedic response (without password)"""
    id: int
    profile_pic_url: Optional[str] = None
    profile_pic_data: Optional[str] = None  # Base64 encoded image data
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ParamedicWithConversations(ParamedicResponse):
    """Schema for paramedic with their conversations"""
    conversations: List['ConversationResponse'] = []
    
    class Config:
        from_attributes = True


# ============ Conversation Schemas ============

class ConversationBase(BaseModel):
    """Base conversation schema"""
    session_id: str
    transcript: str
    analysis: Dict[str, Any]


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: int
    paramedic_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    """Simplified conversation summary for list view"""
    id: int
    session_id: str
    created_at: datetime
    # Extract key info from analysis
    patient_name: Optional[str] = None
    chief_complaint: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int
    limit: int
    total: int
    has_more: bool


class ConversationListResponse(BaseModel):
    """Paginated conversation list response"""
    conversations: List[ConversationSummary]
    pagination: PaginationMeta


# ============ Authentication Schemas ============

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    token_type: str = "bearer"
    user: ParamedicResponse


# Update forward references
ParamedicWithConversations.model_rebuild()


