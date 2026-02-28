"""
Redis caching utilities
Performance optimization through caching
"""

import logging
import json
from typing import Optional, Any
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """Manage Redis caching for performance optimization"""
    
    # Cache TTL (Time To Live) in seconds
    CACHE_TTL = {
        "dashboard": 300,      # 5 minutes
        "brands": 600,         # 10 minutes
        "quotes": 300,         # 5 minutes
        "analytics": 900,      # 15 minutes
        "customer_types": 3600, # 1 hour
        "pricing": 600,        # 10 minutes
        "user_profile": 1800   # 30 minutes
    }
    
    @staticmethod
    def generate_cache_key(prefix: str, user_id: int, **kwargs) -> str:
        """Generate cache key from parameters"""
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:user_{user_id}:{params_hash}"
    
    @staticmethod
    def cache_key_user_dashboard(user_id: int) -> str:
        """Generate dashboard cache key"""
        return f"dashboard:user_{user_id}"
    
    @staticmethod
    def cache_key_user_brands(user_id: int, page: int = 0, limit: int = 20) -> str:
        """Generate brands list cache key"""
        return f"brands:user_{user_id}:page_{page}:limit_{limit}"
    
    @staticmethod
    def cache_key_user_quotes(user_id: int, status: Optional[str] = None) -> str:
        """Generate quotes cache key"""
        status_str = status or "all"
        return f"quotes:user_{user_id}:status_{status_str}"
    
    @staticmethod
    def cache_key_quote_detail(user_id: int, quote_id: int) -> str:
        """Generate quote detail cache key"""
        return f"quote_detail:user_{user_id}:quote_{quote_id}"
    
    @staticmethod
    def cache_key_analytics(user_id: int, metric_type: str) -> str:
        """Generate analytics cache key"""
        return f"analytics:user_{user_id}:{metric_type}"
    
    @staticmethod
    def cache_key_pricing(brand_id: int, customer_type_id: Optional[int] = None) -> str:
        """Generate pricing cache key"""
        type_str = customer_type_id or "default"
        return f"pricing:brand_{brand_id}:type_{type_str}"


class CacheInvalidator:
    """Manage cache invalidation when data changes"""
    
    @staticmethod
    def invalidate_user_cache(user_id: int) -> list:
        """Invalidate all cache for a user"""
        patterns = [
            f"dashboard:user_{user_id}",
            f"brands:user_{user_id}:*",
            f"quotes:user_{user_id}:*",
            f"quote_detail:user_{user_id}:*",
            f"analytics:user_{user_id}:*",
        ]
        return patterns
    
    @staticmethod
    def invalidate_brand_cache(user_id: int, brand_id: int) -> list:
        """Invalidate cache when brand changes"""
        return [
            f"brands:user_{user_id}:*",
            f"pricing:brand_{brand_id}:*",
            f"dashboard:user_{user_id}",
            f"analytics:user_{user_id}:*"
        ]
    
    @staticmethod
    def invalidate_quote_cache(user_id: int, quote_id: int) -> list:
        """Invalidate cache when quote changes"""
        return [
            f"quotes:user_{user_id}:*",
            f"quote_detail:user_{user_id}:quote_{quote_id}",
            f"dashboard:user_{user_id}",
            f"analytics:user_{user_id}:*"
        ]
    
    @staticmethod
    def invalidate_analytics_cache(user_id: int) -> list:
        """Invalidate all analytics cache for user"""
        return [
            f"analytics:user_{user_id}:*",
            f"dashboard:user_{user_id}"
        ]


class QueryOptimizer:
    """Query optimization for database performance"""
    
    @staticmethod
    def get_optimized_brand_query(user_id: int, search: Optional[str] = None, limit: int = 20, offset: int = 0) -> tuple:
        """Get optimized brand query with better indexes"""
        base_query = """
            SELECT id, brand_name, manufacturer, mrp, cost_price, 
                   default_margin, is_active, created_at
            FROM brands
            WHERE user_id = :user_id AND is_active = true
        """
        
        params = {"user_id": user_id, "limit": limit, "offset": offset}
        
        if search:
            base_query += " AND brand_name ILIKE :search"
            params["search"] = f"%{search}%"
        
        base_query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        
        return base_query, params
    
    @staticmethod
    def get_optimized_quote_query(user_id: int, status: Optional[str] = None, limit: int = 20) -> tuple:
        """Get optimized quote query"""
        base_query = """
            SELECT id, quote_number, customer_name, status, total_amount,
                   total_margin, quote_date, quote_expires_at, created_at
            FROM quotes
            WHERE user_id = :user_id
        """
        
        params = {"user_id": user_id, "limit": limit}
        
        if status:
            base_query += " AND status = :status"
            params["status"] = status
        
        base_query += " ORDER BY quote_date DESC LIMIT :limit"
        
        return base_query, params
    
    @staticmethod
    def get_dashboard_aggregation_query(user_id: int) -> str:
        """Get optimized dashboard aggregation query"""
        return """
            WITH quote_stats AS (
                SELECT 
                    COUNT(*) as total_quotes,
                    SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft_count,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent_count,
                    SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted_count,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(SUM(total_margin), 0) as total_margin
                FROM quotes
                WHERE user_id = :user_id
            ),
            brand_stats AS (
                SELECT COUNT(*) as total_brands
                FROM brands
                WHERE user_id = :user_id AND is_active = true
            )
            SELECT qs.*, bs.total_brands
            FROM quote_stats qs, brand_stats bs
        """


class PerformanceIndexes:
    """Database indexes for optimal performance"""
    
    # SQL for creating performance indexes
    INDEXES = [
        # Brands table indexes
        "CREATE INDEX IF NOT EXISTS idx_brands_user_id ON brands(user_id) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_brands_user_name ON brands(user_id, brand_name);",
        "CREATE INDEX IF NOT EXISTS idx_brands_created ON brands(user_id, created_at DESC);",
        
        # Quotes table indexes
        "CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_quotes_user_status ON quotes(user_id, status);",
        "CREATE INDEX IF NOT EXISTS idx_quotes_user_date ON quotes(user_id, quote_date DESC);",
        "CREATE INDEX IF NOT EXISTS idx_quotes_customer ON quotes(user_id, customer_name);",
        
        # Quote line items indexes
        "CREATE INDEX IF NOT EXISTS idx_quote_items_quote_id ON quote_line_items(quote_id);",
        "CREATE INDEX IF NOT EXISTS idx_quote_items_brand_id ON quote_line_items(brand_id);",
        
        # Customer types indexes
        "CREATE INDEX IF NOT EXISTS idx_customer_types_user ON customer_types(user_id);",
        
        # Pricing rules indexes
        "CREATE INDEX IF NOT EXISTS idx_pricing_rules_user ON pricing_rules(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_pricing_rules_brand_type ON pricing_rules(brand_id, customer_type_id);",
        
        # Analytics indexes
        "CREATE INDEX IF NOT EXISTS idx_quotes_date_range ON quotes(user_id, quote_date);",
        "CREATE INDEX IF NOT EXISTS idx_quotes_monthly ON quotes(user_id, DATE_TRUNC('month', quote_date));",
    ]
    
    @staticmethod
    def get_index_creation_script() -> str:
        """Get SQL script to create all indexes"""
        return "\n".join(PerformanceIndexes.INDEXES)
