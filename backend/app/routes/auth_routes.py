"""
Authentication routes/endpoints
Signup, login, profile, refresh token, logout
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.auth import AuthService
from app.schemas.auth import SignupRequest, LoginRequest, UserResponse
from app.utils.auth import decode_token, get_token_from_header

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get current user from JWT token
    Used as dependency for protected routes
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    token = get_token_from_header(authorization)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Create new user account
    
    Args:
        request: Signup request with email, password, and user details
        db: Database session
        
    Returns:
        JWT token and user data
    """
    try:
        result = await AuthService.signup(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            company_name=request.company_name,
            phone=request.phone,
            city=request.city,
            state=request.state,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    
    except ValueError as e:
        logger.warning(f"Signup validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token
    
    Args:
        request: Login request with email and password
        db: Database session
        
    Returns:
        JWT token and user data
    """
    try:
        result = await AuthService.login(
            email=request.email,
            password=request.password,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    
    except ValueError as e:
        logger.warning(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/profile", status_code=status.HTTP_200_OK)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile (Protected route)
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User profile data
    """
    try:
        user_id = current_user.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        result = await AuthService.get_profile(user_id, db)
        
        return {
            "success": True,
            "data": result
        }
    
    except ValueError as e:
        logger.warning(f"Profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

@router.post("/refresh-token", status_code=status.HTTP_200_OK)
async def refresh_token(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh JWT token (Protected route)
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        New JWT token
    """
    try:
        from app.utils.auth import create_access_token
        
        user_id = current_user.get("user_id")
        email = current_user.get("email")
        
        new_token = create_access_token(user_id, email)
        
        return {
            "success": True,
            "data": {
                "token": new_token,
                "expiresIn": "7d"
            }
        }
    
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (Protected route)
    Token invalidation typically handled on client side
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    return {
        "success": True,
        "message": "Logged out successfully"
    }
