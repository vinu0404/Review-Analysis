"""
Custom validators for input validation
"""

import re
from typing import Tuple


def validate_review_text(text: str) -> Tuple[bool, str]:
    """
    Validate review text for quality and safety.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    stripped = text.strip()
    
    if len(stripped) < 10:
        return False, "Review must be at least 10 characters long"
    
    if len(stripped) > 1000:
        return False, "Review must not exceed 1000 characters"
    if len(set(stripped.lower())) < 5:
        return False, "Please write a more detailed review"

    words = stripped.split()
    if len(words) > 3:
        unique_words = set(w.lower() for w in words)
        if len(unique_words) < len(words) * 0.3:
            return False, "Please avoid excessive word repetition"
    
    return True, ""


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Raw user input
        
    Returns:
        Sanitized text
    """
    text = text.replace('\x00', '')
    text = ' '.join(text.split())
    text = ''.join(char for char in text if char == '\n' or (ord(char) >= 32 and ord(char) != 127))
    
    return text.strip()


def is_valid_rating(rating: int) -> bool:
    """Check if rating is valid (1-5)"""
    return isinstance(rating, int) and 1 <= rating <= 5


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rsplit(' ', 1)[0] + suffix
