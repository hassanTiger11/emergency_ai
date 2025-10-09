"""
Authentication Routes
Endpoints for user signup, login, and authentication
"""
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.connection import get_db, is_db_connected, get_db_error
from database.models import Paramedic
from database.schemas import (
    ParamedicCreate, 
    ParamedicResponse, 
    LoginRequest, 
    LoginResponse,
    Token
)
from database.auth import (
    get_password_hash, 
    authenticate_paramedic, 
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(paramedic_data: ParamedicCreate, db: Session = Depends(get_db)):
    """
    Register a new paramedic user
    
    Creates a new paramedic account with hashed password and returns
    an access token for immediate login.
    """
    # Check database connection
    if not is_db_connected() or db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection unavailable: {get_db_error()}"
        )
    
    # Check if email already exists
    existing_user = db.query(Paramedic).filter(Paramedic.email == paramedic_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # For MVP: Skip uniqueness checks for "N/A" values
    # Only check uniqueness for real IDs (not "N/A")
    # Skip validation entirely for "N/A" values to allow multiple users
    
    try:
        # Create new paramedic
        hashed_password = get_password_hash(paramedic_data.password)
        new_paramedic = Paramedic(
            name=paramedic_data.name,
            email=paramedic_data.email,
            medical_id=paramedic_data.medical_id,
            national_id=paramedic_data.national_id,
            age=paramedic_data.age,
            hashed_password=hashed_password
        )
        
        db.add(new_paramedic)
        db.commit()
        db.refresh(new_paramedic)
        
        # Create access token
        access_token = create_access_token(data={"sub": new_paramedic.email})
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=ParamedicResponse.model_validate(new_paramedic)
        )
        
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        if 'email' in error_msg.lower():
            detail = "Email address already registered. Please use a different email or try logging in."
        elif 'medical_id' in error_msg.lower():
            detail = "Medical ID conflict detected. This shouldn't happen with MVP settings. Please try again or contact support."
        elif 'national_id' in error_msg.lower():
            detail = "National ID conflict detected. This shouldn't happen with MVP settings. Please try again or contact support."
        else:
            detail = "User with this information already exists. Please check your details and try again."
            
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password
    
    Returns an access token and user information if credentials are valid.
    """
    # Check database connection
    if not is_db_connected() or db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection unavailable: {get_db_error()}"
        )
    
    paramedic = authenticate_paramedic(db, login_data.email, login_data.password)
    
    if not paramedic:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": paramedic.email})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=ParamedicResponse.model_validate(paramedic)
    )


@router.get("/me", response_model=ParamedicResponse)
async def get_current_user_info(current_user: Paramedic = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header.
    """
    return ParamedicResponse.model_validate(current_user)


@router.post("/verify-token", response_model=ParamedicResponse)
async def verify_token(current_user: Paramedic = Depends(get_current_user)):
    """
    Verify if the provided token is valid
    
    Returns user information if token is valid, otherwise raises 401.
    """
    return ParamedicResponse.model_validate(current_user)


