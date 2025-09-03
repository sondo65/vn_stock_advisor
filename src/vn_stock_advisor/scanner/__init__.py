"""
VN Stock Advisor - Optimized Scanner System

Hệ thống scan cổ phiếu tối ưu với các tính năng:
1. Lightweight Scanner - Phân tích nhanh với token usage tối thiểu
2. Screening Engine - Lọc cổ phiếu theo nhiều tiêu chí
3. Token Optimizer - Tối ưu hóa cache và batch processing
4. Priority Ranking - Xếp hạng để ưu tiên phân tích chuyên sâu

Quick Start:
```python
from vn_stock_advisor.scanner import quick_scan_market, find_opportunities

# Scan nhanh thị trường
results = quick_scan_market(min_score=6.5, max_stocks=20)

# Tìm cơ hội đầu tư
opportunities = find_opportunities(results)
```
"""

from .lightweight_scanner import (
    LightweightStockScanner,
    LightweightScanResult,
    quick_scan_market,
    scan_custom_list
)

from .screening_engine import (
    ScreeningEngine,
    ScreeningCriteria,
    ScreeningFilter,
    quick_screen_value_stocks,
    quick_screen_momentum_stocks,
    find_best_opportunities
)

from .token_optimizer import (
    TokenOptimizer,
    BatchStockProcessor,
    TokenUsageStats,
    batch_analyze_stocks,
    create_optimized_scanner
)

from .priority_ranking import (
    PriorityRankingSystem,
    PriorityLevel,
    RankedStock,
    rank_scan_results,
    get_priority_analysis_queue
)

from .industry_suggester import (
    IndustryStockSuggester,
    IndustryStockSuggestion,
    IndustryBenchmark,
    IndustryType
)

from .industry_analyzer import (
    IndustryAnalyzer,
    IndustryAnalysis,
    IndustryTrend
)

from .industry_stock_advisor import (
    IndustryStockAdvisor,
    IndustryRecommendation
)

# Convenience functions for quick usage

def suggest_industry_stocks(industry: str, max_stocks: int = 10, min_score: float = 7.0) -> list:
    """
    Gợi ý cổ phiếu tiềm năng cho một ngành cụ thể.
    
    Args:
        industry: Tên ngành
        max_stocks: Số lượng cổ phiếu tối đa
        min_score: Điểm tối thiểu
        
    Returns:
        Danh sách gợi ý cổ phiếu
    """
    advisor = IndustryStockAdvisor()
    recommendation = advisor.get_industry_recommendation(
        industry=industry,
        max_stocks=max_stocks,
        min_score=min_score,
        include_analysis=True
    )
    
    if recommendation:
        return recommendation.stock_suggestions
    return []

def get_top_industry_opportunities(max_industries: int = 5, max_stocks_per_industry: int = 5) -> list:
    """
    Lấy top cơ hội đầu tư theo ngành.
    
    Args:
        max_industries: Số ngành tối đa
        max_stocks_per_industry: Số cổ phiếu tối đa mỗi ngành
        
    Returns:
        Danh sách top cơ hội đầu tư
    """
    advisor = IndustryStockAdvisor()
    return advisor.get_top_industry_opportunities(
        max_industries=max_industries,
        max_stocks_per_industry=max_stocks_per_industry
    )

def compare_industries(industries: list, max_stocks_per_industry: int = 5) -> list:
    """
    So sánh nhiều ngành và đưa ra khuyến nghị.
    
    Args:
        industries: Danh sách ngành cần so sánh
        max_stocks_per_industry: Số cổ phiếu tối đa mỗi ngành
        
    Returns:
        Danh sách khuyến nghị được sắp xếp theo tiềm năng
    """
    advisor = IndustryStockAdvisor()
    return advisor.compare_industries(
        industries=industries,
        max_stocks_per_industry=max_stocks_per_industry
    )

def get_available_industries() -> list:
    """
    Lấy danh sách các ngành có sẵn.
    
    Returns:
        Danh sách tên ngành
    """
    advisor = IndustryStockAdvisor()
    return advisor.get_available_industries()

