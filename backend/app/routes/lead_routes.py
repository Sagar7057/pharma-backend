"""
Lead capture routes/endpoints for marketing site.
"""

import logging

from fastapi import APIRouter, HTTPException, status  

from app.schemas.lead import LeadCreate, LeadCreateResponse
from app.services.lead import LeadService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/leads", response_model=LeadCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(request: LeadCreate):
    try:
        await LeadService.save_lead(request)
        return LeadCreateResponse()
    except Exception as exc:
        logger.error(f"Failed to save lead: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit lead",
        )

