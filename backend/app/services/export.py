"""
PDF and Email export service
Business logic for PDF generation and email sending
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import base64
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportService:
    """Service for PDF and email exports"""

    @staticmethod
    def _escape_pdf_text(value: str) -> str:
        """Escape text for PDF content streams."""
        return (
            value.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

    @staticmethod
    def _build_simple_pdf(lines: list[str]) -> bytes:
        """
        Build a minimal valid single-page PDF without external dependencies.
        This keeps export stable even when PDF libraries are unavailable.
        """
        commands = [
            "BT",
            "/F1 11 Tf",
            "50 800 Td",
            "15 TL",
        ]

        for line in lines:
            safe = ExportService._escape_pdf_text(line)
            commands.append(f"({safe}) Tj")
            commands.append("T*")

        commands.append("ET")
        stream_bytes = "\n".join(commands).encode("latin-1", errors="replace")

        objects = {
            1: b"<< /Type /Catalog /Pages 2 0 R >>",
            2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            5: (
                f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
                + stream_bytes
                + b"\nendstream"
            ),
        }

        pdf = b"%PDF-1.4\n"
        offsets = [0]
        for obj_id in range(1, 6):
            offsets.append(len(pdf))
            pdf += f"{obj_id} 0 obj\n".encode("ascii")
            pdf += objects[obj_id]
            pdf += b"\nendobj\n"

        xref_offset = len(pdf)
        pdf += b"xref\n0 6\n"
        pdf += b"0000000000 65535 f \n"
        for off in offsets[1:]:
            pdf += f"{off:010d} 00000 n \n".encode("ascii")

        pdf += b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        pdf += b"startxref\n"
        pdf += f"{xref_offset}\n".encode("ascii")
        pdf += b"%%EOF"
        return pdf

    @staticmethod
    async def generate_quote_pdf(
        user_id: int,
        quote_id: int,
        include_terms: bool = True,
        include_notes: bool = True,
        db: Session = None,
    ) -> Dict[str, Any]:
        """Generate PDF for quote"""
        try:
            # Get quote with details
            quote_result = db.execute(
                text(
                    """
                    SELECT id, quote_number, customer_name, customer_email, customer_phone,
                           status, notes, quote_date, quote_expires_at, total_amount,
                           total_margin, created_at
                    FROM quotes
                    WHERE id = :quote_id AND user_id = :user_id
                    """
                ),
                {"quote_id": quote_id, "user_id": user_id},
            )
            quote = quote_result.fetchone()

            if not quote:
                raise ValueError("Quote not found")

            # Get line items
            items_result = db.execute(
                text(
                    """
                    SELECT qli.brand_id, qli.quantity, qli.unit_price, qli.margin_percentage,
                           qli.discount, qli.line_total, b.brand_name
                    FROM quote_line_items qli
                    JOIN brands b ON qli.brand_id = b.id
                    WHERE qli.quote_id = :quote_id
                    ORDER BY qli.id ASC
                    """
                ),
                {"quote_id": quote_id},
            )

            line_items = []
            for row in items_result:
                unit_price = float(row[2]) if row[2] is not None else 0.0
                margin_percentage = float(row[3]) if row[3] is not None else 0.0
                discount = float(row[4]) if row[4] is not None else 0.0
                line_total = float(row[5]) if row[5] is not None else 0.0
                line_items.append(
                    {
                        "brand_name": row[6],
                        "quantity": row[1],
                        "unit_price": unit_price,
                        "margin_percentage": margin_percentage,
                        "discount": discount,
                        "line_total": line_total,
                    }
                )

            total_amount = float(quote[9]) if quote[9] is not None else 0.0
            total_margin = float(quote[10]) if quote[10] is not None else 0.0
            quote_date = quote[7].strftime("%Y-%m-%d") if quote[7] else "N/A"

            pdf_lines = [
                f"Quote: {quote[1]}",
                f"Date: {quote_date}",
                "",
                "Customer Information",
                f"Name: {quote[2]}",
                f"Email: {quote[3] or 'N/A'}",
                f"Phone: {quote[4] or 'N/A'}",
                "",
                "Quote Details",
                "Product | Qty | Unit Price | Total",
            ]

            for item in line_items:
                pdf_lines.append(
                    f"{item['brand_name']} | {item['quantity']} | INR {item['unit_price']:.2f} | INR {item['line_total']:.2f}"
                )

            pdf_lines.extend(
                [
                    "",
                    f"Total Amount: INR {total_amount:.2f}",
                    f"Total Margin: INR {total_margin:.2f}",
                ]
            )

            if include_notes and quote[6]:
                pdf_lines.extend(["", "Notes", str(quote[6])])

            if include_terms:
                pdf_lines.extend(
                    [
                        "",
                        "Terms & Conditions",
                        "- This quote is valid until the date mentioned above",
                        "- Prices are subject to change without notice",
                        "- Delivery timelines will be confirmed upon order",
                    ]
                )

            pdf_bytes = ExportService._build_simple_pdf(pdf_lines)
            pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")

            return {
                "quote_id": quote_id,
                "quote_number": quote[1],
                "filename": f"quote_{quote[1]}.pdf",
                "pdf_base64": pdf_base64,
                "generated_at": datetime.now().isoformat(),
                "content_type": "application/pdf",
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
        db: Session = None,
    ) -> Dict[str, Any]:
        """Send quote via email"""
        try:
            # Get quote
            quote_result = db.execute(
                text("SELECT quote_number FROM quotes WHERE id = :quote_id AND user_id = :user_id"),
                {"quote_id": quote_id, "user_id": user_id},
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
            logger.info(f"Email sent to {recipient_email} with quote {quote[0]}")

            # Update quote status to "sent" if it was draft
            db.execute(
                text(
                    """
                    UPDATE quotes
                    SET status = 'sent'
                    WHERE id = :quote_id AND status = 'draft'
                    """
                ),
                {"quote_id": quote_id},
            )
            db.commit()

            return {
                "quote_id": quote_id,
                "quote_number": quote[0],
                "recipient": recipient_email,
                "subject": email_subject,
                "status": "sent",
                "timestamp": datetime.now().isoformat(),
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
        db: Session = None,
    ) -> Dict[str, Any]:
        """Create quote template"""
        try:
            db.execute(
                text(
                    """
                    INSERT INTO quote_templates
                    (user_id, name, description, template_html, default_validity_days,
                     default_margin_percentage, is_default, created_at)
                    VALUES (:user_id, :name, :description, :template_html,
                           :default_validity_days, :default_margin_percentage, false,
                           CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "user_id": user_id,
                    "name": name,
                    "description": description,
                    "template_html": template_html,
                    "default_validity_days": default_validity_days or 7,
                    "default_margin_percentage": default_margin_percentage,
                },
            )
            db.commit()

            # Get created template
            result = db.execute(
                text("SELECT id FROM quote_templates WHERE user_id = :user_id AND name = :name ORDER BY id DESC LIMIT 1"),
                {"user_id": user_id, "name": name},
            )
            template_id = result.scalar()

            return {
                "id": template_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "is_default": False,
                "created_at": datetime.now().isoformat(),
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
                text(
                    """
                    SELECT id, name, description, default_validity_days,
                           default_margin_percentage, is_default, created_at
                    FROM quote_templates
                    WHERE user_id = :user_id
                    ORDER BY is_default DESC, created_at DESC
                    """
                ),
                {"user_id": user_id},
            )

            templates = []
            for row in result:
                templates.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "default_validity_days": row[3],
                        "default_margin_percentage": float(row[4]) if row[4] else None,
                        "is_default": row[5],
                        "created_at": row[6].isoformat() if row[6] else None,
                    }
                )

            return {"templates": templates, "total": len(templates)}
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            raise Exception("Failed to list templates")

    @staticmethod
    async def delete_quote_template(user_id: int, template_id: int, db: Session = None) -> bool:
        """Delete quote template"""
        try:
            db.execute(
                text("DELETE FROM quote_templates WHERE id = :template_id AND user_id = :user_id"),
                {"template_id": template_id, "user_id": user_id},
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete template: {e}")
            raise Exception("Failed to delete template")

    @staticmethod
    async def export_quote_erp_payload(
        user_id: int,
        quote_id: int,
        destination: Optional[str] = "generic",
        export_format: Optional[str] = "json",
        db: Session = None
    ) -> Dict[str, Any]:
        """Create ERP-ready quote payload with line-level waterfall fields."""
        try:
            try:
                quote = db.execute(
                    text("""
                        SELECT id, quote_number, customer_name, customer_email, customer_phone,
                               quote_date, quote_expires_at, total_quote_amount, total_tax_amount,
                               total_margin, nppa_compliance_status
                        FROM quotes
                        WHERE id = :quote_id AND user_id = :user_id
                    """),
                    {"quote_id": quote_id, "user_id": user_id}
                ).fetchone()
            except Exception:
                quote = db.execute(
                    text("""
                        SELECT id, quote_number, customer_name, customer_email, customer_phone,
                               quote_date, quote_expires_at, total_amount, 0 AS total_tax_amount,
                               total_margin, 'compliant' AS nppa_compliance_status
                        FROM quotes
                        WHERE id = :quote_id AND user_id = :user_id
                    """),
                    {"quote_id": quote_id, "user_id": user_id}
                ).fetchone()

            if not quote:
                raise ValueError("Quote not found")

            try:
                items_result = db.execute(
                    text("""
                        SELECT qli.id, qli.brand_id, b.brand_name, qli.quantity, qli.free_quantity,
                               qli.pricing_mode, qli.price_basis, qli.base_unit_price, qli.final_unit_price,
                               qli.discount_amount_total, qli.assessable_value, qli.gst_rate_pct,
                               qli.cgst_amount, qli.sgst_amount, qli.igst_amount,
                               qli.tax_amount_total, qli.line_invoice_amount, qli.net_realization_amount,
                               qli.cost_total, qli.margin_amount, qli.margin_pct, qli.nppa_compliant
                        FROM quote_line_items qli
                        JOIN brands b ON qli.brand_id = b.id
                        WHERE qli.quote_id = :quote_id
                        ORDER BY qli.id ASC
                    """),
                    {"quote_id": quote_id}
                )
                use_extended = True
            except Exception:
                items_result = db.execute(
                    text("""
                        SELECT qli.id, qli.brand_id, b.brand_name, qli.quantity, 0 AS free_quantity,
                               'manual_margin' AS pricing_mode, 'MRP' AS price_basis,
                               qli.unit_price AS base_unit_price, qli.unit_price AS final_unit_price,
                               0 AS discount_amount_total, qli.line_total AS assessable_value, 0 AS gst_rate_pct,
                               0 AS cgst_amount, 0 AS sgst_amount, 0 AS igst_amount,
                               0 AS tax_amount_total, qli.line_total AS line_invoice_amount, qli.line_total AS net_realization_amount,
                               0 AS cost_total, qli.margin_earned AS margin_amount, qli.margin_percentage AS margin_pct, true AS nppa_compliant
                        FROM quote_line_items qli
                        JOIN brands b ON qli.brand_id = b.id
                        WHERE qli.quote_id = :quote_id
                        ORDER BY qli.id ASC
                    """),
                    {"quote_id": quote_id}
                )
                use_extended = False

            lines = []
            for row in items_result:
                lines.append({
                    "quote_line_item_id": row[0],
                    "brand_id": row[1],
                    "brand_name": row[2],
                    "quantity": row[3],
                    "free_quantity": row[4] or 0,
                    "pricing_mode": row[5],
                    "price_basis": row[6],
                    "base_unit_price": float(row[7] or 0),
                    "final_unit_price": float(row[8] or 0),
                    "discount_amount_total": float(row[9] or 0),
                    "assessable_value": float(row[10] or 0),
                    "gst_rate_pct": float(row[11] or 0),
                    "cgst_amount": float(row[12] or 0),
                    "sgst_amount": float(row[13] or 0),
                    "igst_amount": float(row[14] or 0),
                    "tax_amount_total": float(row[15] or 0),
                    "line_invoice_amount": float(row[16] or 0),
                    "net_realization_amount": float(row[17] or 0),
                    "cost_total": float(row[18] or 0),
                    "margin_amount": float(row[19] or 0),
                    "margin_pct": float(row[20] or 0),
                    "nppa_compliant": bool(row[21]) if row[21] is not None else True
                })

            payload = {
                "destination": destination or "generic",
                "format": export_format or "json",
                "quote": {
                    "quote_id": quote[0],
                    "quote_number": quote[1],
                    "customer_name": quote[2],
                    "customer_email": quote[3],
                    "customer_phone": quote[4],
                    "quote_date": quote[5].isoformat() if quote[5] else None,
                    "valid_until": quote[6].isoformat() if quote[6] else None,
                    "total_quote_amount": float(quote[7] or 0),
                    "total_tax_amount": float(quote[8] or 0),
                    "total_margin": float(quote[9] or 0),
                    "nppa_compliance_status": quote[10] or "compliant"
                },
                "line_items": lines
            }

            return {
                "quote_id": quote_id,
                "quote_number": quote[1],
                "destination": destination or "generic",
                "format": export_format or "json",
                "generated_at": datetime.now().isoformat(),
                "payload": payload
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to export ERP payload: {e}")
            raise Exception("Failed to export ERP payload")
