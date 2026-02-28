"""
Brand schemas for request/response validation
Pydantic models for brand management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class BrandBase(BaseModel):
    """Base brand schema"""
    brand_name: str = Field(..., min_length=2, max_length=255)
    manufacturer: Optional[str] = Field(None, max_length=255)
    mrp: float = Field(..., gt=0)
    cost_price: float = Field(..., gt=0)
    default_margin: Optional[float] = Field(None, ge=0, le=100)
    therapeutic_category: Optional[str] = Field(None, max_length=100)
    salt_name: Optional[str] = Field(None, max_length=255)
    strength: Optional[str] = Field(None, max_length=100)
    packing: Optional[str] = Field(None, max_length=100)
    gtin_code: Optional[str] = Field(None, max_length=20)
    
    @validator('mrp', 'cost_price')
    def validate_prices(cls, v):
        """Validate prices are positive"""
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v
    
    @validator('default_margin')
    def validate_margin(cls, v):
        """Validate margin is between 0-100"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Margin must be between 0 and 100')
        return v

class BrandCreate(BrandBase):
    """Create brand request"""
    pass

class BrandUpdate(BaseModel):
    """Update brand request"""
    brand_name: Optional[str] = Field(None, min_length=2, max_length=255)
    manufacturer: Optional[str] = Field(None, max_length=255)
    mrp: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    default_margin: Optional[float] = Field(None, ge=0, le=100)
    therapeutic_category: Optional[str] = Field(None, max_length=100)
    salt_name: Optional[str] = Field(None, max_length=255)
    strength: Optional[str] = Field(None, max_length=100)
    packing: Optional[str] = Field(None, max_length=100)
    gtin_code: Optional[str] = Field(None, max_length=20)

class BrandResponse(BrandBase):
    """Brand response schema"""
    id: int
    user_id: int
    current_sell_price: Optional[float] = None
    is_nppa_controlled: bool = False
    nppa_margin_limit: Optional[float] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BrandListResponse(BaseModel):
    """Brand list response"""
    success: bool
    data: dict = Field(..., description="Contains brands list and pagination")

class BrandDetailResponse(BaseModel):
    """Brand detail response"""
    success: bool
    data: BrandResponse

class CSVImportRequest(BaseModel):
    """CSV import request"""
    filename: str
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "brands.csv"
            }
        }

class CSVImportResponse(BaseModel):
    """CSV import response"""
    success: bool
    data: dict = Field(..., description="Import results with imported, failed, skipped counts")

class BrandSearchQuery(BaseModel):
    """Brand search/filter query"""
    search: Optional[str] = None
    sort_by: Optional[str] = Field(None, description="name, margin, or mrp")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
