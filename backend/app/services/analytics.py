"""
Analytics service
Business logic for metrics and dashboard calculations
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Analytics service for business metrics and insights"""
    
    @staticmethod
    def _get_date_range(range_type: str, custom_from: Optional[str] = None, custom_to: Optional[str] = None) -> tuple:
        """Get date range for filtering"""
        now = datetime.now()
        
        if range_type == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif range_type == "week":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif range_type == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif range_type == "last_30":
            start = now - timedelta(days=30)
            end = now
        elif range_type == "last_90":
            start = now - timedelta(days=90)
            end = now
        elif range_type == "year":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif range_type == "custom" and custom_from and custom_to:
            start = datetime.fromisoformat(custom_from)
            end = datetime.fromisoformat(custom_to)
        else:
            # Default to last 30 days
            start = now - timedelta(days=30)
            end = now
        
        return start, end
    
    @staticmethod
    async def get_dashboard_metrics(user_id: int, db: Session) -> Dict[str, Any]:
        """Get overall dashboard metrics"""
        try:
            now = datetime.now()
            month_ago = now - timedelta(days=30)
            
            # Total revenue and quotes (all time)
            revenue_result = db.execute(
                text("""
                    SELECT COALESCE(SUM(total_amount), 0), COUNT(*), COALESCE(SUM(total_margin), 0)
                    FROM quotes
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            total_revenue, total_quotes, total_margin = revenue_result.fetchone()
            
            # This month quotes
            month_result = db.execute(
                text("""
                    SELECT COUNT(*) FROM quotes
                    WHERE user_id = :user_id 
                    AND quote_date >= :month_ago
                """),
                {"user_id": user_id, "month_ago": month_ago}
            )
            monthly_quotes = month_result.scalar() or 0
            
            # Quote status breakdown
            status_result = db.execute(
                text("""
                    SELECT status, COUNT(*) 
                    FROM quotes
                    WHERE user_id = :user_id
                    GROUP BY status
                """),
                {"user_id": user_id}
            )
            status_breakdown = {row[0]: row[1] for row in status_result}
            
            # Active brands
            brands_result = db.execute(
                text("""
                    SELECT COUNT(*) FROM brands
                    WHERE user_id = :user_id AND is_active = true
                """),
                {"user_id": user_id}
            )
            active_brands = brands_result.scalar() or 0
            
            # Average quote value
            avg_value = total_revenue / total_quotes if total_quotes > 0 else 0
            
            # Conversion rate (accepted / sent)
            sent = status_breakdown.get("sent", 0) + status_breakdown.get("accepted", 0) + status_breakdown.get("rejected", 0)
            conversion_rate = (status_breakdown.get("accepted", 0) / sent * 100) if sent > 0 else 0
            
            return {
                "total_revenue": float(total_revenue),
                "total_quotes": int(total_quotes),
                "total_margin": float(total_margin),
                "monthly_quotes": int(monthly_quotes),
                "avg_quote_value": float(avg_value),
                "conversion_rate": float(conversion_rate),
                "active_brands": int(active_brands),
                "pending_quotes": int(status_breakdown.get("draft", 0) + status_breakdown.get("sent", 0)),
                "expired_quotes": int(status_breakdown.get("expired", 0)),
                "status_breakdown": status_breakdown
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            raise Exception("Failed to get dashboard metrics")
    
    @staticmethod
    async def get_revenue_trend(
        user_id: int,
        range_type: str = "month",
        db: Session = None
    ) -> Dict[str, Any]:
        """Get revenue trend over time"""
        try:
            start_date, end_date = AnalyticsService._get_date_range(range_type)
            
            # Get daily revenue
            result = db.execute(
                text("""
                    SELECT DATE(quote_date) as date, 
                           COALESCE(SUM(total_amount), 0) as revenue,
                           COALESCE(SUM(total_margin), 0) as margin,
                           COUNT(*) as quote_count
                    FROM quotes
                    WHERE user_id = :user_id 
                    AND quote_date BETWEEN :start_date AND :end_date
                    GROUP BY DATE(quote_date)
                    ORDER BY date ASC
                """),
                {"user_id": user_id, "start_date": start_date, "end_date": end_date}
            )
            
            data_points = []
            for row in result:
                data_points.append({
                    "date": row[0].isoformat(),
                    "revenue": float(row[1]),
                    "margin": float(row[2]),
                    "quote_count": int(row[3])
                })
            
            return {
                "data_points": data_points,
                "period": range_type,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get revenue trend: {e}")
            raise Exception("Failed to get revenue trend")
    
    @staticmethod
    async def get_quote_metrics(user_id: int, db: Session) -> Dict[str, Any]:
        """Get quote-related metrics"""
        try:
            # Quote status breakdown
            status_result = db.execute(
                text("""
                    SELECT status, COUNT(*), COALESCE(SUM(total_amount), 0), COALESCE(SUM(total_margin), 0)
                    FROM quotes
                    WHERE user_id = :user_id
                    GROUP BY status
                """),
                {"user_id": user_id}
            )
            
            status_metrics = {}
            total_value = 0
            total_margin = 0
            
            for row in status_result:
                status = row[0]
                count = row[1]
                amount = float(row[2])
                margin = float(row[3])
                
                status_metrics[status] = {
                    "count": count,
                    "value": amount,
                    "margin": margin
                }
                total_value += amount
                total_margin += margin
            
            # Get total quotes
            total_result = db.execute(
                text("SELECT COUNT(*) FROM quotes WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            total_quotes = total_result.scalar() or 0
            
            # Conversion rate
            sent = sum(m["count"] for k, m in status_metrics.items() if k in ["sent", "accepted", "rejected"])
            accepted = status_metrics.get("accepted", {}).get("count", 0)
            conversion_rate = (accepted / sent * 100) if sent > 0 else 0
            
            # Average margin
            avg_margin = (total_margin / total_quotes * 100 / total_value) if total_value > 0 else 0
            
            return {
                "total_quotes": total_quotes,
                "total_value": total_value,
                "total_margin": total_margin,
                "avg_margin_percentage": float(avg_margin),
                "conversion_rate": float(conversion_rate),
                "by_status": status_metrics
            }
        except Exception as e:
            logger.error(f"Failed to get quote metrics: {e}")
            raise Exception("Failed to get quote metrics")
    
    @staticmethod
    async def get_brand_metrics(user_id: int, db: Session) -> Dict[str, Any]:
        """Get brand-related metrics"""
        try:
            # Total brands
            brands_result = db.execute(
                text("SELECT COUNT(*) FROM brands WHERE user_id = :user_id AND is_active = true"),
                {"user_id": user_id}
            )
            total_brands = brands_result.scalar() or 0
            
            # NPPA controlled brands
            nppa_result = db.execute(
                text("SELECT COUNT(*) FROM brands WHERE user_id = :user_id AND is_nppa_controlled = true"),
                {"user_id": user_id}
            )
            nppa_brands = nppa_result.scalar() or 0
            
            # Top brands by quote count
            top_result = db.execute(
                text("""
                    SELECT b.brand_name, COUNT(q.id) as quote_count, SUM(q.total_amount) as revenue
                    FROM brands b
                    LEFT JOIN quotes q ON b.id = q.id
                    WHERE b.user_id = :user_id AND b.is_active = true
                    GROUP BY b.id, b.brand_name
                    ORDER BY quote_count DESC
                    LIMIT 10
                """),
                {"user_id": user_id}
            )
            
            top_brands = []
            for row in top_result:
                top_brands.append({
                    "name": row[0],
                    "quote_count": int(row[1]),
                    "revenue": float(row[2]) if row[2] else 0
                })
            
            # Brands by margin
            margin_result = db.execute(
                text("""
                    SELECT brand_name, default_margin
                    FROM brands
                    WHERE user_id = :user_id AND is_active = true
                    ORDER BY default_margin DESC
                    LIMIT 10
                """),
                {"user_id": user_id}
            )
            
            brands_by_margin = []
            for row in margin_result:
                brands_by_margin.append({
                    "name": row[0],
                    "margin": float(row[1]) if row[1] else 0
                })
            
            return {
                "total_brands": total_brands,
                "nppa_brands": nppa_brands,
                "top_brands": top_brands,
                "brands_by_margin": brands_by_margin
            }
        except Exception as e:
            logger.error(f"Failed to get brand metrics: {e}")
            raise Exception("Failed to get brand metrics")
    
    @staticmethod
    async def get_customer_metrics(user_id: int, db: Session) -> Dict[str, Any]:
        """Get customer-related metrics"""
        try:
            # Quote breakdown by customer type
            type_result = db.execute(
                text("""
                    SELECT ct.name, COUNT(q.id)
                    FROM customer_types ct
                    LEFT JOIN quotes q ON ct.id = q.customer_type_id
                    WHERE ct.user_id = :user_id
                    GROUP BY ct.id, ct.name
                """),
                {"user_id": user_id}
            )
            
            quotes_by_type = {}
            for row in type_result:
                quotes_by_type[row[0]] = int(row[1])
            
            # Average order value
            avg_result = db.execute(
                text("""
                    SELECT AVG(total_amount)
                    FROM quotes
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            avg_value = float(avg_result.scalar()) if avg_result.scalar() else 0
            
            # Repeat customers (same customer name multiple quotes)
            repeat_result = db.execute(
                text("""
                    SELECT COUNT(DISTINCT customer_name) 
                    FROM (
                        SELECT customer_name, COUNT(*) as count
                        FROM quotes
                        WHERE user_id = :user_id
                        GROUP BY customer_name
                        HAVING COUNT(*) > 1
                    ) repeated
                """),
                {"user_id": user_id}
            )
            repeat_customers = repeat_result.scalar() or 0
            
            return {
                "quotes_by_type": quotes_by_type,
                "avg_order_value": avg_value,
                "repeat_customers": int(repeat_customers)
            }
        except Exception as e:
            logger.error(f"Failed to get customer metrics: {e}")
            raise Exception("Failed to get customer metrics")
