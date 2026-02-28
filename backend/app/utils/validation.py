"""
Input validation utilities
Email, phone, and other field validations
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email or not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, ""

def validate_phone(phone: str, country_code: str = "IN") -> Tuple[bool, str]:
    """
    Validate phone number
    Currently supports Indian phone numbers
    
    Args:
        phone: Phone number to validate
        country_code: Country code (default: IN)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if country_code == "IN":
        # Indian phone number pattern (10 digits)
        pattern = r'^[6-9]\d{9}$'
        
        if not phone or not re.match(pattern, phone):
            return False, "Invalid Indian phone number (10 digits starting with 6-9)"
        
        return True, ""
    
    # Generic validation
    if not phone or len(phone) < 7:
        return False, "Invalid phone number"
    
    return True, ""

def validate_name(name: str, min_length: int = 2, max_length: int = 255) -> Tuple[bool, str]:
    """
    Validate name field
    
    Args:
        name: Name to validate
        min_length: Minimum length
        max_length: Maximum length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Name is required"
    
    name = name.strip()
    
    if len(name) < min_length:
        return False, f"Name must be at least {min_length} characters"
    
    if len(name) > max_length:
        return False, f"Name must not exceed {max_length} characters"
    
    return True, ""

def validate_company_name(company_name: str) -> Tuple[bool, str]:
    """
    Validate company name
    
    Args:
        company_name: Company name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_name(company_name, min_length=2, max_length=255)

def validate_city(city: str) -> Tuple[bool, str]:
    """
    Validate city name
    
    Args:
        city: City name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return validate_name(city, min_length=2, max_length=100)

def validate_state(state: str) -> Tuple[bool, str]:
    """
    Validate state code
    
    Args:
        state: State code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not state or len(state) < 2:
        return False, "State code is required"
    
    return True, ""

def sanitize_email(email: str) -> str:
    """
    Sanitize email address
    
    Args:
        email: Email to sanitize
        
    Returns:
        Sanitized email
    """
    return email.strip().lower()

def sanitize_string(text: str) -> str:
    """
    Sanitize string input
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    return text.strip()
