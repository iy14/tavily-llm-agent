"""
AWS Kinesis Data Firehose client wrapper

Provides Firehose-specific operations with error handling and batch support.
"""

import logging
import json
from typing import Dict, List, Optional, Any

try:
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from .aws_client import get_aws_client_manager

logger = logging.getLogger(__name__)


class FirehoseClient:
    """AWS Kinesis Data Firehose client wrapper"""
    
    def __init__(self):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for Firehose operations")
        
        self.client_manager = get_aws_client_manager()
        self._client = None
    
    @property
    def client(self):
        """Get Firehose client with lazy initialization"""
        if self._client is None:
            self._client = self.client_manager.get_client('firehose')
        return self._client
    
    def put_record(self, stream_name: str, data: str) -> bool:
        """
        Put a single record to Firehose delivery stream
        
        Args:
            stream_name: Name of the Firehose delivery stream
            data: Data to send (will be encoded as bytes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.client.put_record(
                DeliveryStreamName=stream_name,
                Record={'Data': data.encode('utf-8') if isinstance(data, str) else data}
            )
            
            success = response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200
            if success:
                logger.debug(f"Successfully sent record to Firehose stream: {stream_name}")
            else:
                logger.warning(f"Unexpected response from Firehose: {response}")
            
            return success
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to put record to Firehose {stream_name}: {e}")
            return False
    
    def put_record_batch(self, stream_name: str, records: List[str]) -> Dict[str, Any]:
        """
        Put multiple records to Firehose delivery stream in batch
        
        Args:
            stream_name: Name of the Firehose delivery stream
            records: List of data strings to send
            
        Returns:
            dict: Result with success count, failed count, and failed records
        """
        if not records:
            return {'success_count': 0, 'failed_count': 0, 'failed_records': []}
        
        try:
            # Prepare records for batch (max 500 per batch)
            batch_records = []
            for record in records[:500]:  # Firehose limit
                batch_records.append({
                    'Data': record.encode('utf-8') if isinstance(record, str) else record
                })
            
            response = self.client.put_record_batch(
                DeliveryStreamName=stream_name,
                Records=batch_records
            )
            
            failed_count = response.get('FailedPutCount', 0)
            success_count = len(batch_records) - failed_count
            
            result = {
                'success_count': success_count,
                'failed_count': failed_count,
                'failed_records': []
            }
            
            # Extract failed records if any
            if failed_count > 0:
                request_responses = response.get('RequestResponses', [])
                for i, resp in enumerate(request_responses):
                    if 'ErrorCode' in resp:
                        result['failed_records'].append({
                            'index': i,
                            'error_code': resp.get('ErrorCode'),
                            'error_message': resp.get('ErrorMessage'),
                            'record': records[i] if i < len(records) else None
                        })
                
                logger.warning(f"Firehose batch had {failed_count} failed records out of {len(batch_records)}")
            else:
                logger.debug(f"Successfully sent {success_count} records to Firehose stream: {stream_name}")
            
            return result
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to put record batch to Firehose {stream_name}: {e}")
            return {
                'success_count': 0,
                'failed_count': len(records),
                'failed_records': [{'error': str(e), 'record': record} for record in records]
            }
    
    def describe_delivery_stream(self, stream_name: str) -> Dict[str, Any]:
        """
        Get delivery stream description and status
        
        Args:
            stream_name: Name of the Firehose delivery stream
            
        Returns:
            dict: Stream description or empty dict if failed
        """
        try:
            response = self.client.describe_delivery_stream(
                DeliveryStreamName=stream_name
            )
            
            return response.get('DeliveryStreamDescription', {})
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to describe Firehose stream {stream_name}: {e}")
            return {}
    
    def get_stream_status(self, stream_name: str) -> str:
        """
        Get the status of a Firehose delivery stream
        
        Args:
            stream_name: Name of the Firehose delivery stream
            
        Returns:
            str: Stream status ('ACTIVE', 'CREATING', 'DELETING', 'UNKNOWN')
        """
        description = self.describe_delivery_stream(stream_name)
        status = description.get('DeliveryStreamStatus', 'UNKNOWN')
        
        logger.debug(f"Firehose stream {stream_name} status: {status}")
        return status
    
    def is_stream_active(self, stream_name: str) -> bool:
        """
        Check if delivery stream is active and ready for records
        
        Args:
            stream_name: Name of the Firehose delivery stream
            
        Returns:
            bool: True if stream is active, False otherwise
        """
        return self.get_stream_status(stream_name) == 'ACTIVE'


# Global Firehose client instance
_firehose_client = None

def get_firehose_client() -> FirehoseClient:
    """Get the global Firehose client instance"""
    global _firehose_client
    
    if _firehose_client is None:
        _firehose_client = FirehoseClient()
    
    return _firehose_client