def quick_scan_and_rank(symbols: list = None, min_score: float = 6.0) -> dict:
    """
    Scan nhanh và xếp hạng cổ phiếu.
    
    Args:
        symbols: Danh sách mã cổ phiếu (None = scan thị trường)
        min_score: Điểm tối thiểu
        
    Returns:
        Dict chứa scan results và rankings
    """
    # Scan
    if symbols:
        scan_results = scan_custom_list(symbols, min_score)
    else:
        scan_results = quick_scan_market(min_score)
    
    if not scan_results:
        return {"scan_results": [], "rankings": [], "opportunities": {}}
    
    # Convert to dict format for ranking
    scan_data = []
    for result in scan_results:
        scan_data.append({
            "symbol": result.symbol,
            "company_name": result.company_name,
            "industry": result.industry,
            "pb_ratio": result.pb_ratio,
            "pe_ratio": result.pe_ratio,
            "rsi": result.rsi,
            "macd_signal": result.macd_signal,
            "ma_trend": result.ma_trend,
            "volume_trend": result.volume_trend,
            "value_score": result.value_score,
            "momentum_score": result.momentum_score,
            "overall_score": result.overall_score,
            "roe": 15.0  # Mock ROE for compatibility
        })
    
    # Rank
    rankings = rank_scan_results(scan_data)
    
    # Find opportunities
    opportunities = find_best_opportunities(scan_data)
    
    return {
        "scan_results": scan_results,
        "rankings": rankings,
        "opportunities": opportunities
    }

def find_opportunities(scan_results: list) -> dict:
    """
    Tìm cơ hội đầu tư từ kết quả scan.
    
    Args:
        scan_results: Kết quả từ lightweight scanner
        
    Returns:
        Dict chứa các cơ hội được phân loại
    """
    if not scan_results:
        return {}
    
    # Convert to dict format
    scan_data = []
    for result in scan_results:
        scan_data.append({
            "symbol": result.symbol,
            "pb_ratio": result.pb_ratio,
            "pe_ratio": result.pe_ratio,
            "rsi": result.rsi,
            "macd_signal": result.macd_signal,
            "ma_trend": result.ma_trend,
            "volume_trend": result.volume_trend,
            "industry": result.industry,
            "roe": 15.0  # Mock
        })
    
    return find_best_opportunities(scan_data)

def get_analysis_priorities(scan_results: list) -> dict:
    """
    Lấy danh sách ưu tiên phân tích chuyên sâu.
    
    Args:
        scan_results: Kết quả scan
        
    Returns:
        Dict chứa priority queue
    """
    if not scan_results:
        return {}
    
    # Convert format
    scan_data = []
    for result in scan_results:
        scan_data.append({
            "symbol": result.symbol,
            "company_name": result.company_name,
            "industry": result.industry,
            "pb_ratio": result.pb_ratio,
            "pe_ratio": result.pe_ratio,
            "rsi": result.rsi,
            "macd_signal": result.macd_signal,
            "ma_trend": result.ma_trend,
            "volume_trend": result.volume_trend,
            "value_score": result.value_score,
            "momentum_score": result.momentum_score,
            "overall_score": result.overall_score,
            "roe": 15.0
        })
    
    return get_priority_analysis_queue(scan_data)

# Export all components
__all__ = [
    # Core classes
    "LightweightStockScanner",
    "LightweightScanResult", 
    "ScreeningEngine",
    "ScreeningCriteria",
    "ScreeningFilter",
    "TokenOptimizer",
    "BatchStockProcessor",
    "TokenUsageStats",
    "PriorityRankingSystem",
    "PriorityLevel",
    "RankedStock",
    
    # Quick functions
    "quick_scan_market",
    "scan_custom_list",
    "quick_screen_value_stocks",
    "quick_screen_momentum_stocks",
    "find_best_opportunities",
    "batch_analyze_stocks",
    "create_optimized_scanner",
    "rank_scan_results",
    "get_priority_analysis_queue",
    
    # Convenience functions
    "quick_scan_and_rank",
    "find_opportunities",
    "get_analysis_priorities"
]