"""
Quote service
Business logic for quote management and generation
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from decimal import Decimal
import random
import string

from app.services.pricing import PricingEngineService

logger = logging.getLogger(__name__)

class QuoteService:
    """Quote service for managing quotes"""

    @staticmethod
    def _column_exists(db: Session, table_name: str, column_name: str) -> bool:
        """Check if a column exists in public schema."""
        row = db.execute(
            text("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
                LIMIT 1
            """),
            {"table_name": table_name, "column_name": column_name}
        ).fetchone()
        return bool(row)

    @staticmethod
    def _resolve_base_price(item: Dict[str, Any], cost_price: Decimal, mrp: Decimal, ptr: Optional[Decimal], pts: Optional[Decimal]) -> Decimal:
        """Resolve base price from selected price basis."""
        basis = (item.get("price_basis") or "MRP").upper()
        if basis == "PTR" and ptr is not None:
            return Decimal(ptr)
        if basis == "PTS" and pts is not None:
            return Decimal(pts)
        return Decimal(mrp)

    @staticmethod
    def _split_gst(gst_rate_pct: Decimal, seller_state: Optional[str], pos_state: Optional[str]) -> Dict[str, Decimal]:
        """Split GST as CGST/SGST for intra-state or IGST for inter-state."""
        if seller_state and pos_state and seller_state.upper() == pos_state.upper():
            half = gst_rate_pct / Decimal("2")
            return {
                "cgst_pct": half,
                "sgst_pct": half,
                "igst_pct": Decimal("0")
            }
        return {
            "cgst_pct": Decimal("0"),
            "sgst_pct": Decimal("0"),
            "igst_pct": gst_rate_pct
        }

    @staticmethod
    def _get_gst_rate(brand_id: int, user_id: str, item_gst_rate: Optional[float], db: Session) -> Decimal:
        """Fetch GST rate from payload or tax table via brand HSN."""
        if item_gst_rate is not None:
            return Decimal(str(item_gst_rate))

        try:
            row = db.execute(
                text("""
                    SELECT tgr.gst_rate
                    FROM brands b
                    JOIN tax_gst_rules tgr ON tgr.hsn_code = b.hsn_code
                    WHERE b.id = :brand_id
                      AND b.user_id = :user_id
                      AND tgr.is_active = true
                      AND tgr.effective_from <= CURRENT_DATE
                      AND (tgr.effective_to IS NULL OR tgr.effective_to >= CURRENT_DATE)
                    ORDER BY tgr.effective_from DESC
                    LIMIT 1
                """),
                {"brand_id": brand_id, "user_id": user_id}
            ).fetchone()
            return Decimal(str(row[0])) if row and row[0] is not None else Decimal("0")
        except Exception:
            # Backward-compatible fallback when tax tables/columns are not present yet.
            return Decimal("0")
    
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
        customer_id: Optional[int],
        seller_state_code: Optional[str],
        place_of_supply_state_code: Optional[str],
        price_basis: Optional[str],
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
            total_amount = Decimal("0")
            total_margin = Decimal("0")
            total_discount = Decimal("0")
            total_tax = Decimal("0")
            total_items = len(line_items)
            
            # Validate and calculate line items
            processed_items = []
            for item in line_items:
                # Get brand details
                result = db.execute(
                    text("""
                        SELECT cost_price, mrp, ptr, pts, is_nppa_controlled, nppa_margin_limit
                        FROM brands 
                        WHERE id = :brand_id AND user_id = :user_id AND is_active = true
                    """),
                    {"brand_id": item["brand_id"], "user_id": user_id}
                )
                brand = result.fetchone()
                
                if not brand:
                    raise ValueError(f"Brand {item['brand_id']} not found")
                
                cost_price, mrp, ptr, pts, is_nppa_controlled, nppa_margin_limit = brand
                cost_price = Decimal(cost_price)
                mrp = Decimal(mrp)

                line_price_basis = item.get("price_basis")
                if hasattr(line_price_basis, "value"):
                    line_price_basis = line_price_basis.value
                item["price_basis"] = line_price_basis or (price_basis or "MRP")

                base_price = QuoteService._resolve_base_price(item, cost_price, mrp, ptr, pts)
                pricing_mode = item.get("pricing_mode")
                if hasattr(pricing_mode, "value"):
                    pricing_mode = pricing_mode.value
                pricing_mode = pricing_mode or "manual_margin"

                # Determine candidate unit price
                if pricing_mode == "rule_based":
                    rule_calc = await PricingEngineService.calculate_price(
                        user_id=user_id,
                        brand_id=item["brand_id"],
                        customer_type_id=customer_type_id,
                        quantity=int(item["quantity"]),
                        db=db
                    )
                    candidate_unit_price = Decimal(str(rule_calc["unit_price"]))
                elif pricing_mode == "elasticity_recommended":
                    recommendation = await PricingEngineService.recommend_price(
                        user_id=user_id,
                        brand_id=item["brand_id"],
                        customer_type_id=customer_type_id,
                        quantity=int(item["quantity"]),
                        current_unit_price=item.get("unit_price"),
                        channel=None,
                        region_code=None,
                        db=db
                    )
                    candidate_unit_price = Decimal(str(recommendation["options"]["elasticity_recommended"]["unit_price"]))
                elif item.get("unit_price"):
                    candidate_unit_price = Decimal(str(item["unit_price"]))
                elif item.get("margin_percentage"):
                    margin_pct = Decimal(str(item["margin_percentage"]))
                    candidate_unit_price = cost_price * (Decimal("1") + (margin_pct / Decimal("100")))
                else:
                    candidate_unit_price = base_price

                # Hard cap at MRP
                candidate_unit_price = min(candidate_unit_price, mrp)

                # Additional India discount stack
                retailer_discount = Decimal(str(item.get("retailer_discount_pct", 0) or 0))
                stockist_discount = Decimal(str(item.get("stockist_discount_pct", 0) or 0))
                scheme_discount = Decimal(str(item.get("scheme_discount_pct", 0) or 0))
                cash_discount = Decimal(str(item.get("cash_discount_pct", 0) or 0))
                volume_discount = Decimal(str(item.get("volume_discount_pct", 0) or 0))
                legacy_discount = Decimal(str(item.get("discount", 0) or 0))
                total_discount_pct = retailer_discount + stockist_discount + scheme_discount + cash_discount + volume_discount + legacy_discount
                total_discount_pct = max(Decimal("0"), min(total_discount_pct, Decimal("100")))

                final_unit_price = candidate_unit_price * (Decimal("1") - total_discount_pct / Decimal("100"))

                # NPPA guardrail using final unit economics
                margin_pct_final = ((final_unit_price - cost_price) / cost_price * Decimal("100")) if cost_price > 0 else Decimal("0")
                nppa_compliant = True
                if is_nppa_controlled and nppa_margin_limit is not None:
                    if margin_pct_final > Decimal(str(nppa_margin_limit)):
                        nppa_compliant = False
                        raise ValueError(
                            f"NPPA non-compliant price for brand {item['brand_id']}: "
                            f"margin {margin_pct_final:.2f}% exceeds {Decimal(str(nppa_margin_limit)):.2f}%"
                        )

                # Waterfall components
                quantity = int(item["quantity"])
                freight_amount = Decimal(str(item.get("freight_amount", 0) or 0))
                handling_amount = Decimal(str(item.get("handling_amount", 0) or 0))
                other_charges_amount = Decimal(str(item.get("other_charges_amount", 0) or 0))
                claim_rebate_amount = Decimal(str(item.get("claim_rebate_amount", 0) or 0))

                pre_discount_total = candidate_unit_price * Decimal(quantity)
                post_discount_total = final_unit_price * Decimal(quantity)
                discount_amount_total = pre_discount_total - post_discount_total
                assessable_value = post_discount_total + freight_amount + handling_amount + other_charges_amount

                gst_rate_pct = QuoteService._get_gst_rate(
                    brand_id=item["brand_id"],
                    user_id=user_id,
                    item_gst_rate=item.get("gst_rate_pct"),
                    db=db
                )
                gst_split = QuoteService._split_gst(
                    gst_rate_pct=gst_rate_pct,
                    seller_state=seller_state_code,
                    pos_state=place_of_supply_state_code
                )
                tax_amount_total = assessable_value * gst_rate_pct / Decimal("100")
                cgst_amount = assessable_value * gst_split["cgst_pct"] / Decimal("100")
                sgst_amount = assessable_value * gst_split["sgst_pct"] / Decimal("100")
                igst_amount = assessable_value * gst_split["igst_pct"] / Decimal("100")

                line_invoice_amount = assessable_value + tax_amount_total
                net_realization_amount = line_invoice_amount - claim_rebate_amount
                line_total = line_invoice_amount
                cost_total = cost_price * Decimal(quantity)
                line_margin = net_realization_amount - cost_total
                margin_per_unit = (net_realization_amount / Decimal(quantity)) - cost_price if quantity > 0 else Decimal("0")
                actual_margin = (line_margin / cost_total * Decimal("100")) if cost_total > 0 else Decimal("0")

                total_amount += line_total
                total_margin += line_margin
                total_discount += discount_amount_total
                total_tax += tax_amount_total
                
                processed_items.append({
                    "brand_id": item["brand_id"],
                    "quantity": quantity,
                    "unit_price": final_unit_price,
                    "margin_percentage": actual_margin,
                    "discount": item.get("discount", 0),
                    "line_total": line_total,
                    "margin_earned": line_margin,
                    "pricing_mode": pricing_mode,
                    "price_basis": item.get("price_basis", (price_basis or "MRP")),
                    "base_unit_price": candidate_unit_price,
                    "final_unit_price": final_unit_price,
                    "retailer_discount_pct": retailer_discount,
                    "stockist_discount_pct": stockist_discount,
                    "scheme_discount_pct": scheme_discount,
                    "cash_discount_pct": cash_discount,
                    "volume_discount_pct": volume_discount,
                    "discount_amount_total": discount_amount_total,
                    "freight_amount": freight_amount,
                    "handling_amount": handling_amount,
                    "other_charges_amount": other_charges_amount,
                    "assessable_value": assessable_value,
                    "gst_rate_pct": gst_rate_pct,
                    "cgst_pct": gst_split["cgst_pct"],
                    "sgst_pct": gst_split["sgst_pct"],
                    "igst_pct": gst_split["igst_pct"],
                    "cgst_amount": cgst_amount,
                    "sgst_amount": sgst_amount,
                    "igst_amount": igst_amount,
                    "tax_amount_total": tax_amount_total,
                    "line_invoice_amount": line_invoice_amount,
                    "claim_rebate_amount": claim_rebate_amount,
                    "net_realization_amount": net_realization_amount,
                    "cost_total": cost_total,
                    "margin_amount": line_margin,
                    "margin_pct": actual_margin,
                    "nppa_compliant": nppa_compliant,
                    "override_reason": item.get("override_reason")
                })
            
            # Insert quote
            valid_until = datetime.now() + timedelta(days=validity_days)
            
            quote_payload = {
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
                "total_margin": total_margin,
                "total_discount_amount": total_discount,
                "total_tax_amount": total_tax,
                "total_quote_amount": total_amount,
                "nppa_compliance_status": "compliant",
                "price_basis": price_basis or "MRP",
                "customer_id": customer_id,
                "seller_state_code": seller_state_code,
                "place_of_supply_state_code": place_of_supply_state_code
            }
            use_extended_quote = QuoteService._column_exists(db, "quotes", "total_discount_amount")
            if use_extended_quote:
                db.execute(
                    text("""
                        INSERT INTO quotes 
                        (user_id, quote_number, customer_name, customer_email, customer_phone,
                         customer_type_id, status, notes, quote_date, quote_expires_at,
                         total_amount, total_margin, total_discount_amount, total_tax_amount, total_quote_amount,
                         nppa_compliance_status, price_basis, customer_id, seller_state_code, place_of_supply_state_code,
                         created_at)
                        VALUES (:user_id, :quote_number, :customer_name, :customer_email,
                               :customer_phone, :customer_type_id, :status, :notes,
                               CURRENT_TIMESTAMP, :valid_until, :total_amount, :total_margin, :total_discount_amount,
                               :total_tax_amount, :total_quote_amount, :nppa_compliance_status, :price_basis, :customer_id,
                               :seller_state_code, :place_of_supply_state_code,
                               CURRENT_TIMESTAMP)
                    """),
                    quote_payload
                )
            else:
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
                    quote_payload
                )
            db.commit()
            
            # Get created quote ID
            result = db.execute(
                text("SELECT id FROM quotes WHERE quote_number = :quote_number"),
                {"quote_number": quote_number}
            )
            quote_id = result.scalar()
            
            # Insert line items
            use_extended_line = QuoteService._column_exists(db, "quote_line_items", "pricing_mode")
            for item in processed_items:
                line_payload = {
                    "quote_id": quote_id,
                    "brand_id": item["brand_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "margin_percentage": item["margin_percentage"],
                    "discount": item["discount"],
                    "line_total": item["line_total"],
                    "margin_earned": item["margin_earned"],
                    "pricing_mode": item["pricing_mode"],
                    "price_basis": item["price_basis"],
                    "base_unit_price": item["base_unit_price"],
                    "final_unit_price": item["final_unit_price"],
                    "retailer_discount_pct": item["retailer_discount_pct"],
                    "stockist_discount_pct": item["stockist_discount_pct"],
                    "scheme_discount_pct": item["scheme_discount_pct"],
                    "cash_discount_pct": item["cash_discount_pct"],
                    "volume_discount_pct": item["volume_discount_pct"],
                    "discount_amount_total": item["discount_amount_total"],
                    "freight_amount": item["freight_amount"],
                    "handling_amount": item["handling_amount"],
                    "other_charges_amount": item["other_charges_amount"],
                    "assessable_value": item["assessable_value"],
                    "gst_rate_pct": item["gst_rate_pct"],
                    "cgst_pct": item["cgst_pct"],
                    "sgst_pct": item["sgst_pct"],
                    "igst_pct": item["igst_pct"],
                    "cgst_amount": item["cgst_amount"],
                    "sgst_amount": item["sgst_amount"],
                    "igst_amount": item["igst_amount"],
                    "tax_amount_total": item["tax_amount_total"],
                    "line_invoice_amount": item["line_invoice_amount"],
                    "claim_rebate_amount": item["claim_rebate_amount"],
                    "net_realization_amount": item["net_realization_amount"],
                    "cost_total": item["cost_total"],
                    "margin_amount": item["margin_amount"],
                    "margin_pct": item["margin_pct"],
                    "nppa_compliant": item["nppa_compliant"],
                    "override_reason": item["override_reason"]
                }
                if use_extended_line:
                    db.execute(
                        text("""
                            INSERT INTO quote_line_items 
                            (quote_id, brand_id, quantity, unit_price, margin_percentage, 
                             discount, line_total, margin_earned, pricing_mode, price_basis,
                             base_unit_price, final_unit_price, retailer_discount_pct, stockist_discount_pct,
                             scheme_discount_pct, cash_discount_pct, volume_discount_pct, discount_amount_total,
                             freight_amount, handling_amount, other_charges_amount, assessable_value, gst_rate_pct,
                             cgst_pct, sgst_pct, igst_pct, cgst_amount, sgst_amount, igst_amount, tax_amount_total,
                             line_invoice_amount, claim_rebate_amount, net_realization_amount, cost_total,
                             margin_amount, margin_pct, nppa_compliant, override_reason, created_at)
                            VALUES (:quote_id, :brand_id, :quantity, :unit_price, 
                                   :margin_percentage, :discount, :line_total, :margin_earned, :pricing_mode, :price_basis,
                                   :base_unit_price, :final_unit_price, :retailer_discount_pct, :stockist_discount_pct,
                                   :scheme_discount_pct, :cash_discount_pct, :volume_discount_pct, :discount_amount_total,
                                   :freight_amount, :handling_amount, :other_charges_amount, :assessable_value, :gst_rate_pct,
                                   :cgst_pct, :sgst_pct, :igst_pct, :cgst_amount, :sgst_amount, :igst_amount, :tax_amount_total,
                                   :line_invoice_amount, :claim_rebate_amount, :net_realization_amount, :cost_total,
                                   :margin_amount, :margin_pct, :nppa_compliant, :override_reason,
                                   CURRENT_TIMESTAMP)
                        """),
                        line_payload
                    )
                else:
                    db.execute(
                        text("""
                            INSERT INTO quote_line_items 
                            (quote_id, brand_id, quantity, unit_price, margin_percentage, 
                             discount, line_total, margin_earned, created_at)
                            VALUES (:quote_id, :brand_id, :quantity, :unit_price, 
                                   :margin_percentage, :discount, :line_total, :margin_earned,
                                   CURRENT_TIMESTAMP)
                        """),
                        line_payload
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
            use_extended_quote = QuoteService._column_exists(db, "quotes", "total_discount_amount")
            use_extended_line = QuoteService._column_exists(db, "quote_line_items", "pricing_mode")

            if use_extended_quote:
                result = db.execute(
                    text("""
                        SELECT id, quote_number, customer_name, customer_email, customer_phone,
                               customer_type_id, customer_id, seller_state_code, place_of_supply_state_code,
                               price_basis, status, notes, quote_date, quote_expires_at,
                               total_amount, total_margin, total_discount_amount, total_tax_amount, total_quote_amount,
                               nppa_compliance_status, created_at, updated_at
                        FROM quotes 
                        WHERE id = :quote_id AND user_id = :user_id
                    """),
                    {"quote_id": quote_id, "user_id": user_id}
                )
                quote = result.fetchone()
            else:
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
            if use_extended_line:
                items_result = db.execute(
                    text("""
                        SELECT id, brand_id, quantity, unit_price, margin_percentage,
                               discount, line_total, margin_earned, pricing_mode, price_basis,
                               base_unit_price, final_unit_price, discount_amount_total, assessable_value,
                               tax_amount_total, line_invoice_amount, net_realization_amount,
                               margin_amount, margin_pct, nppa_compliant, confidence_score, model_version, created_at
                        FROM quote_line_items 
                        WHERE quote_id = :quote_id
                        ORDER BY id ASC
                    """),
                    {"quote_id": quote_id}
                )
            else:
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
                if use_extended_line:
                    line_items.append({
                        "id": row[0],
                        "brand_id": row[1],
                        "quantity": row[2],
                        "unit_price": float(row[3]),
                        "margin_percentage": float(row[4]),
                        "discount": float(row[5]) if row[5] else 0,
                        "line_total": float(row[6]),
                        "margin_earned": float(row[7]),
                        "pricing_mode": row[8],
                        "price_basis": row[9],
                        "base_unit_price": float(row[10]) if row[10] is not None else 0.0,
                        "final_unit_price": float(row[11]) if row[11] is not None else 0.0,
                        "discount_amount_total": float(row[12]) if row[12] is not None else 0.0,
                        "assessable_value": float(row[13]) if row[13] is not None else 0.0,
                        "tax_amount_total": float(row[14]) if row[14] is not None else 0.0,
                        "line_invoice_amount": float(row[15]) if row[15] is not None else 0.0,
                        "net_realization_amount": float(row[16]) if row[16] is not None else 0.0,
                        "margin_amount": float(row[17]) if row[17] is not None else 0.0,
                        "margin_pct": float(row[18]) if row[18] is not None else 0.0,
                        "nppa_compliant": bool(row[19]) if row[19] is not None else True,
                        "confidence_score": float(row[20]) if row[20] is not None else None,
                        "model_version": row[21],
                        "created_at": row[22]
                    })
                else:
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

            if use_extended_quote:
                return {
                    "id": quote[0],
                    "user_id": user_id,
                    "quote_number": quote[1],
                    "customer_name": quote[2],
                    "customer_email": quote[3],
                    "customer_phone": quote[4],
                    "customer_type_id": quote[5],
                    "customer_id": quote[6],
                    "seller_state_code": quote[7],
                    "place_of_supply_state_code": quote[8],
                    "price_basis": quote[9],
                    "status": quote[10],
                    "notes": quote[11],
                    "quote_date": quote[12],
                    "valid_until": quote[13],
                    "total_amount": float(quote[14]),
                    "total_margin": float(quote[15]),
                    "total_discount_amount": float(quote[16]) if quote[16] is not None else 0.0,
                    "total_tax_amount": float(quote[17]) if quote[17] is not None else 0.0,
                    "total_quote_amount": float(quote[18]) if quote[18] is not None else float(quote[14]),
                    "nppa_compliance_status": quote[19] or "compliant",
                    "total_items": len(line_items),
                    "line_items": line_items,
                    "created_at": quote[20],
                    "updated_at": quote[21]
                }

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
                "total_discount_amount": 0.0,
                "total_tax_amount": 0.0,
                "total_quote_amount": float(quote[10]),
                "nppa_compliance_status": "compliant",
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
