# Security Architecture & Implementation

Detailed security documentation for the Lambda backend.

## Security Model Overview

The backend implements defense-in-depth with multiple security layers:

```
Internet
    ↓ HTTPS (TLS 1.2+)
API Gateway (API Key + Rate Limiting)
    ↓ VPC (Private Network)
Lambda Function (Input Validation + Auth)
    ↓ Security Group (Least Privilege)
RDS MariaDB (Private Subnet, No Public Access)
```

## Security Layers

### Layer 1: Network Security

**API Gateway**:
- ✅ HTTPS only (TLS 1.2+ enforced)
- ✅ No HTTP endpoints exposed
- ✅ DDoS protection via AWS Shield
- ✅ Optional: AWS WAF for additional protection

**VPC Configuration**:
- ✅ Lambda in VPC (private subnets)
- ✅ RDS in private subnet (no public IP)
- ✅ Security groups: Lambda → RDS only
- ✅ No internet gateway access for RDS

**Security Groups**:
```
Lambda SG:
  Outbound: TCP 3306 → RDS SG only

RDS SG:
  Inbound: TCP 3306 ← Lambda SG only
  No public access
```

### Layer 2: Authentication & Authorization

**API Gateway API Key**:
- Required for all requests
- Validated before Lambda invocation
- Returns 403 if missing/invalid

**Lambda API Key Validation**:
- Validates `x-api-key` header
- Constant-time comparison (prevents timing attacks)
- Supports multiple keys for rotation
- Returns 401 if invalid

**Key Rotation**:
```python
# Environment variable format
API_KEYS=old_key,new_key,backup_key

# Rotation process:
# 1. Add new key: API_KEYS=old_key,new_key
# 2. Update clients to use new_key
# 3. Remove old_key: API_KEYS=new_key
```

### Layer 3: Input Validation

**Request Validation**:
- ✅ JSON schema validation
- ✅ Payload size limits (1MB default)
- ✅ Intent whitelist (only allowed intents)
- ✅ Parameter type validation
- ✅ Range validation (limits, timestamps, etc.)

**Intent Whitelist**:
```python
ALLOWED_INTENTS = {
    'get_access_logs',
    'get_error_logs',
    'store_access_log',
    'store_error_log',
    'get_traffic_summary',
    'get_security_threats',
    'get_performance_metrics',
    'get_anomalies',
}
# All other intents are rejected with 400 Bad Request
```

**Parameter Validation**:
- IP address format validation
- Timestamp format validation
- Status code range validation (100-599)
- Limit validation (1-1000)
- String length limits

### Layer 4: SQL Injection Prevention

**Parameterized Queries Only**:
```python
# ✅ CORRECT - Parameterized
query = "SELECT * FROM logs WHERE ip_address = %s"
db.execute_query(query, (ip_address,))

# ❌ WRONG - String interpolation (NOT USED)
query = f"SELECT * FROM logs WHERE ip_address = '{ip_address}'"  # NEVER DO THIS
```

**All Database Operations**:
- ✅ All queries use `%s` placeholders
- ✅ Parameters passed as tuples
- ✅ No string formatting in SQL
- ✅ No f-strings in SQL
- ✅ Connection pooling with safe defaults

### Layer 5: Secrets Management

**Current Implementation**:
- Environment variables in Lambda
- No secrets in code
- Fail-fast if secrets missing

**Environment Variables**:
```
DB_HOST=...
DB_PASSWORD=...  # Never logged
API_KEYS=...     # Never logged
```

**Upgrade Path (AWS Secrets Manager)**:
```python
# See config.py for commented example
# Benefits:
# - Automatic rotation
# - Audit logging
# - Fine-grained access control
# - Versioning
```

### Layer 6: Error Handling

**Client-Facing Errors**:
- Generic error messages only
- No stack traces exposed
- No database structure leaked
- Request ID for tracing

