"""
Industry Stock Advisor - Hệ thống gợi ý cổ phiếu theo ngành hoàn chỉnh

Chức năng chính:
1. Gợi ý cổ phiếu tiềm năng theo ngành
2. Phân tích và so sánh các ngành
3. Tích hợp với hệ thống hiện có
4. Cung cấp giao diện dễ sử dụng
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from .industry_suggester import IndustryStockSuggester, IndustryStockSuggestion
from .industry_analyzer import IndustryAnalyzer, IndustryAnalysis
from .lightweight_scanner import LightweightStockScanner

@dataclass
class IndustryRecommendation:
    """Khuyến nghị tổng hợp cho ngành"""
    industry: str
    industry_analysis: IndustryAnalysis
    stock_suggestions: List[IndustryStockSuggestion]
    
    # Tóm tắt
    summary: str
    key_insights: List[str]
    risk_factors: List[str]
    investment_strategy: str
    
    # Metadata
    analysis_date: datetime
    confidence: float

class IndustryStockAdvisor:
    """Hệ thống gợi ý cổ phiếu theo ngành hoàn chỉnh"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.suggester = IndustryStockSuggester()
        self.analyzer = IndustryAnalyzer()
        self.scanner = LightweightStockScanner(max_workers=3, use_cache=True)
        
        # Cache for results
        self._cache = {}
        self._cache_ttl = 1800  # 30 minutes
    
    def get_industry_recommendation(self, 
                                  industry: str, 
                                  max_stocks: int = 10,
                                  min_score: float = 7.0,
                                  include_analysis: bool = True) -> Optional[IndustryRecommendation]:
        """
        Lấy khuyến nghị hoàn chỉnh cho một ngành
        
        Args:
            industry: Tên ngành
            max_stocks: Số lượng cổ phiếu tối đa
            min_score: Điểm tối thiểu
            include_analysis: Có bao gồm phân tích chi tiết không
            
        Returns:
            Khuyến nghị hoàn chỉnh cho ngành
        """
        self.logger.info(f"Getting industry recommendation for: {industry}")
        
        try:
            # Check cache
            cache_key = f"industry_rec_{industry}_{max_stocks}_{min_score}"
            if self._is_cache_valid(cache_key):
                return self._cache[cache_key]["data"]
            
            # Get industry analysis
            industry_analysis = self.analyzer.analyze_industry(industry)
            if not industry_analysis:
                self.logger.error(f"Could not analyze industry: {industry}")
                return None
            
            # Get stock suggestions
            stock_suggestions = self.suggester.suggest_stocks_by_industry(
                industry=industry,
                max_stocks=max_stocks,
                min_score=min_score,
                include_analysis=include_analysis
            )
            
            if not stock_suggestions:
                self.logger.warning(f"No stock suggestions for industry: {industry}")
                return None
            
            # Generate summary and insights
            summary = self._generate_industry_summary(industry_analysis, stock_suggestions)
            key_insights = self._generate_key_insights(industry_analysis, stock_suggestions)
            risk_factors = self._generate_risk_factors(industry_analysis, stock_suggestions)
            investment_strategy = self._generate_investment_strategy(industry_analysis, stock_suggestions)
            
            # Calculate overall confidence
            confidence = self._calculate_overall_confidence(industry_analysis, stock_suggestions)
            
            # Create recommendation
            recommendation = IndustryRecommendation(
                industry=industry,
                industry_analysis=industry_analysis,
                stock_suggestions=stock_suggestions,
                summary=summary,
                key_insights=key_insights,
                risk_factors=risk_factors,
                investment_strategy=investment_strategy,
                analysis_date=datetime.now(),
                confidence=confidence
            )
            
            # Cache result
            self._cache[cache_key] = {
                "data": recommendation,
                "timestamp": datetime.now()
            }
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error getting industry recommendation for {industry}: {e}")
            return None
    
    def compare_industries(self, 
                         industries: List[str], 
                         max_stocks_per_industry: int = 5) -> List[IndustryRecommendation]:
        """
        So sánh nhiều ngành và đưa ra khuyến nghị
        
        Args:
            industries: Danh sách ngành cần so sánh
            max_stocks_per_industry: Số cổ phiếu tối đa mỗi ngành
            
        Returns:
            Danh sách khuyến nghị được sắp xếp theo tiềm năng
        """
        self.logger.info(f"Comparing industries: {industries}")
        
        recommendations = []
        
        for industry in industries:
            try:
                recommendation = self.get_industry_recommendation(
                    industry=industry,
                    max_stocks=max_stocks_per_industry,
                    min_score=6.5,  # Lower threshold for comparison
                    include_analysis=True
                )
                
                if recommendation:
                    recommendations.append(recommendation)
                    
            except Exception as e:
                self.logger.error(f"Error comparing industry {industry}: {e}")
                continue
        
        # Sort by industry analysis overall score
        recommendations.sort(
            key=lambda x: x.industry_analysis.overall_score, 
            reverse=True
        )
        
        return recommendations
    
    def get_top_industry_opportunities(self, 
                                     max_industries: int = 5,
                                     max_stocks_per_industry: int = 5) -> List[IndustryRecommendation]:
        """
        Lấy top cơ hội đầu tư theo ngành
        
        Args:
            max_industries: Số ngành tối đa
            max_stocks_per_industry: Số cổ phiếu tối đa mỗi ngành
            
        Returns:
            Danh sách top cơ hội đầu tư
        """
        self.logger.info(f"Getting top industry opportunities")
        
        # Get all available industries
        available_industries = self.suggester.get_available_industries()
        
        # Get recommendations for all industries
        all_recommendations = []
        for industry in available_industries:
            try:
                recommendation = self.get_industry_recommendation(
                    industry=industry,
                    max_stocks=max_stocks_per_industry,
                    min_score=7.0,
                    include_analysis=True
                )
                
                if recommendation:
                    all_recommendations.append(recommendation)
                    
            except Exception as e:
                self.logger.error(f"Error getting recommendation for {industry}: {e}")
                continue
        
        # Sort by combined score (industry score + top stock scores)
        def calculate_combined_score(rec: IndustryRecommendation) -> float:
            industry_score = rec.industry_analysis.overall_score
            if rec.stock_suggestions:
                avg_stock_score = sum(s.total_score for s in rec.stock_suggestions) / len(rec.stock_suggestions)
                return (industry_score + avg_stock_score) / 2
            return industry_score
        
        all_recommendations.sort(key=calculate_combined_score, reverse=True)
        
        return all_recommendations[:max_industries]
    
    def get_industry_summary(self, industry: str) -> Dict[str, Any]:
        """Lấy tóm tắt thông tin ngành"""
        return self.suggester.get_industry_summary(industry)
    
    def get_available_industries(self) -> List[str]:
        """Lấy danh sách các ngành có sẵn"""
        return self.suggester.get_available_industries()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Kiểm tra cache có còn hiệu lực không"""
        if cache_key not in self._cache:
            return False
        
        cache_time = self._cache[cache_key]["timestamp"]
        return (datetime.now() - cache_time).seconds < self._cache_ttl
    
    def _generate_industry_summary(self, 
                                 industry_analysis: IndustryAnalysis, 
                                 stock_suggestions: List[IndustryStockSuggestion]) -> str:
        """Tạo tóm tắt ngành"""
        industry = industry_analysis.industry
        trend = industry_analysis.trend.value
        overall_score = industry_analysis.overall_score
        recommendation = industry_analysis.recommendation
        
        # Count buy recommendations
        buy_count = sum(1 for s in stock_suggestions if s.recommendation in ["BUY", "STRONG_BUY"])
        total_count = len(stock_suggestions)
        
        summary = f"Ngành {industry} hiện có xu hướng {trend} với điểm tổng thể {overall_score:.1f}/10. "
        summary += f"Khuyến nghị ngành: {recommendation}. "
        summary += f"Trong {total_count} cổ phiếu được phân tích, có {buy_count} mã được khuyến nghị MUA. "
        
        if industry_analysis.overall_score >= 7.5:
            summary += "Đây là ngành có tiềm năng đầu tư tốt với nhiều cơ hội hấp dẫn."
        elif industry_analysis.overall_score >= 6.0:
            summary += "Ngành có tiềm năng trung bình, cần lựa chọn kỹ lưỡng."
        else:
            summary += "Ngành có rủi ro cao, cần thận trọng khi đầu tư."
        
        return summary
    
    def _generate_key_insights(self, 
                             industry_analysis: IndustryAnalysis, 
                             stock_suggestions: List[IndustryStockSuggestion]) -> List[str]:
        """Tạo các insight chính"""
        insights = []
        
        # Industry insights
        if industry_analysis.overall_score >= 8.0:
            insights.append("Ngành có điểm số xuất sắc, đáng chú ý đầu tư")
        elif industry_analysis.overall_score >= 7.0:
            insights.append("Ngành có tiềm năng tốt với nhiều cơ hội")
        
        # Trend insights
        if industry_analysis.trend.value == "bullish":
            insights.append("Xu hướng ngành tích cực, hỗ trợ tăng trưởng")
        elif industry_analysis.trend.value == "bearish":
            insights.append("Xu hướng ngành tiêu cực, cần thận trọng")
        
        # Valuation insights
        if industry_analysis.value_score >= 7.0:
            insights.append("Định giá ngành hấp dẫn, nhiều cổ phiếu bị định giá thấp")
        
        # Momentum insights
        if industry_analysis.momentum_score >= 7.0:
            insights.append("Momentum kỹ thuật mạnh, tín hiệu tích cực")
        
        # Top picks insights
        if stock_suggestions:
            top_pick = stock_suggestions[0]
            insights.append(f"Top pick: {top_pick.symbol} với điểm {top_pick.total_score:.1f}/10")
            
            strong_buy_count = sum(1 for s in stock_suggestions if s.recommendation == "STRONG_BUY")
            if strong_buy_count > 0:
                insights.append(f"Có {strong_buy_count} mã được khuyến nghị MUA MẠNH")
        
        return insights
    
    def _generate_risk_factors(self, 
                             industry_analysis: IndustryAnalysis, 
                             stock_suggestions: List[IndustryStockSuggestion]) -> List[str]:
        """Tạo danh sách rủi ro"""
        risks = []
        
        # Industry risks
        if industry_analysis.overall_score < 6.0:
            risks.append("Điểm số ngành thấp, rủi ro cao")
        
        if industry_analysis.trend.value == "volatile":
            risks.append("Ngành biến động cao, rủi ro không ổn định")
        
        # Valuation risks
        if industry_analysis.value_score < 5.0:
            risks.append("Định giá ngành cao, rủi ro điều chỉnh")
        
        # Quality risks
        if industry_analysis.quality_score < 5.0:
            risks.append("Chất lượng tài chính ngành thấp")
        
        # Stock-specific risks
        high_risk_count = sum(1 for s in stock_suggestions if s.risk_level == "HIGH")
        if high_risk_count > len(stock_suggestions) * 0.5:
            risks.append("Nhiều cổ phiếu có rủi ro cao")
        
        # General risks
        risks.extend([
            "Rủi ro lãi suất tăng",
            "Biến động thị trường toàn cầu",
            "Thay đổi chính sách quản lý"
        ])
        
        return risks
    
    def _generate_investment_strategy(self, 
                                    industry_analysis: IndustryAnalysis, 
                                    stock_suggestions: List[IndustryStockSuggestion]) -> str:
        """Tạo chiến lược đầu tư"""
        industry = industry_analysis.industry
        recommendation = industry_analysis.recommendation
        overall_score = industry_analysis.overall_score
        
        if recommendation == "OVERWEIGHT" and overall_score >= 8.0:
            strategy = f"Chiến lược TÍCH CỰC cho ngành {industry}: "
            strategy += "Tăng tỷ trọng đầu tư, tập trung vào các cổ phiếu có điểm cao. "
            strategy += "Có thể đầu tư dài hạn với kỳ vọng tăng trưởng mạnh."
            
        elif recommendation == "OVERWEIGHT":
            strategy = f"Chiến lược TÍCH CỰC VỪA PHẢI cho ngành {industry}: "
            strategy += "Tăng tỷ trọng đầu tư một cách thận trọng. "
            strategy += "Lựa chọn kỹ lưỡng các cổ phiếu có tiềm năng tốt nhất."
            
        elif recommendation == "NEUTRAL":
            strategy = f"Chiến lược TRUNG LẬP cho ngành {industry}: "
            strategy += "Duy trì tỷ trọng đầu tư hiện tại. "
            strategy += "Tập trung vào các cổ phiếu có định giá hấp dẫn và momentum tốt."
            
        else:  # UNDERWEIGHT
            strategy = f"Chiến lược THẬN TRỌNG cho ngành {industry}: "
            strategy += "Giảm tỷ trọng đầu tư hoặc tránh đầu tư. "
            strategy += "Nếu đầu tư, chỉ chọn các cổ phiếu có điểm số cao nhất."
        
        # Add specific recommendations
        if stock_suggestions:
            strong_buy_stocks = [s.symbol for s in stock_suggestions if s.recommendation == "STRONG_BUY"]
            if strong_buy_stocks:
                strategy += f" Ưu tiên các mã: {', '.join(strong_buy_stocks[:3])}."
        
        return strategy
    
    def _calculate_overall_confidence(self, 
                                    industry_analysis: IndustryAnalysis, 
                                    stock_suggestions: List[IndustryStockSuggestion]) -> float:
        """Tính độ tin cậy tổng thể"""
        # Base confidence from industry analysis
        base_confidence = industry_analysis.confidence
        
        # Adjust based on stock suggestions quality
        if stock_suggestions:
            avg_stock_confidence = sum(s.confidence for s in stock_suggestions) / len(stock_suggestions)
            combined_confidence = (base_confidence + avg_stock_confidence) / 2
        else:
            combined_confidence = base_confidence
        
        # Adjust based on data quality
        good_data_count = sum(1 for s in stock_suggestions if s.data_quality == "good")
        if stock_suggestions:
            data_quality_ratio = good_data_count / len(stock_suggestions)
            combined_confidence *= (0.8 + 0.2 * data_quality_ratio)
        
        return max(0.1, min(0.95, combined_confidence))
    
    def clear_cache(self):
        """Xóa cache"""
        self._cache.clear()
        self.logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Lấy thống kê cache"""
        return {
            "cache_size": len(self._cache),
            "cache_ttl": self._cache_ttl,
            "cached_items": list(self._cache.keys())
        }
