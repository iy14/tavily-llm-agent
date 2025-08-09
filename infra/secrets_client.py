"""
AWS Secrets Manager client wrapper

Provides secrets management with caching and fallback to environment variables.
"""

import logging
import json
from typing import Dict, Any, Optional
from functools import lru_cache

try:
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .aws_client import get_aws_client_manager
from .config import get_app_config

logger = logging.getLogger(__name__)


class SecretsClient:
    """AWS Secrets Manager client wrapper with caching and fallback"""
    
    def __init__(self):
        if not BOTO3_AVAILABLE:
            logger.warning("boto3 not available - will use environment variables only")
            self.client_manager = None
            self._client = None
        else:
            self.client_manager = get_aws_client_manager()
            self._client = None
        
        self.config = get_app_config()
        self._secrets_cache: Dict[str, Any] = {}
    
    @property
    def client(self):
        """Get Secrets Manager client with lazy initialization"""
        if self._client is None and self.client_manager:
            self._client = self.client_manager.get_client('secretsmanager')
        return self._client
    
    @lru_cache(maxsize=5)
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager with caching
        Falls back to environment variables if AWS is not available
        
        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            
        Returns:
            dict: Secret key-value pairs
        """
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        # Try AWS Secrets Manager first
        if self.client:
            try:
                response = self.client.get_secret_value(SecretId=secret_name)
                secret_data = json.loads(response['SecretString'])
                self._secrets_cache[secret_name] = secret_data
                logger.info(f"Retrieved secret from AWS Secrets Manager: {secret_name}")
                return secret_data
                
            except (ClientError, BotoCoreError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to retrieve secret from AWS: {e}, falling back to env vars")
        
        # Fallback to environment variables
        env_secrets = {
            'OPENAI_API_KEY': self.config.get('openai_api_key'),
            'TAVILY_API_KEY': self.config.get('tavily_api_key'),
            'REDIS_URL': self.config.get('redis_url')
        }
        
        # Filter out None values
        env_secrets = {k: v for k, v in env_secrets.items() if v is not None}
        
        if env_secrets:
            logger.info("Using environment variables for secrets")
            self._secrets_cache[secret_name] = env_secrets
            return env_secrets
        else:
            logger.error("No secrets found in AWS Secrets Manager or environment variables")
            return {}
    
    def get_secret_value(self, secret_name: str, key: str, default: Any = None) -> Any:
        """
        Get a specific value from a secret
        
        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            key: Key within the secret
            default: Default value if key not found
            
        Returns:
            Secret value or default
        """
        secrets = self.get_secret(secret_name)
        return secrets.get(key, default)
    
    def get_app_secrets(self) -> Dict[str, Any]:
        """
        Get all application secrets using configured secret name
        
        Returns:
            dict: All application secrets
        """
        secret_name = self.config.get('aws_secret_name', 'tavily-ai-agent-secrets-dev')
        return self.get_secret(secret_name)
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from secrets or environment"""
        secrets = self.get_app_secrets()
        return secrets.get('OPENAI_API_KEY')
    
    def get_tavily_api_key(self) -> Optional[str]:
        """Get Tavily API key from secrets or environment"""
        secrets = self.get_app_secrets()
        return secrets.get('TAVILY_API_KEY')
    
    def get_redis_url(self) -> Optional[str]:
        """Get Redis URL from secrets or environment"""
        secrets = self.get_app_secrets()
        return secrets.get('REDIS_URL')
    
    def clear_cache(self):
        """Clear the secrets cache (useful for testing or credential rotation)"""
        self._secrets_cache.clear()
        # Clear the lru_cache as well
        self.get_secret.cache_clear()
        logger.info("Cleared secrets cache")


# Global Secrets client instance
_secrets_client = None

def get_secrets_client() -> SecretsClient:
    """Get the global Secrets client instance"""
    global _secrets_client
    
    if _secrets_client is None:
        _secrets_client = SecretsClient()
    
    return _secrets_client
