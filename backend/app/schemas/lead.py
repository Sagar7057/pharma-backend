"""
Schemas for marketing/demo lead capture.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    company: Optional[str] = Field(default=None, max_length=160)
    phone: str = Field(..., min_length=8, max_length=25)
    email: EmailStr
    city: Optional[str] = Field(default=None, max_length=120)
    requirement: str = Field(..., min_length=1, max_length=80)
    preferred_time: Optional[str] = Field(default=None, max_length=80)
    message: Optional[str] = Field(default=None, max_length=2000)
    source: Optional[str] = Field(default="marketing-site", max_length=80)
    submitted_at: Optional[datetime] = None


class LeadCreateResponse(BaseModel):
    success: bool = True
    message: str = "Lead submitted successfully"

