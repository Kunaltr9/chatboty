# Deployment Guide: Secure Lambda Backend

Step-by-step guide for deploying the chatbot Lambda backend to AWS.

## Prerequisites Checklist

- [ ] AWS Account with appropriate permissions
- [ ] VPC with private subnets (for RDS)
- [ ] RDS MariaDB instance created
- [ ] Database tables created (see README.md)
- [ ] AWS CLI configured
- [ ] Python 3.9+ installed locally

## Step 1: Prepare Lambda Package

```bash
# Navigate to lambda_backend directory
cd lambda_backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -t .

# Create deployment package
zip -r lambda_function.zip . -x "*.pyc" "__pycache__/*" "*.git*" "venv/*" "*.md"

# Verify package size (should be < 50MB for direct upload)
ls -lh lambda_function.zip
```

**Note**: If package exceeds 50MB, upload to S3 first and reference from Lambda.

## Step 2: Create IAM Role for Lambda

### Using AWS Console:

1. Go to **IAM** → **Roles** → **Create Role**
2. Select **AWS Service** → **Lambda**
3. Attach policies:
   - `AWSLambdaVPCAccessExecutionRole` (for VPC access)
   - Create custom policy for CloudWatch Logs (see below)

### Custom CloudWatch Policy:

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
    }
  ]
}
```

### Using AWS CLI:

```bash
# Create trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name ChatbotLambdaRole \
  --assume-role-policy-document file://trust-policy.json

# Attach VPC access policy
aws iam attach-role-policy \
  --role-name ChatbotLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# Attach CloudWatch Logs policy (create custom policy first)
aws iam put-role-policy \
  --role-name ChatbotLambdaRole \
  --policy-name CloudWatchLogsPolicy \
  --policy-document file://cloudwatch-policy.json
```

**Save the Role ARN** - you'll need it for Lambda creation.

## Step 3: Create Lambda Function

### Using AWS Console:

1. Go to **Lambda** → **Create Function**
2. **Author from scratch**
3. Basic Information:
   - Function name: `chatbot-backend`
   - Runtime: `Python 3.9` (or newer)
   - Architecture: `x86_64`
   - Execution role: Select the role created in Step 2
4. Click **Create Function**

5. **Upload Code**:
   - Upload `lambda_function.zip` (or upload to S3 first if > 50MB)
   - Handler: `lambda_function.lambda_handler`

6. **Configuration**:
   - **General**:
     - Timeout: 30 seconds
     - Memory: 256 MB
   - **Environment Variables**:
     ```
     DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
     DB_PORT=3306
     DB_NAME=chatbot_db
     DB_USER=app_user
     DB_PASSWORD=your-secure-password
     API_KEYS=your-api-key-1,your-api-key-2
     MAX_PAYLOAD_SIZE=1048576
     MAX_QUERY_LIMIT=1000
     LOG_LEVEL=INFO
     ```
   - **VPC**:
     - VPC: Select your VPC
     - Subnets: Select private subnets (same as RDS)
     - Security Groups: Select Lambda security group (created in Step 4)

7. **Save** the function

### Using AWS CLI:

```bash
# Create function
aws lambda create-function \
  --function-name chatbot-backend \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT_ID:role/ChatbotLambdaRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables="{
    DB_HOST=your-rds-endpoint.region.rds.amazonaws.com,
    DB_PORT=3306,
    DB_NAME=chatbot_db,
    DB_USER=app_user,
    DB_PASSWORD=your-secure-password,
    API_KEYS=your-api-key-1,your-api-key-2,
    MAX_PAYLOAD_SIZE=1048576,
    MAX_QUERY_LIMIT=1000,
    LOG_LEVEL=INFO
  }" \
  --vpc-config SubnetIds=subnet-xxx,subnet-yyy,SecurityGroupIds=sg-xxx

# Update code (if needed later)
aws lambda update-function-code \
  --function-name chatbot-backend \
  --zip-file fileb://lambda_function.zip
