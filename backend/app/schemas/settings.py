"""
Settings schemas for user-level common metric defaults.
"""

from pydantic import BaseModel, Field


class CommonMetricsBase(BaseModel):
    default_gst_pct: float = Field(12, ge=0, le=100)
    default_retailer_discount_pct: float = Field(0, ge=0, le=100)
    default_stockist_discount_pct: float = Field(0, ge=0, le=100)
    default_scheme_discount_pct: float = Field(0, ge=0, le=100)
    default_cash_discount_pct: float = Field(0, ge=0, le=100)
    default_volume_discount_pct: float = Field(0, ge=0, le=100)
    default_freight_amount: float = Field(0, ge=0)
    default_handling_amount: float = Field(0, ge=0)
    default_other_charges_amount: float = Field(0, ge=0)
    default_claim_rebate_amount: float = Field(0, ge=0)


class CommonMetricsUpdate(CommonMetricsBase):
    """Update request for common metrics."""


class CommonMetricsResponse(BaseModel):
    success: bool
    data: dict
  
