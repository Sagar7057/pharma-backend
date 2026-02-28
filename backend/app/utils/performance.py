"""
Performance monitoring and optimization
Request timing, query analysis, performance metrics
"""

import logging
import time
from typing import Callable
from functools import wraps
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor application performance"""
    
    @staticmethod
    def measure_execution_time(func: Callable) -> Callable:
        """Decorator to measure function execution time"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if execution_time > 1.0:  # Log slow queries
                    logger.warning(
                        f"SLOW_QUERY: {func.__name__} took {execution_time:.2f}s",
                        extra={
                            "function": func.__name__,
                            "execution_time": execution_time,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"ERROR in {func.__name__}: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "execution_time": execution_time,
                        "error": str(e)
                    }
                )
                raise
        
        return async_wrapper
    
    @staticmethod
    def log_query_performance(query_str: str, execution_time: float, params: dict = None) -> None:
        """Log database query performance"""
        if execution_time > 0.5:  # Log queries taking more than 500ms
            logger.warning(
                f"SLOW_DB_QUERY: {execution_time:.3f}s",
                extra={
                    "execution_time": execution_time,
                    "query_preview": query_str[:100],
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    @staticmethod
    def get_performance_metrics() -> dict:
        """Get current performance metrics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": "calculated_from_start_time",
            "request_count": "from_metrics_store",
            "avg_response_time": "from_metrics_store",
            "error_rate": "from_metrics_store",
            "cache_hit_rate": "from_redis"
        }


class QueryAnalyzer:
    """Analyze and optimize database queries"""
    
    @staticmethod
    def analyze_query_plan(query: str) -> dict:
        """Get query execution plan"""
        return {
            "query": query,
            "analysis": "EXPLAIN PLAN would be run in production",
            "recommendations": [
                "Ensure indexes exist on WHERE clauses",
                "Avoid SELECT *, specify columns",
                "Use JOINs instead of subqueries where possible",
                "Consider partitioning large tables"
            ]
        }
    
    @staticmethod
    def get_query_optimization_tips() -> list:
        """Get general query optimization tips"""
        return [
            "Always specify columns instead of SELECT *",
            "Use indexes on frequently filtered columns",
            "Batch operations when possible",
            "Use connection pooling",
            "Cache frequently accessed data",
            "Avoid N+1 query problems",
            "Use LIMIT for large result sets",
            "Analyze slow queries with EXPLAIN PLAN"
        ]


class DatabaseOptimization:
    """Database-specific optimizations"""
    
    @staticmethod
    def get_postgresql_settings() -> dict:
        """Get recommended PostgreSQL settings"""
        return {
            "shared_buffers": "25% of available RAM",
            "effective_cache_size": "50-75% of available RAM",
            "work_mem": "total_ram / (max_connections * 2)",
            "maintenance_work_mem": "1-2GB for large tables",
            "random_page_cost": "1.1 for SSD",
            "effective_io_concurrency": "200 for SSD",
            "max_connections": "100-500 depending on load"
        }
    
    @staticmethod
    def get_connection_pool_config() -> dict:
        """Get connection pool configuration"""
        return {
            "pool_size": 20,
            "max_overflow": 40,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
            "echo_pool": False
        }


class CacheOptimization:
    """Cache optimization strategies"""
    
    @staticmethod
    def get_cache_strategy() -> dict:
        """Get caching strategy"""
        return {
            "layer_1": {
                "type": "Application memory cache",
                "ttl": "1-5 minutes",
                "items": "Frequently accessed user data"
            },
            "layer_2": {
                "type": "Redis distributed cache",
                "ttl": "5-30 minutes",
                "items": "Dashboard, analytics, brand lists"
            },
            "layer_3": {
                "type": "Database query cache",
                "ttl": "Direct DB",
                "items": "Raw data with indexes"
            }
        }
    
    @staticmethod
    def get_cache_invalidation_strategy() -> list:
        """Get cache invalidation strategy"""
        return [
            "Invalidate on create: Dashboard, analytics",
            "Invalidate on update: Item + related caches",
            "Invalidate on delete: Item + list caches",
            "TTL-based expiration for time-sensitive data",
            "Manual invalidation for critical updates"
        ]


class LoadOptimization:
    """Load optimization techniques"""
    
    @staticmethod
    def get_load_optimization_techniques() -> list:
        """Get load optimization techniques"""
        return [
            {
                "technique": "Database Connection Pooling",
                "benefit": "Reduces connection overhead",
                "implementation": "SQLAlchemy pool"
            },
            {
                "technique": "Query Pagination",
                "benefit": "Reduces memory usage",
                "implementation": "LIMIT/OFFSET in queries"
            },
            {
                "technique": "Lazy Loading",
                "benefit": "Loads data only when needed",
                "implementation": "SQLAlchemy lazy loading"
            },
            {
                "technique": "Batch Processing",
                "benefit": "Reduces round trips",
                "implementation": "Bulk inserts/updates"
            },
            {
                "technique": "Compression",
                "benefit": "Reduces bandwidth",
                "implementation": "Gzip middleware"
            },
            {
                "technique": "CDN for Static Assets",
                "benefit": "Faster content delivery",
                "implementation": "AWS CloudFront"
            }
        ]
    
    @staticmethod
    def get_scaling_recommendations() -> dict:
        """Get scaling recommendations"""
        return {
            "vertical_scaling": {
                "increase_cpu": "For CPU-bound operations",
                "increase_ram": "For caching and in-memory operations",
                "upgrade_disk": "For faster I/O"
            },
            "horizontal_scaling": {
                "load_balancer": "Distribute requests across servers",
                "database_replication": "Read replicas for reporting",
                "cache_cluster": "Redis cluster for distributed caching",
                "microservices": "Split by domain later"
            }
        }


class MonitoringMetrics:
    """Key metrics to monitor"""
    
    METRICS = {
        "response_time": {
            "target": "< 200ms p50, < 500ms p95",
            "monitor": "Request duration histogram"
        },
        "error_rate": {
            "target": "< 0.1%",
            "monitor": "5xx errors per minute"
        },
        "database_latency": {
            "target": "< 50ms p50",
            "monitor": "Query execution time"
        },
        "cache_hit_rate": {
            "target": "> 80%",
            "monitor": "Cache hits / total requests"
        },
        "cpu_usage": {
            "target": "< 70%",
            "monitor": "Server CPU percentage"
        },
        "memory_usage": {
            "target": "< 80%",
            "monitor": "Available memory percentage"
        },
        "disk_usage": {
            "target": "< 80%",
            "monitor": "Disk space percentage"
        },
        "active_connections": {
            "target": "< 80% of max",
            "monitor": "Database connections"
        }
    }
    
    @staticmethod
    def get_monitoring_setup() -> dict:
        """Get monitoring setup recommendations"""
        return {
            "metrics_collection": "Prometheus",
            "time_series_storage": "Prometheus/InfluxDB",
            "visualization": "Grafana",
            "alerting": "Alertmanager",
            "logging": "ELK Stack (Elasticsearch, Logstash, Kibana)",
            "apm": "New Relic / DataDog"
        }
