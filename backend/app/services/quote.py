"""
Quote service
Business logic for quote management and generation
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import random
import string

logger = logging.getLogger(__name__)

class QuoteService:
    """Quote service for managing quotes"""
    
    @staticmethod
    def _generate_quote_number(user_id: int) -> str:
        """Generate unique quote number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"QT-{user_id}-{timestamp}-{random_suffix}"
    
    @staticmethod
    async def create_quote(
        user_id: int,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        customer_type_id: Optional[int],
        notes: str,
        line_items: List[Dict[str, Any]],
        validity_days: int,
        db: Session
    ) -> Dict[str, Any]:
        """Create new quote with line items"""
        try:
            # Generate quote number
            quote_number = QuoteService._generate_quote_number(user_id)
            
            # Calculate totals
            total_amount = 0
            total_margin = 0
            total_items = len(line_items)
            
            # Validate and calculate line items
            processed_items = []
            for item in line_items:
                # Get brand details
                result = db.execute(
                    text("""
                        SELECT cost_price, mrp FROM brands 
                        WHERE id = :brand_id AND user_id = :user_id AND is_active = true
                    """),
                    {"brand_id": item["brand_id"], "user_id": user_id}
                )
                brand = result.fetchone()
                
                if not brand:
                    raise ValueError(f"Brand {item['brand_id']} not found")
                
                cost_price, mrp = brand
                
                # Use provided unit_price or calculate from margin
                if item.get("unit_price"):
                    unit_price = item["unit_price"]
                elif item.get("margin_percentage"):
                    unit_price = cost_price * (1 + item["margin_percentage"] / 100)
                    unit_price = min(unit_price, mrp)  # Cap at MRP
                else:
                    unit_price = mrp  # Default to MRP
                
                # Apply discount if provided
                if item.get("discount", 0) > 0:
                    unit_price = unit_price * (1 - item["discount"] / 100)
                
                # Calculate line totals
                line_total = unit_price * item["quantity"]
                margin_per_unit = unit_price - cost_price
                line_margin = margin_per_unit * item["quantity"]
                
                # Recalculate actual margin percentage
                actual_margin = (margin_per_unit / cost_price * 100) if cost_price > 0 else 0
                
                total_amount += line_total
                total_margin += line_margin
                
                processed_items.append({
                    "brand_id": item["brand_id"],
                    "quantity": item["quantity"],
                    "unit_price": unit_price,
                    "margin_percentage": actual_margin,
                    "discount": item.get("discount", 0),
                    "line_total": line_total,
                    "margin_earned": line_margin
                })
            
            # Insert quote
            valid_until = datetime.now() + timedelta(days=validity_days)
            
            db.execute(
                text("""
                    INSERT INTO quotes 
                    (user_id, quote_number, customer_name, customer_email, customer_phone,
                     customer_type_id, status, notes, quote_date, quote_expires_at,
                     total_amount, total_margin, created_at)
                    VALUES (:user_id, :quote_number, :customer_name, :customer_email,
                           :customer_phone, :customer_type_id, :status, :notes,
                           CURRENT_TIMESTAMP, :valid_until, :total_amount, :total_margin,
                           CURRENT_TIMESTAMP)
                """),
                {
                    "user_id": user_id,
                    "quote_number": quote_number,
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "customer_phone": customer_phone,
                    "customer_type_id": customer_type_id,
                    "status": "draft",
                    "notes": notes,
                    "valid_until": valid_until,
                    "total_amount": total_amount,
                    "total_margin": total_margin
                }
            )
            db.commit()
            
            # Get created quote ID
            result = db.execute(
                text("SELECT id FROM quotes WHERE quote_number = :quote_number"),
                {"quote_number": quote_number}
            )
            quote_id = result.scalar()
            
            # Insert line items
            for item in processed_items:
                db.execute(
                    text("""
                        INSERT INTO quote_line_items 
                        (quote_id, brand_id, quantity, unit_price, margin_percentage, 
                         discount, line_total, margin_earned, created_at)
                        VALUES (:quote_id, :brand_id, :quantity, :unit_price, 
                               :margin_percentage, :discount, :line_total, :margin_earned,
                               CURRENT_TIMESTAMP)
                    """),
                    {
                        "quote_id": quote_id,
                        "brand_id": item["brand_id"],
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                        "margin_percentage": item["margin_percentage"],
                        "discount": item["discount"],
                        "line_total": item["line_total"],
                        "margin_earned": item["margin_earned"]
                    }
                )
            
            db.commit()
            
            # Return created quote
            return await QuoteService.get_quote(user_id, quote_id, db)
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create quote: {e}")
            raise Exception("Failed to create quote")
    
    @staticmethod
    async def get_quote(user_id: int, quote_id: int, db: Session) -> Dict[str, Any]:
        """Get single quote with line items"""
        try:
            # Get quote
            result = db.execute(
                text("""
                    SELECT id, quote_number, customer_name, customer_email, customer_phone,
                           customer_type_id, status, notes, quote_date, quote_expires_at,
                           total_amount, total_margin, created_at, updated_at
                    FROM quotes 
                    WHERE id = :quote_id AND user_id = :user_id
                """),
                {"quote_id": quote_id, "user_id": user_id}
            )
            quote = result.fetchone()
            
            if not quote:
                raise ValueError("Quote not found")
            
            # Get line items
            items_result = db.execute(
                text("""
                    SELECT id, brand_id, quantity, unit_price, margin_percentage,
                           discount, line_total, margin_earned, created_at
                    FROM quote_line_items 
                    WHERE quote_id = :quote_id
                    ORDER BY id ASC
                """),
                {"quote_id": quote_id}
            )
            
            line_items = []
            for row in items_result:
                line_items.append({
                    "id": row[0],
                    "brand_id": row[1],
                    "quantity": row[2],
                    "unit_price": float(row[3]),
                    "margin_percentage": float(row[4]),
                    "discount": float(row[5]) if row[5] else 0,
                    "line_total": float(row[6]),
                    "margin_earned": float(row[7]),
                    "created_at": row[8]
                })
            
            return {
                "id": quote[0],
                "user_id": user_id,
                "quote_number": quote[1],
                "customer_name": quote[2],
                "customer_email": quote[3],
                "customer_phone": quote[4],
                "customer_type_id": quote[5],
                "status": quote[6],
                "notes": quote[7],
                "quote_date": quote[8],
                "valid_until": quote[9],
                "total_amount": float(quote[10]),
                "total_margin": float(quote[11]),
                "total_items": len(line_items),
                "line_items": line_items,
                "created_at": quote[12],
                "updated_at": quote[13]
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get quote: {e}")
            raise Exception("Failed to get quote")
    
    @staticmethod
    async def list_quotes(
        user_id: int,
        status: Optional[str],
        customer_name: Optional[str],
        sort_by: Optional[str],
        limit: int,
        offset: int,
        db: Session
    ) -> Dict[str, Any]:
        """List quotes with filtering and pagination"""
        try:
            # Build query
            where_clause = "WHERE user_id = :user_id"
            params = {"user_id": user_id, "limit": limit, "offset": offset}
            
            if status:
                where_clause += " AND status = :status"
                params["status"] = status
            
            if customer_name:
                where_clause += " AND customer_name ILIKE :customer_name"
                params["customer_name"] = f"%{customer_name}%"
            
            # Sort
            order_by = "ORDER BY quote_date DESC"
            if sort_by == "amount":
                order_by = "ORDER BY total_amount DESC"
            elif sort_by == "status":
                order_by = "ORDER BY status ASC, quote_date DESC"
            
            # Count total
            count_result = db.execute(
                text(f"SELECT COUNT(*) FROM quotes {where_clause}"),
                params
            )
            total = count_result.scalar()
            
            # Get quotes
            result = db.execute(
                text(f"""
                    SELECT id, quote_number, customer_name, status, total_amount,
                           total_margin, quote_date, quote_expires_at, created_at
                    FROM quotes 
                    {where_clause}
                    {order_by}
                    LIMIT :limit OFFSET :offset
                """),
                params
            )
            
            quotes = []
            for row in result:
                quotes.append({
                    "id": row[0],
                    "quote_number": row[1],
                    "customer_name": row[2],
                    "status": row[3],
                    "total_amount": float(row[4]),
                    "total_margin": float(row[5]),
                    "quote_date": row[6],
                    "valid_until": row[7],
                    "created_at": row[8]
                })
            
            return {
                "quotes": quotes,
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < total
            }
        except Exception as e:
            logger.error(f"Failed to list quotes: {e}")
            raise Exception("Failed to list quotes")
    
    @staticmethod
    async def update_quote_status(
        user_id: int,
        quote_id: int,
        status: str,
        db: Session
    ) -> Dict[str, Any]:
        """Update quote status"""
        try:
            db.execute(
                text("""
                    UPDATE quotes 
                    SET status = :status, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :quote_id AND user_id = :user_id
                """),
                {"quote_id": quote_id, "user_id": user_id, "status": status}
            )
            db.commit()
            
            return await QuoteService.get_quote(user_id, quote_id, db)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update quote: {e}")
            raise Exception("Failed to update quote")
    
    @staticmethod
    async def delete_quote(user_id: int, quote_id: int, db: Session) -> bool:
        """Delete quote (only if draft)"""
        try:
            # Check if draft
            result = db.execute(
                text("SELECT status FROM quotes WHERE id = :quote_id AND user_id = :user_id"),
                {"quote_id": quote_id, "user_id": user_id}
            )
            row = result.fetchone()
            
            if not row:
                raise ValueError("Quote not found")
            
            if row[0] != "draft":
                raise ValueError("Can only delete draft quotes")
            
            # Delete line items
            db.execute(
                text("DELETE FROM quote_line_items WHERE quote_id = :quote_id"),
                {"quote_id": quote_id}
            )
            
            # Delete quote
            db.execute(
                text("DELETE FROM quotes WHERE id = :quote_id AND user_id = :user_id"),
                {"quote_id": quote_id, "user_id": user_id}
            )
            
            db.commit()
            return True
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete quote: {e}")
            raise Exception("Failed to delete quote")
