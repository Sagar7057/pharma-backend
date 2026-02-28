"""
Analytics schemas for metrics and dashboard data
Pydantic models for analytics operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DateRange(str, Enum):
    """Date range enum"""
    TODAY = "today"
    THIS_WEEK = "week"
    THIS_MONTH = "month"
    LAST_30_DAYS = "last_30"
    LAST_90_DAYS = "last_90"
    THIS_YEAR = "year"
    CUSTOM = "custom"

class MetricType(str, Enum):
    """Metric type enum"""
    REVENUE = "revenue"
    QUOTES = "quotes"
    BRANDS = "brands"
    CUSTOMERS = "customers"
    MARGIN = "margin"

class DashboardMetrics(BaseModel):
    """Dashboard metrics summary"""
    total_revenue: float
    total_quotes: int
    total_margin: float
    avg_quote_value: float
    conversion_rate: float
    active_brands: int
    pending_quotes: int
    expired_quotes: int

class QuoteMetrics(BaseModel):
    """Quote-related metrics"""
    total_quotes: int
    draft_quotes: int
    sent_quotes: int
    accepted_quotes: int
    rejected_quotes: int
    expired_quotes: int
    total_value: float
    total_margin: float
    avg_margin_percentage: float
    conversion_rate: float  # accepted / sent

class BrandMetrics(BaseModel):
    """Brand-related metrics"""
    total_brands: int
    top_brands: List[Dict[str, Any]]  # name, revenue, quotes
    brands_by_margin: List[Dict[str, Any]]
    nppa_brands: int

class CustomerMetrics(BaseModel):
    """Customer-related metrics"""
    total_customers: int
    quotes_by_type: Dict[str, int]
    avg_order_value: float
    repeat_customers: int

class RevenueMetric(BaseModel):
    """Single revenue data point"""
    date: str
    revenue: float
    margin: float
    quote_count: int

class TrendData(BaseModel):
    """Trend data for charts"""
    success: bool
    data: dict = Field(..., description="Contains trend data points")

class RevenueMetricsResponse(BaseModel):
    """Revenue metrics response"""
    success: bool
    data: dict = Field(..., description="Contains revenue metrics")

class BrandAnalyticsResponse(BaseModel):
    """Brand analytics response"""
    success: bool
    data: dict = Field(..., description="Contains brand metrics")

class QuoteAnalyticsResponse(BaseModel):
    """Quote analytics response"""
    success: bool
    data: dict = Field(..., description="Contains quote metrics")

class DashboardResponse(BaseModel):
    """Complete dashboard response"""
    success: bool
    data: dict = Field(..., description="Contains all dashboard metrics")
