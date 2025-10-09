"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import sys

from endpoints.config import DATABASE_URL, ENABLE_AUTH
from database.models import Base

# Create database engine
engine = None
SessionLocal = None
DB_CONNECTION_ERROR = None

if ENABLE_AUTH:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False,  # Set to True for SQL logging during development
            connect_args={"connect_timeout": 10}  # 10 second connection timeout
        )
        # Test the connection immediately
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("✅ Database connection established successfully")
    except Exception as e:
        DB_CONNECTION_ERROR = str(e)
        print(f"❌ Database connection failed: {DB_CONNECTION_ERROR}")
        print("⚠️  Application will run in limited mode. Database features disabled.")
        engine = None
        SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Usage in FastAPI routes:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    if not ENABLE_AUTH or SessionLocal is None:
        # Instead of raising an error, yield None to allow graceful degradation
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_db_connected() -> bool:
    """Check if database is connected and available"""
    return ENABLE_AUTH and engine is not None and SessionLocal is not None


def get_db_error() -> str:
    """Get the database connection error message if any"""
    return DB_CONNECTION_ERROR if DB_CONNECTION_ERROR else ""


def init_db():
    """
    Initialize database tables
    Creates all tables defined in models.py
    """
    if not ENABLE_AUTH or engine is None:
        if ENABLE_AUTH and DB_CONNECTION_ERROR:
            print(f"⚠️  Cannot initialize database due to connection error: {DB_CONNECTION_ERROR}")
        else:
            print("⚠️  Authentication disabled. Skipping database initialization.")
        return
    
    try:
        print("🔧 Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database tables: {str(e)}")


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


