"""
Settings routes/endpoints
User-level common quote metric defaults.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.routes.auth_routes import get_current_user
from app.services.settings import SettingsService
from app.schemas.settings import CommonMetricsUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/common-metrics", status_code=status.HTTP_200_OK)
async def get_common_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user-level common metrics defaults."""
    try:
        data = await SettingsService.get_common_metrics(
            user_id=current_user["user_id"],
            db=db
        )
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error fetching common metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch common metrics"
        )


@router.put("/common-metrics", status_code=status.HTTP_200_OK)
async def update_common_metrics(
    request: CommonMetricsUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user-level common metrics defaults."""
    try:
        data = await SettingsService.upsert_common_metrics(
            user_id=current_user["user_id"],
            metrics=request.model_dump(),
            db=db
        )
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Error updating common metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update common metrics"
        )
