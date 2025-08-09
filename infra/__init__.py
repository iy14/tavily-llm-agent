"""
Infrastructure module for AI Newsletter Agent

Provides configuration management, AWS service wrappers, and infrastructure utilities.
"""

from .config import get_app_config, validate_config
from .aws_client import get_aws_client_manager
from .firehose_client import get_firehose_client
from .s3_client import get_s3_client
from .secrets_client import get_secrets_client

__all__ = [
    'get_app_config', 
    'validate_config',
    'get_aws_client_manager',
    'get_firehose_client',
    'get_s3_client', 
    'get_secrets_client'
]
