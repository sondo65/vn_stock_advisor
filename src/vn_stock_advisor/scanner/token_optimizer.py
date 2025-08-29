"""
Token Usage Optimizer - Tối ưu hóa việc sử dụng token

Các tính năng:
1. Batch processing để giảm số lần gọi API
2. Intelligent caching với TTL phù hợp
3. Data deduplication
4. Priority-based processing
5. Token usage tracking và báo cáo
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging
import hashlib

try:
    from ..data_integration.cache_manager import CacheManager
    from ..tools.custom_tool import FundDataTool, TechDataTool
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("Warning: Dependencies not available for token optimizer")

@dataclass
class TokenUsageStats:
    """Thống kê sử dụng token."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_processing_time: float = 0.0
    tokens_saved_estimate: int = 0
    batch_efficiency: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Tỷ lệ cache hit."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    @property
    def average_processing_time(self) -> float:
        """Thời gian xử lý trung bình."""
        if self.total_requests == 0:
            return 0.0
        return self.total_processing_time / self.total_requests

@dataclass
class BatchRequest:
    """Request được batch lại."""
    symbols: List[str]
    request_type: str  # "fundamental", "technical", "both"
    priority: int  # 1-5, 1 = highest priority
    timestamp: datetime
    requester_id: str

class TokenOptimizer:
    """Hệ thống tối ưu hóa token usage."""
    
    def __init__(self, 
                 cache_ttl_minutes: int = 30,
                 batch_size: int = 10,
                 batch_timeout_seconds: int = 5):
        """
        Initialize token optimizer.
        
        Args:
            cache_ttl_minutes: TTL cho cache (phút)
            batch_size: Kích thước batch tối đa
            batch_timeout_seconds: Timeout cho batch processing
        """
        self.cache_ttl = cache_ttl_minutes * 60
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout_seconds
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache
        if DEPENDENCIES_AVAILABLE:
            self.cache_manager = CacheManager(
                max_memory_size=50 * 1024 * 1024,  # 50MB
                default_ttl=self.cache_ttl
            )
            self.fund_tool = FundDataTool()
            self.tech_tool = TechDataTool()
        else:
            self.cache_manager = None
            self.fund_tool = None
            self.tech_tool = None
        
        # Batch processing queues
        self.pending_requests: List[BatchRequest] = []
        self.processing_batches: Dict[str, List[str]] = {}
        
        # Statistics
        self.stats = TokenUsageStats()
        
        # Deduplication tracking
        self.recent_requests: Dict[str, datetime] = {}
        self.dedup_window_minutes = 5
    
    def _generate_cache_key(self, symbol: str, data_type: str, extra_params: str = "") -> str:
        """Tạo cache key cho dữ liệu."""
        base_key = f"token_opt_{symbol}_{data_type}_{extra_params}"
        return hashlib.md5(base_key.encode()).hexdigest()[:16]
    
    def _is_duplicate_request(self, symbol: str, request_type: str) -> bool:
        """Kiểm tra request có bị duplicate không."""
        request_key = f"{symbol}_{request_type}"
        now = datetime.now()
        
        if request_key in self.recent_requests:
            last_request = self.recent_requests[request_key]
            if now - last_request < timedelta(minutes=self.dedup_window_minutes):
                return True
        
        self.recent_requests[request_key] = now
        return False
    
    async def get_cached_data(self, symbol: str, data_type: str) -> Optional[Dict]:
        """Lấy dữ liệu từ cache."""
        if not self.cache_manager:
            return None
        
        cache_key = self._generate_cache_key(symbol, data_type)
        try:
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                self.stats.cache_hits += 1
                return cached_data
            else:
                self.stats.cache_misses += 1
                return None
        except Exception as e:
            self.logger.warning(f"Cache get error for {symbol}: {e}")
            self.stats.cache_misses += 1
            return None
    
    async def cache_data(self, symbol: str, data_type: str, data: Any) -> None:
        """Lưu dữ liệu vào cache."""
        if not self.cache_manager:
            return
        
        cache_key = self._generate_cache_key(symbol, data_type)
        cache_data = {
            "symbol": symbol,
            "data_type": data_type,
            "data": data,
            "cached_at": datetime.now().isoformat(),
            "ttl_minutes": self.cache_ttl // 60
        }
        
        try:
            await self.cache_manager.set(cache_key, cache_data, ttl=self.cache_ttl)
        except Exception as e:
            self.logger.warning(f"Cache set error for {symbol}: {e}")
    
    def add_batch_request(self, symbols: List[str], request_type: str, 
                         priority: int = 3, requester_id: str = "default") -> str:
        """
        Thêm request vào batch queue.
        
        Args:
            symbols: Danh sách mã cổ phiếu
            request_type: Loại request ("fundamental", "technical", "both")
            priority: Độ ưu tiên (1-5, 1 cao nhất)
            requester_id: ID của người request
            
        Returns:
            Batch ID
        """
        # Filter out duplicate requests
        filtered_symbols = []
        for symbol in symbols:
            if not self._is_duplicate_request(symbol, request_type):
                filtered_symbols.append(symbol)
        
        if not filtered_symbols:
            self.logger.info("All symbols filtered out as duplicates")
            return ""
        
        batch_request = BatchRequest(
            symbols=filtered_symbols,
            request_type=request_type,
            priority=priority,
            timestamp=datetime.now(),
            requester_id=requester_id
        )
        
        self.pending_requests.append(batch_request)
        batch_id = f"batch_{int(time.time())}_{len(self.pending_requests)}"
        
        self.logger.info(f"Added batch request {batch_id}: {len(filtered_symbols)} symbols")
        return batch_id
    
    async def process_single_symbol(self, symbol: str, request_type: str) -> Dict[str, Any]:
        """
        Xử lý một symbol với cache check.
        
        Args:
            symbol: Mã cổ phiếu
            request_type: Loại request
            
        Returns:
            Dữ liệu đã xử lý
        """
        start_time = time.time()
        result = {"symbol": symbol, "request_type": request_type}
        
        try:
            # Check cache first
            if request_type in ["fundamental", "both"]:
                cached_fund = await self.get_cached_data(symbol, "fundamental")
                if cached_fund:
                    result["fundamental_data"] = cached_fund["data"]
                    result["fundamental_from_cache"] = True
                else:
                    if self.fund_tool:
                        fund_data = self.fund_tool._run(symbol)
                        result["fundamental_data"] = fund_data
                        result["fundamental_from_cache"] = False
                        await self.cache_data(symbol, "fundamental", fund_data)
                    else:
                        result["fundamental_data"] = f"Mock fundamental data for {symbol}"
                        result["fundamental_from_cache"] = False
            
            if request_type in ["technical", "both"]:
                cached_tech = await self.get_cached_data(symbol, "technical")
                if cached_tech:
                    result["technical_data"] = cached_tech["data"]
                    result["technical_from_cache"] = True
                else:
                    if self.tech_tool:
                        tech_data = self.tech_tool._run(symbol)
                        result["technical_data"] = tech_data
                        result["technical_from_cache"] = False
                        await self.cache_data(symbol, "technical", tech_data)
                    else:
                        result["technical_data"] = f"Mock technical data for {symbol}"
                        result["technical_from_cache"] = False
            
            # Update stats
            self.stats.total_requests += 1
            processing_time = time.time() - start_time
            self.stats.total_processing_time += processing_time
            
            result["processing_time"] = processing_time
            result["success"] = True
            
        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {e}")
            result["error"] = str(e)
            result["success"] = False
        
        return result
    
    async def process_batch(self, batch_request: BatchRequest) -> List[Dict[str, Any]]:
        """
        Xử lý một batch request.
        
        Args:
            batch_request: Batch request cần xử lý
            
        Returns:
            Danh sách kết quả
        """
        self.logger.info(f"Processing batch: {len(batch_request.symbols)} symbols, type: {batch_request.request_type}")
        
        # Process symbols in parallel (with limit)
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def process_with_semaphore(symbol: str):
            async with semaphore:
                return await self.process_single_symbol(symbol, batch_request.request_type)
        
        tasks = [process_with_semaphore(symbol) for symbol in batch_request.symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Batch processing exception: {result}")
            else:
                valid_results.append(result)
        
        # Calculate batch efficiency
        cache_hits = sum(1 for r in valid_results 
                        if r.get("fundamental_from_cache") or r.get("technical_from_cache"))
        total_requests = len(valid_results)
        if total_requests > 0:
            efficiency = (cache_hits / total_requests) * 100
            self.stats.batch_efficiency = efficiency
        
        self.logger.info(f"Batch processed: {len(valid_results)} results, {cache_hits} cache hits")
        return valid_results
    
    async def process_pending_batches(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Xử lý tất cả pending batches.
        
        Returns:
            Dictionary với kết quả từng batch
        """
        if not self.pending_requests:
            return {}
        
        # Sort by priority (1 = highest)
        self.pending_requests.sort(key=lambda x: (x.priority, x.timestamp))
        
        results = {}
        processed_batches = []
        
        while self.pending_requests:
            # Take batch_size requests or all remaining
            current_batch_requests = self.pending_requests[:self.batch_size]
            self.pending_requests = self.pending_requests[self.batch_size:]
            
            # Group by request type for efficiency
            grouped_requests = defaultdict(list)
            for req in current_batch_requests:
                grouped_requests[req.request_type].extend(req.symbols)
            
            # Process each group
            for request_type, symbols in grouped_requests.items():
                # Remove duplicates
                unique_symbols = list(set(symbols))
                
                batch_request = BatchRequest(
                    symbols=unique_symbols,
                    request_type=request_type,
                    priority=1,  # High priority for processing
                    timestamp=datetime.now(),
                    requester_id="batch_processor"
                )
                
                batch_results = await self.process_batch(batch_request)
                batch_id = f"processed_{request_type}_{int(time.time())}"
                results[batch_id] = batch_results
                processed_batches.append(batch_id)
        
        self.logger.info(f"Processed {len(processed_batches)} batches")
        return results
    
    def estimate_token_savings(self) -> int:
        """Ước tính số token đã tiết kiệm được."""
        # Rough estimate: each cache hit saves ~100-500 tokens
        estimated_tokens_per_hit = 300
        self.stats.tokens_saved_estimate = self.stats.cache_hits * estimated_tokens_per_hit
        return self.stats.tokens_saved_estimate
    
    def get_optimization_report(self) -> str:
        """Tạo báo cáo tối ưu hóa token."""
        self.estimate_token_savings()
        
        report = ["🚀 **TOKEN USAGE OPTIMIZATION REPORT**"]
        report.append("=" * 50)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 📊 **PERFORMANCE STATISTICS**")
        report.append(f"• Total Requests: {self.stats.total_requests}")
        report.append(f"• Cache Hit Rate: {self.stats.cache_hit_rate:.1f}%")
        report.append(f"• Cache Hits: {self.stats.cache_hits}")
        report.append(f"• Cache Misses: {self.stats.cache_misses}")
        report.append(f"• Avg Processing Time: {self.stats.average_processing_time:.2f}s")
        report.append(f"• Batch Efficiency: {self.stats.batch_efficiency:.1f}%")
        report.append("")
        
        report.append("## 💰 **TOKEN SAVINGS**")
        report.append(f"• Estimated Tokens Saved: {self.stats.tokens_saved_estimate:,}")
        report.append(f"• Cache Effectiveness: {'High' if self.stats.cache_hit_rate > 60 else 'Medium' if self.stats.cache_hit_rate > 30 else 'Low'}")
        report.append("")
        
        report.append("## ⚡ **OPTIMIZATION TIPS**")
        if self.stats.cache_hit_rate < 50:
            report.append("• Consider increasing cache TTL for better hit rates")
        if self.stats.batch_efficiency < 70:
            report.append("• Increase batch size for better efficiency")
        if self.stats.average_processing_time > 2.0:
            report.append("• Consider reducing concurrent request limit")
        
        if self.stats.cache_hit_rate > 70:
            report.append("• ✅ Excellent cache performance!")
        if self.stats.batch_efficiency > 80:
            report.append("• ✅ Great batch processing efficiency!")
        
        return "\n".join(report)
    
    def reset_stats(self):
        """Reset thống kê."""
        self.stats = TokenUsageStats()
        self.recent_requests.clear()
        self.logger.info("Token optimizer stats reset")

class BatchStockProcessor:
    """Processor chuyên xử lý batch stocks với token optimization."""
    
    def __init__(self, token_optimizer: TokenOptimizer = None):
        """Initialize batch processor."""
        self.optimizer = token_optimizer or TokenOptimizer()
        self.logger = logging.getLogger(__name__)
    
    async def quick_scan_batch(self, symbols: List[str], 
                              analysis_type: str = "both",
                              priority: int = 2) -> List[Dict[str, Any]]:
        """
        Quét nhanh một batch cổ phiếu.
        
        Args:
            symbols: Danh sách mã cổ phiếu
            analysis_type: Loại phân tích ("fundamental", "technical", "both")
            priority: Độ ưu tiên
            
        Returns:
            Danh sách kết quả phân tích
        """
        batch_id = self.optimizer.add_batch_request(
            symbols=symbols,
            request_type=analysis_type,
            priority=priority,
            requester_id="quick_scanner"
        )
        
        if not batch_id:
            return []
        
        # Process immediately for quick scan
        batch_results = await self.optimizer.process_pending_batches()
        
        # Flatten results
        all_results = []
        for batch_data in batch_results.values():
            all_results.extend(batch_data)
        
        self.logger.info(f"Quick scan completed: {len(all_results)} stocks processed")
        return all_results
    
    def get_processing_stats(self) -> str:
        """Lấy thống kê xử lý."""
        return self.optimizer.get_optimization_report()

# Convenience functions
async def batch_analyze_stocks(symbols: List[str], 
                              analysis_type: str = "both") -> List[Dict[str, Any]]:
    """Phân tích batch cổ phiếu với token optimization."""
    processor = BatchStockProcessor()
    return await processor.quick_scan_batch(symbols, analysis_type)

def create_optimized_scanner(cache_ttl_minutes: int = 30, 
                           batch_size: int = 10) -> TokenOptimizer:
    """Tạo scanner tối ưu hóa token."""
    return TokenOptimizer(
        cache_ttl_minutes=cache_ttl_minutes,
        batch_size=batch_size,
        batch_timeout_seconds=5
    )
