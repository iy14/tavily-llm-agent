"""
Telemetry module for AI Newsletter Agent

Provides cache-focused metadata collection for Tavily data engineering insights.
"""

from .metadata_emitter import TelemetryEmitter, EventBuilder

__all__ = ['TelemetryEmitter', 'EventBuilder']
