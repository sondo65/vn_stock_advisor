"""
Data Integration Module - Phase 3

This module provides real-time data integration capabilities
for the VN Stock Advisor system.
"""

from .realtime_data_collector import RealtimeDataCollector
from .data_validator import DataValidator
from .cache_manager import CacheManager
from .multi_source_aggregator import MultiSourceAggregator
from .macro_cache_manager import MacroCacheManager, macro_cache

__all__ = [
    'RealtimeDataCollector',
    'DataValidator', 
    'CacheManager',
    'MultiSourceAggregator',
    'MacroCacheManager',
    'macro_cache'
]
