"""
Metadata emitter for AI Newsletter Agent telemetry

Provides event builders and AWS Firehose integration for cache-focused telemetry.
"""

import os
import json
import uuid
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

try:
    from infra.firehose_client import get_firehose_client
    from infra.config import get_app_config
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logging.warning("AWS services not available - telemetry will use local fallback only")


logger = logging.getLogger(__name__)


class EventBuilder:
    """Builds telemetry events according to the defined schema"""
    
    def __init__(self, app_version: str = "0.1.0", env: str = "dev", region: str = "us-east-1"):
        self.app_version = app_version
        self.env = env
        self.region = region
    
    def _base_event(self, event_type: str, session_id: str) -> Dict[str, Any]:
        """Create base event envelope with common fields"""
        return {
            "event_id": str(uuid.uuid4()),
            "event_ts": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "session_id": session_id,
            "app_version": self.app_version,
            "env": self.env,
            "region": self.region
        }
    
    def query_fingerprint(self, query: str) -> str:
        """Generate stable hash for cache key generation"""
        # Normalize and create stable hash
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def semantic_fingerprint(self, query: str) -> str:
        """Generate coarse cluster ID for near-duplicate detection"""
        # Simple implementation - can be enhanced with semantic similarity
        words = set(query.lower().split())
        # Remove common words for better clustering
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        meaningful_words = words - stop_words
        sorted_words = sorted(meaningful_words)
        cluster_text = ' '.join(sorted_words[:5])  # Use top 5 meaningful words
        return hashlib.md5(cluster_text.encode('utf-8')).hexdigest()[:8]
    
    def classify_intent(self, query: str, profession: str = "") -> str:
        """Classify query intent based on content"""
        query_lower = query.lower()
        
        # Simple keyword-based classification
        if any(word in query_lower for word in ['news', 'recent', 'latest', 'today', 'this week', 'current']):
            return "news"
        elif any(word in query_lower for word in ['tool', 'software', 'platform', 'app', 'service', 'resource']):
            return "tools"
        else:
            return "general"
    
    def get_query_length_bucket(self, query: str) -> str:
        """Categorize query by length"""
        length = len(query)
        if length < 20:
            return "short"
        elif length <= 100:
            return "medium"
        else:
            return "long"
    
    def query_processed(self, session_id: str, query: str, profession: str, 
                       time_range: str, normalization_applied: bool = False) -> Dict[str, Any]:
        """Build query_processed event"""
        normalized_query = query.strip()
        event = self._base_event("query_processed", session_id)
        
        event.update({
            "normalized_query": normalized_query,
            "query_fingerprint": self.query_fingerprint(normalized_query),
            "semantic_fingerprint": self.semantic_fingerprint(normalized_query),
            "profession": profession,
            "time_range": time_range,
            "intent_group": self.classify_intent(normalized_query, profession),
            "query_length_bucket": self.get_query_length_bucket(normalized_query),
            "normalization_applied": normalization_applied
        })
        
        return event
    
    def cache_operation(self, session_id: str, query_fingerprint: str, cache_hit: bool,
                       cache_item_age_s: Optional[int] = None, ttl_assigned_s: Optional[int] = None,
                       ttl_remaining_s: Optional[int] = None, miss_reason: Optional[str] = None) -> Dict[str, Any]:
        """Build cache_operation event"""
        event = self._base_event("cache_operation", session_id)
        
        event.update({
            "query_fingerprint": query_fingerprint,
            "cache_hit": cache_hit,
            "cache_key_version": "v1"
        })
        
        # Add optional fields based on hit/miss
        if cache_hit and cache_item_age_s is not None:
            event["cache_item_age_s"] = cache_item_age_s
        if cache_hit and ttl_remaining_s is not None:
            event["ttl_remaining_s"] = ttl_remaining_s
        if not cache_hit and ttl_assigned_s is not None:
            event["ttl_assigned_s"] = ttl_assigned_s
        if not cache_hit and miss_reason:
            event["miss_reason"] = miss_reason
            
        return event
    
    def search_completed(self, session_id: str, query_fingerprint: str, search_latency_ms: int,
                        result_count_filtered: int, avg_relevance_score: float,
                        domain_diversity: float, top_domains: Optional[List[str]] = None,
                        coverage_flag: Optional[str] = None) -> Dict[str, Any]:
        """Build search_completed event"""
        event = self._base_event("search_completed", session_id)
        
        event.update({
            "query_fingerprint": query_fingerprint,
            "search_latency_ms": search_latency_ms,
            "result_count_filtered": result_count_filtered,
            "avg_relevance_score": round(avg_relevance_score, 4),
            "domain_diversity": round(domain_diversity, 4)
        })
        
        if top_domains:
            event["top_domains"] = top_domains[:5]  # Limit to top 5
        if coverage_flag:
            event["coverage_flag"] = coverage_flag
            
        return event
    
    def summary_generated(self, session_id: str, query_fingerprint: str, llm_latency_ms: int,
                         total_tokens: int, model: str, cited_results_count: int,
                         original_result_count: int, num_points_in_summary: int,
                         prompt_tokens: Optional[int] = None, completion_tokens: Optional[int] = None,
                         cost_estimate_usd: Optional[float] = None) -> Dict[str, Any]:
        """Build summary_generated event"""
        event = self._base_event("summary_generated", session_id)
        
        consumption_rate = cited_results_count / max(original_result_count, 1)
        
        event.update({
            "query_fingerprint": query_fingerprint,
            "llm_latency_ms": llm_latency_ms,
            "total_tokens": total_tokens,
            "model": model,
            "cited_results_count": cited_results_count,
            "consumption_rate": round(consumption_rate, 4),
            "num_points_in_summary": num_points_in_summary
        })
        
        if prompt_tokens is not None:
            event["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            event["completion_tokens"] = completion_tokens
        if cost_estimate_usd is not None:
            event["cost_estimate_usd"] = round(cost_estimate_usd, 4)
            
        return event
    
    def error_occurred(self, session_id: str, error_type: str, error_stage: str,
                      retry_count: int = 0, recovered: bool = False,
                      error_message: Optional[str] = None, query_fingerprint: Optional[str] = None) -> Dict[str, Any]:
        """Build error_occurred event"""
        event = self._base_event("error_occurred", session_id)
        
        event.update({
            "error_type": error_type,
            "error_stage": error_stage,
            "retry_count": retry_count,
            "recovered": recovered
        })
        
        if error_message:
            # Sanitize error message - remove potential PII/secrets
            sanitized = error_message.replace('\n', ' ')[:200]  # Limit length
            event["error_message_sanitized"] = sanitized
        if query_fingerprint:
            event["query_fingerprint"] = query_fingerprint
            
        return event
    
    def session_completed(self, session_id: str, end_to_end_latency_ms: int,
                         events_emitted: int, final_status: str,
                         followups_in_session: int = 0) -> Dict[str, Any]:
        """Build session_completed event"""
        event = self._base_event("session_completed", session_id)
        
        event.update({
            "end_to_end_latency_ms": end_to_end_latency_ms,
            "events_emitted": events_emitted,
            "final_status": final_status,
            "followups_in_session": followups_in_session
        })
        
        return event


class TelemetryEmitter:
    """Handles event emission to AWS Firehose or local fallback"""
    
    def __init__(self, stream_name: str = "", enabled: bool = True, local_fallback: bool = False):
        self.config = get_app_config() if AWS_AVAILABLE else {}
        self.stream_name = stream_name or self.config.get('firehose_stream_name', '')
        self.enabled = enabled and self.config.get('telemetry_enabled', False)
        self.local_fallback = local_fallback or not AWS_AVAILABLE
        
        self.event_builder = EventBuilder(
            app_version=self.config.get('app_version', '0.1.0'),
            env=self.config.get('app_env', 'dev'),
            region=self.config.get('aws_region', 'us-east-1')
        )
        
        # Initialize Firehose client if available and not in fallback mode
        self.firehose_client = None
        if not self.local_fallback and AWS_AVAILABLE and self.enabled:
            try:
                self.firehose_client = get_firehose_client()
                logger.info(f"Initialized Firehose client for stream: {self.stream_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize Firehose client: {e}, using local fallback")
                self.local_fallback = True
        
        # Setup local fallback directory
        if self.local_fallback:
            self.local_dir = Path("./.telemetry")
            self.local_dir.mkdir(exist_ok=True)
            logger.info(f"Using local telemetry fallback: {self.local_dir}")
    
    def emit_event(self, event: Dict[str, Any]) -> bool:
        """Emit a single event to Firehose or local fallback"""
        if not self.enabled:
            return True
            
        try:
            event_json = json.dumps(event, separators=(',', ':'))
            
            if self.local_fallback:
                return self._emit_local(event_json)
            else:
                return self._emit_firehose(event_json)
                
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
            return False
    
    def emit_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Emit multiple events in a batch"""
        if not self.enabled or not events:
            return True
            
        try:
            if self.local_fallback:
                return all(self.emit_event(event) for event in events)
            else:
                return self._emit_firehose_batch(events)
                
        except Exception as e:
            logger.error(f"Failed to emit event batch: {e}")
            return False
    
    def _emit_local(self, event_json: str) -> bool:
        """Write event to local NDJSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = self.local_dir / f"telemetry_{timestamp}.ndjson"
            
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(event_json + '\n')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write local telemetry: {e}")
            return False
    
    def _emit_firehose(self, event_json: str) -> bool:
        """Send single event to Firehose"""
        if not self.firehose_client:
            return False
            
        return self.firehose_client.put_record(self.stream_name, event_json + '\n')
    
    def _emit_firehose_batch(self, events: List[Dict[str, Any]]) -> bool:
        """Send batch of events to Firehose"""
        if not self.firehose_client:
            return False
            
        try:
            # Convert events to JSON strings
            event_strings = []
            for event in events:
                event_json = json.dumps(event, separators=(',', ':'))
                event_strings.append(event_json + '\n')
            
            result = self.firehose_client.put_record_batch(self.stream_name, event_strings)
            
            # Log results
            if result['failed_count'] > 0:
                logger.warning(f"Firehose batch had {result['failed_count']} failed records out of {len(events)}")
                return False
            
            logger.debug(f"Successfully sent {result['success_count']} events to Firehose")
            return True
            
        except Exception as e:
            logger.error(f"Failed to emit event batch: {e}")
            return False
    
    # Convenience methods for common events
    def query_processed(self, session_id: str, query: str, profession: str, 
                       time_range: str, **kwargs) -> bool:
        """Emit query_processed event"""
        event = self.event_builder.query_processed(session_id, query, profession, time_range, **kwargs)
        return self.emit_event(event)
    
    def cache_operation(self, session_id: str, query_fingerprint: str, cache_hit: bool, **kwargs) -> bool:
        """Emit cache_operation event"""
        event = self.event_builder.cache_operation(session_id, query_fingerprint, cache_hit, **kwargs)
        return self.emit_event(event)
    
    def search_completed(self, session_id: str, query_fingerprint: str, search_latency_ms: int,
                        result_count_filtered: int, avg_relevance_score: float, 
                        domain_diversity: float, **kwargs) -> bool:
        """Emit search_completed event"""
        event = self.event_builder.search_completed(
            session_id, query_fingerprint, search_latency_ms, 
            result_count_filtered, avg_relevance_score, domain_diversity, **kwargs
        )
        return self.emit_event(event)
    
    def summary_generated(self, session_id: str, query_fingerprint: str, llm_latency_ms: int,
                         total_tokens: int, model: str, cited_results_count: int,
                         original_result_count: int, num_points_in_summary: int, **kwargs) -> bool:
        """Emit summary_generated event"""
        event = self.event_builder.summary_generated(
            session_id, query_fingerprint, llm_latency_ms, total_tokens, model,
            cited_results_count, original_result_count, num_points_in_summary, **kwargs
        )
        return self.emit_event(event)
    
    def error_occurred(self, session_id: str, error_type: str, error_stage: str, **kwargs) -> bool:
        """Emit error_occurred event"""
        event = self.event_builder.error_occurred(session_id, error_type, error_stage, **kwargs)
        return self.emit_event(event)
    
    def session_completed(self, session_id: str, end_to_end_latency_ms: int,
                         events_emitted: int, final_status: str, **kwargs) -> bool:
        """Emit session_completed event"""
        event = self.event_builder.session_completed(
            session_id, end_to_end_latency_ms, events_emitted, final_status, **kwargs
        )
        return self.emit_event(event)


# Global telemetry instance - initialized from environment
_telemetry_instance = None

def get_telemetry() -> TelemetryEmitter:
    """Get the global telemetry instance"""
    global _telemetry_instance
    
    if _telemetry_instance is None:
        if AWS_AVAILABLE:
            config = get_app_config()
            enabled = config.get('telemetry_enabled', False)
            stream_name = config.get('firehose_stream_name', '')
        else:
            enabled = False
            stream_name = ''
        
        _telemetry_instance = TelemetryEmitter(
            stream_name=stream_name,
            enabled=enabled,
            local_fallback=not stream_name  # Use local fallback if no stream configured
        )
    
    return _telemetry_instance
