"""
API Key Authentication
======================
Validates x-api-key header using constant-time comparison to prevent timing attacks.
Supports multiple API keys for rotation.

Security Notes:
- Constant-time string comparison prevents timing attacks
- Multiple keys supported for zero-downtime rotation
- Returns 401 if key is missing or invalid
"""

import hmac
import hashlib
from typing import List, Optional
from config import Config
from logger import get_logger

logger = get_logger()


def constant_time_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks.
    
    Uses HMAC comparison which is safe against timing attacks.
    This prevents attackers from learning valid API keys through
    timing differences in comparison operations.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings match, False otherwise
    """
    if len(a) != len(b):
        return False
    
    # Use HMAC comparison for constant-time operation
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate API key against configured keys.
    
    Security:
    - Constant-time comparison prevents timing attacks
    - Supports multiple keys for rotation
    - Returns False (not error details) to prevent information leakage
    
    Args:
        api_key: API key from x-api-key header (may be None)
        
    Returns:
        True if key is valid, False otherwise
    """
    if not api_key:
        logger.warning('API request missing x-api-key header')
        return False
    
    # Get valid keys from config
    valid_keys = Config.get_api_keys()
    
    if not valid_keys:
        logger.error('No API keys configured in environment')
        return False
    
    # Check against all valid keys (supports rotation)
    for valid_key in valid_keys:
        if constant_time_compare(api_key, valid_key):
            logger.debug('API key validated successfully')
            return True
    
    # Log failed attempt (but don't leak which key was tried)
    logger.warning('Invalid API key provided')
    return False


def extract_api_key(headers: dict) -> Optional[str]:
    """
    Extract API key from request headers.
    Checks both x-api-key and X-Api-Key (case-insensitive).
    
    Args:
        headers: Request headers dictionary
        
    Returns:
        API key string if found, None otherwise
    """
    # API Gateway normalizes headers, but check both cases
    api_key = headers.get('x-api-key') or headers.get('X-Api-Key')
    
    if api_key:
        # Strip whitespace
        return api_key.strip()
    
    return None


def authenticate_request(headers: dict) -> tuple:
    """
    Authenticate incoming request.
    
    Args:
        headers: Request headers dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if authenticated, False otherwise
        - error_message: Error message if not authenticated, None otherwise
    """
    api_key = extract_api_key(headers)
    
    if not validate_api_key(api_key):
        return False, 'Unauthorized: Invalid or missing API key'
    
    return True, None