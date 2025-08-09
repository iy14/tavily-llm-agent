"""
AWS S3 client wrapper

Provides S3-specific operations for monitoring and data access.
"""

import logging
from typing import Dict, List, Optional, Any

try:
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .aws_client import get_aws_client_manager

logger = logging.getLogger(__name__)


class S3Client:
    """AWS S3 client wrapper for monitoring and data operations"""
    
    def __init__(self):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3 operations")
        
        self.client_manager = get_aws_client_manager()
        self._client = None
    
    @property
    def client(self):
        """Get S3 client with lazy initialization"""
        if self._client is None:
            self._client = self.client_manager.get_client('s3')
        return self._client
    
    def list_objects(self, bucket_name: str, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List objects in S3 bucket with optional prefix
        
        Args:
            bucket_name: S3 bucket name
            prefix: Object key prefix filter
            max_keys: Maximum number of objects to return
            
        Returns:
            list: List of S3 object metadata dicts
        """
        try:
            kwargs = {
                'Bucket': bucket_name,
                'MaxKeys': max_keys
            }
            if prefix:
                kwargs['Prefix'] = prefix
            
            response = self.client.list_objects_v2(**kwargs)
            objects = response.get('Contents', [])
            
            logger.debug(f"Listed {len(objects)} objects in {bucket_name}/{prefix}")
            return objects
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to list S3 objects in {bucket_name}/{prefix}: {e}")
            return []
    
    def get_object(self, bucket_name: str, key: str) -> Optional[str]:
        """
        Get S3 object content as string
        
        Args:
            bucket_name: S3 bucket name
            key: S3 object key
            
        Returns:
            str: Object content or None if failed
        """
        try:
            response = self.client.get_object(Bucket=bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            logger.debug(f"Retrieved object {bucket_name}/{key} ({len(content)} chars)")
            return content
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get S3 object {bucket_name}/{key}: {e}")
            return None
    
    def get_object_metadata(self, bucket_name: str, key: str) -> Dict[str, Any]:
        """
        Get S3 object metadata without downloading content
        
        Args:
            bucket_name: S3 bucket name
            key: S3 object key
            
        Returns:
            dict: Object metadata or empty dict if failed
        """
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=key)
            
            metadata = {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'content_type': response.get('ContentType', ''),
                'metadata': response.get('Metadata', {})
            }
            
            logger.debug(f"Retrieved metadata for {bucket_name}/{key}")
            return metadata
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get metadata for {bucket_name}/{key}: {e}")
            return {}
    
    def check_bucket_access(self, bucket_name: str) -> bool:
        """
        Check if S3 bucket is accessible
        
        Args:
            bucket_name: S3 bucket name
            
        Returns:
            bool: True if accessible, False otherwise
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
            logger.debug(f"S3 bucket {bucket_name} is accessible")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to access S3 bucket {bucket_name}: {e}")
            return False
    
    def get_bucket_location(self, bucket_name: str) -> Optional[str]:
        """
        Get S3 bucket region/location
        
        Args:
            bucket_name: S3 bucket name
            
        Returns:
            str: Bucket region or None if failed
        """
        try:
            response = self.client.get_bucket_location(Bucket=bucket_name)
            location = response.get('LocationConstraint') or 'us-east-1'  # Default region
            
            logger.debug(f"S3 bucket {bucket_name} is in region: {location}")
            return location
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get location for S3 bucket {bucket_name}: {e}")
            return None
    
    def count_objects_by_prefix(self, bucket_name: str, prefix: str = "") -> int:
        """
        Count objects in bucket with given prefix (useful for monitoring)
        
        Args:
            bucket_name: S3 bucket name
            prefix: Object key prefix filter
            
        Returns:
            int: Number of objects found
        """
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            count = 0
            for page in page_iterator:
                count += len(page.get('Contents', []))
            
            logger.debug(f"Counted {count} objects in {bucket_name}/{prefix}")
            return count
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to count objects in {bucket_name}/{prefix}: {e}")
            return 0
    
    def get_total_size_by_prefix(self, bucket_name: str, prefix: str = "") -> int:
        """
        Get total size of objects with given prefix (useful for monitoring)
        
        Args:
            bucket_name: S3 bucket name
            prefix: Object key prefix filter
            
        Returns:
            int: Total size in bytes
        """
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            total_size = 0
            for page in page_iterator:
                for obj in page.get('Contents', []):
                    total_size += obj.get('Size', 0)
            
            logger.debug(f"Total size for {bucket_name}/{prefix}: {total_size} bytes")
            return total_size
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to calculate total size for {bucket_name}/{prefix}: {e}")
            return 0


# Global S3 client instance
_s3_client = None

def get_s3_client() -> S3Client:
    """Get the global S3 client instance"""
    global _s3_client
    
    if _s3_client is None:
        _s3_client = S3Client()
    
    return _s3_client