```

## Step 4: Configure VPC & Security Groups

### Create Lambda Security Group:

1. Go to **EC2** → **Security Groups** → **Create Security Group**
2. Name: `lambda-chatbot-sg`
3. Description: `Security group for chatbot Lambda`
4. VPC: Select your VPC
5. **Outbound Rules**:
   - Type: MySQL/Aurora (TCP 3306)
   - Destination: RDS security group (created below)
6. **Create**

### Create/Configure RDS Security Group:

1. Go to **EC2** → **Security Groups**
2. Find your RDS security group (or create new)
3. **Inbound Rules** → **Edit**
4. Add rule:
   - Type: MySQL/Aurora (TCP 3306)
   - Source: Lambda security group (`lambda-chatbot-sg`)
5. **Save**

### Update Lambda VPC Configuration:

1. Go to **Lambda** → Your function → **Configuration** → **VPC**
2. Edit VPC configuration:
   - VPC: Your VPC
   - Subnets: Private subnets (same as RDS)
   - Security Groups: `lambda-chatbot-sg`
3. **Save**

**Note**: Lambda ENI creation takes 1-2 minutes. Monitor CloudWatch Logs.

## Step 5: Create API Gateway REST API

### Using AWS Console:

1. Go to **API Gateway** → **Create API**
2. Choose **REST API** → **Build**
3. **New API**:
   - API name: `chatbot-api`
   - Endpoint Type: **Regional** (or Edge if using CloudFront)
4. **Create API**

5. **Create Resource**:
   - Actions → **Create Resource**
   - Resource Name: `chatbot`
   - Resource Path: `/chatbot`
   - **Create Resource**

6. **Create Method**:
   - Select `/chatbot` resource
   - Actions → **Create Method** → **POST**
   - Integration Type: **Lambda Function**
   - Lambda Region: Your region
   - Lambda Function: `chatbot-backend`
   - **Use Lambda Proxy Integration**: ✅ Checked
   - **Save** → **OK** (when prompted to grant permissions)

7. **Enable API Key Requirement**:
   - Select **POST** method
   - **Method Request**:
     - **API Key Required**: `true`
   - **Save**

8. **Deploy API**:
   - Actions → **Deploy API**
   - Deployment Stage: `prod` (or create new)
   - **Deploy**

**Save the Invoke URL** - you'll need it for API calls.

## Step 6: Create API Key & Usage Plan

### Create API Key:

1. Go to **API Gateway** → **API Keys** → **Create**
2. Name: `chatbot-api-key`
3. **Save**
4. **Show** the API key value → **Copy and save securely**

### Create Usage Plan:

1. Go to **API Gateway** → **Usage Plans** → **Create**
2. Name: `chatbot-usage-plan`
3. **Throttle**:
   - Rate: `100` requests/second
   - Burst: `200` requests/second
4. **Quota**:
   - Enable quota: ✅
   - Requests: `100000` per month
5. **Add API Stage**:
   - API: `chatbot-api`
   - Stage: `prod`
   - **Add**
6. **Add API Key**:
   - Select `chatbot-api-key`
   - **Add**
7. **Create**

### Associate Usage Plan with API:

1. Select your usage plan
2. **API Keys** tab → **Add API Key to Usage Plan**
3. Select `chatbot-api-key` → **Add**

## Step 7: Test the API

### Test from AWS Console:

1. Go to **API Gateway** → Your API → **POST** method
2. **TEST**
3. **Headers**:
   ```
   x-api-key: your-api-key-here
   Content-Type: application/json
   ```
4. **Request Body**:
   ```json
   {
     "intent": "get_traffic_summary",
     "params": {}
   }
   ```
5. **Test** → Check response (should be 200)

### Test from Command Line:

```bash
# Replace with your API Gateway URL
API_URL="https://your-api-id.execute-api.region.amazonaws.com/prod/chatbot"
API_KEY="your-api-key-here"

curl -X POST "$API_URL" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "get_traffic_summary",
    "params": {}
  }'
```

Expected response:
```json
{
  "request_id": "uuid-here",
  "success": true,
  "data": {
    "total_requests": 0,
    "error_count": 0,
    "error_rate": 0,
    "top_endpoints": {},
    "top_ips": {}
  }
}
```

## Step 8: Configure CloudWatch Alarms (Optional)

### Create Error Rate Alarm:

1. Go to **CloudWatch** → **Alarms** → **Create Alarm**
2. **Metric**: Lambda Errors
3. **Dimensions**: FunctionName = `chatbot-backend`
4. **Conditions**:
   - Threshold: `> 10` errors in 5 minutes
5. **Actions**: Send SNS notification (optional)
6. **Create**

### Create API Gateway 4xx Alarm:

1. **CloudWatch** → **Alarms** → **Create Alarm**
2. **Metric**: API Gateway 4XXError
3. **Dimensions**: API Name = `chatbot-api`, Stage = `prod`
4. **Conditions**: `> 50` errors in 5 minutes
5. **Create**

## Step 9: Update Chatbot to Use API

### Python Example:

```python
import requests
import os

