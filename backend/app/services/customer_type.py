"""
Customer Type service
Business logic for customer type management
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Default customer types for new users
DEFAULT_CUSTOMER_TYPES = [
    {"name": "Hospital", "default_margin": 15, "is_predefined": True},
    {"name": "Retail Pharmacy", "default_margin": 12, "is_predefined": True},
    {"name": "Modern Trade", "default_margin": 8, "is_predefined": True},
    {"name": "Chemist Association", "default_margin": 10, "is_predefined": True},
]

class CustomerTypeService:
    """Customer type service for CRUD operations"""
    
    @staticmethod
    async def create_customer_type(
        user_id: int,
        name: str,
        default_margin: float,
        description: str,
        db: Session
    ) -> Dict[str, Any]:
        """Create new customer type"""
        try:
            # Check for duplicate
            result = db.execute(
                text("""
                    SELECT id FROM customer_types 
                    WHERE user_id = :user_id AND name = :name
                """),
                {"user_id": user_id, "name": name}
            )
            if result.fetchone():
                raise ValueError("Customer type already exists")
            
            # Insert
            db.execute(
                text("""
                    INSERT INTO customer_types 
                    (user_id, name, default_margin, description, is_predefined, created_at)
                    VALUES (:user_id, :name, :default_margin, :description, false, CURRENT_TIMESTAMP)
                """),
                {
                    "user_id": user_id,
                    "name": name,
                    "default_margin": default_margin or 0,
                    "description": description or ""
                }
            )
            db.commit()
            
            # Get created type
            result = db.execute(
                text("""
                    SELECT id, name, default_margin, description, is_predefined, created_at
                    FROM customer_types 
                    WHERE user_id = :user_id AND name = :name
                    ORDER BY id DESC LIMIT 1
                """),
                {"user_id": user_id, "name": name}
            )
            row = result.fetchone()
            
            return {
                "id": row[0],
                "user_id": user_id,
                "name": row[1],
                "default_margin": float(row[2]) if row[2] else 0,
                "description": row[3],
                "is_predefined": row[4],
                "created_at": row[5]
            }
            
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create customer type: {e}")
            raise Exception("Failed to create customer type")
    
    @staticmethod
    async def list_customer_types(user_id: int, db: Session) -> List[Dict[str, Any]]:
        """List all customer types for user"""
        try:
            result = db.execute(
                text("""
                    SELECT id, user_id, name, default_margin, description, is_predefined, created_at
                    FROM customer_types 
                    WHERE user_id = :user_id
                    ORDER BY is_predefined DESC, name ASC
                """),
                {"user_id": user_id}
            )
            
            types = []
            for row in result:
                types.append({
                    "id": row[0],
                    "user_id": row[1],
                    "name": row[2],
                    "default_margin": float(row[3]) if row[3] else 0,
                    "description": row[4],
                    "is_predefined": row[5],
                    "created_at": row[6]
                })
            
            return types
        except Exception as e:
            logger.error(f"Failed to list customer types: {e}")
            raise Exception("Failed to list customer types")
    
    @staticmethod
    async def get_customer_type(user_id: int, type_id: int, db: Session) -> Dict[str, Any]:
        """Get single customer type"""
        try:
            result = db.execute(
                text("""
                    SELECT id, user_id, name, default_margin, description, is_predefined, created_at
                    FROM customer_types 
                    WHERE id = :type_id AND user_id = :user_id
                """),
                {"type_id": type_id, "user_id": user_id}
            )
            row = result.fetchone()
            
            if not row:
                raise ValueError("Customer type not found")
            
            return {
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "default_margin": float(row[3]) if row[3] else 0,
                "description": row[4],
                "is_predefined": row[5],
                "created_at": row[6]
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get customer type: {e}")
            raise Exception("Failed to get customer type")
    
    @staticmethod
    async def update_customer_type(
        user_id: int,
        type_id: int,
        name: Optional[str],
        default_margin: Optional[float],
        description: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """Update customer type"""
        try:
            # Build update query
            set_clauses = []
            params = {"type_id": type_id, "user_id": user_id}
            
            if name is not None:
                set_clauses.append("name = :name")
                params["name"] = name
            
            if default_margin is not None:
                set_clauses.append("default_margin = :default_margin")
                params["default_margin"] = default_margin
            
            if description is not None:
                set_clauses.append("description = :description")
                params["description"] = description
            
            if set_clauses:
                db.execute(
                    text(f"""
                        UPDATE customer_types 
                        SET {', '.join(set_clauses)}
                        WHERE id = :type_id AND user_id = :user_id
                    """),
                    params
                )
                db.commit()
            
            return await CustomerTypeService.get_customer_type(user_id, type_id, db)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update customer type: {e}")
            raise Exception("Failed to update customer type")
    
    @staticmethod
    async def delete_customer_type(user_id: int, type_id: int, db: Session) -> bool:
        """Delete customer type (only if not predefined)"""
        try:
            # Check if predefined
            result = db.execute(
                text("""
                    SELECT is_predefined FROM customer_types 
                    WHERE id = :type_id AND user_id = :user_id
                """),
                {"type_id": type_id, "user_id": user_id}
            )
            row = result.fetchone()
            
            if not row:
                raise ValueError("Customer type not found")
            
            if row[0]:  # is_predefined
                raise ValueError("Cannot delete predefined customer type")
            
            db.execute(
                text("""
                    DELETE FROM customer_types 
                    WHERE id = :type_id AND user_id = :user_id
                """),
                {"type_id": type_id, "user_id": user_id}
            )
            db.commit()
            return True
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete customer type: {e}")
            raise Exception("Failed to delete customer type")
    
    @staticmethod
    async def init_default_types(user_id: int, db: Session) -> bool:
        """Initialize default customer types for new user"""
        try:
            for ctype in DEFAULT_CUSTOMER_TYPES:
                # Check if already exists
                result = db.execute(
                    text("""
                        SELECT id FROM customer_types 
                        WHERE user_id = :user_id AND name = :name
                    """),
                    {"user_id": user_id, "name": ctype["name"]}
                )
                
                if not result.fetchone():
                    db.execute(
                        text("""
                            INSERT INTO customer_types 
                            (user_id, name, default_margin, is_predefined, created_at)
                            VALUES (:user_id, :name, :default_margin, :is_predefined, CURRENT_TIMESTAMP)
                        """),
                        {
                            "user_id": user_id,
                            "name": ctype["name"],
                            "default_margin": ctype["default_margin"],
                            "is_predefined": ctype["is_predefined"]
                        }
                    )
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to init default types: {e}")
            return False
