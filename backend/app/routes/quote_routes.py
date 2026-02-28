"""
Quote routes/endpoints
CRUD operations for quotes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.quote import QuoteService
from app.schemas.quote import (
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteListResponse,
    QuoteDetailResponse, QuoteStatus
)
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_quote(
    request: QuoteCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new quote with line items
    
    Request:
    {
      "customer_name": "ABC Hospital",
      "customer_email": "contact@abchospital.com",
      "customer_phone": "9876543210",
      "customer_type_id": 1,
      "validity_days": 7,
      "line_items": [
        {
          "brand_id": 1,
          "quantity": 100,
          "margin_percentage": 15
        }
      ]
    }
    """
    try:
        result = await QuoteService.create_quote(
            user_id=current_user["user_id"],
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            customer_phone=request.customer_phone,
            customer_type_id=request.customer_type_id,
            notes=request.notes,
            line_items=[item.dict() for item in request.line_items],
            validity_days=request.validity_days or 7,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating quote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quote"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def list_quotes(
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_name: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List quotes with filtering and pagination"""
    try:
        result = await QuoteService.list_quotes(
            user_id=current_user["user_id"],
            status=status_filter,
            customer_name=customer_name,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error listing quotes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quotes"
        )

@router.get("/{quote_id}", status_code=status.HTTP_200_OK)
async def get_quote(
    quote_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single quote with line items"""
    try:
        result = await QuoteService.get_quote(
            user_id=current_user["user_id"],
            quote_id=quote_id,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting quote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quote"
        )

@router.put("/{quote_id}", status_code=status.HTTP_200_OK)
async def update_quote_status(
    quote_id: int,
    request: QuoteUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update quote status"""
    try:
        if not request.status:
            raise ValueError("Status is required")
        
        result = await QuoteService.update_quote_status(
            user_id=current_user["user_id"],
            quote_id=quote_id,
            status=request.status,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating quote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quote"
        )

@router.delete("/{quote_id}", status_code=status.HTTP_200_OK)
async def delete_quote(
    quote_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete quote (only draft quotes)"""
    try:
        await QuoteService.delete_quote(
            user_id=current_user["user_id"],
            quote_id=quote_id,
            db=db
        )
        
        return {
            "success": True,
            "message": "Quote deleted"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting quote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quote"
        )
