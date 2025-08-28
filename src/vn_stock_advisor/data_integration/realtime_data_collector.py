"""
Real-time Data Collector - Phase 3

Collects real-time stock data from multiple sources including:
- VnStock API
- Alternative financial data APIs
- News feeds
- Social media sentiment
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import logging

try:
    import vnstock as vn
    VNSTOCK_AVAILABLE = True
except ImportError:
    VNSTOCK_AVAILABLE = False
    print("Warning: vnstock not available for real-time data collection")

@dataclass
class RealtimeQuote:
    """Real-time stock quote data structure."""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    bid: float
    ask: float
    high: float
    low: float
    open_price: float
    market_cap: float
    source: str

@dataclass
class MarketSentiment:
    """Market sentiment data structure."""
    symbol: str
    sentiment_score: float
    news_count: int
    social_mentions: int
    timestamp: datetime
    sentiment_trend: str
    key_topics: List[str]

class RealtimeDataCollector:
    """Collects real-time financial data from multiple sources."""
    
    def __init__(self, update_interval: int = 30):
        """
        Initialize real-time data collector.
        
        Args:
            update_interval: Update interval in seconds
        """
        self.update_interval = update_interval
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.data_cache = {}
        self.last_update = {}
        
        # Data source endpoints
        self.sources = {
            'vnstock': self._get_vnstock_data,
            'vietstock': self._get_vietstock_data,
            'cafef': self._get_cafef_data,
            'investing': self._get_investing_data
        }
        
        # News sources for sentiment
        self.news_sources = [
            'https://vnexpress.net/kinh-doanh/chung-khoan',
            'https://cafef.vn/chung-khoan.chn',
            'https://vietstock.vn/news',
            'https://ndh.vn/chung-khoan'
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_realtime_quote(self, symbol: str) -> Optional[RealtimeQuote]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'HPG')
            
        Returns:
            RealtimeQuote object or None if failed
        """
        try:
            # Check cache first
            cache_key = f"quote_{symbol}"
            if self._is_cache_valid(cache_key):
                return self.data_cache[cache_key]
            
            # Try multiple sources
            for source_name, source_func in self.sources.items():
                try:
                    quote = await source_func(symbol)
                    if quote:
                        self.data_cache[cache_key] = quote
                        self.last_update[cache_key] = datetime.now()
                        return quote
                except Exception as e:
                    self.logger.warning(f"Failed to get data from {source_name}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting real-time quote for {symbol}: {e}")
            return None
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, RealtimeQuote]:
        """
        Get real-time quotes for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to RealtimeQuote objects
        """
        tasks = [self.get_realtime_quote(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quotes = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, RealtimeQuote):
                quotes[symbol] = result
            elif isinstance(result, Exception):
                self.logger.error(f"Error getting quote for {symbol}: {result}")
        
        return quotes
    
    async def get_market_sentiment(self, symbol: str) -> Optional[MarketSentiment]:
        """
        Get market sentiment for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            MarketSentiment object or None if failed
        """
        try:
            # Check cache first
            cache_key = f"sentiment_{symbol}"
            if self._is_cache_valid(cache_key, cache_duration=300):  # 5 min cache
                return self.data_cache[cache_key]
            
            # Collect sentiment from multiple sources
            sentiment_data = await self._collect_sentiment_data(symbol)
            
            if sentiment_data:
                sentiment = MarketSentiment(
                    symbol=symbol,
                    sentiment_score=sentiment_data.get('score', 0.0),
                    news_count=sentiment_data.get('news_count', 0),
                    social_mentions=sentiment_data.get('social_mentions', 0),
                    timestamp=datetime.now(),
                    sentiment_trend=sentiment_data.get('trend', 'neutral'),
                    key_topics=sentiment_data.get('topics', [])
                )
                
                self.data_cache[cache_key] = sentiment
                self.last_update[cache_key] = datetime.now()
                return sentiment
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting market sentiment for {symbol}: {e}")
            return None
    
    async def _get_vnstock_data(self, symbol: str) -> Optional[RealtimeQuote]:
        """Get data from vnstock API."""
        if not VNSTOCK_AVAILABLE:
            return None
        
        try:
            # Get real-time quote
            quote_data = vn.stock_intraday_data(symbol, page_size=1)
            
            if quote_data is not None and not quote_data.empty:
                latest = quote_data.iloc[-1]
                
                return RealtimeQuote(
                    symbol=symbol,
                    price=float(latest.get('close', 0)),
                    change=float(latest.get('change', 0)),
                    change_percent=float(latest.get('change_percent', 0)),
                    volume=int(latest.get('volume', 0)),
                    timestamp=datetime.now(),
                    bid=float(latest.get('bid', 0)),
                    ask=float(latest.get('ask', 0)),
                    high=float(latest.get('high', 0)),
                    low=float(latest.get('low', 0)),
                    open_price=float(latest.get('open', 0)),
                    market_cap=0.0,  # Calculate separately if needed
                    source='vnstock'
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"VnStock API error for {symbol}: {e}")
            return None
    
    async def _get_vietstock_data(self, symbol: str) -> Optional[RealtimeQuote]:
        """Get data from VietStock API (placeholder)."""
        try:
            # This would implement VietStock API integration
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            self.logger.error(f"VietStock API error for {symbol}: {e}")
            return None
    
    async def _get_cafef_data(self, symbol: str) -> Optional[RealtimeQuote]:
        """Get data from CafeF API (placeholder)."""
        try:
            # This would implement CafeF API integration
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            self.logger.error(f"CafeF API error for {symbol}: {e}")
            return None
    
    async def _get_investing_data(self, symbol: str) -> Optional[RealtimeQuote]:
        """Get data from Investing.com API (placeholder)."""
        try:
            # This would implement Investing.com API integration
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            self.logger.error(f"Investing.com API error for {symbol}: {e}")
            return None
    
    async def _collect_sentiment_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Collect sentiment data from news and social sources."""
        try:
            sentiment_scores = []
            news_count = 0
            social_mentions = 0
            topics = []
            
            # Collect news sentiment (placeholder implementation)
            for source in self.news_sources:
                try:
                    # This would implement actual news scraping and sentiment analysis
                    # For now, generate mock data
                    sentiment_scores.append(np.random.normal(0, 0.3))
                    news_count += np.random.randint(0, 5)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get sentiment from {source}: {e}")
            
            if sentiment_scores:
                avg_sentiment = np.mean(sentiment_scores)
                trend = 'positive' if avg_sentiment > 0.1 else 'negative' if avg_sentiment < -0.1 else 'neutral'
                
                return {
                    'score': avg_sentiment,
                    'news_count': news_count,
                    'social_mentions': social_mentions,
                    'trend': trend,
                    'topics': topics
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error collecting sentiment data: {e}")
            return None
    
    def _is_cache_valid(self, cache_key: str, cache_duration: int = 30) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.data_cache:
            return False
        
        if cache_key not in self.last_update:
            return False
        
        time_diff = datetime.now() - self.last_update[cache_key]
        return time_diff.total_seconds() < cache_duration
    
    async def start_realtime_monitoring(self, symbols: List[str], callback=None):
        """
        Start real-time monitoring for multiple symbols.
        
        Args:
            symbols: List of symbols to monitor
            callback: Optional callback function for real-time updates
        """
        self.logger.info(f"Starting real-time monitoring for {len(symbols)} symbols")
        
        while True:
            try:
                quotes = await self.get_multiple_quotes(symbols)
                
                if callback and quotes:
                    await callback(quotes)
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in real-time monitoring: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def get_cached_data(self, symbol: str) -> Optional[RealtimeQuote]:
        """Get cached quote data for a symbol."""
        cache_key = f"quote_{symbol}"
        return self.data_cache.get(cache_key)
    
    def clear_cache(self):
        """Clear all cached data."""
        self.data_cache.clear()
        self.last_update.clear()
        self.logger.info("Cache cleared")

# Example usage and testing
async def test_realtime_collector():
    """Test the real-time data collector."""
    symbols = ['HPG', 'VIC', 'VCB', 'FPT']
    
    async with RealtimeDataCollector(update_interval=10) as collector:
        print("Testing real-time data collection...")
        
        # Test single quote
        quote = await collector.get_realtime_quote('HPG')
        if quote:
            print(f"HPG Quote: {quote.price} ({quote.change_percent:+.2f}%)")
        
        # Test multiple quotes
        quotes = await collector.get_multiple_quotes(symbols)
        print(f"Retrieved {len(quotes)} quotes")
        
        # Test sentiment
        sentiment = await collector.get_market_sentiment('HPG')
        if sentiment:
            print(f"HPG Sentiment: {sentiment.sentiment_score:.2f} ({sentiment.sentiment_trend})")

if __name__ == "__main__":
    asyncio.run(test_realtime_collector())
