"""
Database Performance Indexes Migration
Adds indexes to improve query performance for conversations and paramedics tables.

This script creates indexes that will speed up:
- Loading conversations for a specific paramedic (sorted by date)
- Finding conversations by session_id
- Looking up paramedics by email (for login)

Expected improvement: 500ms → 50-100ms for conversation queries

Run once after deploying:
    python -m database.add_indexes
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Get database configuration directly
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/emergency_ai")

# Handle Render's postgres:// to postgresql:// conversion
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def add_performance_indexes():
    """
    Add performance indexes to database tables.
    Indexes are created with IF NOT EXISTS to allow safe re-runs.
    """
    if not ENABLE_AUTH:
        print("[ERROR] Authentication is disabled. No database to index.")
        return
    
    try:
        # Create database engine
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        
        print("\n" + "=" * 60)
        print("Database Performance Indexes")
        print("=" * 60)
        print(f"Connecting to database...\n")
        
        with engine.connect() as conn:
            # Index 1: Conversations by paramedic_id and created_at (for sorted list queries)
            print("[1/3] Creating index on conversations(paramedic_id, created_at)...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_conversations_paramedic_created 
                ON conversations(paramedic_id, created_at DESC)
            """))
            print("  [OK] idx_conversations_paramedic_created created/verified\n")
            
            # Index 2: Conversations by session_id (for quick lookups)
            print("[2/3] Creating index on conversations(session_id)...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
                ON conversations(session_id)
            """))
            print("  [OK] idx_conversations_session_id created/verified\n")
            
            # Index 3: Paramedics by email (for login queries)
            print("[3/3] Creating index on paramedics(email)...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_paramedics_email 
                ON paramedics(email)
            """))
            print("  [OK] idx_paramedics_email created/verified\n")
            
            # Commit the transaction
            conn.commit()
            
            # Verify indexes were created
            print("Verifying indexes...")
            result = conn.execute(text("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE indexname IN (
                    'idx_conversations_paramedic_created',
                    'idx_conversations_session_id',
                    'idx_paramedics_email'
                )
                ORDER BY tablename, indexname
            """))
            
            indexes = result.fetchall()
            print(f"\nFound {len(indexes)} performance indexes:")
            for idx in indexes:
                print(f"  - {idx.indexname} on {idx.tablename}")
        
        print("\n" + "=" * 60)
        print("Indexes created successfully!")
        print("=" * 60)
        print("\nExpected performance improvement:")
        print("  - Conversation queries: 500ms -> 50-100ms (80% faster)")
        print("  - Email lookups: Significantly faster")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create indexes: {e}")
        print("\nPlease check:")
        print("  1. DATABASE_URL is correct in .env")
        print("  2. Database is accessible")
        print("  3. You have CREATE INDEX permissions")
        raise


if __name__ == "__main__":
    add_performance_indexes()

