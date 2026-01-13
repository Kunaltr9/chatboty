"""
Structured JSON Logging
=======================
Production-grade logging with JSON output for CloudWatch Logs Insights.
Never logs sensitive data (passwords, API keys, full request bodies).

Security Notes:
- All logs are JSON for easy parsing
- Sensitive fields are masked
- Request IDs included for traceability
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import traceback


class StructuredLogger:
    """
    JSON-structured logger for CloudWatch Logs.
    Outputs one JSON object per log line for easy querying.
    """
    
    def __init__(self, name: str = 'lambda_backend', level: str = 'INFO'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Remove default handlers
        self.logger.handlers = []
        
        # Add JSON formatter handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
    
    def _sanitize(self, data: Any) -> Any:
        """
        Remove sensitive fields from log data.
        Never log passwords, API keys, or full request bodies.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = [
                'password', 'api_key', 'x-api-key', 'authorization',
                'token', 'secret', 'credential', 'db_password'
            ]
            
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in sensitive_keys):
                    sanitized[key] = '***REDACTED***'
                else:
                    sanitized[key] = self._sanitize(value)
            return sanitized
        
        elif isinstance(data, list):
            return [self._sanitize(item) for item in data]
        
        elif isinstance(data, str) and len(data) > 1000:
            # Truncate very long strings
            return data[:1000] + '... [TRUNCATED]'
        
        return data
    
    def _log(self, level: str, message: str, **kwargs):
        """
        Internal logging method with structured data.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            **kwargs: Additional structured fields
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'message': message,
            **self._sanitize(kwargs)
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_data))
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log('warning', message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """
        Log error message with optional exception.
        Stack traces are logged internally but never sent to client.
        
        Args:
            message: Error message
            error: Optional exception object
            **kwargs: Additional context
        """
        log_data = kwargs.copy()
        
        if error:
            log_data['error_type'] = type(error).__name__
            log_data['error_message'] = str(error)
            # Include stack trace for internal debugging
            log_data['stack_trace'] = traceback.format_exc()
        
        self._log('error', message, **log_data)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical error"""
        self.error(message, error, **kwargs)
    
    def log_request(self, request_id: str, intent: str, caller_ip: Optional[str] = None, **kwargs):
        """
        Log incoming API request.
        
        Args:
            request_id: Unique request identifier
            intent: Intent name
            caller_ip: Client IP address (if available)
            **kwargs: Additional request context
        """
        self.info(
            'API request received',
            request_id=request_id,
            intent=intent,
            caller_ip=caller_ip,
            **kwargs
        )
    
    def log_response(self, request_id: str, status_code: int, intent: str, **kwargs):
        """
        Log API response.
        
        Args:
            request_id: Unique request identifier
            status_code: HTTP status code
            intent: Intent name
            **kwargs: Additional response context
        """
        self.info(
            'API response sent',
            request_id=request_id,
            status_code=status_code,
            intent=intent,
            **kwargs
        )


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON"""
    
    def format(self, record):
        # If message is already JSON, return as-is
        if isinstance(record.msg, str) and record.msg.startswith('{'):
            return record.msg
        return super().format(record)


# Global logger instance
_logger: Optional[StructuredLogger] = None


def get_logger() -> StructuredLogger:
    """
    Get or create global logger instance.
    Singleton pattern for Lambda reuse.
    
    Returns:
        StructuredLogger instance
    """
    global _logger
    if _logger is None:
        from config import Config
        _logger = StructuredLogger(level=Config.LOG_LEVEL)
    return _logger