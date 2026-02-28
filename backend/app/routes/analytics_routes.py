"""
Analytics routes/endpoints
Dashboard and business intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.analytics import AnalyticsService
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete dashboard metrics"""
    try:
        metrics = await AnalyticsService.get_dashboard_metrics(
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard metrics"
        )

@router.get("/revenue-trend")
async def get_revenue_trend(
    range_type: str = Query("month", regex="^(today|week|month|last_30|last_90|year|custom)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get revenue trend over time"""
    try:
        trend = await AnalyticsService.get_revenue_trend(
            user_id=current_user["user_id"],
            range_type=range_type,
            db=db
        )
        
        return {
            "success": True,
            "data": trend
        }
    except Exception as e:
        logger.error(f"Error getting revenue trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue trend"
        )

@router.get("/quotes-metrics")
async def get_quote_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quote-related metrics and breakdown"""
    try:
        metrics = await AnalyticsService.get_quote_metrics(
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error getting quote metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quote metrics"
        )

@router.get("/brands-metrics")
async def get_brand_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get brand-related metrics"""
    try:
        metrics = await AnalyticsService.get_brand_metrics(
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error getting brand metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand metrics"
        )

@router.get("/customers-metrics")
async def get_customer_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer-related metrics"""
    try:
        metrics = await AnalyticsService.get_customer_metrics(
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error getting customer metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customer metrics"
        )
