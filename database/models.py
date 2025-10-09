"""
SQLAlchemy Database Models
ORM models for PostgreSQL database
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Paramedic(Base):
    """
    Paramedic user model
    Stores paramedic information and credentials
    """
    __tablename__ = "paramedics"
    
    id = Column(Integer, primary_key=True, index=True)
    medical_id = Column(String(50), nullable=True)
    national_id = Column(String(50), nullable=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    profile_pic_url = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to conversations
    conversations = relationship("Conversation", back_populates="paramedic", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Paramedic(id={self.id}, name={self.name}, email={self.email})>"


class Conversation(Base):
    """
    Conversation model
    Stores conversation/session data from paramedic reports
    """
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    paramedic_id = Column(Integer, ForeignKey("paramedics.id"), nullable=False)
    
    # Transcript
    transcript = Column(Text, nullable=False)
    
    # Analysis results stored as JSON
    analysis = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to paramedic
    paramedic = relationship("Paramedic", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id={self.session_id}, paramedic_id={self.paramedic_id})>"


