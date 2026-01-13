"""
Lambda Function Entry Point
============================
API Gateway integration handler for the chatbot backend.

This is the main entry point for all API requests.
Handles authentication, validation, routing, and error handling.

Security Flow:
1. Extract and validate API key
2. Validate request schema
3. Route to intent handler
4. Return JSON response
5. Log all operations (no sensitive data)

Error Handling:
- Never expose stack traces to client
- Generic error messages only
- Detailed errors logged internally
"""

import json
import uuid
from typing import Dict, Any, Optional
from auth import authenticate_request
from validators import validate_request
from intents import execute_intent
from logger import get_logger
from config import Config

logger = get_logger()


def create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create API Gateway response format.
    
    Args:
        status_code: HTTP status code
        body: Response body dictionary
        headers: Optional custom headers
        
    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)  # default=str handles datetime serialization
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function (API Gateway integration).
    
    This function is called by API Gateway for each HTTP request.
    
    Args:
        event: API Gateway event (contains headers, body, etc.)
        context: Lambda context (request ID, etc.)
        
    Returns:
        API Gateway response dictionary
    """
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())
    
    try:
        # Validate configuration at cold start
        try:
            Config.validate()
        except ValueError as e:
            logger.critical('Configuration validation failed', error=e)
            return create_response(
                500,
                {'error': 'Server configuration error', 'request_id': request_id}
            )
        
        # Extract request components
        headers = event.get('headers', {}) or {}
        body_str = event.get('body', '') or '{}'
        http_method = event.get('httpMethod', 'POST')
        
        # Extract caller IP (from API Gateway)
        caller_ip = (
            headers.get('X-Forwarded-For', '').split(',')[0].strip() or
            headers.get('X-Real-Ip', '') or
            event.get('requestContext', {}).get('identity', {}).get('sourceIp', '')
        )
        
        # Log incoming request
        logger.log_request(
            request_id=request_id,
            intent='unknown',
            caller_ip=caller_ip,
            http_method=http_method
        )
        
        # 1. AUTHENTICATION: Validate API key
        is_authenticated, auth_error = authenticate_request(headers)
        if not is_authenticated:
            logger.warning(
                'Authentication failed',
                request_id=request_id,
                caller_ip=caller_ip
            )
            return create_response(
                401,
                {'error': auth_error, 'request_id': request_id}
            )
        
        # 2. HTTP Method validation (only POST allowed for security)
        if http_method != 'POST':
            logger.warning(
                'Invalid HTTP method',
                request_id=request_id,
                http_method=http_method
            )
            return create_response(
                405,
                {'error': 'Method not allowed. Use POST.', 'request_id': request_id}
            )
        
        # 3. VALIDATION: Validate request body
        is_valid, data, validation_error = validate_request(body_str)
        if not is_valid:
            logger.warning(
                'Request validation failed',
                request_id=request_id,
                error=validation_error
            )
            return create_response(
                400,
                {'error': validation_error, 'request_id': request_id}
            )
        
        # Extract intent and parameters
        intent = data.get('intent')
        params = data.get('params', {})
        
        # Log intent execution
        logger.info(
            'Executing intent',
            request_id=request_id,
            intent=intent,
            params_count=len(params)
        )
        
        # 4. EXECUTE: Route to intent handler
        try:
            result = execute_intent(intent, params)
            
            # Determine status code based on result
            status_code = 200 if result.get('success', False) else 500
            
            # Log response
            logger.log_response(
                request_id=request_id,
                status_code=status_code,
                intent=intent
            )
            
            # Return response with request_id for tracing
            response_body = {
                'request_id': request_id,
                **result
            }
            
            return create_response(status_code, response_body)
        
        except Exception as e:
            # Internal error - log but don't expose details
            logger.error(
                'Intent execution failed',
                error=e,
                request_id=request_id,
                intent=intent
            )
            
            return create_response(
                500,
                {
                    'error': 'Internal server error',
                    'request_id': request_id
                }
            )
    
    except Exception as e:
        # Unexpected error - log but return generic message
        logger.critical(
            'Unexpected error in lambda_handler',
            error=e,
            request_id=request_id
        )
        
        return create_response(
            500,
            {
                'error': 'Internal server error',
                'request_id': request_id
            }
        )