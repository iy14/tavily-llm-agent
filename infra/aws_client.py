"""
Generic AWS client wrapper for AI Newsletter Agent

Provides centralized boto3 client management with configuration, error handling,
and retry logic for all AWS services.
"""

import logging
from typing import Dict, Any, Optional
from functools import lru_cache

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError
    from botocore.config import Config
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logging.warning("boto3 not available - AWS services will not be functional")

from .config import get_app_config

logger = logging.getLogger(__name__)


class AWSClientManager:
    """Generic AWS client manager with consistent configuration and error handling"""
    
    def __init__(self, region_name: Optional[str] = None):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for AWS services")
        
        self.config = get_app_config()
        self.region_name = region_name or self.config['aws_region']
        
        # Boto3 configuration with retries
        self.boto_config = Config(
            region_name=self.region_name,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            }
        )
        
        # Cache for service clients
        self._clients: Dict[str, Any] = {}
        
        logger.info(f"Initialized AWS client manager for region: {self.region_name}")
    
    @lru_cache(maxsize=10)
    def get_client(self, service_name: str):
        """
        Get AWS service client with lazy initialization and caching
        
        Args:
            service_name: AWS service name (e.g., 'firehose', 's3', 'secretsmanager')
            
        Returns:
            Boto3 client for the specified service
        """
        if service_name not in self._clients:
            try:
                self._clients[service_name] = boto3.client(
                    service_name, 
                    config=self.boto_config
                )
                logger.debug(f"Initialized {service_name} client")
            except Exception as e:
                logger.error(f"Failed to initialize {service_name} client: {e}")
                raise
        
        return self._clients[service_name]
    
    def check_credentials(self) -> bool:
        """
        Check if AWS credentials are available and valid
        
        Returns:
            bool: True if credentials are available, False otherwise
        """
        try:
            # Try to get caller identity to validate credentials
            sts_client = self.get_client('sts')
            sts_client.get_caller_identity()
            logger.info("AWS credentials are valid")
            return True
            
        except (ClientError, BotoCoreError, NoCredentialsError) as e:
            logger.warning(f"AWS credentials validation failed: {e}")
            return False
    
    def check_service_access(self, service_name: str, test_operation: str = None) -> bool:
        """
        Check if a specific AWS service is accessible
        
        Args:
            service_name: AWS service name
            test_operation: Optional test operation to verify access
            
        Returns:
            bool: True if service is accessible, False otherwise
        """
        try:
            client = self.get_client(service_name)
            
            # Perform a basic test operation if specified
            if test_operation and hasattr(client, test_operation):
                # For most services, listing operations are good tests
                getattr(client, test_operation)()
            
            logger.debug(f"AWS {service_name} service is accessible")
            return True
            
        except Exception as e:
            logger.warning(f"AWS {service_name} service access check failed: {e}")
            return False


# Global AWS client manager instance
_aws_client_manager = None

def get_aws_client_manager() -> AWSClientManager:
    """Get the global AWS client manager instance"""
    global _aws_client_manager
    
    if _aws_client_manager is None:
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for AWS services")
        
        _aws_client_manager = AWSClientManager()
    
    return _aws_client_manager
