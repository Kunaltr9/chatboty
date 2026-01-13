"""
Secure Configuration Management
===============================
Loads configuration from environment variables with fail-fast validation.
No secrets in code - all sensitive values come from Lambda environment variables.

Security Notes:
- Fail fast if required secrets are missing
- Never log sensitive values
- Support AWS Secrets Manager as optional upgrade path
"""

import os
from typing import List, Optional


class Config:
    """Centralized configuration with security-first defaults"""
    
    # Database Configuration (from Lambda environment variables)
    DB_HOST: str = os.getenv('DB_HOST', '')
    DB_PORT: int = int(os.getenv('DB_PORT', '3306'))
    DB_NAME: str = os.getenv('DB_NAME', '')
    DB_USER: str = os.getenv('DB_USER', '')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # API Key Configuration (comma-separated list for key rotation)
    # Format: "key1,key2,key3" - supports multiple valid keys
    API_KEYS_STR: str = os.getenv('API_KEYS', '')
    
    # Request Limits
    MAX_PAYLOAD_SIZE: int = int(os.getenv('MAX_PAYLOAD_SIZE', '1048576'))  # 1MB default
    MAX_QUERY_LIMIT: int = int(os.getenv('MAX_QUERY_LIMIT', '1000'))  # Max rows per query
    
    # Database Connection Pool Settings
    DB_CONNECTION_TIMEOUT: int = int(os.getenv('DB_CONNECTION_TIMEOUT', '5'))  # seconds
    DB_QUERY_TIMEOUT: int = int(os.getenv('DB_QUERY_TIMEOUT', '30'))  # seconds
    DB_MAX_RETRIES: int = int(os.getenv('DB_MAX_RETRIES', '3'))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_api_keys(cls) -> List[str]:
        """
        Parse API keys from environment variable.
        Supports multiple keys for rotation (comma-separated).
        
        Returns:
            List of valid API keys (non-empty strings)
        """
        if not cls.API_KEYS_STR:
            return []
        
        # Split by comma and strip whitespace
        keys = [key.strip() for key in cls.API_KEYS_STR.split(',')]
        # Filter out empty strings
        return [key for key in keys if key]
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.
        Raises ValueError if any required config is missing.
        
        This is called at Lambda cold start to fail fast.
        """
        missing = []
        
        # Database configuration
        if not cls.DB_HOST:
            missing.append('DB_HOST')
        if not cls.DB_NAME:
            missing.append('DB_NAME')
        if not cls.DB_USER:
            missing.append('DB_USER')
        if not cls.DB_PASSWORD:
            missing.append('DB_PASSWORD')
        
        # API keys
        api_keys = cls.get_api_keys()
        if not api_keys:
            missing.append('API_KEYS')
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Set these in Lambda configuration or use AWS Secrets Manager."
            )
    
    @classmethod
    def get_db_config(cls) -> dict:
        """
        Get database configuration as a dictionary.
        Does NOT include password in the dict (security).
        
        Returns:
            Dictionary with DB config (excluding password)
        """
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'database': cls.DB_NAME,
            'user': cls.DB_USER,
            # Password is accessed separately via cls.DB_PASSWORD
        }


# Optional: AWS Secrets Manager integration
# Uncomment and implement if you want to use Secrets Manager instead of env vars
"""
import boto3
import json
from botocore.exceptions import ClientError

def load_secrets_from_manager(secret_name: str, region: str = 'us-east-1') -> dict:
    '''
    Load secrets from AWS Secrets Manager.
    Use this as an upgrade path for production deployments.
    
    Example secret JSON:
    {
        "DB_HOST": "rds-instance.region.rds.amazonaws.com",
        "DB_NAME": "chatbot_db",
        "DB_USER": "app_user",
        "DB_PASSWORD": "secure_password",
        "API_KEYS": "key1,key2,key3"
    }
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region: AWS region
        
    Returns:
        Dictionary of secrets
        
    Raises:
        ClientError: If secret cannot be retrieved
    '''
    client = boto3.client('secretsmanager', region_name=region)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return secret
    except ClientError as e:
        raise ValueError(f"Failed to load secrets from Secrets Manager: {e}")
"""