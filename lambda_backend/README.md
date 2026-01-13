# Secure Lambda Backend for Chatbot

Production-grade, security-first AWS Lambda backend for the Watermark Security Intelligence Chatbot.

## Architecture

```
Chatbot (LLM) 
    ↓ HTTPS
API Gateway (API Key + Throttling)
    ↓ VPC
Lambda Function (VPC-attached)
    ↓ Private Network
RDS MariaDB (Private Subnet)
```

## Security Features

### 1. Authentication & Authorization
- **API Gateway API Key**: Required for all requests
- **Lambda Validation**: Validates `x-api-key` header
- **Key Rotation**: Supports multiple keys (comma-separated)
- **Constant-Time Comparison**: Prevents timing attacks

### 2. Network Security
- **VPC Attachment**: Lambda runs in VPC
- **Private RDS**: Database has no public access
- **Security Groups**: Lambda → RDS only
- **HTTPS Only**: API Gateway enforces TLS

### 3. Secrets Management
- **Environment Variables**: DB credentials from Lambda env vars
- **No Secrets in Code**: All sensitive values externalized
- **AWS Secrets Manager**: Optional upgrade path (see `config.py`)

### 4. Input Validation
- **JSON Schema Validation**: Strict request validation
- **Intent Whitelist**: Only allowed intents executed
- **Parameter Validation**: Type checking and limits
- **Payload Size Limits**: Prevents DoS attacks

### 5. SQL Safety
- **Parameterized Queries Only**: No string interpolation
- **SQL Injection Prevention**: All queries use placeholders
- **Connection Pooling**: Efficient resource usage

### 6. Rate Limiting
- **API Gateway Usage Plans**: Per-key throttling
- **429 Responses**: Graceful rate limit handling
- **Configurable Limits**: Adjustable per environment

### 7. Observability
- **Structured JSON Logging**: CloudWatch Logs Insights compatible
- **Request Tracing**: Unique request_id per request
- **No Sensitive Data Logged**: Passwords/keys masked
- **Error Logging**: Internal errors logged, not exposed

### 8. Error Handling
- **Generic Error Messages**: No stack traces to client
- **Internal Error Logging**: Detailed errors in CloudWatch
- **Graceful Degradation**: Fail-safe error responses

### 9. Least Privilege IAM
- **Minimal Permissions**: RDS + CloudWatch only
- **No Wildcards**: Explicit resource ARNs
- **VPC Permissions**: ENI creation/management

### 10. LLM-Optimized
- **JSON-Only Output**: No markdown or UI formatting
- **Structured Responses**: Easy for LLM tool-calling
- **Clear Error Messages**: LLM-friendly error handling

## Deployment

### Prerequisites

1. **AWS Account** with:
   - Lambda
   - API Gateway
   - RDS (MariaDB)
   - VPC with private subnets
   - IAM roles

2. **Database Setup**:
   - Create MariaDB instance in private subnet
   - Create tables (see `db_client.py` for schema)
   - Note connection details

3. **Python 3.9+** (Lambda runtime)

### Step 1: Package Lambda Function

```bash
cd lambda_backend
pip install -r requirements.txt -t .
zip -r lambda_function.zip . -x "*.pyc" "__pycache__/*" "*.git*"
```

### Step 2: Create Lambda Function

1. **Create IAM Role** with:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "logs:CreateLogGroup",
           "logs:CreateLogStream",
           "logs:PutLogEvents"
         ],
         "Resource": "arn:aws:logs:*:*:*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "ec2:CreateNetworkInterface",
           "ec2:DescribeNetworkInterfaces",
           "ec2:DeleteNetworkInterface"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

2. **Create Lambda Function**:
   - Runtime: Python 3.9+
   - Handler: `lambda_function.lambda_handler`
   - Role: IAM role created above
   - VPC: Attach to VPC with RDS access
   - Timeout: 30 seconds
   - Memory: 256 MB (adjust as needed)

3. **Set Environment Variables**:
   ```
   DB_HOST=rds-instance.region.rds.amazonaws.com
   DB_PORT=3306
   DB_NAME=chatbot_db
   DB_USER=app_user
   DB_PASSWORD=secure_password_here
   API_KEYS=your_api_key_1,your_api_key_2
   MAX_PAYLOAD_SIZE=1048576
   MAX_QUERY_LIMIT=1000
   LOG_LEVEL=INFO
   ```

### Step 3: Configure API Gateway

1. **Create REST API**:
   - Type: REST API
   - Endpoint Type: Regional (or Edge if using CloudFront)

2. **Create Resource & Method**:
   - Resource: `/chatbot` (or `/api/v1`)
   - Method: POST
   - Integration: Lambda Function
   - Integration Request: Use Lambda Proxy Integration

3. **Enable API Key Requirement**:
   - Method Request → API Key Required: Yes
   - Deploy API to a stage (e.g., `prod`)

