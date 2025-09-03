"""
Industry Analyzer - Phân tích và so sánh ngành

Chức năng:
1. Phân tích xu hướng ngành
2. So sánh hiệu suất giữa các ngành
3. Xác định ngành có tiềm năng nhất
4. Phân tích chu kỳ ngành
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from .industry_suggester import IndustryStockSuggester, IndustryBenchmark
from .lightweight_scanner import LightweightStockScanner

class IndustryTrend(Enum):
    """Xu hướng ngành"""
    BULLISH = "bullish"      # Tăng trưởng mạnh
    NEUTRAL = "neutral"      # Ổn định
    BEARISH = "bearish"      # Suy giảm
    VOLATILE = "volatile"    # Biến động cao

@dataclass
class IndustryAnalysis:
    """Phân tích tổng quan ngành"""
    industry: str
    trend: IndustryTrend
    momentum_score: float      # 0-10
    value_score: float         # 0-10
    quality_score: float       # 0-10
    overall_score: float       # 0-10
    
    # Thống kê
    avg_pe: float
    avg_pb: float
    avg_roe: float
    market_cap_total: float
    stock_count: int
    
    # Phân tích
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    
    # Khuyến nghị
    recommendation: str        # "OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT"
    confidence: float          # 0-1
    top_picks: List[str]       # Top 3 cổ phiếu
    analysis_date: datetime

class IndustryAnalyzer:
    """Phân tích và so sánh các ngành"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.suggester = IndustryStockSuggester()
        self.scanner = LightweightStockScanner(max_workers=1, use_cache=True)
        
        # Industry cycle patterns
        self.industry_cycles = {
            "Tài chính ngân hàng": {"cycle_length": 4, "current_phase": "recovery"},
            "Bất động sản": {"cycle_length": 5, "current_phase": "consolidation"},
            "Phần mềm và dịch vụ công nghệ thông tin": {"cycle_length": 3, "current_phase": "growth"},
            "Kim loại và khai khoáng": {"cycle_length": 6, "current_phase": "recovery"},
            "Dược phẩm": {"cycle_length": 4, "current_phase": "stable"},
            "Thực phẩm và thuốc lá": {"cycle_length": 2, "current_phase": "stable"},
            "Dầu và khí đốt": {"cycle_length": 7, "current_phase": "volatile"},
            "Ngành điện": {"cycle_length": 5, "current_phase": "stable"}
        }
    
    def analyze_industry(self, industry: str) -> Optional[IndustryAnalysis]:
        """Phân tích một ngành cụ thể"""
        self.logger.info(f"Analyzing industry: {industry}")
        
        try:
            # Get industry benchmark
            benchmark = self.suggester.industry_benchmarks.get(industry)
            if not benchmark:
                self.logger.error(f"No benchmark found for industry: {industry}")
                return None
            
            # Get industry stocks
            industry_stocks = self.suggester.industry_stocks.get(industry, [])
            if not industry_stocks:
                self.logger.error(f"No stocks found for industry: {industry}")
                return None
            
            # Analyze industry stocks
            stock_analyses = []
            for symbol in industry_stocks[:15]:  # Analyze top 15 stocks
                try:
                    scan_result = self.scanner.analyze_single_stock_lightweight(symbol)
                    if scan_result:
                        stock_analyses.append(scan_result)
                except Exception as e:
                    self.logger.warning(f"Error analyzing {symbol}: {e}")
                    continue
            
            if not stock_analyses:
                self.logger.error(f"No valid stock analyses for industry: {industry}")
                return None
            
            # Calculate industry metrics
            industry_metrics = self._calculate_industry_metrics(stock_analyses, benchmark)
            
            # Determine industry trend
            trend = self._determine_industry_trend(industry_metrics, benchmark)
            
            # Calculate scores
            momentum_score = self._calculate_industry_momentum_score(stock_analyses)
            value_score = self._calculate_industry_value_score(stock_analyses, benchmark)
            quality_score = self._calculate_industry_quality_score(stock_analyses, benchmark)
            overall_score = (momentum_score + value_score + quality_score) / 3
            
            # Generate SWOT analysis
            strengths, weaknesses, opportunities, threats = self._generate_swot_analysis(
                industry, industry_metrics, benchmark
            )
            
            # Make recommendation
            recommendation, confidence = self._make_industry_recommendation(
                overall_score, trend, industry_metrics
            )
            
            # Get top picks
            top_picks = self._get_top_industry_picks(stock_analyses, 3)
            
            return IndustryAnalysis(
                industry=industry,
                trend=trend,
                momentum_score=momentum_score,
                value_score=value_score,
                quality_score=quality_score,
                overall_score=overall_score,
                avg_pe=industry_metrics["avg_pe"],
                avg_pb=industry_metrics["avg_pb"],
                avg_roe=industry_metrics["avg_roe"],
                market_cap_total=industry_metrics["market_cap_total"],
                stock_count=len(stock_analyses),
                strengths=strengths,
                weaknesses=weaknesses,
                opportunities=opportunities,
                threats=threats,
                recommendation=recommendation,
                confidence=confidence,
                top_picks=top_picks,
                analysis_date=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing industry {industry}: {e}")
            return None
    
    def compare_industries(self, industries: List[str]) -> List[IndustryAnalysis]:
        """So sánh nhiều ngành"""
        analyses = []
        
        for industry in industries:
            analysis = self.analyze_industry(industry)
            if analysis:
                analyses.append(analysis)
        
        # Sort by overall score
        analyses.sort(key=lambda x: x.overall_score, reverse=True)
        return analyses
    
    def get_top_industries(self, max_industries: int = 5) -> List[IndustryAnalysis]:
        """Lấy top ngành có tiềm năng nhất"""
        all_industries = self.suggester.get_available_industries()
        analyses = self.compare_industries(all_industries)
        return analyses[:max_industries]
    
    def _calculate_industry_metrics(self, stock_analyses: List, benchmark: IndustryBenchmark) -> Dict[str, float]:
        """Tính toán các chỉ số ngành"""
        valid_stocks = [
            s for s in stock_analyses
            if (getattr(s, 'pe_ratio', 0) or 0) > 0 and (getattr(s, 'pb_ratio', 0) or 0) > 0
        ]
        
        if not valid_stocks:
            return {
                "avg_pe": benchmark.pe_ratio,
                "avg_pb": benchmark.pb_ratio,
                "avg_roe": benchmark.roe,
                "market_cap_total": 0,
                "pe_vs_benchmark": 1.0,
                "pb_vs_benchmark": 1.0
            }
        
        # Calculate averages
        avg_pe = sum((getattr(s, 'pe_ratio', 0) or 0) for s in valid_stocks) / len(valid_stocks)
        avg_pb = sum((getattr(s, 'pb_ratio', 0) or 0) for s in valid_stocks) / len(valid_stocks)
        avg_roe = sum((getattr(s, 'roe', benchmark.roe) or benchmark.roe) for s in valid_stocks) / len(valid_stocks)
        market_cap_total = sum((getattr(s, 'market_cap', 0) or 0) for s in stock_analyses)
        
        # Compare with benchmark
        pe_vs_benchmark = avg_pe / benchmark.pe_ratio if benchmark.pe_ratio > 0 else 1.0
        pb_vs_benchmark = avg_pb / benchmark.pb_ratio if benchmark.pb_ratio > 0 else 1.0
        
        return {
            "avg_pe": avg_pe,
            "avg_pb": avg_pb,
            "avg_roe": avg_roe,
            "market_cap_total": market_cap_total,
            "pe_vs_benchmark": pe_vs_benchmark,
            "pb_vs_benchmark": pb_vs_benchmark
        }
    
    def _determine_industry_trend(self, metrics: Dict[str, float], benchmark: IndustryBenchmark) -> IndustryTrend:
        """Xác định xu hướng ngành"""
        # Analyze valuation vs benchmark
        pe_ratio = metrics["pe_vs_benchmark"]
        pb_ratio = metrics["pb_vs_benchmark"]
        
        # Analyze momentum (simplified)
        momentum_positive = 0
        momentum_negative = 0
        
        # This would be enhanced with actual momentum data
        # For now, use valuation as proxy
        
        if pe_ratio < 0.8 and pb_ratio < 0.8:
            return IndustryTrend.BEARISH  # Undervalued might indicate bearish sentiment
        elif pe_ratio > 1.2 and pb_ratio > 1.2:
            return IndustryTrend.VOLATILE  # Overvalued might indicate volatility
        elif 0.9 <= pe_ratio <= 1.1 and 0.9 <= pb_ratio <= 1.1:
            return IndustryTrend.NEUTRAL  # Fairly valued
        else:
            return IndustryTrend.BULLISH  # Moderate overvaluation might indicate bullish sentiment
    
    def _calculate_industry_momentum_score(self, stock_analyses: List) -> float:
        """Tính điểm momentum ngành"""
        if not stock_analyses:
            return 5.0
        
        momentum_signals = []
        
        for stock in stock_analyses:
            stock_momentum = 0
            
            # RSI analysis
            rsi_value = (getattr(stock, 'rsi', 0) or 0)
            if rsi_value > 0:
                if 40 <= rsi_value <= 60:
                    stock_momentum += 2
                elif 60 < rsi_value <= 70:
                    stock_momentum += 3
                elif rsi_value > 70:
                    stock_momentum += 1
            
            # MACD analysis
            macd_signal = getattr(stock, 'macd_signal', None)
            if macd_signal == "positive":
                stock_momentum += 3
            elif macd_signal == "neutral":
                stock_momentum += 1
            
            # Trend analysis
            ma_trend = getattr(stock, 'ma_trend', None)
            if ma_trend == "upward":
                stock_momentum += 3
            elif ma_trend == "sideways":
                stock_momentum += 1
            
            # Volume analysis
            volume_trend = getattr(stock, 'volume_trend', None)
            if volume_trend == "increasing":
                stock_momentum += 2
            
            momentum_signals.append(stock_momentum)
        
        avg_momentum = sum(momentum_signals) / len(momentum_signals)
        return min(10.0, avg_momentum)
    
    def _calculate_industry_value_score(self, stock_analyses: List, benchmark: IndustryBenchmark) -> float:
        """Tính điểm giá trị ngành"""
        if not stock_analyses:
            return 5.0
        
        value_signals = []
        
        for stock in stock_analyses:
            stock_value = 0
            
            # P/B analysis
            pb_value = (getattr(stock, 'pb_ratio', 0) or 0)
            if pb_value > 0 and benchmark.pb_ratio > 0:
                pb_ratio = pb_value / benchmark.pb_ratio
                if pb_ratio <= 0.7:
                    stock_value += 4
                elif pb_ratio <= 0.9:
                    stock_value += 3
                elif pb_ratio <= 1.1:
                    stock_value += 2
                else:
                    stock_value += 1
            
            # P/E analysis
            pe_value = (getattr(stock, 'pe_ratio', 0) or 0)
            if pe_value > 0 and benchmark.pe_ratio > 0:
                pe_ratio = pe_value / benchmark.pe_ratio
                if pe_ratio <= 0.8:
                    stock_value += 3
                elif pe_ratio <= 1.0:
                    stock_value += 2.5
                elif pe_ratio <= 1.2:
                    stock_value += 2
                else:
                    stock_value += 1
            
            value_signals.append(stock_value)
        
        avg_value = sum(value_signals) / len(value_signals)
        return min(10.0, avg_value)
    
    def _calculate_industry_quality_score(self, stock_analyses: List, benchmark: IndustryBenchmark) -> float:
        """Tính điểm chất lượng ngành"""
        if not stock_analyses:
            return 5.0
        
        quality_signals = []
        
        for stock in stock_analyses:
            stock_quality = 0
            
            # ROE analysis
            roe_value = (getattr(stock, 'roe', 0) or 0)
            if roe_value > 0 and benchmark.roe > 0:
                roe_ratio = roe_value / benchmark.roe
                if roe_ratio >= 1.2:
                    stock_quality += 3
                elif roe_ratio >= 1.0:
                    stock_quality += 2.5
                elif roe_ratio >= 0.8:
                    stock_quality += 2
                else:
                    stock_quality += 1
            
            # Market cap analysis
            market_cap_value = (getattr(stock, 'market_cap', 0) or 0)
            if market_cap_value > 10000000000000:  # > 10T
                stock_quality += 2
            elif market_cap_value > 5000000000000:  # > 5T
                stock_quality += 1.5
            else:
                stock_quality += 1
            
            # Data quality
            data_quality_value = getattr(stock, 'data_quality', 'fair')
            if data_quality_value == "good":
                stock_quality += 2
            elif data_quality_value == "fair":
                stock_quality += 1.5
            else:
                stock_quality += 1
            
            quality_signals.append(stock_quality)
        
        avg_quality = sum(quality_signals) / len(quality_signals)
        return min(10.0, avg_quality)
    
    def _generate_swot_analysis(self, industry: str, metrics: Dict[str, float], benchmark: IndustryBenchmark) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Tạo phân tích SWOT cho ngành"""
        strengths = []
        weaknesses = []
        opportunities = []
        threats = []
        
        # Strengths
        if metrics["avg_roe"] > benchmark.roe * 1.1:
            strengths.append("ROE trung bình cao hơn benchmark ngành")
        
        if metrics["market_cap_total"] > 100000000000000:  # > 100T
            strengths.append("Vốn hóa thị trường lớn, thanh khoản tốt")
        
        if metrics["pe_vs_benchmark"] < 1.0:
            strengths.append("Định giá hấp dẫn so với lịch sử")
        
        # Weaknesses
        if metrics["avg_roe"] < benchmark.roe * 0.9:
            weaknesses.append("ROE trung bình thấp hơn benchmark")
        
        if metrics["pe_vs_benchmark"] > 1.2:
            weaknesses.append("Định giá cao so với lịch sử")
        
        # Opportunities (industry-specific)
        if industry == "Phần mềm và dịch vụ công nghệ thông tin":
            opportunities.append("Xu hướng chuyển đổi số mạnh mẽ")
            opportunities.append("Chính sách hỗ trợ công nghệ")
        elif industry == "Năng lượng tái tạo":
            opportunities.append("Chính sách năng lượng xanh")
            opportunities.append("Nhu cầu năng lượng tăng cao")
        elif industry == "Dược phẩm":
            opportunities.append("Dân số già hóa")
            opportunities.append("Nhu cầu chăm sóc sức khỏe tăng")
        
        # Threats (general)
        threats.append("Rủi ro lãi suất tăng")
        threats.append("Biến động thị trường toàn cầu")
        threats.append("Thay đổi chính sách quản lý")
        
        return strengths, weaknesses, opportunities, threats
    
    def _make_industry_recommendation(self, overall_score: float, trend: IndustryTrend, metrics: Dict[str, float]) -> Tuple[str, float]:
        """Tạo khuyến nghị cho ngành"""
        if overall_score >= 8.0 and trend in [IndustryTrend.BULLISH, IndustryTrend.NEUTRAL]:
            recommendation = "OVERWEIGHT"
            confidence = min(0.9, 0.6 + (overall_score - 8.0) * 0.1)
        elif overall_score >= 6.5:
            recommendation = "NEUTRAL"
            confidence = min(0.8, 0.5 + (overall_score - 6.5) * 0.1)
        else:
            recommendation = "UNDERWEIGHT"
            confidence = min(0.7, 0.4 + overall_score * 0.1)
        
        # Adjust confidence based on trend
        if trend == IndustryTrend.BULLISH:
            confidence += 0.1
        elif trend == IndustryTrend.BEARISH:
            confidence -= 0.1
        elif trend == IndustryTrend.VOLATILE:
            confidence -= 0.05
        
        confidence = max(0.1, min(0.95, confidence))
        
        return recommendation, confidence
    
    def _get_top_industry_picks(self, stock_analyses: List, count: int = 3) -> List[str]:
        """Lấy top picks trong ngành"""
        # Sort by overall score (simplified calculation)
        scored_stocks = []
        for stock in stock_analyses:
            score = 0
            
            # Value score
            pb_val = (getattr(stock, 'pb_ratio', 0) or 0)
            if pb_val > 0 and pb_val < 2.0:
                score += 2
            pe_val = (getattr(stock, 'pe_ratio', 0) or 0)
            if pe_val > 0 and pe_val < 20:
                score += 2
            
            # Momentum score
            if getattr(stock, 'macd_signal', None) == "positive":
                score += 2
            if getattr(stock, 'ma_trend', None) == "upward":
                score += 2
            rsi_val = (getattr(stock, 'rsi', 0) or 0)
            if rsi_val > 0 and 40 <= rsi_val <= 60:
                score += 1
            
            scored_stocks.append((stock.symbol, score))
        
        # Sort by score and return top picks
        scored_stocks.sort(key=lambda x: x[1], reverse=True)
        return [symbol for symbol, score in scored_stocks[:count]]
