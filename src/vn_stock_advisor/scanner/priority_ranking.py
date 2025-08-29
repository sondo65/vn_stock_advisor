"""
Priority Ranking System - Hệ thống xếp hạng ưu tiên

Xếp hạng cổ phiếu để ưu tiên phân tích chuyên sâu dựa trên:
1. Tiềm năng tăng trưởng
2. Rủi ro/Reward ratio
3. Momentum và timing
4. Chất lượng dữ liệu
5. Market conditions
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
import math

class PriorityLevel(Enum):
    """Mức độ ưu tiên."""
    CRITICAL = 1    # Phân tích ngay lập tức
    HIGH = 2        # Phân tích trong 1 giờ
    MEDIUM = 3      # Phân tích trong ngày
    LOW = 4         # Phân tích khi rảnh
    SKIP = 5        # Bỏ qua

@dataclass
class RankingFactors:
    """Các yếu tố để xếp hạng."""
    
    # Định giá và giá trị
    value_score: float = 0.0        # 0-10, P/B, P/E so với ngành
    undervaluation_degree: float = 0.0  # % undervalued
    
    # Momentum và kỹ thuật
    momentum_score: float = 0.0     # 0-10, từ RSI, MACD, MA
    breakout_potential: float = 0.0 # 0-10, khả năng breakout
    volume_strength: float = 0.0    # 0-10, sức mạnh volume
    
    # Cơ bản và chất lượng
    quality_score: float = 0.0      # 0-10, ROE, growth, stability
    financial_health: float = 0.0   # 0-10, debt, cash flow
    
    # Timing và catalyst
    timing_score: float = 0.0       # 0-10, thời điểm vào lệnh
    catalyst_potential: float = 0.0 # 0-10, có catalyst sắp tới không
    
    # Risk factors
    volatility_risk: float = 5.0    # 0-10, 10 = rủi ro cao
    liquidity_risk: float = 5.0     # 0-10, 10 = thanh khoản thấp
    sector_risk: float = 5.0        # 0-10, rủi ro ngành

@dataclass
class RankedStock:
    """Cổ phiếu đã được xếp hạng."""
    symbol: str
    company_name: str
    industry: str
    
    # Ranking results
    priority_level: PriorityLevel
    overall_score: float
    ranking_factors: RankingFactors
    
    # Analysis recommendations
    recommended_analysis_type: str  # "full", "technical", "fundamental"
    estimated_analysis_time: int   # minutes
    confidence_level: float        # 0-1
    
    # Metadata
    ranked_at: datetime
    expires_at: datetime
    notes: List[str] = field(default_factory=list)

class PriorityRankingSystem:
    """Hệ thống xếp hạng ưu tiên cho phân tích chuyên sâu."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Trọng số cho các yếu tố ranking
        self.ranking_weights = {
            "value": 0.25,          # 25% - Định giá
            "momentum": 0.20,       # 20% - Momentum
            "quality": 0.20,        # 20% - Chất lượng cơ bản
            "timing": 0.15,         # 15% - Timing
            "risk_adjusted": 0.20   # 20% - Điều chỉnh rủi ro
        }
        
        # Threshold cho các mức ưu tiên
        self.priority_thresholds = {
            PriorityLevel.CRITICAL: 8.5,   # Score >= 8.5
            PriorityLevel.HIGH: 7.0,       # Score >= 7.0
            PriorityLevel.MEDIUM: 5.5,     # Score >= 5.5
            PriorityLevel.LOW: 4.0,        # Score >= 4.0
            PriorityLevel.SKIP: 0.0        # Score < 4.0
        }
        
        # Industry risk multipliers
        self.industry_risk_factors = {
            "Banking": 1.2,           # Rủi ro cao hơn do regulation
            "Real Estate": 1.3,       # Rủi ro market cycle
            "Technology": 1.1,        # Volatility cao
            "Energy": 1.4,           # Commodity price risk
            "Healthcare": 0.9,        # Defensive sector
            "Consumer Staples": 0.8,  # Ổn định
            "Default": 1.0
        }
    
    def extract_ranking_factors_from_scan_data(self, scan_data: Dict) -> RankingFactors:
        """
        Trích xuất các yếu tố ranking từ dữ liệu scan.
        
        Args:
            scan_data: Dữ liệu từ lightweight scanner
            
        Returns:
            RankingFactors object
        """
        factors = RankingFactors()
        
        try:
            # Value factors
            factors.value_score = scan_data.get("value_score", 0.0)
            pb_ratio = scan_data.get("pb_ratio", 0)
            industry = scan_data.get("industry", "Default")
            
            # Calculate undervaluation degree
            industry_pb_benchmark = {
                "Real Estate": 1.9, "Banking": 1.3, "Technology": 3.0,
                "Default": 2.0
            }.get(industry, 2.0)
            
            if pb_ratio > 0:
                factors.undervaluation_degree = max(0, (industry_pb_benchmark - pb_ratio) / industry_pb_benchmark * 100)
            
            # Momentum factors
            factors.momentum_score = scan_data.get("momentum_score", 0.0)
            
            # RSI-based breakout potential
            rsi = scan_data.get("rsi", 50)
            if 45 <= rsi <= 65:  # Sweet spot for breakout
                factors.breakout_potential = 8.0
            elif 35 <= rsi <= 75:
                factors.breakout_potential = 6.0
            else:
                factors.breakout_potential = 3.0
            
            # Volume strength
            volume_trend = scan_data.get("volume_trend", "normal")
            if volume_trend == "increasing":
                factors.volume_strength = 8.0
            elif volume_trend == "normal":
                factors.volume_strength = 5.0
            else:
                factors.volume_strength = 2.0
            
            # Quality factors (simplified)
            factors.quality_score = scan_data.get("overall_score", 0.0) * 0.8  # Scale down
            
            pe_ratio = scan_data.get("pe_ratio", 0)
            if 5 <= pe_ratio <= 20:
                factors.financial_health = 7.0
            elif pe_ratio > 0:
                factors.financial_health = 5.0
            else:
                factors.financial_health = 3.0
            
            # Timing factors
            macd_signal = scan_data.get("macd_signal", "neutral")
            ma_trend = scan_data.get("ma_trend", "sideways")
            
            timing_score = 5.0  # Base
            if macd_signal == "positive":
                timing_score += 2.0
            if ma_trend == "upward":
                timing_score += 2.0
            if rsi < 35:  # Oversold opportunity
                timing_score += 1.5
            
            factors.timing_score = min(10.0, timing_score)
            
            # Risk factors
            factors.volatility_risk = self._estimate_volatility_risk(scan_data)
            factors.liquidity_risk = self._estimate_liquidity_risk(scan_data)
            factors.sector_risk = self._get_sector_risk(industry)
            
        except Exception as e:
            self.logger.warning(f"Error extracting ranking factors: {e}")
        
        return factors
    
    def _estimate_volatility_risk(self, scan_data: Dict) -> float:
        """Ước tính rủi ro volatility."""
        rsi = scan_data.get("rsi", 50)
        
        # RSI extreme values indicate higher volatility
        if rsi > 80 or rsi < 20:
            return 8.0
        elif rsi > 70 or rsi < 30:
            return 6.0
        else:
            return 4.0  # Normal volatility
    
    def _estimate_liquidity_risk(self, scan_data: Dict) -> float:
        """Ước tính rủi ro thanh khoản."""
        volume_trend = scan_data.get("volume_trend", "normal")
        
        if volume_trend == "decreasing":
            return 7.0  # Higher liquidity risk
        elif volume_trend == "normal":
            return 4.0  # Medium risk
        else:
            return 2.0  # Low risk
    
    def _get_sector_risk(self, industry: str) -> float:
        """Lấy rủi ro ngành."""
        risk_multiplier = self.industry_risk_factors.get(industry, 1.0)
        base_risk = 5.0
        return min(10.0, base_risk * risk_multiplier)
    
    def calculate_overall_score(self, factors: RankingFactors) -> float:
        """
        Tính điểm tổng thể cho ranking.
        
        Args:
            factors: Các yếu tố ranking
            
        Returns:
            Điểm từ 0-10
        """
        # Component scores
        value_component = (factors.value_score + factors.undervaluation_degree / 10) / 2
        
        momentum_component = (
            factors.momentum_score * 0.4 + 
            factors.breakout_potential * 0.3 + 
            factors.volume_strength * 0.3
        )
        
        quality_component = (factors.quality_score + factors.financial_health) / 2
        
        timing_component = (factors.timing_score + factors.catalyst_potential) / 2
        
        # Risk adjustment (lower risk = higher score)
        risk_penalty = (
            factors.volatility_risk * 0.4 + 
            factors.liquidity_risk * 0.3 + 
            factors.sector_risk * 0.3
        ) / 10  # Normalize to 0-1
        
        risk_adjusted_component = max(0, 10 - risk_penalty * 10)
        
        # Weighted combination
        overall_score = (
            value_component * self.ranking_weights["value"] +
            momentum_component * self.ranking_weights["momentum"] +
            quality_component * self.ranking_weights["quality"] +
            timing_component * self.ranking_weights["timing"] +
            risk_adjusted_component * self.ranking_weights["risk_adjusted"]
        )
        
        return min(10.0, max(0.0, overall_score))
    
    def determine_priority_level(self, overall_score: float, factors: RankingFactors) -> PriorityLevel:
        """
        Xác định mức độ ưu tiên.
        
        Args:
            overall_score: Điểm tổng thể
            factors: Các yếu tố ranking
            
        Returns:
            Mức độ ưu tiên
        """
        # Base priority từ score
        for priority, threshold in self.priority_thresholds.items():
            if overall_score >= threshold:
                base_priority = priority
                break
        else:
            base_priority = PriorityLevel.SKIP
        
        # Adjustments based on special conditions
        if factors.breakout_potential >= 8.0 and factors.volume_strength >= 7.0:
            # Potential breakout - increase priority
            if base_priority.value > PriorityLevel.HIGH.value:
                base_priority = PriorityLevel.HIGH
        
        if factors.undervaluation_degree >= 30:  # Significantly undervalued
            if base_priority.value > PriorityLevel.MEDIUM.value:
                base_priority = PriorityLevel.MEDIUM
        
        # Risk-based downgrade
        avg_risk = (factors.volatility_risk + factors.liquidity_risk + factors.sector_risk) / 3
        if avg_risk >= 8.0 and base_priority.value <= PriorityLevel.MEDIUM.value:
            # High risk - downgrade priority
            base_priority = PriorityLevel(min(PriorityLevel.LOW.value, base_priority.value + 1))
        
        return base_priority
    
    def recommend_analysis_type(self, priority_level: PriorityLevel, factors: RankingFactors) -> Tuple[str, int]:
        """
        Khuyến nghị loại phân tích và thời gian ước tính.
        
        Args:
            priority_level: Mức độ ưu tiên
            factors: Các yếu tố ranking
            
        Returns:
            (analysis_type, estimated_minutes)
        """
        if priority_level == PriorityLevel.CRITICAL:
            return "full", 45  # Full analysis
        elif priority_level == PriorityLevel.HIGH:
            if factors.momentum_score > factors.value_score:
                return "technical", 20
            else:
                return "fundamental", 25
        elif priority_level == PriorityLevel.MEDIUM:
            return "technical", 15
        elif priority_level == PriorityLevel.LOW:
            return "technical", 10
        else:
            return "skip", 0
    
    def generate_analysis_notes(self, factors: RankingFactors, priority_level: PriorityLevel) -> List[str]:
        """Tạo ghi chú cho phân tích."""
        notes = []
        
        if factors.undervaluation_degree >= 20:
            notes.append(f"Undervalued by ~{factors.undervaluation_degree:.1f}% vs industry")
        
        if factors.breakout_potential >= 7.0:
            notes.append("High breakout potential - watch for volume confirmation")
        
        if factors.momentum_score >= 8.0:
            notes.append("Strong momentum - consider technical analysis priority")
        
        if factors.timing_score >= 8.0:
            notes.append("Excellent timing for entry")
        
        avg_risk = (factors.volatility_risk + factors.liquidity_risk + factors.sector_risk) / 3
        if avg_risk >= 7.0:
            notes.append("Higher risk profile - implement strict stop-loss")
        
        if priority_level == PriorityLevel.CRITICAL:
            notes.append("⚡ CRITICAL: Analyze immediately")
        elif priority_level == PriorityLevel.HIGH:
            notes.append("🔥 HIGH PRIORITY: Analyze within 1 hour")
        
        return notes
    
    def rank_stocks(self, scan_results: List[Dict]) -> List[RankedStock]:
        """
        Xếp hạng danh sách cổ phiếu.
        
        Args:
            scan_results: Kết quả từ lightweight scanner
            
        Returns:
            Danh sách cổ phiếu đã xếp hạng
        """
        ranked_stocks = []
        
        for scan_data in scan_results:
            try:
                # Extract factors
                factors = self.extract_ranking_factors_from_scan_data(scan_data)
                
                # Calculate overall score
                overall_score = self.calculate_overall_score(factors)
                
                # Determine priority
                priority_level = self.determine_priority_level(overall_score, factors)
                
                # Analysis recommendation
                analysis_type, estimated_time = self.recommend_analysis_type(priority_level, factors)
                
                # Generate notes
                notes = self.generate_analysis_notes(factors, priority_level)
                
                # Calculate confidence
                confidence = min(0.95, 0.5 + (overall_score / 20))
                
                # Create ranked stock
                ranked_stock = RankedStock(
                    symbol=scan_data.get("symbol", ""),
                    company_name=scan_data.get("company_name", ""),
                    industry=scan_data.get("industry", ""),
                    priority_level=priority_level,
                    overall_score=overall_score,
                    ranking_factors=factors,
                    recommended_analysis_type=analysis_type,
                    estimated_analysis_time=estimated_time,
                    confidence_level=confidence,
                    ranked_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=4),  # Rankings expire in 4 hours
                    notes=notes
                )
                
                ranked_stocks.append(ranked_stock)
                
            except Exception as e:
                self.logger.error(f"Error ranking stock {scan_data.get('symbol', 'unknown')}: {e}")
        
        # Sort by priority and score
        ranked_stocks.sort(key=lambda x: (x.priority_level.value, -x.overall_score))
        
        return ranked_stocks
    
    def get_priority_queue(self, ranked_stocks: List[RankedStock]) -> Dict[PriorityLevel, List[RankedStock]]:
        """Tạo priority queue từ danh sách ranked stocks."""
        priority_queue = {level: [] for level in PriorityLevel}
        
        for stock in ranked_stocks:
            priority_queue[stock.priority_level].append(stock)
        
        return priority_queue
    
    def generate_ranking_report(self, ranked_stocks: List[RankedStock]) -> str:
        """Tạo báo cáo ranking."""
        if not ranked_stocks:
            return "📊 **STOCK RANKING REPORT**\n\nNo stocks to rank."
        
        report = ["📊 **STOCK RANKING REPORT**"]
        report.append("=" * 50)
        report.append(f"🕒 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📈 Total stocks ranked: {len(ranked_stocks)}")
        report.append("")
        
        # Priority breakdown
        priority_counts = {}
        for stock in ranked_stocks:
            priority_counts[stock.priority_level] = priority_counts.get(stock.priority_level, 0) + 1
        
        report.append("## 🎯 **PRIORITY BREAKDOWN**")
        for priority in PriorityLevel:
            count = priority_counts.get(priority, 0)
            if count > 0:
                emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "SKIP": "⚪"}.get(priority.name, "")
                report.append(f"• {emoji} {priority.name}: {count} stocks")
        report.append("")
        
        # Top recommendations by priority
        for priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM]:
            priority_stocks = [s for s in ranked_stocks if s.priority_level == priority]
            if priority_stocks:
                report.append(f"## {priority.name} PRIORITY STOCKS")
                for stock in priority_stocks[:5]:  # Top 5 per category
                    report.append(f"**{stock.symbol}** - Score: {stock.overall_score:.1f}/10")
                    report.append(f"   Analysis: {stock.recommended_analysis_type} ({stock.estimated_analysis_time}min)")
                    if stock.notes:
                        report.append(f"   Notes: {stock.notes[0]}")
                    report.append("")
        
        # Summary statistics
        avg_score = sum(s.overall_score for s in ranked_stocks) / len(ranked_stocks)
        total_analysis_time = sum(s.estimated_analysis_time for s in ranked_stocks if s.priority_level != PriorityLevel.SKIP)
        
        report.append("## 📊 **SUMMARY STATISTICS**")
        report.append(f"• Average Score: {avg_score:.1f}/10")
        report.append(f"• Total Analysis Time Needed: {total_analysis_time} minutes")
        report.append(f"• High Priority Stocks: {len([s for s in ranked_stocks if s.priority_level.value <= 2])}")
        
        return "\n".join(report)

# Convenience functions
def rank_scan_results(scan_results: List[Dict]) -> List[RankedStock]:
    """Xếp hạng kết quả scan."""
    ranking_system = PriorityRankingSystem()
    return ranking_system.rank_stocks(scan_results)

def get_priority_analysis_queue(scan_results: List[Dict]) -> Dict[PriorityLevel, List[RankedStock]]:
    """Lấy queue ưu tiên phân tích."""
    ranked_stocks = rank_scan_results(scan_results)
    ranking_system = PriorityRankingSystem()
    return ranking_system.get_priority_queue(ranked_stocks)