4. **Create API Key**:
   - Create API Key
   - Name: `chatbot-api-key`
   - Copy the key value (you'll need it)

5. **Create Usage Plan**:
   - Name: `chatbot-usage-plan`
   - Throttle: 100 requests/second, 10000 requests/day
   - Quota: 100000 requests/month
   - Associate API Key
   - Associate API Stage

6. **Enable HTTPS Only**:
   - API Gateway automatically enforces HTTPS
   - No HTTP endpoints available

### Step 4: Configure VPC & Security Groups

1. **Lambda Security Group**:
   - Outbound: Allow TCP 3306 to RDS security group
   - No inbound rules needed

2. **RDS Security Group**:
   - Inbound: Allow TCP 3306 from Lambda security group
   - No public access

3. **Lambda VPC Configuration**:
   - Subnets: Private subnets (same as RDS)
   - Security Group: Lambda security group

### Step 5: Database Schema

Run these SQL commands in your RDS instance:

```sql
CREATE DATABASE chatbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE chatbot_db;

CREATE TABLE access_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    method VARCHAR(10) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    http_version VARCHAR(10),
    status_code INT NOT NULL,
    response_size INT,
    response_time_ms INT,
    user_agent VARCHAR(500),
    department VARCHAR(100),
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_ip (ip_address),
    INDEX idx_status (status_code),
    INDEX idx_endpoint (endpoint(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE error_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    process_id INT,
    thread_id INT,
    client_ip VARCHAR(45),
    error_code VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    file_path VARCHAR(500),
    line_number INT,
    severity_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (log_level),
    INDEX idx_severity (severity_score),
    INDEX idx_error_code (error_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## API Usage

### Request Format

```json
{
  "intent": "get_access_logs",
  "params": {
    "ip_address": "192.168.1.1",
    "status_code": 401,
    "start_time": "2025-01-06 08:00:00",
    "end_time": "2025-01-06 18:00:00",
    "limit": 100
  }
}
```

### Response Format

```json
{
  "request_id": "uuid-here",
  "success": true,
  "data": {
    "logs": [...],
    "count": 10
  }
}
```

### Error Response

```json
{
  "request_id": "uuid-here",
  "success": false,
  "error": "Error message here"
}
```

### Available Intents

- `get_access_logs` - Query access logs with filters
- `get_error_logs` - Query error logs with filters
- `store_access_log` - Store new access log entry
- `store_error_log` - Store new error log entry
- `get_traffic_summary` - Get aggregated traffic statistics
- `get_security_threats` - Detect security threats
- `get_performance_metrics` - Get performance metrics
- `get_anomalies` - Detect anomalies from error logs

## Calling from Chatbot

### Python Example

```python
import requests
import json

API_URL = "https://your-api-id.execute-api.region.amazonaws.com/prod/chatbot"
API_KEY = "your-api-key-here"

def call_backend(intent, params):
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "intent": intent,
        "params": params
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# Example: Get access logs
result = call_backend("get_access_logs", {
    "ip_address": "192.168.1.1",
    "limit": 50
})

if result.get("success"):
    logs = result["data"]["logs"]
    print(f"Found {len(logs)} logs")
else:
    print(f"Error: {result['error']}")
```

### cURL Example

```bash
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/chatbot \
  -H "x-api-key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "get_traffic_summary",
    "params": {
      "start_time": "2025-01-06 00:00:00",
      "end_time": "2025-01-06 23:59:59"
    }
  }'
```

## API Gateway Security Configuration

### API Key Enforcement

API Gateway automatically:
- Requires `x-api-key` header
- Validates key against usage plan
- Returns 403 if key is missing/invalid

### Throttling Configuration

Configure in Usage Plan:
- **Rate**: 100 requests/second per key
- **Burst**: 200 requests/second
- **Quota**: 100,000 requests/month

### HTTPS Enforcement

- API Gateway only exposes HTTPS endpoints
- TLS 1.2+ required
- No HTTP endpoints available

## Monitoring & Debugging

### CloudWatch Logs

All logs are in CloudWatch Logs:
- Log Group: `/aws/lambda/your-function-name`
- JSON format for easy querying

### Example CloudWatch Logs Insights Query

```
fields @timestamp, level, message, intent, request_id
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

### Metrics to Monitor

- Lambda invocations
- Lambda errors
- Lambda duration
- API Gateway 4xx/5xx errors
- API Gateway throttles (429)
- Database connection errors

## Key Rotation

To rotate API keys:

1. **Add new key** to `API_KEYS` env var: `old_key,new_key`
2. **Update chatbot** to use new key
3. **Remove old key** after verification: `new_key`
4. **Update API Gateway** usage plan if needed

## Troubleshooting

### Lambda Timeout

- Increase Lambda timeout (max 15 minutes)
- Check database query performance
- Review CloudWatch Logs for slow queries

### Database Connection Errors

- Verify Lambda is in VPC
- Check security group rules
- Verify DB credentials
- Check RDS endpoint is correct

### 401 Unauthorized

- Verify API key is correct
- Check `x-api-key` header is present
- Verify API key is associated with usage plan
- Check API Gateway stage is deployed

### 429 Too Many Requests

- Reduce request rate
- Increase throttling limits in usage plan
- Implement exponential backoff in chatbot

## Security Best Practices

1. **Rotate API keys regularly** (every 90 days)
2. **Use AWS Secrets Manager** for production (upgrade from env vars)
3. **Enable CloudWatch Alarms** for error rates
4. **Review CloudWatch Logs** regularly
5. **Monitor API Gateway metrics** for abuse
6. **Keep Lambda runtime updated**
7. **Use least privilege IAM roles**
8. **Enable VPC Flow Logs** for network monitoring
9. **Regular security audits** of code and config
10. **Enable AWS WAF** on API Gateway for additional protection

## Cost Optimization

- **Lambda**: Pay per request (first 1M free/month)
- **API Gateway**: Pay per API call (first 1M free/month)
- **RDS**: Pay for instance size and storage
- **CloudWatch Logs**: Pay per GB ingested

Tips:
- Use Lambda provisioned concurrency only if needed
- Set appropriate RDS instance size
- Archive old CloudWatch logs to S3
- Use API Gateway caching for read-heavy workloads

## Support

For issues or questions:
1. Check CloudWatch Logs for errors
2. Review API Gateway logs
3. Verify environment variables
4. Test database connectivity from Lambda
5. Review security group rules

## License

Internal use only - Security-first backend for enterprise chatbot deployment.