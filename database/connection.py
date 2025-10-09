"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from endpoints.config import DATABASE_URL, ENABLE_AUTH
from database.models import Base

# Create database engine
engine = None
SessionLocal = None

if ENABLE_AUTH:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,   # Recycle connections after 1 hour
        echo=False  # Set to True for SQL logging during development
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Usage in FastAPI routes:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    if not ENABLE_AUTH or SessionLocal is None:
        raise RuntimeError("Database is not configured. Set ENABLE_AUTH=true in .env")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables
    Creates all tables defined in models.py
    """
    if not ENABLE_AUTH or engine is None:
        print("⚠️  Authentication disabled. Skipping database initialization.")
        return
    
    print("🔧 Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized successfully")


def drop_all_tables():
    """
    WARNING: Drop all tables from database
    Use only for development/testing
    """
    if not ENABLE_AUTH or engine is None:
        print("⚠️  Authentication disabled. No tables to drop.")
        return
    
    print("⚠️  Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")


