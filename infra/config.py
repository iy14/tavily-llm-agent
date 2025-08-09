"""
Configuration management for AI Newsletter Agent

Simple configuration management with AWS Secrets Manager integration.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


def get_app_config() -> Dict[str, Any]:
    """Get application configuration with all required values"""
    
    # Core app configuration from environment
    app_config = {
        'app_env': os.getenv('APP_ENV', 'dev'),
        'app_version': os.getenv('APP_VERSION', '0.1.0'),
        'aws_region': os.getenv('AWS_REGION', 'us-east-1'),
        'aws_secret_name': os.getenv('AWS_SECRET_NAME', 'tavily-ai-agent-secrets-dev'),
        
        # Telemetry configuration
        'telemetry_enabled': os.getenv('TELEMETRY_ENABLED', 'false').lower() == 'true',
        'firehose_stream_name': os.getenv('FIREHOSE_STREAM_NAME', ''),
        
        # Local fallback values (for development)
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'tavily_api_key': os.getenv('TAVILY_API_KEY'),
        'redis_url': os.getenv('REDIS_URL'),
    }
    
    return app_config


def validate_config() -> bool:
    """Validate that all required configuration is available"""
    config = get_app_config()
    
    # Check if we have local keys or AWS secrets configured
    has_local_keys = config.get('openai_api_key') and config.get('tavily_api_key')
    has_aws_secrets = config.get('aws_secret_name')
    
    if not has_local_keys and not has_aws_secrets:
        logger.error("Missing required configuration: no local API keys or AWS secret name configured")
        return False
    
    # Validate telemetry config if enabled
    if config['telemetry_enabled'] and not config['firehose_stream_name']:
        logger.warning("Telemetry enabled but no Firehose stream name configured")
    
    logger.info("Configuration validation passed")
    return True
