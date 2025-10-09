"""
Authentication Utilities
Password hashing, JWT token creation/validation, and authentication dependencies
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from endpoints.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, ENABLE_AUTH
from database.connection import get_db
from database.models import Paramedic
from database.schemas import TokenData

# Simple password hashing functions (no bcrypt dependency issues)
def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, pwd_hash = hashed_password.split(':')
        return hashlib.sha256((plain_password + salt).encode()).hexdigest() == pwd_hash
    except:
        return False

# HTTP Bearer token security
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """
    Hash a password using SHA-256 with salt
    """
    return hash_password(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT access token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return TokenData(email=email)
    except JWTError:
        return None


def authenticate_paramedic(db: Session, email: str, password: str) -> Optional[Paramedic]:
    """
    Authenticate a paramedic by email and password
    
    Args:
        db: Database session
        email: Paramedic email
        password: Plain text password
        
    Returns:
        Paramedic object if authenticated, None otherwise
    """
    paramedic = db.query(Paramedic).filter(Paramedic.email == email).first()
    if not paramedic:
        return None
    if not verify_password(password, paramedic.hashed_password):
        return None
    return paramedic


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Paramedic:
    """
    Dependency to get the current authenticated user from JWT token
    
    Usage in routes:
        @app.get("/protected")
        async def protected_route(current_user: Paramedic = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None or token_data.email is None:
        raise credentials_exception
    
    paramedic = db.query(Paramedic).filter(Paramedic.email == token_data.email).first()
    if paramedic is None:
        raise credentials_exception
    
    return paramedic


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[Paramedic]:
    """
    Dependency to get the current user if authenticated, otherwise None
    Used for routes that work with or without authentication
    """
    if not ENABLE_AUTH or credentials is None:
        return None
    
    try:
        token = credentials.credentials
        token_data = decode_access_token(token)
        
        if token_data is None or token_data.email is None:
            return None
        
        paramedic = db.query(Paramedic).filter(Paramedic.email == token_data.email).first()
        return paramedic
    except:
        return None


