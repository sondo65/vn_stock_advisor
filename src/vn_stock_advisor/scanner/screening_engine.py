"""
Screening Engine - Bộ lọc cổ phiếu thông minh

Tối ưu hóa việc lọc cổ phiếu dựa trên:
1. Giá trị vs giá thị trường (P/B, P/E)
2. Momentum kỹ thuật (RSI, MACD, MA)
3. Chất lượng và thanh khoản
4. Tiềm năng tăng trưởng
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

class ScreeningCriteria(Enum):
    """Các tiêu chí lọc cổ phiếu."""
    
    # Định giá
    UNDERVALUED_PB = "pb_undervalued"      # P/B thấp so với ngành
    REASONABLE_PE = "pe_reasonable"        # P/E hợp lý (5-25)
    VALUE_STOCK = "value_stock"           # Cổ phiếu giá trị
    
    # Momentum kỹ thuật
    STRONG_MOMENTUM = "strong_momentum"    # Momentum mạnh
    OVERSOLD_RSI = "oversold_rsi"         # RSI quá bán (cơ hội)
    MACD_POSITIVE = "macd_positive"       # MACD tích cực
    UPWARD_TREND = "upward_trend"         # Xu hướng tăng
    
    # Chất lượng
    HIGH_ROE = "high_roe"                 # ROE cao (>15%)
    GOOD_LIQUIDITY = "good_liquidity"     # Thanh khoản tốt
    STABLE_GROWTH = "stable_growth"       # Tăng trưởng ổn định
    
    # Đặc biệt
    BREAKOUT_CANDIDATE = "breakout"       # Ứng viên breakout
    DIVIDEND_YIELD = "dividend_yield"     # Cổ tức cao
    SMALL_CAP_GROWTH = "small_cap_growth" # Small cap tiềm năng

@dataclass
class ScreeningFilter:
    """Bộ lọc với các tiêu chí cụ thể."""
    name: str
    criteria: List[ScreeningCriteria]
    min_score: float
    max_results: int
    description: str

class ScreeningEngine:
    """Bộ máy lọc cổ phiếu thông minh."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Định nghĩa các bộ lọc sẵn có
        self.predefined_filters = {
            "value_opportunities": ScreeningFilter(
                name="Value Opportunities",
                criteria=[
                    ScreeningCriteria.UNDERVALUED_PB,
                    ScreeningCriteria.REASONABLE_PE,
                    ScreeningCriteria.HIGH_ROE
                ],
                min_score=7.0,
                max_results=10,
                description="Cổ phiếu có giá trị, định giá hấp dẫn"
            ),
            
            "momentum_plays": ScreeningFilter(
                name="Momentum Plays",
                criteria=[
                    ScreeningCriteria.STRONG_MOMENTUM,
                    ScreeningCriteria.MACD_POSITIVE,
                    ScreeningCriteria.UPWARD_TREND
                ],
                min_score=6.5,
                max_results=15,
                description="Cổ phiếu có momentum mạnh, xu hướng tăng"
            ),
            
            "oversold_bounce": ScreeningFilter(
                name="Oversold Bounce",
                criteria=[
                    ScreeningCriteria.OVERSOLD_RSI,
                    ScreeningCriteria.VALUE_STOCK,
                    ScreeningCriteria.GOOD_LIQUIDITY
                ],
                min_score=6.0,
                max_results=12,
                description="Cổ phiếu quá bán, có cơ hội phục hồi"
            ),
            
            "quality_growth": ScreeningFilter(
                name="Quality Growth",
                criteria=[
                    ScreeningCriteria.HIGH_ROE,
                    ScreeningCriteria.STABLE_GROWTH,
                    ScreeningCriteria.REASONABLE_PE
                ],
                min_score=7.5,
                max_results=8,
                description="Cổ phiếu chất lượng cao, tăng trưởng ổn định"
            ),
            
            "breakout_candidates": ScreeningFilter(
                name="Breakout Candidates",
                criteria=[
                    ScreeningCriteria.BREAKOUT_CANDIDATE,
                    ScreeningCriteria.STRONG_MOMENTUM,
                    ScreeningCriteria.GOOD_LIQUIDITY
                ],
                min_score=6.8,
                max_results=10,
                description="Ứng viên breakout, volume tốt"
            )
        }
        
        # Trọng số cho từng tiêu chí
        self.criteria_weights = {
            ScreeningCriteria.UNDERVALUED_PB: 2.5,
            ScreeningCriteria.REASONABLE_PE: 2.0,
            ScreeningCriteria.VALUE_STOCK: 2.2,
            ScreeningCriteria.STRONG_MOMENTUM: 2.8,
            ScreeningCriteria.OVERSOLD_RSI: 2.0,
            ScreeningCriteria.MACD_POSITIVE: 2.3,
            ScreeningCriteria.UPWARD_TREND: 2.5,
            ScreeningCriteria.HIGH_ROE: 2.0,
            ScreeningCriteria.GOOD_LIQUIDITY: 1.5,
            ScreeningCriteria.STABLE_GROWTH: 1.8,
            ScreeningCriteria.BREAKOUT_CANDIDATE: 3.0,
            ScreeningCriteria.DIVIDEND_YIELD: 1.2,
            ScreeningCriteria.SMALL_CAP_GROWTH: 2.2
        }
    
    def evaluate_stock_against_criteria(self, stock_data: Dict, criteria: ScreeningCriteria) -> Tuple[bool, float]:
        """
        Đánh giá một cổ phiếu theo tiêu chí cụ thể.
        
        Args:
            stock_data: Dữ liệu cổ phiếu từ lightweight scanner
            criteria: Tiêu chí đánh giá
            
        Returns:
            (meets_criteria, score_contribution)
        """
        try:
            pb_ratio = stock_data.get("pb_ratio", 0)
            pe_ratio = stock_data.get("pe_ratio", 0)
            rsi = stock_data.get("rsi", 50)
            roe = stock_data.get("roe", 0)
            macd_signal = stock_data.get("macd_signal", "neutral")
            ma_trend = stock_data.get("ma_trend", "sideways")
            volume_trend = stock_data.get("volume_trend", "normal")
            industry = stock_data.get("industry", "Default")
            
            # Industry benchmarks
            industry_pb_benchmarks = {
                "Real Estate": 1.9, "Banking": 1.3, "Technology": 3.0,
                "Manufacturing": 2.0, "Retail": 2.5, "Default": 2.0
            }
            
            if criteria == ScreeningCriteria.UNDERVALUED_PB:
                benchmark = industry_pb_benchmarks.get(industry, 2.0)
                if 0 < pb_ratio <= benchmark * 0.8:
                    return True, 3.0
                elif 0 < pb_ratio <= benchmark:
                    return True, 2.0
                return False, 0.0
            
            elif criteria == ScreeningCriteria.REASONABLE_PE:
                if 5 <= pe_ratio <= 25:
                    if pe_ratio <= 15:
                        return True, 2.5
                    else:
                        return True, 1.5
                return False, 0.0
            
            elif criteria == ScreeningCriteria.VALUE_STOCK:
                # Kết hợp P/B và P/E
                pb_good = 0 < pb_ratio <= 2.5
                pe_good = 5 <= pe_ratio <= 20
                if pb_good and pe_good:
                    return True, 2.5
                elif pb_good or pe_good:
                    return True, 1.5
                return False, 0.0
            
            elif criteria == ScreeningCriteria.STRONG_MOMENTUM:
                momentum_score = 0
                if macd_signal == "positive":
                    momentum_score += 1.5
                if ma_trend == "upward":
                    momentum_score += 1.5
                if volume_trend == "increasing":
                    momentum_score += 1.0
                
                if momentum_score >= 2.5:
                    return True, 3.0
                elif momentum_score >= 1.5:
                    return True, 2.0
                return False, 0.0
            
            elif criteria == ScreeningCriteria.OVERSOLD_RSI:
                if rsi <= 30:
                    return True, 3.0
                elif rsi <= 35:
                    return True, 2.0
                return False, 0.0
            
            elif criteria == ScreeningCriteria.MACD_POSITIVE:
                if macd_signal == "positive":
                    return True, 2.5
                return False, 0.0
            
            elif criteria == ScreeningCriteria.UPWARD_TREND:
                if ma_trend == "upward":
                    return True, 2.5
                return False, 0.0
            
            elif criteria == ScreeningCriteria.HIGH_ROE:
                if roe >= 20:
                    return True, 3.0
                elif roe >= 15:
                    return True, 2.0
                elif roe >= 10:
                    return True, 1.0
                return False, 0.0
            
            elif criteria == ScreeningCriteria.GOOD_LIQUIDITY:
                # Simplified liquidity check based on volume trend
                if volume_trend == "increasing":
                    return True, 2.0
                elif volume_trend == "normal":
                    return True, 1.0
                return False, 0.0
            
            elif criteria == ScreeningCriteria.BREAKOUT_CANDIDATE:
                # Breakout: RSI 50-70, MACD positive, volume increasing
                breakout_score = 0
                if 50 <= rsi <= 70:
                    breakout_score += 1.5
                if macd_signal == "positive":
                    breakout_score += 1.5
                if volume_trend == "increasing":
                    breakout_score += 1.5
                
                if breakout_score >= 3.0:
                    return True, 3.5
                elif breakout_score >= 2.0:
                    return True, 2.5
                return False, 0.0
            
            else:
                # Default case for other criteria
                return False, 0.0
        
        except Exception as e:
            self.logger.warning(f"Error evaluating criteria {criteria}: {e}")
            return False, 0.0
    
    def calculate_filter_score(self, stock_data: Dict, screening_filter: ScreeningFilter) -> float:
        """
        Tính điểm của cổ phiếu theo bộ lọc cụ thể.
        
        Args:
            stock_data: Dữ liệu cổ phiếu
            screening_filter: Bộ lọc áp dụng
            
        Returns:
            Điểm số từ 0-10
        """
        total_score = 0.0
        total_weight = 0.0
        criteria_met = 0
        
        for criteria in screening_filter.criteria:
            meets_criteria, score_contribution = self.evaluate_stock_against_criteria(stock_data, criteria)
            weight = self.criteria_weights.get(criteria, 1.0)
            
            if meets_criteria:
                total_score += score_contribution * weight
                criteria_met += 1
            
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # Normalize score to 0-10 range
        normalized_score = (total_score / total_weight) * 3.33  # Scale to ~10
        
        # Bonus for meeting multiple criteria
        criteria_bonus = (criteria_met / len(screening_filter.criteria)) * 2.0
        
        final_score = min(10.0, normalized_score + criteria_bonus)
        return final_score
    
    def apply_filter(self, stocks_data: List[Dict], filter_name: str) -> List[Dict]:
        """
        Áp dụng bộ lọc lên danh sách cổ phiếu.
        
        Args:
            stocks_data: Danh sách dữ liệu cổ phiếu
            filter_name: Tên bộ lọc
            
        Returns:
            Danh sách cổ phiếu đã lọc và sắp xếp
        """
        if filter_name not in self.predefined_filters:
            self.logger.error(f"Unknown filter: {filter_name}")
            return []
        
        screening_filter = self.predefined_filters[filter_name]
        results = []
        
        for stock_data in stocks_data:
            filter_score = self.calculate_filter_score(stock_data, screening_filter)
            
            if filter_score >= screening_filter.min_score:
                stock_result = stock_data.copy()
                stock_result["filter_score"] = filter_score
                stock_result["filter_name"] = filter_name
                results.append(stock_result)
        
        # Sắp xếp theo điểm giảm dần
        results.sort(key=lambda x: x["filter_score"], reverse=True)
        
        # Giới hạn số kết quả
        return results[:screening_filter.max_results]
    
    def multi_filter_analysis(self, stocks_data: List[Dict], 
                            filter_names: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Áp dụng nhiều bộ lọc cùng lúc.
        
        Args:
            stocks_data: Danh sách dữ liệu cổ phiếu
            filter_names: Danh sách tên bộ lọc (None = tất cả)
            
        Returns:
            Dictionary với kết quả từng bộ lọc
        """
        if filter_names is None:
            filter_names = list(self.predefined_filters.keys())
        
        results = {}
        for filter_name in filter_names:
            results[filter_name] = self.apply_filter(stocks_data, filter_name)
            self.logger.info(f"Filter '{filter_name}': {len(results[filter_name])} stocks found")
        
        return results
    
    def get_top_opportunities(self, stocks_data: List[Dict], 
                            top_n: int = 5) -> Dict[str, List[Dict]]:
        """
        Tìm top cơ hội đầu tư từ tất cả bộ lọc.
        
        Args:
            stocks_data: Danh sách dữ liệu cổ phiếu
            top_n: Số lượng top picks cho mỗi category
            
        Returns:
            Dictionary với top picks từng loại
        """
        all_results = self.multi_filter_analysis(stocks_data)
        
        top_opportunities = {}
        for filter_name, results in all_results.items():
            if results:
                top_opportunities[filter_name] = results[:top_n]
        
        # Tạo danh sách tổng hợp (unique stocks)
        all_stocks = {}
        for filter_name, results in top_opportunities.items():
            for stock in results:
                symbol = stock["symbol"]
                if symbol not in all_stocks or stock["filter_score"] > all_stocks[symbol]["filter_score"]:
                    all_stocks[symbol] = stock
        
        # Top overall
        overall_top = sorted(all_stocks.values(), key=lambda x: x["filter_score"], reverse=True)
        top_opportunities["overall_top"] = overall_top[:top_n * 2]
        
        return top_opportunities
    
    def generate_screening_report(self, screening_results: Dict[str, List[Dict]]) -> str:
        """Tạo báo cáo kết quả screening."""
        report = ["🔍 **STOCK SCREENING REPORT**"]
        report.append("=" * 60)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for filter_name, results in screening_results.items():
            if not results:
                continue
            
            filter_obj = self.predefined_filters.get(filter_name)
            if filter_obj:
                report.append(f"## 📊 {filter_obj.name}")
                report.append(f"*{filter_obj.description}*")
                report.append("")
            
            for i, stock in enumerate(results[:5], 1):
                report.append(
                    f"{i}. **{stock['symbol']}** - Score: {stock['filter_score']:.1f}/10"
                )
                report.append(
                    f"   P/B: {stock.get('pb_ratio', 0):.2f}, "
                    f"P/E: {stock.get('pe_ratio', 0):.1f}, "
                    f"RSI: {stock.get('rsi', 0):.1f}"
                )
            report.append("")
        
        return "\n".join(report)

# Convenience functions
def quick_screen_value_stocks(stocks_data: List[Dict]) -> List[Dict]:
    """Nhanh chóng lọc cổ phiếu giá trị."""
    engine = ScreeningEngine()
    return engine.apply_filter(stocks_data, "value_opportunities")

def quick_screen_momentum_stocks(stocks_data: List[Dict]) -> List[Dict]:
    """Nhanh chóng lọc cổ phiếu momentum."""
    engine = ScreeningEngine()
    return engine.apply_filter(stocks_data, "momentum_plays")

def find_best_opportunities(stocks_data: List[Dict]) -> Dict[str, List[Dict]]:
    """Tìm các cơ hội đầu tư tốt nhất."""
    engine = ScreeningEngine()
    return engine.get_top_opportunities(stocks_data)
