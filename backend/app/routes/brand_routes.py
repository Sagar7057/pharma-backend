"""
Brand routes/endpoints
CRUD operations and CSV import
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.brand import BrandService
from app.services.auth import AuthService
from app.schemas.brand import (
    BrandCreate, BrandUpdate, BrandResponse, BrandListResponse,
    CSVImportResponse, BrandSearchQuery
)
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_brand(
    request: BrandCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new brand
    """
    try:
        result = await BrandService.create_brand(
            user_id=current_user["user_id"],
            brand_name=request.brand_name,
            manufacturer=request.manufacturer or "",
            mrp=request.mrp,
            cost_price=request.cost_price,
            default_margin=request.default_margin or 0,
            therapeutic_category=request.therapeutic_category or "",
            salt_name=request.salt_name or "",
            strength=request.strength or "",
            packing=request.packing or "",
            gtin_code=request.gtin_code or "",
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create brand"
        )

@router.get("/", status_code=status.HTTP_200_OK)
async def list_brands(
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List brands with search, sort, and pagination
    """
    try:
        result = await BrandService.list_brands(
            user_id=current_user["user_id"],
            search=search,
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
        logger.error(f"Error listing brands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list brands"
        )

@router.get("/{brand_id}", status_code=status.HTTP_200_OK)
async def get_brand(
    brand_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get single brand by ID
    """
    try:
        result = await BrandService.get_brand(
            user_id=current_user["user_id"],
            brand_id=brand_id,
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
        logger.error(f"Error getting brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand"
        )

@router.put("/{brand_id}", status_code=status.HTTP_200_OK)
async def update_brand(
    brand_id: int,
    request: BrandUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update brand
    """
    try:
        # Only include non-None fields
        update_data = {}
        for key, value in request.dict().items():
            if value is not None:
                update_data[key] = value
        
        result = await BrandService.update_brand(
            user_id=current_user["user_id"],
            brand_id=brand_id,
            update_data=update_data,
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
        logger.error(f"Error updating brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update brand"
        )

@router.delete("/{brand_id}", status_code=status.HTTP_200_OK)
async def delete_brand(
    brand_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete brand (soft delete)
    """
    try:
        await BrandService.delete_brand(
            user_id=current_user["user_id"],
            brand_id=brand_id,
            db=db
        )
        
        return {
            "success": True,
            "message": "Brand deleted successfully"
        }
    
    except Exception as e:
        logger.error(f"Error deleting brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete brand"
        )

@router.post("/import", status_code=status.HTTP_200_OK)
async def import_brands_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import brands from CSV file
    
    Expected CSV format:
    Brand,Manufacturer,MRP,CostPrice,DefaultMargin
    Amoxicillin 500mg,Cipla,35.00,30.00,15
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV and XLSX files are supported"
            )
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Import
        result = await BrandService.import_csv(
            user_id=current_user["user_id"],
            csv_content=csv_content,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import CSV"
        )