# Configuration
API_URL = os.getenv('CHATBOT_API_URL', 'https://your-api-id.execute-api.region.amazonaws.com/prod/chatbot')
API_KEY = os.getenv('CHATBOT_API_KEY', 'your-api-key-here')

def call_backend(intent: str, params: dict = None) -> dict:
    """Call Lambda backend API"""
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'intent': intent,
        'params': params or {}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {str(e)}'
        }

# Usage in chatbot
result = call_backend('get_access_logs', {
    'ip_address': '192.168.1.1',
    'limit': 50
})

if result.get('success'):
    logs = result['data']['logs']
    # Process logs...
else:
    print(f"Error: {result['error']}")
```

## Troubleshooting

### Lambda Timeout

**Symptoms**: Lambda times out after 30 seconds

**Solutions**:
- Increase Lambda timeout (max 15 minutes)
- Check database query performance
- Review CloudWatch Logs for slow queries
- Verify RDS instance size is adequate

### Database Connection Errors

**Symptoms**: `Failed to connect to database` in logs

**Solutions**:
- Verify Lambda is in VPC (Configuration → VPC)
- Check security group rules (Lambda → RDS)
- Verify DB credentials in environment variables
- Check RDS endpoint is correct
- Verify RDS is in same VPC as Lambda
- Check RDS security group allows Lambda security group

### 401 Unauthorized

**Symptoms**: API returns 401 Unauthorized

**Solutions**:
- Verify `x-api-key` header is present
- Check API key value is correct
- Verify API key is associated with usage plan
- Check API Gateway stage is deployed
- Verify API key requirement is enabled on method

### 403 Forbidden (API Key)

**Symptoms**: API returns 403 Forbidden

**Solutions**:
- API key not associated with usage plan
- Usage plan not associated with API stage
- API Gateway stage not deployed

### 429 Too Many Requests

**Symptoms**: API returns 429 Too Many Requests

**Solutions**:
- Reduce request rate in chatbot
- Increase throttling limits in usage plan
- Implement exponential backoff in chatbot
- Check burst limit vs rate limit

### VPC ENI Creation Delays

**Symptoms**: Lambda cold starts take 30+ seconds

**Solutions**:
- This is normal for first invocation
- Consider Lambda Provisioned Concurrency for production
- Ensure sufficient ENI capacity in subnet
- Use multiple subnets for redundancy

## Security Checklist

- [ ] API Gateway requires API key
- [ ] Lambda validates API key
- [ ] Database credentials in environment variables (not code)
- [ ] RDS in private subnet (no public access)
- [ ] Security groups configured correctly
- [ ] Lambda in VPC
- [ ] HTTPS only (API Gateway default)
- [ ] CloudWatch Logs enabled
- [ ] IAM role follows least privilege
- [ ] API keys rotated regularly
- [ ] Error messages don't leak sensitive info
- [ ] Input validation enabled
- [ ] Rate limiting configured

## Cost Estimation

**Monthly costs (approximate)**:

- Lambda: $0.20 per 1M requests (first 1M free)
- API Gateway: $3.50 per 1M requests (first 1M free)
- RDS: $15-100+ depending on instance size
- CloudWatch Logs: $0.50 per GB ingested
- Data Transfer: $0.09 per GB (outbound)

**Total**: ~$20-150/month for moderate usage

## Next Steps

1. **Enable AWS Secrets Manager** (upgrade from env vars)
2. **Set up CloudWatch Dashboards** for monitoring
3. **Configure AWS WAF** on API Gateway
4. **Set up CI/CD pipeline** for deployments
5. **Enable X-Ray tracing** for debugging
6. **Implement API versioning** (`/v1`, `/v2`)
7. **Add request signing** for additional security
8. **Set up automated backups** for RDS

## Support

For issues:
1. Check CloudWatch Logs: `/aws/lambda/chatbot-backend`
2. Review API Gateway logs
3. Test database connectivity from Lambda
4. Verify all environment variables
5. Check security group rules
6. Review IAM role permissions