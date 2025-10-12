"""
Migration script to compress existing profile pictures in the database.
Reduces base64-encoded images from ~5MB to ~50-100KB by resizing to 300x300px and compressing to 80% quality JPEG.

Run once after deploying the optimization changes:
    python -m database.migrate_profile_pictures
"""

# Import only what we need to avoid circular imports
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PIL import Image
import io
import base64

# Add parent directory to path to enable imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Get database configuration directly (avoid importing endpoints which triggers circular import)
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/emergency_ai")
# Handle Render's postgres:// to postgresql:// conversion
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Import models after setting up path
from database.models import Paramedic

# Create our own engine and session for this migration
engine = None
SessionLocal = None

if ENABLE_AUTH:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args={"connect_timeout": 10}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        SessionLocal = None


def compress_profile_picture(base64_data: str, max_size: int = 300) -> str:
    """
    Compress existing base64 profile picture.
    
    Args:
        base64_data: Base64-encoded image string (with or without data URI prefix)
        max_size: Maximum width/height in pixels (default 300)
    
    Returns:
        Compressed base64-encoded image string
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',', 1)[1]
        
        # Decode base64 to bytes
        img_data = base64.b64decode(base64_data)
        img = Image.open(io.BytesIO(img_data))
        
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
        
        # Compress to JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=80, optimize=True)
        
        # Re-encode to base64
        return base64.b64encode(output.getvalue()).decode('utf-8')
    
    except Exception as e:
        raise Exception(f"Failed to compress image: {str(e)}")


def migrate_existing_pictures():
    """
    Migrate all existing profile pictures to compressed versions.
    """
    if SessionLocal is None:
        print("\n[ERROR] Database connection not available.")
        print("Make sure ENABLE_AUTH is True and DATABASE_URL is configured.")
        return
    
    db = SessionLocal()
    
    try:
        # Get all paramedics with profile pictures
        paramedics = db.query(Paramedic).filter(
            Paramedic.profile_pic_data.isnot(None)
        ).all()
        
        total_count = len(paramedics)
        print(f"\n{'='*60}")
        print(f"Profile Picture Migration")
        print(f"{'='*60}")
        print(f"Found {total_count} paramedic(s) with profile pictures\n")
        
        if total_count == 0:
            print("No profile pictures to migrate.")
            return
        
        total_old_size = 0
        total_new_size = 0
        success_count = 0
        error_count = 0
        
        for idx, paramedic in enumerate(paramedics, 1):
            try:
                print(f"[{idx}/{total_count}] Processing Paramedic ID {paramedic.id} ({paramedic.email})...")
                
                old_size = len(paramedic.profile_pic_data)
                total_old_size += old_size
                
                # Compress the existing picture
                compressed = compress_profile_picture(paramedic.profile_pic_data)
                paramedic.profile_pic_data = compressed
                
                new_size = len(compressed)
                total_new_size += new_size
                reduction = ((old_size - new_size) / old_size) * 100
                
                print(f"  [OK] Reduced from {old_size:,} to {new_size:,} bytes ({reduction:.1f}% smaller)\n")
                success_count += 1
                
            except Exception as e:
                print(f"  [ERROR] Error: {e}\n")
                error_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        # Print summary
        print(f"{'='*60}")
        print(f"Migration Summary")
        print(f"{'='*60}")
        print(f"Total processed: {total_count}")
        print(f"Successful: {success_count}")
        print(f"Errors: {error_count}")
        
        if success_count > 0:
            total_reduction = ((total_old_size - total_new_size) / total_old_size) * 100
            print(f"\nTotal size before: {total_old_size:,} bytes ({total_old_size / 1024 / 1024:.2f} MB)")
            print(f"Total size after: {total_new_size:,} bytes ({total_new_size / 1024 / 1024:.2f} MB)")
            print(f"Total reduction: {total_reduction:.1f}%")
        
        print(f"\n{'='*60}")
        print("Migration complete!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    migrate_existing_pictures()

