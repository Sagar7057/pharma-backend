"""
Security hardening utilities
Rate limiting, input sanitization, security headers
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import hashlib
import re

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    # Rate limit configurations (requests per time window)
    LIMITS = {
        "login": (5, 15),           # 5 requests per 15 minutes
        "signup": (3, 60),          # 3 requests per 60 minutes
        "password_reset": (3, 60),  # 3 requests per 60 minutes
        "email_send": (10, 60),     # 10 emails per 60 minutes
        "api_general": (100, 60),   # 100 requests per 60 minutes
        "api_heavy": (30, 60),      # 30 requests per 60 minutes (for heavy operations)
    }
    
    @staticmethod
    def get_rate_limit_key(endpoint: str, identifier: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{endpoint}:{identifier}"
    
    @staticmethod
    def check_rate_limit(
        endpoint: str,
        identifier: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """Check if request is within rate limit"""
        # In production, use Redis for distributed rate limiting
        # For now, return True (would implement with Redis)
        return True
    
    @staticmethod
    def get_rate_limit_headers(
        endpoint: str,
        remaining: int,
        reset_time: datetime
    ) -> Dict[str, str]:
        """Get rate limit headers for response"""
        return {
            "X-RateLimit-Limit": str(RateLimiter.LIMITS[endpoint][0]),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": reset_time.isoformat()
        }


class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number"""
        pattern = r'^[\d\s\-\+\(\)]{10,}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain number"
        
        return True, "Password is strong"
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 255) -> str:
        """Sanitize user input"""
        if not input_str:
            return ""
        
        # Remove null bytes
        sanitized = input_str.replace('\x00', '')
        
        # Limit length
        sanitized = sanitized[:max_length]
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>\"\'%;()&+]', '', sanitized)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$'
        return re.match(pattern, url) is not None


class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
    
    @staticmethod
    def apply_security_headers(response) -> None:
        """Apply security headers to response"""
        headers = SecurityHeaders.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value


class DataProtection:
    """Data protection and encryption utilities"""
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def redact_email(email: str) -> str:
        """Redact email for logging"""
        if not email:
            return ""
        parts = email.split('@')
        if len(parts) != 2:
            return "***"
        return f"{parts[0][:2]}***@{parts[1]}"
    
    @staticmethod
    def redact_phone(phone: str) -> str:
        """Redact phone for logging"""
        if not phone:
            return ""
        return f"***{phone[-4:]}"
    
    @staticmethod
    def mask_credit_card(card: str) -> str:
        """Mask credit card number"""
        if not card or len(card) < 4:
            return "****"
        return f"****{card[-4:]}"


class AuditLogger:
    """Audit logging for security events"""
    
    @staticmethod
    def log_authentication(user_id: int, status: str, details: Optional[str] = None) -> None:
        """Log authentication event"""
        logger.info(
            f"AUTH_EVENT",
            extra={
                "user_id": user_id,
                "status": status,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_data_access(user_id: int, resource_type: str, action: str, resource_id: Optional[int] = None) -> None:
        """Log data access event"""
        logger.info(
            f"DATA_ACCESS",
            extra={
                "user_id": user_id,
                "resource_type": resource_type,
                "action": action,
                "resource_id": resource_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_security_event(event_type: str, severity: str, details: Dict) -> None:
        """Log security event"""
        log_func = logger.warning if severity == "medium" else logger.error if severity == "high" else logger.info
        log_func(
            f"SECURITY_EVENT:{event_type}",
            extra={
                "severity": severity,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )


class CSRFProtection:
    """CSRF token generation and validation"""
    
    @staticmethod
    def generate_csrf_token(session_id: str) -> str:
        """Generate CSRF token"""
        import secrets
        token = secrets.token_urlsafe(32)
        # In production, store in Redis/session
        return token
    
    @staticmethod
    def validate_csrf_token(token: str, session_id: str) -> bool:
        """Validate CSRF token"""
        # In production, check against stored token
        return True


class CORSSecurityConfig:
    """CORS security configuration"""
    
    @staticmethod
    def get_cors_config(allowed_origins: list) -> Dict:
        """Get CORS configuration"""
        return {
            "allow_origins": allowed_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-CSRF-Token"
            ],
            "max_age": 3600,
            "expose_headers": [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset"
            ]
        }
