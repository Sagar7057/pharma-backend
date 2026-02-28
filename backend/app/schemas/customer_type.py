"""
Customer Type schemas for request/response validation
Pydantic models for customer type management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class CustomerTypeBase(BaseModel):
    """Base customer type schema"""
    name: str = Field(..., min_length=2, max_length=255)
    default_margin: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = Field(None, max_length=500)

class CustomerTypeCreate(CustomerTypeBase):
    """Create customer type request"""
    pass

class CustomerTypeUpdate(BaseModel):
    """Update customer type request"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    default_margin: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = Field(None, max_length=500)

class CustomerTypeResponse(CustomerTypeBase):
    """Customer type response schema"""
    id: int
    user_id: int
    is_predefined: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CustomerTypeListResponse(BaseModel):
    """Customer type list response"""
    success: bool
    data: List[CustomerTypeResponse]
