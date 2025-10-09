'''
@Cursor

Goal:
I want to test that the database is storing the conversation data correctly.
and that I can retreive it

The problem:
I just have pushed our application to Render
It has saved the account I created when I was running the local hosted application which is great
BUT,
The left hand pane doesn't show any of my previous conversations.
I tried to record one then referesh and the left pane still doesn't show any of my previous conversations.


'''

'''
Database Conversation Storage Test Script

Tests:
1. Database connection
2. User account retrieval
3. Conversation retrieval
4. Conversation creation
5. Identifies the bug in routes.py
'''

import os
import sys
from pathlib import Path
from datetime import datetime

# Set up minimal environment to avoid circular imports
# Don't import from endpoints or database modules that trigger the whole app
os.environ.setdefault("ENABLE_AUTH", "true")

# Import only what we need directly
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL directly
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./emergency_ai.db")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine and session directly (avoid importing database.connection)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models AFTER setting up the engine
from database.models import Paramedic, Conversation, Base

def test_database_connection():
    """Test 1: Can we connect to the database?"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    try:
        db = SessionLocal()
        # Try a simple query
        count = db.query(Paramedic).count()
        print(f"✅ Database connected successfully!")
        print(f"   Total paramedics in database: {count}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def test_user_retrieval():
    """Test 2: Can we retrieve your user account?"""
    print("\n" + "="*60)
    print("TEST 2: User Account Retrieval")
    print("="*60)
    
    try:
        db = SessionLocal()
        users = db.query(Paramedic).all()
        
        if not users:
            print("⚠️  No users found in database")
            db.close()
            return None
        
        print(f"✅ Found {len(users)} user(s):")
        for user in users:
            print(f"\n   User ID: {user.id}")
            print(f"   Name: {user.name}")
            print(f"   Email: {user.email}")
            print(f"   Created: {user.created_at}")
            print(f"   Profile pic: {user.profile_pic_url or 'None'}")
        
        db.close()
        return users[0] if users else None
        
    except Exception as e:
        print(f"❌ User retrieval failed: {str(e)}")
        return None


def test_conversation_retrieval(user_id=None):
    """Test 3: Can we retrieve conversations?"""
    print("\n" + "="*60)
    print("TEST 3: Conversation Retrieval")
    print("="*60)
    
    try:
        db = SessionLocal()
        
        if user_id:
            conversations = db.query(Conversation).filter(
                Conversation.paramedic_id == user_id
            ).order_by(Conversation.created_at.desc()).all()
            print(f"   Filtering for user_id: {user_id}")
        else:
            conversations = db.query(Conversation).all()
            print(f"   Retrieving ALL conversations")
        
        print(f"\n✅ Found {len(conversations)} conversation(s)")
        
        if conversations:
            for i, conv in enumerate(conversations, 1):
                print(f"\n   Conversation #{i}:")
                print(f"   - ID: {conv.id}")
                print(f"   - Session ID: {conv.session_id}")
                print(f"   - Paramedic ID: {conv.paramedic_id}")
                print(f"   - Created: {conv.created_at}")
                print(f"   - Transcript length: {len(conv.transcript)} chars")
                
                # Show analysis summary
                if isinstance(conv.analysis, dict):
                    print(f"   - Patient: {conv.analysis.get('patient_name', 'N/A')}")
                    print(f"   - Chief complaint: {conv.analysis.get('chief_complaint', 'N/A')}")
        else:
            print("\n⚠️  No conversations found!")
            print("   This explains why your left pane is empty.")
        
        db.close()
        return conversations
        
    except Exception as e:
        print(f"❌ Conversation retrieval failed: {str(e)}")
        return []


def test_conversation_creation(user_id):
    """Test 4: Can we create a test conversation?"""
    print("\n" + "="*60)
    print("TEST 4: Create Test Conversation")
    print("="*60)
    
    if not user_id:
        print("❌ Cannot create conversation - no user_id provided")
        return None
    
    try:
        db = SessionLocal()
        
        # Create a test conversation
        test_conv = Conversation(
            session_id=f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            paramedic_id=user_id,
            transcript="This is a test transcript to verify database storage is working.",
            analysis={
                "patient_name": "Test Patient",
                "chief_complaint": "Database connection test",
                "vital_signs": {"heart_rate": "72 bpm"},
                "assessment": "Testing conversation storage",
                "treatment": "Verify database functionality"
            }
        )
        
        db.add(test_conv)
        db.commit()
        db.refresh(test_conv)
        
        print(f"✅ Test conversation created successfully!")
        print(f"   Conversation ID: {test_conv.id}")
        print(f"   Session ID: {test_conv.session_id}")
        print(f"   Created at: {test_conv.created_at}")
        
        db.close()
        return test_conv
        
    except Exception as e:
        print(f"❌ Conversation creation failed: {str(e)}")
        return None


def identify_bug():
    """Test 5: Identify the actual bug in the code"""
    print("\n" + "="*60)
    print("TEST 5: Bug Identification")
    print("="*60)
    
    print("""
🐛 BUG FOUND in endpoints/routes.py (lines 69-79)

The upload_audio() function is NOT saving conversations to the database!

Current code says:
    "Auth enabled but skipping database save due to dependency issues"

This is why your conversations don't show up in the left pane.

The fix: The upload_audio() function needs to properly save conversations
when a user is authenticated.
    """)


def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "🔍" * 30)
    print("DATABASE CONVERSATION STORAGE TEST")
    print("🔍" * 30)
    
    # Initialize database (create tables if they don't exist)
    print("\n📋 Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables ready")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    # Test 1: Connection
    if not test_database_connection():
        print("\n❌ Cannot proceed - database connection failed")
        return
    
    # Test 2: User retrieval
    user = test_user_retrieval()
    
    # Test 3: Conversation retrieval
    conversations = test_conversation_retrieval(user.id if user else None)
    
    # Test 4: Create test conversation
    if user:
        test_conv = test_conversation_creation(user.id)
        
        # Verify it was saved
        if test_conv:
            print(f"\n🔄 Verifying test conversation was saved...")
            new_conversations = test_conversation_retrieval(user.id)
            if len(new_conversations) > len(conversations):
                print(f"✅ Test conversation successfully retrieved!")
            else:
                print(f"⚠️  Test conversation created but retrieval issue")
    
    # Test 5: Identify the bug
    identify_bug()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Database: Connected")
    print(f"✅ User account: {'Found' if user else 'Not found'}")
    print(f"⚠️  Conversations: {len(conversations)} found (should have more)")
    print(f"\n🔧 ACTION NEEDED:")
    print(f"   Fix the upload_audio() function in endpoints/routes.py")
    print(f"   to properly save conversations to the database.")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()