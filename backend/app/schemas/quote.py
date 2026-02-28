"""
Quote schemas for request/response validation
Pydantic models for quote management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

class QuoteStatus(str, Enum):
    """Quote status enum"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class QuoteLineItemBase(BaseModel):
    """Base quote line item"""
    brand_id: int
    quantity: int = Field(..., gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    margin_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount: Optional[float] = Field(0, ge=0, le=100)

class QuoteLineItemCreate(QuoteLineItemBase):
    """Create quote line item"""
    pass

class QuoteLineItemResponse(QuoteLineItemBase):
    """Quote line item response"""
    id: int
    quote_id: int
    line_total: float
    margin_earned: float
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class QuoteCreate(BaseModel):
    """Create quote request"""
    customer_name: str = Field(..., min_length=2, max_length=255)
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_type_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=1000)
    line_items: List[QuoteLineItemCreate] = Field(..., min_items=1)
    validity_days: Optional[int] = Field(7, ge=1, le=90)

class QuoteUpdate(BaseModel):
    """Update quote request"""
    customer_name: Optional[str] = Field(None, min_length=2, max_length=255)
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[QuoteStatus] = None

class QuoteResponse(BaseModel):
    """Quote response"""
    id: int
    user_id: int
    quote_number: str
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_type_id: Optional[int] = None
    status: QuoteStatus
    notes: Optional[str] = None
    quote_date: datetime
    valid_until: datetime
    total_amount: float
    total_margin: float
    total_items: int
    line_items: List[QuoteLineItemResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class QuoteListResponse(BaseModel):
    """Quote list response"""
    success: bool
    data: dict = Field(..., description="Contains quotes list and pagination")

class QuoteDetailResponse(BaseModel):
    """Quote detail response"""
    success: bool
    data: QuoteResponse

class QuoteShareRequest(BaseModel):
    """Share quote request"""
    email: str = Field(..., description="Email to send quote to")
    message: Optional[str] = Field(None, max_length=500)

class QuoteFilterQuery(BaseModel):
    """Quote filter query"""
    status: Optional[QuoteStatus] = None
    customer_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Optional[str] = Field(None, description="date, amount, or status")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