**Internal Logging**:
- Full stack traces in CloudWatch
- Request ID included
- Intent and parameters logged
- No sensitive data logged

**Error Response Example**:
```json
{
  "request_id": "uuid",
  "success": false,
  "error": "Internal server error"  // Generic, no details
}
```

### Layer 7: Rate Limiting & Abuse Prevention

**API Gateway Usage Plans**:
- Rate: 100 requests/second
- Burst: 200 requests/second
- Quota: 100,000 requests/month
- Per-key throttling

**Response to Abuse**:
- 429 Too Many Requests
- Graceful degradation
- No service disruption

**Monitoring**:
- CloudWatch metrics for throttles
- Alarms for abuse patterns
- Log analysis for anomalies

### Layer 8: Observability & Audit

**Structured Logging**:
- JSON format for CloudWatch Logs Insights
- Request ID for tracing
- Intent and parameters logged
- No sensitive data logged

**Log Format**:
```json
{
  "timestamp": "2025-01-06T10:30:00Z",
  "level": "INFO",
  "message": "API request received",
  "request_id": "uuid",
  "intent": "get_access_logs",
  "caller_ip": "192.168.1.1"
}
```

**Sensitive Data Masking**:
- Passwords: `***REDACTED***`
- API keys: `***REDACTED***`
- Long strings: Truncated with `[TRUNCATED]`

**Audit Trail**:
- All requests logged
- Authentication failures logged
- Validation failures logged
- Intent execution logged
- Errors logged with context

### Layer 9: IAM Least Privilege

**Lambda IAM Role**:
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

**No Wildcard Permissions**:
- ✅ Explicit resource ARNs
- ✅ No `*` actions
- ✅ No `*` resources
- ✅ VPC permissions only

**RDS Access**:
- Via VPC security groups (not IAM)
- No IAM database authentication needed
- Traditional username/password

### Layer 10: LLM Safety

**JSON-Only Output**:
- No markdown formatting
- No HTML/UI code
- Pure JSON for tool-calling
- Consistent structure

**Structured Responses**:
```json
{
  "success": true,
  "data": {
    // Structured data only
  }
}
```

**Error Messages**:
- LLM-friendly error messages
- Clear intent names
- Consistent parameter names
- Request ID for debugging

## Threat Model

### Threats Mitigated

1. **SQL Injection**
   - ✅ Parameterized queries only
   - ✅ No string interpolation
   - ✅ Input validation

2. **API Key Theft**
   - ✅ HTTPS only
   - ✅ Constant-time comparison
   - ✅ Key rotation support

3. **DDoS Attacks**
   - ✅ API Gateway rate limiting
   - ✅ Payload size limits
   - ✅ AWS Shield protection

4. **Data Exfiltration**
   - ✅ Private RDS (no public access)
   - ✅ VPC-only access
   - ✅ Security group restrictions

5. **Credential Leakage**
   - ✅ No secrets in code
   - ✅ Environment variables
   - ✅ Optional: Secrets Manager

6. **Information Disclosure**
   - ✅ Generic error messages
   - ✅ No stack traces to client
   - ✅ No database structure leaked

7. **Unauthorized Access**
   - ✅ API key required
   - ✅ Intent whitelist
   - ✅ Input validation

8. **Timing Attacks**
   - ✅ Constant-time key comparison
   - ✅ No early returns in auth

## Security Checklist

### Deployment Checklist

- [ ] API Gateway requires API key
- [ ] Lambda validates API key
- [ ] Database credentials in env vars (not code)
- [ ] RDS in private subnet
- [ ] Security groups configured correctly
- [ ] Lambda in VPC
- [ ] HTTPS only enforced
- [ ] Rate limiting configured
- [ ] CloudWatch Logs enabled
- [ ] IAM role follows least privilege
- [ ] Error messages don't leak info
- [ ] Input validation enabled
- [ ] Parameterized queries only

### Runtime Checklist

