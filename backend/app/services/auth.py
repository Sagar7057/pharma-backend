"""
Authentication service
Business logic for signup, login, profile management
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.auth import hash_password, verify_password, create_access_token
from app.utils.validation import (
    validate_email, validate_phone, validate_name, 
    validate_company_name, validate_city, validate_state,
    sanitize_email, sanitize_string
)

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service"""
    
    @staticmethod
    async def signup(
        email: str,
        password: str,
        full_name: str,
        company_name: str,
        phone: str,
        city: str,
        state: str,
        db: Session
    ) -> dict:
        """
        Create new user account
        
        Args:
            email: User email
            password: User password
            full_name: Full name
            company_name: Company name
            phone: Phone number
            city: City
            state: State
            db: Database session
            
        Returns:
            Dictionary with token and user data
        """
        # Validate inputs
        is_valid, error = validate_email(email)
        if not is_valid:
            raise ValueError(error)
        
        is_valid, error = validate_name(full_name)
        if not is_valid:
            raise ValueError(error)
        
        is_valid, error = validate_company_name(company_name)
        if not is_valid:
            raise ValueError(error)
        
        is_valid, error = validate_city(city)
        if not is_valid:
            raise ValueError(error)
        
        is_valid, error = validate_state(state)
        if not is_valid:
            raise ValueError(error)
        
        if phone:
            is_valid, error = validate_phone(phone)
            if not is_valid:
                raise ValueError(error)
        
        # Sanitize inputs
        email = sanitize_email(email)
        full_name = sanitize_string(full_name)
        company_name = sanitize_string(company_name)
        city = sanitize_string(city)
        state = sanitize_string(state)
        
        # Check if email already exists
        try:
            result = db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            )
            if result.fetchone():
                raise ValueError("Email already exists")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise Exception("Database error")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert user
        try:
            db.execute(
                text("""
                    INSERT INTO users (email, password_hash, full_name, company_name, 
                                      phone, city, state, is_active, created_at, updated_at)
                    VALUES (:email, :password_hash, :full_name, :company_name, 
                           :phone, :city, :state, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """),
                {
                    "email": email,
                    "password_hash": password_hash,
                    "full_name": full_name,
                    "company_name": company_name,
                    "phone": phone or None,
                    "city": city,
                    "state": state
                }
            )
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise Exception("Failed to create user")
        
        # Get user ID
        try:
            result = db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()
            user_id = user[0] if user else None
        except Exception as e:
            logger.error(f"Failed to retrieve user: {e}")
            raise Exception("Failed to retrieve user")
        
        # Generate token
        token = create_access_token(user_id, email)
        
        return {
            "token": token,
            "user": {
                "id": user_id,
                "email": email,
                "fullName": full_name,
                "companyName": company_name
            }
        }
    
    @staticmethod
    async def login(email: str, password: str, db: Session) -> dict:
        """
        Authenticate user and return token
        
        Args:
            email: User email
            password: User password
            db: Database session
            
        Returns:
            Dictionary with token
        """
        # Validate inputs
        if not email or not password:
            raise ValueError("Email and password are required")
        
        email = sanitize_email(email)
        
        # Find user
        try:
            result = db.execute(
                text("""
                    SELECT id, email, password_hash, full_name, is_active 
                    FROM users WHERE email = :email
                """),
                {"email": email}
            )
            user = result.fetchone()
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise Exception("Database error")
        
        if not user:
            raise ValueError("Invalid credentials")
        
        user_id, user_email, password_hash, full_name, is_active = user
        
        # Check if user is active
        if not is_active:
            raise ValueError("Account is disabled")
        
        # Verify password
        if not verify_password(password, password_hash):
            raise ValueError("Invalid credentials")
        
        # Generate token
        token = create_access_token(user_id, user_email)
        
        return {
            "token": token,
            "expiresIn": "7d",
            "user": {
                "id": user_id,
                "email": user_email,
                "fullName": full_name
            }
        }
    
    @staticmethod
    async def get_profile(user_id: int, db: Session) -> dict:
        """
        Get user profile
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            User profile data
        """
        try:
            result = db.execute(
                text("""
                    SELECT id, email, full_name, company_name, phone, city, state, created_at
                    FROM users WHERE id = :user_id
                """),
                {"user_id": user_id}
            )
            user = result.fetchone()
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise Exception("Database error")
        
        if not user:
            raise ValueError("User not found")
        
        user_id, email, full_name, company_name, phone, city, state, created_at = user
        
        return {
            "id": user_id,
            "email": email,
            "fullName": full_name,
            "companyName": company_name,
            "phone": phone,
            "city": city,
            "state": state,
            "createdAt": created_at.isoformat() if created_at else None
        }
