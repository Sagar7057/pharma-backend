"""
Pydantic schemas for authentication
Request and response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class SignupRequest(BaseModel):
    """User signup request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    company_name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    
    @validator('password')
    def validate_password(cls, v):
        """
        Validate password strength
        - Min 8 characters
        - Must have uppercase
        - Must have lowercase
        - Must have numbers
        """
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letters')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letters')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain numbers')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@pharmapricing.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "company_name": "ABC Pharma",
                "phone": "9876543210",
                "city": "Bangalore",
                "state": "KA"
            }
        }

class LoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=1)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@pharmapricing.com",
                "password": "SecurePass123!"
            }
        }

class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "email": "user@pharmapricing.com",
                "full_name": "John Doe",
                "company_name": "ABC Pharma",
                "phone": "9876543210",
                "city": "Bangalore",
                "state": "KA",
                "created_at": "2024-02-26T10:30:00Z"
            }
        }

class SignupResponse(BaseModel):
    """Signup response schema"""
    success: bool
    data: dict = Field(..., description="Contains token and user")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "user": {
                        "id": 1,
                        "email": "user@pharmapricing.com",
                        "full_name": "John Doe"
                    }
                }
            }
        }

class LoginResponse(BaseModel):
    """Login response schema"""
    success: bool
    data: dict = Field(..., description="Contains token and expiry")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "expiresIn": "7d",
                    "user": {
                        "id": 1,
                        "email": "user@pharmapricing.com",
                        "full_name": "John Doe"
                    }
                }
            }
        }

class ProfileResponse(BaseModel):
    """Profile response schema"""
    success: bool
    data: UserResponse

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: dict = Field(..., description="Contains error code and message")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Email is invalid"
                }
            }
        }
