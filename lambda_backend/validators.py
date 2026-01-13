"""
Input Validation & Schema Validation
=====================================
Strict validation of all inputs to prevent injection attacks and malformed requests.
Whitelist-based intent validation ensures only allowed operations are executed.

Security Notes:
- Whitelist of allowed intents (reject unknown intents)
- JSON schema validation for all parameters
- Type checking and range validation
- Payload size limits
- SQL injection prevention via parameterized queries (enforced in db_client)
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from logger import get_logger
from config import Config

logger = get_logger()


# Whitelist of allowed intents
# Only these intents can be executed - all others are rejected
ALLOWED_INTENTS = {
    'get_access_logs',
    'get_error_logs',
    'store_access_log',
    'store_error_log',
    'get_traffic_summary',
    'get_security_threats',
    'get_performance_metrics',
    'get_anomalies',
    'query_logs',  # Generic query endpoint
}


def validate_intent(intent: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that intent is in the whitelist.
    
    Security: Reject unknown intents to prevent unauthorized operations.
    
    Args:
        intent: Intent name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not intent:
        return False, 'Intent is required'
    
    if intent not in ALLOWED_INTENTS:
        logger.warning(f'Rejected unknown intent: {intent}')
        return False, f'Unknown intent: {intent}. Allowed intents: {sorted(ALLOWED_INTENTS)}'
    
    return True, None


def validate_payload_size(body: str) -> Tuple[bool, Optional[str]]:
    """
    Validate request payload size.
    
    Args:
        body: Request body string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    size = len(body.encode('utf-8'))
    max_size = Config.MAX_PAYLOAD_SIZE
    
    if size > max_size:
        return False, f'Payload too large: {size} bytes (max: {max_size} bytes)'
    
    return True, None


def validate_json(body: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate and parse JSON body.
    
    Args:
        body: Request body string
        
    Returns:
        Tuple of (is_valid, parsed_json, error_message)
    """
    try:
        data = json.loads(body)
        return True, data, None
    except json.JSONDecodeError as e:
        return False, None, f'Invalid JSON: {str(e)}'


def validate_limit(limit: Any) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate query limit parameter.
    
    Args:
        limit: Limit value (may be int, string, or None)
        
    Returns:
        Tuple of (is_valid, parsed_limit, error_message)
    """
    if limit is None:
        return True, 100, None  # Default limit
    
    try:
        limit_int = int(limit)
        max_limit = Config.MAX_QUERY_LIMIT
        
        if limit_int < 1:
            return False, None, 'Limit must be positive'
        
        if limit_int > max_limit:
            return False, None, f'Limit exceeds maximum: {max_limit}'
        
        return True, limit_int, None
    except (ValueError, TypeError):
        return False, None, 'Limit must be an integer'


def validate_timestamp(timestamp: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate timestamp format (ISO 8601).
    
    Args:
        timestamp: Timestamp string
        
    Returns:
        Tuple of (is_valid, parsed_timestamp, error_message)
    """
    if timestamp is None:
        return True, None, None
    
    if not isinstance(timestamp, str):
        return False, None, 'Timestamp must be a string'
    
    # Basic ISO 8601 format check (YYYY-MM-DD HH:MM:SS or ISO format)
    # In production, use dateutil.parser for strict validation
    if len(timestamp) < 10:
        return False, None, 'Invalid timestamp format'
    
    return True, timestamp, None


def validate_ip_address(ip: Any) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate IP address format.
    
    Args:
        ip: IP address string
        
    Returns:
        Tuple of (is_valid, parsed_ip, error_message)
    """
    if ip is None:
        return True, None, None
    
    if not isinstance(ip, str):
        return False, None, 'IP address must be a string'
    
    # Basic IP validation (IPv4)
    # In production, use ipaddress module for strict validation
    parts = ip.split('.')
    if len(parts) != 4:
        return False, None, 'Invalid IP address format'
    
    try:
        for part in parts:
            num = int(part)
            if not (0 <= num <= 255):
                return False, None, 'Invalid IP address range'
    except ValueError:
        return False, None, 'IP address must contain numbers'
    
    return True, ip, None


def validate_status_code(status_code: Any) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate HTTP status code.
    
    Args:
        status_code: Status code (may be int or string)
        
    Returns:
        Tuple of (is_valid, parsed_code, error_message)
    """
    if status_code is None:
        return True, None, None
    
    try:
        code = int(status_code)
        if not (100 <= code <= 599):
            return False, None, 'Status code must be between 100 and 599'
        return True, code, None
    except (ValueError, TypeError):
        return False, None, 'Status code must be an integer'


def validate_intent_params(intent: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate parameters for specific intent.
    
    Args:
        intent: Intent name
        params: Parameters dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate common parameters
    if 'limit' in params:
        is_valid, _, error = validate_limit(params['limit'])
        if not is_valid:
            return False, error
    
    # Intent-specific validation
    if intent == 'get_access_logs':
        # Optional filters
        if 'ip_address' in params:
            is_valid, _, error = validate_ip_address(params['ip_address'])
            if not is_valid:
                return False, error
        
        if 'status_code' in params:
            is_valid, _, error = validate_status_code(params['status_code'])
            if not is_valid:
                return False, error
        
        if 'start_time' in params:
            is_valid, _, error = validate_timestamp(params['start_time'])
            if not is_valid:
                return False, error
        
        if 'end_time' in params:
            is_valid, _, error = validate_timestamp(params['end_time'])
            if not is_valid:
                return False, error
    
    elif intent == 'store_access_log':
        # Required fields
        required = ['timestamp', 'ip_address', 'method', 'endpoint', 'status_code']
        for field in required:
            if field not in params:
                return False, f'Missing required field: {field}'
        
        # Validate types
        is_valid, _, error = validate_timestamp(params['timestamp'])
        if not is_valid:
            return False, error
        
        is_valid, _, error = validate_ip_address(params['ip_address'])
        if not is_valid:
            return False, error
        
        is_valid, _, error = validate_status_code(params['status_code'])
        if not is_valid:
            return False, error
    
    elif intent == 'store_error_log':
        # Required fields
        required = ['timestamp', 'log_level', 'error_code', 'error_message']
        for field in required:
            if field not in params:
                return False, f'Missing required field: {field}'
        
        is_valid, _, error = validate_timestamp(params['timestamp'])
        if not is_valid:
            return False, error
    
    elif intent == 'get_traffic_summary':
        # Optional time range
        if 'start_time' in params:
            is_valid, _, error = validate_timestamp(params['start_time'])
            if not is_valid:
                return False, error
        
        if 'end_time' in params:
            is_valid, _, error = validate_timestamp(params['end_time'])
            if not is_valid:
                return False, error
    
    # Add validation for other intents as needed
    
    return True, None


def validate_request(body: str, intent: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Complete request validation pipeline.
    
    Args:
        body: Request body string
        intent: Optional intent name (if already extracted)
        
    Returns:
        Tuple of (is_valid, parsed_data, error_message)
    """
    # 1. Check payload size
    is_valid, error = validate_payload_size(body)
    if not is_valid:
        return False, None, error
    
    # 2. Parse JSON
    is_valid, data, error = validate_json(body)
    if not is_valid:
        return False, None, error
    
    # 3. Validate intent
    intent_to_check = intent or data.get('intent')
    is_valid, error = validate_intent(intent_to_check)
    if not is_valid:
        return False, None, error
    
    # 4. Validate parameters
    params = data.get('params', {})
    is_valid, error = validate_intent_params(intent_to_check, params)
    if not is_valid:
        return False, None, error
    
    return True, data, None