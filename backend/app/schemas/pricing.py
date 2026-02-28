"""
Pricing schemas for pricing engine and rules
Pydantic models for pricing operations
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, datetime

class PricingRuleBase(BaseModel):
    """Base pricing rule schema"""
    margin_percentage: Optional[float] = Field(None, ge=0, le=100)
    sell_price: Optional[float] = Field(None, gt=0)
    min_quantity: int = Field(1, ge=1)
    max_quantity: Optional[int] = Field(None)
    volume_discount: Optional[float] = Field(0, ge=0, le=100)
    special_price_reason: Optional[str] = Field(None, max_length=255)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None

class PricingRuleCreate(PricingRuleBase):
    """Create pricing rule request"""
    brand_id: int
    customer_type_id: Optional[int] = None

class PricingRuleUpdate(BaseModel):
    """Update pricing rule request"""
    margin_percentage: Optional[float] = Field(None, ge=0, le=100)
    sell_price: Optional[float] = Field(None, gt=0)
    min_quantity: Optional[int] = Field(None, ge=1)
    max_quantity: Optional[int] = None
    volume_discount: Optional[float] = Field(None, ge=0, le=100)
    special_price_reason: Optional[str] = Field(None, max_length=255)
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None

class PricingRuleResponse(PricingRuleBase):
    """Pricing rule response schema"""
    id: int
    user_id: int
    brand_id: int
    customer_type_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PriceCalculationRequest(BaseModel):
    """Price calculation request"""
    brand_id: int
    customer_type_id: Optional[int] = None
    quantity: int = Field(..., gt=0)

class PriceCalculationResponse(BaseModel):
    """Price calculation response"""
    success: bool
    data: dict = Field(..., description="Contains calculated price details")

class NPPACheckRequest(BaseModel):
    """NPPA compliance check request"""
    brand_id: int
    proposed_price: float = Field(..., gt=0)
    proposed_margin: Optional[float] = Field(None, ge=0, le=100)

class NPPACheckResponse(BaseModel):
    """NPPA compliance check response"""
    success: bool
    data: dict = Field(..., description="Contains NPPA compliance info")
