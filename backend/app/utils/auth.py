"""
Authentication utilities
Password hashing, JWT token generation, validation
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import jwt
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    logger.error("❌ JWT_SECRET not set in environment")
    raise ValueError("JWT_SECRET must be set")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 168))  # 7 days

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    user_id: Union[str, int],
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
    
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "user_id": str(user_id) if user_id is not None else None,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

def get_token_from_header(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]
