"""
Multi-Source Data Aggregator - Phase 3

Aggregates financial data from multiple sources with:
- Data source prioritization
- Conflict resolution
- Quality-based weighting
- Real-time synchronization
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from statistics import median, mean
import json

from .realtime_data_collector import RealtimeDataCollector, RealtimeQuote
from .data_validator import DataValidator, ValidationResult, ValidationLevel
from .cache_manager import CacheManager

class DataSourcePriority(Enum):
    """Data source priority levels."""
    CRITICAL = 1    # Official exchange data
    HIGH = 2        # Established financial data providers
    MEDIUM = 3      # Secondary financial websites
    LOW = 4         # Alternative sources

class ConflictResolution(Enum):
    """Methods for resolving data conflicts."""
    PRIORITY_BASED = "priority"          # Use highest priority source
    WEIGHTED_AVERAGE = "weighted_avg"    # Weight by source reliability
    MEDIAN = "median"                    # Use median value
    LATEST = "latest"                    # Use most recent data
    VALIDATION_BASED = "validation"     # Use source with best validation score

@dataclass
class DataSource:
    """Data source configuration."""
    name: str
    priority: DataSourcePriority
    reliability_score: float  # 0.0 to 1.0
    update_frequency: int      # seconds
    enabled: bool = True
    last_update: Optional[datetime] = None
    error_count: int = 0
    success_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0.0

@dataclass
class AggregatedData:
    """Aggregated financial data from multiple sources."""
    symbol: str
    timestamp: datetime
    primary_data: Dict[str, Any]
    source_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    data_quality_score: float = 0.0
    conflicts_detected: List[str] = field(default_factory=list)
    resolution_method: Optional[ConflictResolution] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MultiSourceAggregator:
    """Aggregates financial data from multiple sources."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize multi-source aggregator.
        
        Args:
            cache_manager: Optional cache manager for performance
        """
        self.logger = logging.getLogger(__name__)
        self.cache_manager = cache_manager
        self.validator = DataValidator()
        
        # Data sources configuration
        self.data_sources = {
            'vnstock': DataSource(
                name='vnstock',
                priority=DataSourcePriority.HIGH,
                reliability_score=0.9,
                update_frequency=30
            ),
            'vietstock': DataSource(
                name='vietstock',
                priority=DataSourcePriority.HIGH,
                reliability_score=0.85,
                update_frequency=60
            ),
            'cafef': DataSource(
                name='cafef',
                priority=DataSourcePriority.MEDIUM,
                reliability_score=0.75,
                update_frequency=120
            ),
            'investing': DataSource(
                name='investing',
                priority=DataSourcePriority.MEDIUM,
                reliability_score=0.7,
                update_frequency=300
            )
        }
        
        # Conflict resolution strategies by data type
        self.resolution_strategies = {
            'price': ConflictResolution.WEIGHTED_AVERAGE,
            'volume': ConflictResolution.PRIORITY_BASED,
            'financial_ratios': ConflictResolution.VALIDATION_BASED,
            'news_sentiment': ConflictResolution.WEIGHTED_AVERAGE,
            'technical_indicators': ConflictResolution.MEDIAN
        }
        
        # Data collectors
        self.collectors = {}
        
        # Thresholds for conflict detection
        self.conflict_thresholds = {
            'price': 0.02,      # 2% difference
            'volume': 0.1,      # 10% difference
            'PE': 0.05,         # 5% difference
            'PB': 0.05,         # 5% difference
            'sentiment': 0.3    # 0.3 point difference
        }
    
    async def initialize(self):
        """Initialize data collectors for each source."""
        try:
            for source_name in self.data_sources.keys():
                if self.data_sources[source_name].enabled:
                    collector = RealtimeDataCollector()
                    await collector.__aenter__()
                    self.collectors[source_name] = collector
            
            self.logger.info(f"Initialized {len(self.collectors)} data collectors")
            
        except Exception as e:
            self.logger.error(f"Error initializing collectors: {e}")
    
    async def aggregate_stock_data(self, 
                                 symbol: str, 
                                 data_types: List[str] = None,
                                 use_cache: bool = True) -> Optional[AggregatedData]:
        """
        Aggregate stock data from multiple sources.
        
        Args:
            symbol: Stock symbol
            data_types: Types of data to aggregate ['price', 'ratios', 'sentiment']
            use_cache: Whether to use cached data
            
        Returns:
            AggregatedData object or None if failed
        """
        try:
            if data_types is None:
                data_types = ['price', 'ratios', 'sentiment']
            
            # Check cache first
            cache_key = f"aggregated_{symbol}_{'-'.join(data_types)}"
            if use_cache and self.cache_manager:
                cached_data = await self.cache_manager.get(cache_key)
                if cached_data:
                    return cached_data
            
            # Collect data from all sources
            source_data = {}
            validation_results = {}
            
            for source_name, collector in self.collectors.items():
                if not self.data_sources[source_name].enabled:
                    continue
                
                try:
                    data = await self._collect_from_source(collector, symbol, data_types)
                    if data:
                        source_data[source_name] = data
                        
                        # Validate data quality
                        validation_results[source_name] = self._validate_source_data(data, source_name)
                        
                        # Update source statistics
                        self.data_sources[source_name].success_count += 1
                        self.data_sources[source_name].last_update = datetime.now()
                    
                except Exception as e:
                    self.logger.warning(f"Error collecting from {source_name}: {e}")
                    self.data_sources[source_name].error_count += 1
            
            if not source_data:
                self.logger.warning(f"No data collected for {symbol}")
                return None
            
            # Aggregate and resolve conflicts
            aggregated = await self._aggregate_source_data(
                symbol, source_data, validation_results
            )
            
            # Cache result
            if use_cache and self.cache_manager:
                await self.cache_manager.set(
                    cache_key, 
                    aggregated, 
                    ttl=60,  # 1 minute cache
                    tags=['stock_data', symbol]
                )
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Error aggregating data for {symbol}: {e}")
            return None
    
    async def get_best_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get best available price data using quality-based selection.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Best price data or None
        """
        try:
            aggregated = await self.aggregate_stock_data(symbol, ['price'])
            if aggregated and aggregated.primary_data:
                return {
                    'symbol': symbol,
                    'price': aggregated.primary_data.get('price'),
                    'change': aggregated.primary_data.get('change'),
                    'change_percent': aggregated.primary_data.get('change_percent'),
                    'volume': aggregated.primary_data.get('volume'),
                    'timestamp': aggregated.timestamp,
                    'confidence': aggregated.data_quality_score,
                    'sources_used': list(aggregated.source_data.keys())
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting best price data for {symbol}: {e}")
            return None
    
    async def detect_data_anomalies(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Detect anomalies by comparing data across sources.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of detected anomalies
        """
        try:
            aggregated = await self.aggregate_stock_data(symbol)
            if not aggregated or len(aggregated.source_data) < 2:
                return []
            
            anomalies = []
            
            # Check price anomalies
            prices = []
            for source, data in aggregated.source_data.items():
                if 'price' in data:
                    prices.append((source, data['price']))
            
            if len(prices) > 1:
                price_values = [p[1] for p in prices]
                price_std = np.std(price_values)
                price_mean = np.mean(price_values)
                
                if price_std / price_mean > self.conflict_thresholds['price']:
                    anomalies.append({
                        'type': 'price_inconsistency',
                        'severity': 'high',
                        'message': f"Price variance {price_std/price_mean:.1%} exceeds threshold",
                        'sources': dict(prices),
                        'timestamp': datetime.now()
                    })
            
            # Check volume anomalies
            volumes = []
            for source, data in aggregated.source_data.items():
                if 'volume' in data:
                    volumes.append((source, data['volume']))
            
            if len(volumes) > 1:
                volume_values = [v[1] for v in volumes if v[1] > 0]
                if len(volume_values) > 1:
                    volume_ratio = max(volume_values) / min(volume_values)
                    
                    if volume_ratio > (1 + self.conflict_thresholds['volume']):
                        anomalies.append({
                            'type': 'volume_inconsistency',
                            'severity': 'medium',
                            'message': f"Volume ratio {volume_ratio:.1f} exceeds threshold",
                            'sources': dict(volumes),
                            'timestamp': datetime.now()
                        })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies for {symbol}: {e}")
            return []
    
    async def _collect_from_source(self, 
                                 collector: RealtimeDataCollector, 
                                 symbol: str, 
                                 data_types: List[str]) -> Optional[Dict[str, Any]]:
        """Collect data from a specific source."""
        try:
            data = {}
            
            if 'price' in data_types:
                quote = await collector.get_realtime_quote(symbol)
                if quote:
                    data.update({
                        'price': quote.price,
                        'change': quote.change,
                        'change_percent': quote.change_percent,
                        'volume': quote.volume,
                        'open': quote.open_price,
                        'high': quote.high,
                        'low': quote.low,
                        'timestamp': quote.timestamp
                    })
            
            if 'sentiment' in data_types:
                sentiment = await collector.get_market_sentiment(symbol)
                if sentiment:
                    data.update({
                        'sentiment_score': sentiment.sentiment_score,
                        'sentiment_trend': sentiment.sentiment_trend,
                        'news_count': sentiment.news_count
                    })
            
            # Add ratios data (would be implemented based on source capabilities)
            if 'ratios' in data_types:
                # Placeholder for financial ratios collection
                pass
            
            return data if data else None
            
        except Exception as e:
            self.logger.error(f"Error collecting data from source: {e}")
            return None
    
    def _validate_source_data(self, data: Dict[str, Any], source_name: str) -> List[ValidationResult]:
        """Validate data from a specific source."""
        try:
            results = []
            
            # Validate price data if present
            if any(k in data for k in ['price', 'volume', 'change_percent']):
                results.extend(self.validator.validate_price_data(data))
            
            # Validate financial ratios if present
            ratios = {k: v for k, v in data.items() if k in ['PE', 'PB', 'ROE', 'ROA']}
            if ratios:
                results.extend(self.validator.validate_financial_ratios(ratios))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error validating data from {source_name}: {e}")
            return []
    
    async def _aggregate_source_data(self, 
                                   symbol: str, 
                                   source_data: Dict[str, Dict[str, Any]], 
                                   validation_results: Dict[str, List[ValidationResult]]) -> AggregatedData:
        """Aggregate data from multiple sources."""
        try:
            # Calculate quality scores for each source
            quality_scores = {}
            for source_name, results in validation_results.items():
                if results:
                    error_count = len([r for r in results if r.level == ValidationLevel.ERROR])
                    warning_count = len([r for r in results if r.level == ValidationLevel.WARNING])
                    total_checks = len(results)
                    
                    score = max(0, (total_checks - error_count * 2 - warning_count) / total_checks)
                else:
                    score = 1.0
                
                # Combine with source reliability
                source_reliability = self.data_sources[source_name].reliability_score
                quality_scores[source_name] = score * source_reliability
            
            # Resolve conflicts and create primary data
            primary_data = {}
            conflicts = []
            
            # Aggregate each data field
            for field in ['price', 'volume', 'change_percent', 'sentiment_score']:
                if field in ['price', 'change_percent']:
                    resolution_method = self.resolution_strategies.get('price', ConflictResolution.WEIGHTED_AVERAGE)
                elif field == 'volume':
                    resolution_method = self.resolution_strategies.get('volume', ConflictResolution.PRIORITY_BASED)
                else:
                    resolution_method = self.resolution_strategies.get('sentiment', ConflictResolution.WEIGHTED_AVERAGE)
                
                field_data = {}
                for source_name, data in source_data.items():
                    if field in data:
                        field_data[source_name] = data[field]
                
                if field_data:
                    resolved_value, conflict_detected = self._resolve_field_conflict(
                        field, field_data, quality_scores, resolution_method
                    )
                    
                    primary_data[field] = resolved_value
                    
                    if conflict_detected:
                        conflicts.append(field)
            
            # Calculate overall quality score
            overall_quality = mean(quality_scores.values()) if quality_scores else 0.0
            
            return AggregatedData(
                symbol=symbol,
                timestamp=datetime.now(),
                primary_data=primary_data,
                source_data=source_data,
                confidence_scores=quality_scores,
                data_quality_score=overall_quality,
                conflicts_detected=conflicts,
                resolution_method=resolution_method,
                metadata={
                    'sources_count': len(source_data),
                    'validation_results': validation_results
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error aggregating source data: {e}")
            return AggregatedData(symbol=symbol, timestamp=datetime.now(), primary_data={})
    
    def _resolve_field_conflict(self, 
                              field: str, 
                              field_data: Dict[str, Any], 
                              quality_scores: Dict[str, float],
                              resolution_method: ConflictResolution) -> Tuple[Any, bool]:
        """Resolve conflicts for a specific field."""
        try:
            if len(field_data) == 1:
                return list(field_data.values())[0], False
            
            values = list(field_data.values())
            sources = list(field_data.keys())
            
            # Detect conflict
            conflict_detected = False
            if field in self.conflict_thresholds:
                threshold = self.conflict_thresholds[field]
                if isinstance(values[0], (int, float)):
                    value_range = max(values) - min(values)
                    avg_value = mean(values)
                    if avg_value != 0 and value_range / avg_value > threshold:
                        conflict_detected = True
            
            # Resolve based on strategy
            if resolution_method == ConflictResolution.PRIORITY_BASED:
                # Use highest priority source
                best_source = min(sources, key=lambda s: self.data_sources[s].priority.value)
                return field_data[best_source], conflict_detected
            
            elif resolution_method == ConflictResolution.WEIGHTED_AVERAGE:
                if all(isinstance(v, (int, float)) for v in values):
                    # Weight by quality scores
                    weights = [quality_scores.get(s, 0.5) for s in sources]
                    weighted_sum = sum(v * w for v, w in zip(values, weights))
                    weight_sum = sum(weights)
                    return weighted_sum / weight_sum if weight_sum > 0 else mean(values), conflict_detected
                else:
                    # For non-numeric values, use highest quality source
                    best_source = max(sources, key=lambda s: quality_scores.get(s, 0))
                    return field_data[best_source], conflict_detected
            
            elif resolution_method == ConflictResolution.MEDIAN:
                if all(isinstance(v, (int, float)) for v in values):
                    return median(values), conflict_detected
                else:
                    # For non-numeric, use middle value or highest quality
                    best_source = max(sources, key=lambda s: quality_scores.get(s, 0))
                    return field_data[best_source], conflict_detected
            
            elif resolution_method == ConflictResolution.LATEST:
                # Use most recent data (assuming all are recent for real-time)
                return values[-1], conflict_detected
            
            elif resolution_method == ConflictResolution.VALIDATION_BASED:
                # Use source with best validation score
                best_source = max(sources, key=lambda s: quality_scores.get(s, 0))
                return field_data[best_source], conflict_detected
            
            # Default: use first value
            return values[0], conflict_detected
            
        except Exception as e:
            self.logger.error(f"Error resolving field conflict for {field}: {e}")
            return field_data[list(field_data.keys())[0]], True
    
    def get_source_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all data sources."""
        stats = {}
        for source_name, source in self.data_sources.items():
            stats[source_name] = {
                'enabled': source.enabled,
                'priority': source.priority.name,
                'reliability_score': source.reliability_score,
                'success_rate': source.success_rate,
                'last_update': source.last_update.isoformat() if source.last_update else None,
                'error_count': source.error_count,
                'success_count': source.success_count
            }
        return stats
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            for collector in self.collectors.values():
                await collector.__aexit__(None, None, None)
            self.collectors.clear()
            self.logger.info("Aggregator cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# Example usage and testing
async def test_multi_source_aggregator():
    """Test the multi-source aggregator."""
    cache_manager = CacheManager()
    aggregator = MultiSourceAggregator(cache_manager)
    
    try:
        await aggregator.initialize()
        
        print("Testing multi-source aggregation...")
        
        # Test aggregating stock data
        result = await aggregator.aggregate_stock_data('HPG', ['price', 'sentiment'])
        if result:
            print(f"Aggregated data for HPG:")
            print(f"  Price: {result.primary_data.get('price')}")
            print(f"  Quality Score: {result.data_quality_score:.2f}")
            print(f"  Sources: {list(result.source_data.keys())}")
            print(f"  Conflicts: {result.conflicts_detected}")
        
        # Test best price data
        best_price = await aggregator.get_best_price_data('HPG')
        if best_price:
            print(f"Best price data: {best_price}")
        
        # Test anomaly detection
        anomalies = await aggregator.detect_data_anomalies('HPG')
        print(f"Anomalies detected: {len(anomalies)}")
        
        # Get source statistics
        stats = aggregator.get_source_statistics()
        print("Source statistics:")
        for source, stat in stats.items():
            print(f"  {source}: Success rate {stat['success_rate']:.1%}")
        
    finally:
        await aggregator.cleanup()

if __name__ == "__main__":
    asyncio.run(test_multi_source_aggregator())
