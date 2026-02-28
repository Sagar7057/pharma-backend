"""
Export and template routes/endpoints
PDF generation, email sending, and quote templates
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.services.export import ExportService
from app.schemas.export import (
    QuotePDFRequest, QuoteEmailRequest, 
    QuoteTemplateCreate, QuoteTemplateUpdate
)
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================
# PDF EXPORT ENDPOINTS
# ============================================

@router.post("/quotes/{quote_id}/export-pdf")
async def export_quote_pdf(
    quote_id: int,
    request: QuotePDFRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export quote as PDF"""
    try:
        result = await ExportService.generate_quote_pdf(
            user_id=current_user["user_id"],
            quote_id=quote_id,
            include_terms=request.include_terms,
            include_notes=request.include_notes,
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
        logger.error(f"Error exporting PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export PDF"
        )

# ============================================
# EMAIL ENDPOINTS
# ============================================

@router.post("/quotes/{quote_id}/send-email")
async def send_quote_email(
    quote_id: int,
    request: QuoteEmailRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send quote via email"""
    try:
        result = await ExportService.send_quote_email(
            user_id=current_user["user_id"],
            quote_id=quote_id,
            recipient_email=request.recipient_email,
            subject=request.subject,
            message=request.message,
            include_pdf=request.include_pdf,
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
        logger.error(f"Error sending email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email"
        )

# ============================================
# QUOTE TEMPLATE ENDPOINTS
# ============================================

@router.post("/quote-templates", status_code=status.HTTP_201_CREATED)
async def create_quote_template(
    request: QuoteTemplateCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create quote template"""
    try:
        result = await ExportService.create_quote_template(
            user_id=current_user["user_id"],
            name=request.name,
            description=request.description,
            template_html=request.template_html,
            default_validity_days=request.default_validity_days,
            default_margin_percentage=request.default_margin_percentage,
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )

@router.get("/quote-templates")
async def list_quote_templates(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List quote templates"""
    try:
        result = await ExportService.list_quote_templates(
            user_id=current_user["user_id"],
            db=db
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates"
        )

@router.delete("/quote-templates/{template_id}")
async def delete_quote_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete quote template"""
    try:
        await ExportService.delete_quote_template(
            user_id=current_user["user_id"],
            template_id=template_id,
            db=db
        )
        
        return {
            "success": True,
            "message": "Template deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )
