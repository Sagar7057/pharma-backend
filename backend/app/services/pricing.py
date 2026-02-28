"""
Pricing Engine Service
Core pricing calculation logic
"""

import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date

logger = logging.getLogger(__name__)

class PricingEngineService:
    """Pricing engine for calculating prices and checking compliance"""
    
    @staticmethod
    async def calculate_price(
        user_id: int,
        brand_id: int,
        customer_type_id: Optional[int],
        quantity: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Calculate price for a brand
        
        Algorithm:
        1. Get brand details (MRP, cost price)
        2. Check for custom pricing rule
        3. Apply customer type margin if no rule
        4. Apply volume discount if applicable
        5. Cap at MRP
        6. Check NPPA compliance
        """
        try:
            # Get brand details
            brand_result = db.execute(
                text("""
                    SELECT cost_price, mrp, is_nppa_controlled, nppa_margin_limit
                    FROM brands 
                    WHERE id = :brand_id AND user_id = :user_id AND is_active = true
                """),
                {"brand_id": brand_id, "user_id": user_id}
            )
            brand = brand_result.fetchone()
            
            if not brand:
                raise ValueError("Brand not found")
            
            cost_price, mrp, is_nppa_controlled, nppa_margin_limit = brand
            
            # Try to get custom pricing rule
            rule = None
            if customer_type_id:
                rule_result = db.execute(
                    text("""
                        SELECT margin_percentage, sell_price, volume_discount, min_quantity, max_quantity
                        FROM pricing_rules 
                        WHERE user_id = :user_id 
                        AND brand_id = :brand_id 
                        AND customer_type_id = :customer_type_id
                        AND is_active = true
                        AND (valid_from IS NULL OR valid_from <= CURRENT_DATE)
                        AND (valid_until IS NULL OR valid_until >= CURRENT_DATE)
                        LIMIT 1
                    """),
                    {
                        "user_id": user_id,
                        "brand_id": brand_id,
                        "customer_type_id": customer_type_id
                    }
                )
                rule = rule_result.fetchone()
            
            # Calculate sell price
            margin_percentage = 0
            volume_discount = 0
            
            if rule:
                # Use custom rule
                if rule[1]:  # sell_price is set
                    sell_price = rule[1]
                else:
                    margin_percentage = rule[0] or 0
                    sell_price = cost_price * (1 + margin_percentage / 100)
                
                # Apply volume discount if quantity matches
                if rule[3] and rule[4]:  # min and max quantity
                    if rule[3] <= quantity <= rule[4]:
                        volume_discount = rule[2] or 0
                elif rule[3]:  # only min quantity
                    if quantity >= rule[3]:
                        volume_discount = rule[2] or 0
            else:
                # Use customer type default margin or brand default
                if customer_type_id:
                    type_result = db.execute(
                        text("""
                            SELECT default_margin FROM customer_types 
                            WHERE id = :customer_type_id AND user_id = :user_id
                        """),
                        {"customer_type_id": customer_type_id, "user_id": user_id}
                    )
                    type_row = type_result.fetchone()
                    if type_row:
                        margin_percentage = type_row[0] or 0
                
                # Fallback to brand default margin
                brand_margin_result = db.execute(
                    text("""
                        SELECT default_margin FROM brands 
                        WHERE id = :brand_id AND user_id = :user_id
                    """),
                    {"brand_id": brand_id, "user_id": user_id}
                )
                brand_margin_row = brand_margin_result.fetchone()
                if brand_margin_row and brand_margin_row[0]:
                    margin_percentage = brand_margin_row[0]
                
                # Calculate base sell price
                sell_price = cost_price * (1 + margin_percentage / 100)
            
            # Apply volume discount
            if volume_discount > 0:
                sell_price = sell_price * (1 - volume_discount / 100)
            
            # Cap at MRP
            sell_price = min(sell_price, mrp)
            
            # Recalculate margin based on final sell price
            final_margin_percentage = ((sell_price - cost_price) / cost_price * 100) if cost_price > 0 else 0
            
            # Check NPPA compliance
            nppa_compliant = True
            nppa_message = "Compliant"
            
            if is_nppa_controlled and nppa_margin_limit:
                if final_margin_percentage > nppa_margin_limit:
                    nppa_compliant = False
                    nppa_message = f"Margin {final_margin_percentage:.2f}% exceeds NPPA limit of {nppa_margin_limit}%"
            
            # Calculate totals
            margin_earned = (sell_price - cost_price) * quantity
            total_amount = sell_price * quantity
            
            return {
                "brand_id": brand_id,
                "cost_price": float(cost_price),
                "mrp": float(mrp),
                "unit_price": float(sell_price),
                "quantity": quantity,
                "margin_percentage": float(final_margin_percentage),
                "margin_per_unit": float(sell_price - cost_price),
                "total_margin": float(margin_earned),
                "total_amount": float(total_amount),
                "volume_discount": volume_discount,
                "nppa_controlled": is_nppa_controlled,
                "nppa_compliant": nppa_compliant,
                "nppa_message": nppa_message
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate price: {e}")
            raise Exception("Failed to calculate price")
    
    @staticmethod
    async def check_nppa_compliance(
        brand_id: int,
        proposed_price: float,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Check if proposed price is NPPA compliant"""
        try:
            # Get brand details
            result = db.execute(
                text("""
                    SELECT cost_price, is_nppa_controlled, nppa_margin_limit
                    FROM brands 
                    WHERE id = :brand_id AND user_id = :user_id AND is_active = true
                """),
                {"brand_id": brand_id, "user_id": user_id}
            )
            row = result.fetchone()
            
            if not row:
                raise ValueError("Brand not found")
            
            cost_price, is_nppa_controlled, nppa_margin_limit = row
            
            # Calculate margin
            margin_percentage = ((proposed_price - cost_price) / cost_price * 100) if cost_price > 0 else 0
            
            # Check compliance
            is_compliant = True
            message = "Price is NPPA compliant"
            
            if is_nppa_controlled:
                if not nppa_margin_limit:
                    return {
                        "brand_id": brand_id,
                        "proposed_price": float(proposed_price),
                        "cost_price": float(cost_price),
                        "margin_percentage": float(margin_percentage),
                        "is_nppa_controlled": is_nppa_controlled,
                        "is_compliant": True,
                        "message": "NPPA controlled but no margin limit set"
                    }
                
                if margin_percentage > nppa_margin_limit:
                    is_compliant = False
                    message = f"Margin {margin_percentage:.2f}% exceeds NPPA limit of {nppa_margin_limit}%"
            
            return {
                "brand_id": brand_id,
                "proposed_price": float(proposed_price),
                "cost_price": float(cost_price),
                "margin_percentage": float(margin_percentage),
                "is_nppa_controlled": is_nppa_controlled,
                "nppa_limit": float(nppa_margin_limit) if nppa_margin_limit else None,
                "is_compliant": is_compliant,
                "message": message
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to check NPPA compliance: {e}")
            raise Exception("Failed to check NPPA compliance")
    
    @staticmethod
    async def get_nppa_data(brand_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Get NPPA controlled drug information"""
        try:
            result = db.execute(
                text("""
                    SELECT drug_name, salt_name, strength, max_allowed_margin, price_cap
                    FROM nppa_controlled_drugs 
                    WHERE drug_name ILIKE (
                        SELECT brand_name FROM brands WHERE id = :brand_id LIMIT 1
                    )
                    LIMIT 1
                """),
                {"brand_id": brand_id}
            )
            row = result.fetchone()
            
            if not row:
                return None
            
            return {
                "drug_name": row[0],
                "salt_name": row[1],
                "strength": row[2],
                "max_allowed_margin": float(row[3]) if row[3] else None,
                "price_cap": float(row[4]) if row[4] else None
            }
        except Exception as e:
            logger.error(f"Failed to get NPPA data: {e}")
            return None
