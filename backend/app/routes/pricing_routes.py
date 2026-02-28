"""
Customer Type and Pricing routes/endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.customer_type import CustomerTypeService
from app.services.pricing import PricingEngineService
from app.schemas.customer_type import CustomerTypeCreate, CustomerTypeUpdate, CustomerTypeResponse
from app.schemas.pricing import (
    PriceCalculationRequest, PricingRuleCreate, 
    NPPACheckRequest
)
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================
# CUSTOMER TYPE ENDPOINTS
# ============================================

@router.post("/customer-types", status_code=status.HTTP_201_CREATED)
async def create_customer_type(
    request: CustomerTypeCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new customer type"""
    try:
        result = await CustomerTypeService.create_customer_type(
            user_id=current_user["user_id"],
            name=request.name,
            default_margin=request.default_margin,
            description=request.description,
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
        logger.error(f"Error creating customer type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer type"
        )

@router.get("/customer-types")
async def list_customer_types(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all customer types"""
    try:
        types = await CustomerTypeService.list_customer_types(
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": types
        }
    except Exception as e:
        logger.error(f"Error listing customer types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list customer types"
        )

@router.get("/customer-types/{type_id}")
async def get_customer_type(
    type_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single customer type"""
    try:
        result = await CustomerTypeService.get_customer_type(
            user_id=current_user["user_id"],
            type_id=type_id,
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
        logger.error(f"Error getting customer type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customer type"
        )

@router.put("/customer-types/{type_id}")
async def update_customer_type(
    type_id: int,
    request: CustomerTypeUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update customer type"""
    try:
        result = await CustomerTypeService.update_customer_type(
            user_id=current_user["user_id"],
            type_id=type_id,
            name=request.name,
            default_margin=request.default_margin,
            description=request.description,
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
        logger.error(f"Error updating customer type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer type"
        )

@router.delete("/customer-types/{type_id}")
async def delete_customer_type(
    type_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete customer type"""
    try:
        await CustomerTypeService.delete_customer_type(
            user_id=current_user["user_id"],
            type_id=type_id,
            db=db
        )
        
        return {
            "success": True,
            "message": "Customer type deleted"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting customer type: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer type"
        )

# ============================================
# PRICING ENDPOINTS
# ============================================

@router.post("/pricing/calculate")
async def calculate_price(
    request: PriceCalculationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate price for a brand
    
    Request:
    {
      "brand_id": 1,
      "customer_type_id": 2,
      "quantity": 100
    }
    """
    try:
        result = await PricingEngineService.calculate_price(
            user_id=current_user["user_id"],
            brand_id=request.brand_id,
            customer_type_id=request.customer_type_id,
            quantity=request.quantity,
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
        logger.error(f"Error calculating price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate price"
        )

@router.post("/pricing/check-nppa")
async def check_nppa_compliance(
    request: NPPACheckRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check NPPA compliance for proposed price
    
    Request:
    {
      "brand_id": 1,
      "proposed_price": 35.00,
      "proposed_margin": 16.5
    }
    """
    try:
        result = await PricingEngineService.check_nppa_compliance(
            brand_id=request.brand_id,
            proposed_price=request.proposed_price,
            user_id=current_user["user_id"],
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
        logger.error(f"Error checking NPPA compliance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check NPPA compliance"
        )

@router.get("/pricing/nppa-data/{brand_id}")
async def get_nppa_data(
    brand_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get NPPA controlled drug data"""
    try:
        result = await PricingEngineService.get_nppa_data(
            brand_id=brand_id,
            db=db
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NPPA data not found for this brand"
            )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting NPPA data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get NPPA data"
        )
