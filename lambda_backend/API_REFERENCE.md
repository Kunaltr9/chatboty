# API Reference: Chatbot Lambda Backend

Complete API reference for the secure Lambda backend.

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/chatbot
```

Example:
```
https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod/chatbot
```

## Authentication

All requests require an API key in the `x-api-key` header:

```http
x-api-key: your-api-key-here
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: API key not associated with usage plan

## Request Format

All requests use `POST` method with JSON body:

```json
{
  "intent": "intent_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## Response Format

### Success Response

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "data": {
    // Intent-specific data
  }
}
```

### Error Response

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": false,
  "error": "Error message here"
}
```

## HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: API key not authorized
- `405 Method Not Allowed`: Wrong HTTP method (must be POST)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error (check logs)

## Intents

### get_access_logs

Retrieve access logs with optional filters.

**Parameters**:
- `ip_address` (string, optional): Filter by IP address
- `status_code` (integer, optional): Filter by HTTP status code
- `endpoint` (string, optional): Filter by endpoint (partial match)
- `start_time` (string, optional): Start timestamp (ISO 8601 or 'YYYY-MM-DD HH:MM:SS')
- `end_time` (string, optional): End timestamp
- `limit` (integer, optional): Max results (default: 100, max: 1000)

**Example Request**:
```json
{
  "intent": "get_access_logs",
  "params": {
    "ip_address": "192.168.1.1",
    "status_code": 401,
    "start_time": "2025-01-06 08:00:00",
    "end_time": "2025-01-06 18:00:00",
    "limit": 50
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "timestamp": "2025-01-06 08:15:23",
        "ip_address": "192.168.1.1",
        "method": "POST",
        "endpoint": "/login",
        "status_code": 401,
        "response_size": 234,
        "response_time_ms": 45,
        "user_agent": "Mozilla/5.0",
        "department": "Engineering",
        "user_id": "user_1001"
      }
    ],
    "count": 1
  }
}
```

---

### get_error_logs

Retrieve error logs with optional filters.

**Parameters**:
- `log_level` (string, optional): Filter by log level (warn, error, critical)
- `severity_score` (integer, optional): Minimum severity score (1-10)
- `error_code` (string, optional): Filter by error code
- `start_time` (string, optional): Start timestamp
- `end_time` (string, optional): End timestamp
- `limit` (integer, optional): Max results (default: 100, max: 1000)

**Example Request**:
```json
{
  "intent": "get_error_logs",
  "params": {
    "log_level": "error",
    "severity_score": 7,
    "limit": 20
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "timestamp": "2025-01-06 08:18:34",
        "log_level": "error",
        "error_code": "AUTH_FAILED",
        "error_message": "Authentication failed",
        "severity_score": 7,
        "client_ip": "203.45.12.89"
      }
    ],
    "count": 1
  }
}
```

---

### store_access_log

Store a new access log entry.

**Parameters** (required):
- `timestamp` (string): Timestamp (ISO 8601 or 'YYYY-MM-DD HH:MM:SS')
- `ip_address` (string): Client IP address
- `method` (string): HTTP method (GET, POST, etc.)
- `endpoint` (string): Request endpoint
- `status_code` (integer): HTTP status code (100-599)

**Parameters** (optional):
- `http_version` (string): HTTP version
- `response_size` (integer): Response size in bytes
- `response_time_ms` (integer): Response time in milliseconds
- `user_agent` (string): User agent string
- `department` (string): Department name
- `user_id` (string): User identifier

**Example Request**:
```json
{
  "intent": "store_access_log",
  "params": {
    "timestamp": "2025-01-06 10:30:00",
    "ip_address": "192.168.1.100",
    "method": "POST",
    "endpoint": "/api/data",
    "status_code": 200,
    "response_size": 1024,
    "response_time_ms": 150,
    "user_agent": "Mozilla/5.0",
    "department": "IT",
    "user_id": "user_2001"
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "id": 123,
    "message": "Access log stored successfully"
  }
}
```

---

### store_error_log

Store a new error log entry.

**Parameters** (required):
- `timestamp` (string): Timestamp
- `log_level` (string): Log level (warn, error, critical)
- `error_code` (string): Error code
- `error_message` (string): Error message

**Parameters** (optional):
- `process_id` (integer): Process ID
- `thread_id` (integer): Thread ID
- `client_ip` (string): Client IP address
- `file_path` (string): File path where error occurred
- `line_number` (integer): Line number
- `severity_score` (integer): Severity score 1-10 (default: 5)

**Example Request**:
```json
{
  "intent": "store_error_log",
  "params": {
    "timestamp": "2025-01-06 10:30:00",
    "log_level": "error",
    "error_code": "DB_CONNECTION_FAILED",
    "error_message": "Failed to connect to database",
    "severity_score": 8,
    "client_ip": "192.168.1.100"
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "id": 456,
    "message": "Error log stored successfully"
  }
}
```

---

### get_traffic_summary

Get aggregated traffic statistics.

**Parameters** (optional):
- `start_time` (string): Start timestamp
- `end_time` (string): End timestamp

**Example Request**:
```json
{
  "intent": "get_traffic_summary",
  "params": {
    "start_time": "2025-01-06 00:00:00",
    "end_time": "2025-01-06 23:59:59"
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "total_requests": 1000,
    "error_count": 50,
    "error_rate": 5.0,
    "top_endpoints": {
      "/api/login": 200,
      "/api/data": 150,
      "/api/logout": 100
    },
    "top_ips": {
      "192.168.1.1": 300,
      "192.168.1.2": 250,
      "192.168.1.3": 200
    }
  }
}
```

---

### get_security_threats

Detect security threats from access logs.

**Parameters** (optional):
- `start_time` (string): Start timestamp
- `end_time` (string): End timestamp

**Example Request**:
```json
{
  "intent": "get_security_threats",
  "params": {
    "start_time": "2025-01-06 00:00:00",
    "end_time": "2025-01-06 23:59:59"
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "threats": [
      {
        "severity": "HIGH",
        "type": "Brute Force Attack",
        "details": "5 failed login attempts from IP 192.168.1.1",
        "ip_address": "192.168.1.1",
        "count": 5
      },
      {
        "severity": "MEDIUM",
        "type": "SQL Injection Attempt",
        "details": "Suspicious tool detected: sqlmap/1.6.12 from 203.45.12.89",
        "ip_address": "203.45.12.89",
        "endpoint": "/admin/"
      }
    ],
    "count": 2
  }
}
```

---

### get_performance_metrics

Get performance metrics (slow endpoints).

**Parameters** (optional):
- `start_time` (string): Start timestamp
- `end_time` (string): End timestamp
- `threshold_ms` (integer): Response time threshold in ms (default: 1000)

**Example Request**:
```json
{
  "intent": "get_performance_metrics",
  "params": {
    "start_time": "2025-01-06 00:00:00",
    "threshold_ms": 2000
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "issues": [
      {
        "endpoint": "/api/slow-endpoint",
        "avg_response_time_ms": 2500.5,
        "peak_response_time_ms": 5000,
        "request_count": 10,
        "severity": "HIGH"
      }
    ],
    "count": 1
  }
}
```

---

### get_anomalies

Detect anomalies from error logs.

**Parameters** (optional):
- `start_time` (string): Start timestamp
- `end_time` (string): End timestamp
- `min_severity` (integer): Minimum severity score (default: 8)

**Example Request**:
```json
{
  "intent": "get_anomalies",
  "params": {
    "min_severity": 8
  }
}
```

**Example Response**:
```json
{
  "request_id": "uuid",
  "success": true,
  "data": {
    "anomalies": [
      {
        "timestamp": "2025-01-06 08:18:38",
        "error_code": "BRUTE_FORCE",
        "error_message": "Brute force attack detected",
        "severity_score": 9,
        "severity": "CRITICAL",
        "client_ip": "203.45.12.89",
        "file_path": "/path/to/file.php"
      }
    ],
    "count": 1
  }
}
```

## Error Codes

Common error messages:

- `"Unauthorized: Invalid or missing API key"`: API key missing or invalid
- `"Unknown intent: {intent}"`: Intent not in whitelist
- `"Missing required field: {field}"`: Required parameter missing
- `"Invalid JSON: {error}"`: Malformed JSON request
- `"Payload too large: {size} bytes"`: Request body exceeds limit
- `"Limit exceeds maximum: {max}"`: Limit parameter too high
- `"Internal server error"`: Server error (check CloudWatch Logs)

## Rate Limiting

Default limits (configurable in Usage Plan):
- **Rate**: 100 requests/second per API key
- **Burst**: 200 requests/second
- **Quota**: 100,000 requests/month

When rate limit is exceeded, API returns `429 Too Many Requests`.

## Best Practices

1. **Always include request_id** in error handling for tracing
2. **Implement exponential backoff** for 429 responses
3. **Validate responses** before processing data
4. **Handle timeouts** (30 seconds default)
5. **Log request_id** for debugging
6. **Cache responses** when appropriate
7. **Use appropriate limits** to avoid large responses
8. **Monitor error rates** and adjust accordingly

## Example: Python Client

```python
import requests
import time
from typing import Dict, Any, Optional

class ChatbotAPIClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        })
    
    def call(self, intent: str, params: Dict[str, Any] = None, retries: int = 3) -> Dict[str, Any]:
        """Call API with retry logic"""
        payload = {
            'intent': intent,
            'params': params or {}
        }
        
        for attempt in range(retries):
            try:
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=30
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.RequestException as e:
                if attempt == retries - 1:
                    return {
                        'success': False,
                        'error': f'API request failed: {str(e)}'
                    }
                time.sleep(2 ** attempt)
        
        return {'success': False, 'error': 'Max retries exceeded'}

# Usage
client = ChatbotAPIClient(
    api_url='https://your-api-id.execute-api.region.amazonaws.com/prod/chatbot',
    api_key='your-api-key-here'
)

result = client.call('get_access_logs', {
    'ip_address': '192.168.1.1',
    'limit': 50
})

if result.get('success'):
    logs = result['data']['logs']
    print(f"Found {len(logs)} logs")
else:
    print(f"Error: {result['error']}")
    print(f"Request ID: {result.get('request_id')}")
```

## Example: cURL

```bash
#!/bin/bash

API_URL="https://your-api-id.execute-api.region.amazonaws.com/prod/chatbot"
API_KEY="your-api-key-here"

# Get access logs
curl -X POST "$API_URL" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "get_access_logs",
    "params": {
      "ip_address": "192.168.1.1",
      "limit": 50
    }
  }'

# Get traffic summary
curl -X POST "$API_URL" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "get_traffic_summary",
    "params": {
      "start_time": "2025-01-06 00:00:00",
      "end_time": "2025-01-06 23:59:59"
    }
  }'
```