"""
Macro Analysis Cache Manager - Optimized for Market Trend Analysis

Specialized caching system for macroeconomic and market trend analysis
that prevents redundant daily analysis requests and saves token costs.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

class MacroCacheManager:
    """
    Specialized cache manager for macroeconomic and market analysis.
    Ensures that market trend and economic analysis is only performed once per day.
    """
    
    def __init__(self, cache_dir: str = ".macro_cache"):
        """
        Initialize macro cache manager.
        
        Args:
            cache_dir: Directory for storing macro analysis cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Cache file paths
        self.news_cache_file = self.cache_dir / "daily_news_analysis.json"
        self.macro_cache_file = self.cache_dir / "daily_macro_analysis.json"
        
        # TTL for different types of analysis (in hours)
        self.ttl_config = {
            "news_analysis": 24,      # 24 hours - daily news update
            "macro_trends": 24,       # 24 hours - daily macro analysis
            "market_sentiment": 12,   # 12 hours - twice daily update
            "policy_updates": 48      # 48 hours - policy changes less frequent
        }
    
    def _get_cache_key(self, analysis_type: str, date: str = None) -> str:
        """
        Generate cache key for analysis type and date.
        
        Args:
            analysis_type: Type of analysis (news_analysis, macro_trends, etc.)
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Cache key string
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        return f"{analysis_type}_{date}"
    
    def _is_cache_valid(self, cache_data: Dict[str, Any], analysis_type: str) -> bool:
        """
        Check if cached data is still valid based on TTL.
        
        Args:
            cache_data: Cached data with timestamp
            analysis_type: Type of analysis to check TTL for
            
        Returns:
            True if cache is valid, False otherwise
        """
        if "timestamp" not in cache_data:
            return False
        
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        ttl_hours = self.ttl_config.get(analysis_type, 24)
        expiry_time = cache_time + timedelta(hours=ttl_hours)
        
        return datetime.now() < expiry_time
    
    def get_daily_news_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Get cached daily news analysis if available and valid.
        
        Returns:
            Cached news analysis data or None if not available/expired
        """
        try:
            if not self.news_cache_file.exists():
                return None
            
            with open(self.news_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if self._is_cache_valid(cache_data, "news_analysis"):
                self.logger.info("Using cached daily news analysis")
                return cache_data
            else:
                self.logger.info("Daily news analysis cache expired")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading news analysis cache: {e}")
            return None
    
    def save_daily_news_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Save daily news analysis to cache.
        
        Args:
            analysis_data: News analysis data to cache
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            cache_entry = {
                "timestamp": datetime.now().isoformat(),
                "data": analysis_data,
                "analysis_type": "news_analysis",
                "cache_key": self._get_cache_key("news_analysis")
            }
            
            with open(self.news_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Daily news analysis cached successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving news analysis cache: {e}")
            return False
    
    def get_macro_analysis(self, analysis_type: str = "macro_trends") -> Optional[Dict[str, Any]]:
        """
        Get cached macro analysis by type.
        
        Args:
            analysis_type: Type of macro analysis
            
        Returns:
            Cached macro analysis data or None if not available/expired
        """
        try:
            cache_file = self.cache_dir / f"{analysis_type}.json"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if self._is_cache_valid(cache_data, analysis_type):
                self.logger.info(f"Using cached {analysis_type} analysis")
                return cache_data
            else:
                self.logger.info(f"{analysis_type} analysis cache expired")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading {analysis_type} cache: {e}")
            return None
    
    def save_macro_analysis(self, analysis_data: Dict[str, Any], analysis_type: str = "macro_trends") -> bool:
        """
        Save macro analysis to cache.
        
        Args:
            analysis_data: Macro analysis data to cache
            analysis_type: Type of macro analysis
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            cache_file = self.cache_dir / f"{analysis_type}.json"
            
            cache_entry = {
                "timestamp": datetime.now().isoformat(),
                "data": analysis_data,
                "analysis_type": analysis_type,
                "cache_key": self._get_cache_key(analysis_type)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"{analysis_type} analysis cached successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving {analysis_type} cache: {e}")
            return False
    
    def is_analysis_needed(self, analysis_type: str) -> bool:
        """
        Check if analysis needs to be performed (cache miss or expired).
        
        Args:
            analysis_type: Type of analysis to check
            
        Returns:
            True if analysis is needed, False if cached data is available
        """
        if analysis_type == "news_analysis":
            return self.get_daily_news_analysis() is None
        else:
            return self.get_macro_analysis(analysis_type) is None
    
    def clear_expired_cache(self) -> int:
        """
        Clear all expired cache files.
        
        Returns:
            Number of files cleared
        """
        cleared_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    analysis_type = cache_data.get("analysis_type", "macro_trends")
                    
                    if not self._is_cache_valid(cache_data, analysis_type):
                        cache_file.unlink()
                        cleared_count += 1
                        self.logger.info(f"Cleared expired cache: {cache_file.name}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing cache file {cache_file}: {e}")
            
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing expired cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and status.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "cache_dir": str(self.cache_dir),
            "total_cache_files": 0,
            "valid_cache_files": 0,
            "expired_cache_files": 0,
            "cache_types": {}
        }
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                stats["total_cache_files"] += 1
                
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    analysis_type = cache_data.get("analysis_type", "unknown")
                    is_valid = self._is_cache_valid(cache_data, analysis_type)
                    
                    if is_valid:
                        stats["valid_cache_files"] += 1
                    else:
                        stats["expired_cache_files"] += 1
                    
                    if analysis_type not in stats["cache_types"]:
                        stats["cache_types"][analysis_type] = {"valid": 0, "expired": 0}
                    
                    if is_valid:
                        stats["cache_types"][analysis_type]["valid"] += 1
                    else:
                        stats["cache_types"][analysis_type]["expired"] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error reading cache file {cache_file}: {e}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return stats

# Global instance for easy access
macro_cache = MacroCacheManager()
