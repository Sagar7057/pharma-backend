"""
PDF export schemas for quote and report generation
Pydantic models for PDF operations
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class PDFFormat(str, Enum):
    """PDF format enum"""
    QUOTE = "quote"
    INVOICE = "invoice"
    REPORT = "report"

class PDFExportRequest(BaseModel):
    """PDF export request"""
    format: PDFFormat = Field(..., description="PDF format type")
    include_terms: Optional[bool] = True
    include_notes: Optional[bool] = True
    logo_url: Optional[str] = None
    company_name: Optional[str] = None

class QuotePDFRequest(BaseModel):
    """Quote PDF export request"""
    quote_id: int
    include_terms: Optional[bool] = True
    include_notes: Optional[bool] = True

class PDFResponse(BaseModel):
    """PDF export response"""
    success: bool
    data: dict = Field(..., description="Contains PDF file data")

class EmailRequest(BaseModel):
    """Email request"""
    to_email: str
    subject: Optional[str] = None
    message: Optional[str] = None
    attachment_type: Optional[str] = None

class QuoteEmailRequest(BaseModel):
    """Quote email request"""
    quote_id: int
    recipient_email: str
    subject: Optional[str] = None
    message: Optional[str] = None
    include_pdf: Optional[bool] = True

class EmailResponse(BaseModel):
    """Email response"""
    success: bool
    data: dict = Field(..., description="Contains email status")

class QuoteTemplateBase(BaseModel):
    """Base quote template"""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    template_html: Optional[str] = None
    default_validity_days: Optional[int] = 7
    default_margin_percentage: Optional[float] = None

class QuoteTemplateCreate(QuoteTemplateBase):
    """Create quote template request"""
    pass

class QuoteTemplateUpdate(BaseModel):
    """Update quote template request"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    template_html: Optional[str] = None
    default_validity_days: Optional[int] = None
    default_margin_percentage: Optional[float] = None

class QuoteTemplateResponse(QuoteTemplateBase):
    """Quote template response"""
    id: int
    user_id: int
    is_default: bool = False
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class QuoteTemplateListResponse(BaseModel):
    """Quote template list response"""
    success: bool
    data: dict = Field(..., description="Contains templates list")
