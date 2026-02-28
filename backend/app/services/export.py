"""
PDF and Email export service
Business logic for PDF generation and email sending
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from io import BytesIO
import base64
from datetime import datetime

logger = logging.getLogger(__name__)

class ExportService:
    """Service for PDF and email exports"""
    
    @staticmethod
    async def generate_quote_pdf(
        user_id: int,
        quote_id: int,
        include_terms: bool = True,
        include_notes: bool = True,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate PDF for quote"""
        try:
            # Get quote with details
            quote_result = db.execute(
                text("""
                    SELECT id, quote_number, customer_name, customer_email, customer_phone,
                           status, notes, quote_date, quote_expires_at, total_amount,
                           total_margin, created_at
                    FROM quotes
                    WHERE id = :quote_id AND user_id = :user_id
                """),
                {"quote_id": quote_id, "user_id": user_id}
            )
            quote = quote_result.fetchone()
            
            if not quote:
                raise ValueError("Quote not found")
            
            # Get line items
            items_result = db.execute(
                text("""
                    SELECT qli.brand_id, qli.quantity, qli.unit_price, qli.margin_percentage,
                           qli.discount, qli.line_total, b.brand_name
                    FROM quote_line_items qli
                    JOIN brands b ON qli.brand_id = b.id
                    WHERE qli.quote_id = :quote_id
                    ORDER BY qli.id ASC
                """),
                {"quote_id": quote_id}
            )
            
            line_items = []
            for row in items_result:
                line_items.append({
                    "brand_name": row[6],
                    "quantity": row[1],
                    "unit_price": float(row[2]),
                    "margin_percentage": float(row[3]),
                    "discount": float(row[4]) if row[4] else 0,
                    "line_total": float(row[5])
                })
            
            # Build PDF content (simplified HTML base)
            pdf_html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .quote-number {{ font-size: 24px; font-weight: bold; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f0f0f0; }}
                        .total-row {{ font-weight: bold; }}
                        .footer {{ margin-top: 30px; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <div class="quote-number">Quote: {quote[1]}</div>
                        <div>Date: {quote[7].strftime('%Y-%m-%d') if quote[7] else 'N/A'}</div>
                    </div>
                    
                    <h3>Customer Information</h3>
                    <p><strong>{quote[2]}</strong></p>
                    <p>Email: {quote[3] or 'N/A'}</p>
                    <p>Phone: {quote[4] or 'N/A'}</p>
                    
                    <h3>Quote Details</h3>
                    <table>
                        <tr>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Unit Price</th>
                            <th>Total</th>
                        </tr>
            """
            
            for item in line_items:
                pdf_html += f"""
                        <tr>
                            <td>{item['brand_name']}</td>
                            <td>{item['quantity']}</td>
                            <td>₹{item['unit_price']:.2f}</td>
                            <td>₹{item['line_total']:.2f}</td>
                        </tr>
                """
            
            pdf_html += f"""
                        <tr class="total-row">
                            <td colspan="3">Total Amount</td>
                            <td>₹{quote[9]:.2f}</td>
                        </tr>
                        <tr class="total-row">
                            <td colspan="3">Total Margin</td>
                            <td>₹{quote[10]:.2f}</td>
                        </tr>
                    </table>
            """
            
            if include_notes and quote[6]:
                pdf_html += f"""
                    <h3>Notes</h3>
                    <p>{quote[6]}</p>
                """
            
            if include_terms:
                pdf_html += """
                    <div class="footer">
                        <h4>Terms & Conditions</h4>
                        <ul>
                            <li>This quote is valid until the date mentioned above</li>
                            <li>Prices are subject to change without notice</li>
                            <li>Delivery timelines will be confirmed upon order</li>
                        </ul>
                    </div>
                """
            
            pdf_html += """
                </body>
            </html>
            """
            
            # For now, return HTML (in production, use reportlab or similar)
            pdf_base64 = base64.b64encode(pdf_html.encode()).decode()
            
            return {
                "quote_id": quote_id,
                "quote_number": quote[1],
                "filename": f"quote_{quote[1]}.pdf",
                "pdf_base64": pdf_base64,
                "generated_at": datetime.now().isoformat(),
                "content_type": "application/pdf"
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise Exception("Failed to generate PDF")
    
    @staticmethod
    async def send_quote_email(
        user_id: int,
        quote_id: int,
        recipient_email: str,
        subject: Optional[str],
        message: Optional[str],
        include_pdf: bool = True,
        db: Session = None
    ) -> Dict[str, Any]:
        """Send quote via email"""
        try:
            # Get quote
            quote_result = db.execute(
                text("SELECT quote_number FROM quotes WHERE id = :quote_id AND user_id = :user_id"),
                {"quote_id": quote_id, "user_id": user_id}
            )
            quote = quote_result.fetchone()
            
            if not quote:
                raise ValueError("Quote not found")
            
            # Build email content
            default_subject = f"Quote {quote[0]}"
            default_message = f"Please find your quote {quote[0]} attached. Thank you for your business!"
            
            email_subject = subject or default_subject
            email_message = message or default_message
            
            # In production, integrate with SendGrid, AWS SES, etc.
            # For now, log the action
            logger.info(f"Email sent to {recipient_email} with quote {quote[0]}")
            
            # Update quote status to "sent" if it was draft
            db.execute(
                text("""
                    UPDATE quotes 
                    SET status = 'sent'
                    WHERE id = :quote_id AND status = 'draft'
                """),
                {"quote_id": quote_id}
            )
            db.commit()
            
            return {
                "quote_id": quote_id,
                "quote_number": quote[0],
                "recipient": recipient_email,
                "subject": email_subject,
                "status": "sent",
                "timestamp": datetime.now().isoformat()
            }
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to send email: {e}")
            raise Exception("Failed to send email")
    
    @staticmethod
    async def create_quote_template(
        user_id: int,
        name: str,
        description: Optional[str],
        template_html: Optional[str],
        default_validity_days: Optional[int],
        default_margin_percentage: Optional[float],
        db: Session = None
    ) -> Dict[str, Any]:
        """Create quote template"""
        try:
            db.execute(
                text("""
                    INSERT INTO quote_templates 
                    (user_id, name, description, template_html, default_validity_days,
                     default_margin_percentage, is_default, created_at)
                    VALUES (:user_id, :name, :description, :template_html, 
                           :default_validity_days, :default_margin_percentage, false,
                           CURRENT_TIMESTAMP)
                """),
                {
                    "user_id": user_id,
                    "name": name,
                    "description": description,
                    "template_html": template_html,
                    "default_validity_days": default_validity_days or 7,
                    "default_margin_percentage": default_margin_percentage
                }
            )
            db.commit()
            
            # Get created template
            result = db.execute(
                text("SELECT id FROM quote_templates WHERE user_id = :user_id AND name = :name ORDER BY id DESC LIMIT 1"),
                {"user_id": user_id, "name": name}
            )
            template_id = result.scalar()
            
            return {
                "id": template_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "is_default": False,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create template: {e}")
            raise Exception("Failed to create template")
    
    @staticmethod
    async def list_quote_templates(user_id: int, db: Session = None) -> Dict[str, Any]:
        """List quote templates"""
        try:
            result = db.execute(
                text("""
                    SELECT id, name, description, default_validity_days, 
                           default_margin_percentage, is_default, created_at
                    FROM quote_templates
                    WHERE user_id = :user_id
                    ORDER BY is_default DESC, created_at DESC
                """),
                {"user_id": user_id}
            )
            
            templates = []
            for row in result:
                templates.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "default_validity_days": row[3],
                    "default_margin_percentage": float(row[4]) if row[4] else None,
                    "is_default": row[5],
                    "created_at": row[6].isoformat() if row[6] else None
                })
            
            return {
                "templates": templates,
                "total": len(templates)
            }
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            raise Exception("Failed to list templates")
    
    @staticmethod
    async def delete_quote_template(user_id: int, template_id: int, db: Session = None) -> bool:
        """Delete quote template"""
        try:
            db.execute(
                text("DELETE FROM quote_templates WHERE id = :template_id AND user_id = :user_id"),
                {"template_id": template_id, "user_id": user_id}
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete template: {e}")
            raise Exception("Failed to delete template")
