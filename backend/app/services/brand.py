"""
Brand service
Business logic for brand management
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import csv
from io import StringIO

logger = logging.getLogger(__name__)

class BrandService:
    """Brand service for CRUD operations"""
    
    @staticmethod
    async def create_brand(
        user_id: int,
        brand_name: str,
        manufacturer: str,
        mrp: float,
        cost_price: float,
        default_margin: float,
        therapeutic_category: str,
        salt_name: str,
        strength: str,
        packing: str,
        gtin_code: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Create new brand
        """
        try:
            # Check if brand already exists for this user
            result = db.execute(
                text("""
                    SELECT id FROM brands 
                    WHERE user_id = :user_id 
                    AND brand_name = :brand_name 
                    AND strength = :strength 
                    AND packing = :packing
                """),
                {
                    "user_id": user_id,
                    "brand_name": brand_name,
                    "strength": strength,
                    "packing": packing
                }
            )
            if result.fetchone():
                raise ValueError("Brand already exists for this configuration")
            
            # Validate prices
            if mrp < cost_price:
                raise ValueError("MRP must be >= Cost Price")
            
            # Insert brand
            db.execute(
                text("""
                    INSERT INTO brands 
                    (user_id, brand_name, manufacturer, mrp, cost_price, 
                     default_margin, therapeutic_category, salt_name, 
                     strength, packing, gtin_code, is_active, created_at, updated_at)
                    VALUES (:user_id, :brand_name, :manufacturer, :mrp, :cost_price,
                           :default_margin, :therapeutic_category, :salt_name,
                           :strength, :packing, :gtin_code, true, 
                           CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {
                    "user_id": user_id,
                    "brand_name": brand_name,
                    "manufacturer": manufacturer,
                    "mrp": mrp,
                    "cost_price": cost_price,
                    "default_margin": default_margin,
                    "therapeutic_category": therapeutic_category,
                    "salt_name": salt_name,
                    "strength": strength,
                    "packing": packing,
                    "gtin_code": gtin_code
                }
            )
            db.commit()
            
            # Get created brand
            result = db.execute(
                text("""
                    SELECT id FROM brands 
                    WHERE user_id = :user_id 
                    AND brand_name = :brand_name 
                    ORDER BY id DESC LIMIT 1
                """),
                {"user_id": user_id, "brand_name": brand_name}
            )
            brand_id = result.scalar()
            
            return await BrandService.get_brand(user_id, brand_id, db)
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create brand: {e}")
            raise Exception("Failed to create brand")
    
    @staticmethod
    async def get_brand(user_id: int, brand_id: int, db: Session) -> Dict[str, Any]:
        """Get single brand"""
        try:
            result = db.execute(
                text("""
                    SELECT id, brand_name, manufacturer, mrp, cost_price, 
                           current_sell_price, default_margin, therapeutic_category,
                           is_nppa_controlled, nppa_margin_limit, salt_name, 
                           strength, packing, gtin_code, is_active, created_at, updated_at
                    FROM brands 
                    WHERE id = :brand_id AND user_id = :user_id
                """),
                {"brand_id": brand_id, "user_id": user_id}
            )
            brand = result.fetchone()
            
            if not brand:
                raise ValueError("Brand not found")
            
            return {
                "id": brand[0],
                "brand_name": brand[1],
                "manufacturer": brand[2],
                "mrp": float(brand[3]),
                "cost_price": float(brand[4]),
                "current_sell_price": float(brand[5]) if brand[5] else None,
                "default_margin": float(brand[6]) if brand[6] else None,
                "therapeutic_category": brand[7],
                "is_nppa_controlled": brand[8],
                "nppa_margin_limit": float(brand[9]) if brand[9] else None,
                "salt_name": brand[10],
                "strength": brand[11],
                "packing": brand[12],
                "gtin_code": brand[13],
                "is_active": brand[14],
                "created_at": brand[15],
                "updated_at": brand[16]
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get brand: {e}")
            raise Exception("Failed to get brand")
    
    @staticmethod
    async def list_brands(
        user_id: int,
        search: Optional[str],
        sort_by: Optional[str],
        limit: int,
        offset: int,
        db: Session
    ) -> Dict[str, Any]:
        """List brands with filtering and pagination"""
        try:
            # Build query
            where_clause = "WHERE user_id = :user_id AND is_active = true"
            params = {"user_id": user_id, "limit": limit, "offset": offset}
            
            if search:
                where_clause += " AND brand_name ILIKE :search"
                params["search"] = f"%{search}%"
            
            # Sort
            order_by = "ORDER BY created_at DESC"
            if sort_by == "margin":
                order_by = "ORDER BY default_margin DESC"
            elif sort_by == "mrp":
                order_by = "ORDER BY mrp DESC"
            elif sort_by == "name":
                order_by = "ORDER BY brand_name ASC"
            
            # Count total
            count_result = db.execute(
                text(f"SELECT COUNT(*) FROM brands {where_clause}"),
                params
            )
            total = count_result.scalar()
            
            # Get brands
            result = db.execute(
                text(f"""
                    SELECT id, brand_name, manufacturer, mrp, cost_price, 
                           current_sell_price, default_margin, therapeutic_category,
                           is_nppa_controlled, salt_name, strength, packing, 
                           gtin_code, is_active, created_at, updated_at
                    FROM brands 
                    {where_clause}
                    {order_by}
                    LIMIT :limit OFFSET :offset
                """),
                params
            )
            
            brands = []
            for row in result:
                brands.append({
                    "id": row[0],
                    "brand_name": row[1],
                    "manufacturer": row[2],
                    "mrp": float(row[3]),
                    "cost_price": float(row[4]),
                    "current_sell_price": float(row[5]) if row[5] else None,
                    "default_margin": float(row[6]) if row[6] else None,
                    "therapeutic_category": row[7],
                    "is_nppa_controlled": row[8],
                    "salt_name": row[9],
                    "strength": row[10],
                    "packing": row[11],
                    "gtin_code": row[12],
                    "is_active": row[13],
                    "created_at": row[14],
                    "updated_at": row[15]
                })
            
            return {
                "brands": brands,
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < total
            }
        except Exception as e:
            logger.error(f"Failed to list brands: {e}")
            raise Exception("Failed to list brands")
    
    @staticmethod
    async def update_brand(
        user_id: int,
        brand_id: int,
        update_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Update brand"""
        try:
            # Build update query
            set_clause = []
            params = {"brand_id": brand_id, "user_id": user_id}
            
            for key, value in update_data.items():
                if value is not None:
                    # Convert snake_case to database column names
                    col_name = key
                    set_clause.append(f"{col_name} = :{key}")
                    params[key] = value
            
            if not set_clause:
                # No updates provided
                return await BrandService.get_brand(user_id, brand_id, db)
            
            set_clause.append("updated_at = CURRENT_TIMESTAMP")
            
            db.execute(
                text(f"""
                    UPDATE brands 
                    SET {', '.join(set_clause)}
                    WHERE id = :brand_id AND user_id = :user_id
                """),
                params
            )
            db.commit()
            
            return await BrandService.get_brand(user_id, brand_id, db)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update brand: {e}")
            raise Exception("Failed to update brand")
    
    @staticmethod
    async def delete_brand(user_id: int, brand_id: int, db: Session) -> bool:
        """Soft delete brand"""
        try:
            db.execute(
                text("""
                    UPDATE brands 
                    SET is_active = false, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :brand_id AND user_id = :user_id
                """),
                {"brand_id": brand_id, "user_id": user_id}
            )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete brand: {e}")
            raise Exception("Failed to delete brand")
    
    @staticmethod
    async def import_csv(
        user_id: int,
        csv_content: str,
        db: Session
    ) -> Dict[str, Any]:
        """Import brands from CSV"""
        try:
            imported = 0
            failed = 0
            skipped = 0
            errors = []
            
            # Parse CSV
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (after header)
                try:
                    # Extract fields
                    brand_name = row.get('Brand', '').strip()
                    manufacturer = row.get('Manufacturer', '').strip()
                    mrp = float(row.get('MRP', 0))
                    cost_price = float(row.get('CostPrice', 0))
                    default_margin = float(row.get('DefaultMargin', 0))
                    
                    # Validate
                    if not brand_name:
                        errors.append({"row": row_num, "error": "Brand name is required"})
                        failed += 1
                        continue
                    
                    if mrp <= 0 or cost_price <= 0:
                        errors.append({"row": row_num, "error": "Prices must be > 0"})
                        failed += 1
                        continue
                    
                    if mrp < cost_price:
                        errors.append({"row": row_num, "error": "MRP must be >= Cost Price"})
                        failed += 1
                        continue
                    
                    # Check for duplicate
                    result = db.execute(
                        text("""
                            SELECT id FROM brands 
                            WHERE user_id = :user_id AND brand_name = :brand_name
                        """),
                        {"user_id": user_id, "brand_name": brand_name}
                    )
                    if result.fetchone():
                        skipped += 1
                        continue
                    
                    # Insert
                    db.execute(
                        text("""
                            INSERT INTO brands 
                            (user_id, brand_name, manufacturer, mrp, cost_price, 
                             default_margin, is_active, created_at, updated_at)
                            VALUES (:user_id, :brand_name, :manufacturer, :mrp, :cost_price,
                                   :default_margin, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """),
                        {
                            "user_id": user_id,
                            "brand_name": brand_name,
                            "manufacturer": manufacturer,
                            "mrp": mrp,
                            "cost_price": cost_price,
                            "default_margin": default_margin
                        }
                    )
                    imported += 1
                    
                except ValueError as e:
                    errors.append({"row": row_num, "error": str(e)})
                    failed += 1
                except Exception as e:
                    errors.append({"row": row_num, "error": "Invalid data"})
                    failed += 1
            
            db.commit()
            
            return {
                "imported": imported,
                "failed": failed,
                "skipped": skipped,
                "total": imported + failed + skipped,
                "errors": errors[:10]  # Limit to first 10 errors
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to import CSV: {e}")
            raise Exception("Failed to import CSV")