- [ ] Monitor CloudWatch Logs for errors
- [ ] Review API Gateway metrics
- [ ] Check for 401/403 spikes (auth issues)
- [ ] Monitor 429 responses (rate limiting)
- [ ] Review database connection errors
- [ ] Check Lambda timeout errors
- [ ] Monitor VPC ENI creation delays

### Maintenance Checklist

- [ ] Rotate API keys every 90 days
- [ ] Review CloudWatch Logs weekly
- [ ] Update Lambda runtime regularly
- [ ] Review IAM permissions quarterly
- [ ] Audit security groups annually
- [ ] Test disaster recovery procedures
- [ ] Review cost optimization opportunities

## Security Best Practices

1. **Never log sensitive data**
   - Passwords, API keys, tokens
   - Full request bodies
   - Database credentials

2. **Always validate input**
   - Type checking
   - Range validation
   - Format validation

3. **Use parameterized queries**
   - Never string interpolation
   - Always use placeholders
   - Validate parameters before query

4. **Fail securely**
   - Generic error messages
   - Detailed errors in logs only
   - No information leakage

5. **Monitor everything**
   - CloudWatch Logs
   - API Gateway metrics
   - Lambda metrics
   - Database metrics

6. **Rotate credentials**
   - API keys every 90 days
   - Database passwords annually
   - IAM roles as needed

7. **Keep dependencies updated**
   - Lambda runtime
   - Python packages
   - Security patches

8. **Use least privilege**
   - Minimal IAM permissions
   - Minimal security group rules
   - Minimal network access

## Compliance Considerations

### GDPR
- ✅ No personal data logged
- ✅ Request IDs for audit
- ✅ Data retention policies

### SOC 2
- ✅ Access controls (API keys)
- ✅ Audit logging (CloudWatch)
- ✅ Encryption in transit (HTTPS)
- ✅ Encryption at rest (RDS)

### PCI DSS
- ✅ Network segmentation (VPC)
- ✅ Access controls
- ✅ Logging and monitoring
- ✅ Secure configuration

## Incident Response

### If API Key Compromised

1. **Immediate**:
   - Remove compromised key from `API_KEYS`
   - Deploy updated Lambda
   - Revoke key in API Gateway

2. **Investigation**:
   - Review CloudWatch Logs for abuse
   - Check API Gateway metrics
   - Identify affected requests

3. **Recovery**:
   - Issue new API keys
   - Update all clients
   - Monitor for continued abuse

### If Database Breach Suspected

1. **Immediate**:
   - Rotate database password
   - Review security group rules
   - Check VPC flow logs

2. **Investigation**:
   - Review database access logs
   - Check Lambda execution logs
   - Analyze network traffic

3. **Recovery**:
   - Update credentials
   - Tighten security groups
   - Enable additional monitoring

## Security Testing

### Penetration Testing

Test scenarios:
1. SQL injection attempts
2. API key brute force
3. Rate limit bypass attempts
4. Invalid intent execution
5. Oversized payloads
6. Malformed JSON

### Security Scanning

Tools:
- AWS Security Hub
- AWS Config
- CloudWatch Logs Insights
- Third-party scanners

### Code Review

Checklist:
- ✅ No secrets in code
- ✅ Parameterized queries only
- ✅ Input validation present
- ✅ Error handling secure
- ✅ Logging doesn't leak data

## Future Enhancements

1. **AWS Secrets Manager**: Upgrade from env vars
2. **AWS WAF**: Additional API protection
3. **Request Signing**: HMAC request signatures
4. **IP Whitelisting**: Restrict by source IP
5. **MFA**: Multi-factor authentication
6. **Audit Logging**: Dedicated audit trail
7. **Encryption**: End-to-end encryption
8. **Token-Based Auth**: JWT tokens
9. **OAuth 2.0**: Standard authentication
10. **API Versioning**: `/v1`, `/v2` support