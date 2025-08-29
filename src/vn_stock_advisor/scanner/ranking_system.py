"""
Ranking System - Hệ thống chấm điểm và xếp hạng cổ phiếu
"""
import re
from typing import Dict, List, Optional


class RankingSystem:
    """Hệ thống chấm điểm và xếp hạng cổ phiếu"""
    
    def __init__(self):
        """Initialize ranking system with scoring weights"""
        self.weights = {
            'fundamental': 0.4,  # 40% trọng số cho phân tích cơ bản
            'technical': 0.3,    # 30% trọng số cho phân tích kỹ thuật
            'macro': 0.2,        # 20% trọng số cho phân tích vĩ mô
            'sentiment': 0.1     # 10% trọng số cho sentiment
        }
        
        # Scoring criteria
        self.fundamental_criteria = {
            'pe_good': 2.0,      # P/E hợp lý
            'pb_good': 1.5,      # P/B hấp dẫn
            'roe_high': 2.0,     # ROE cao
            'debt_low': 1.5,     # Nợ thấp
            'profit_growth': 2.0, # Tăng trưởng lợi nhuận
            'revenue_growth': 1.0 # Tăng trưởng doanh thu
        }
        
        self.technical_criteria = {
            'trend_up': 2.0,     # Xu hướng tăng
            'rsi_good': 1.0,     # RSI tốt
            'macd_positive': 1.5, # MACD tích cực
            'volume_good': 1.0,   # Khối lượng tốt
            'support_strong': 1.5 # Hỗ trợ mạnh
        }
    
    def extract_score_from_reasoning(self, reasoning: str, criteria: Dict[str, float]) -> float:
        """
        Trích xuất điểm từ text reasoning
        
        Args:
            reasoning: Text mô tả phân tích
            criteria: Dict các tiêu chí chấm điểm
            
        Returns:
            Điểm số từ 0-10
        """
        if not reasoning:
            return 0.0
            
        score = 0.0
        reasoning_lower = reasoning.lower()
        
        # Đếm các từ khóa tích cực
        positive_keywords = [
            'tốt', 'tăng', 'mạnh', 'cao', 'hấp dẫn', 'ổn định', 'tích cực',
            'good', 'strong', 'high', 'positive', 'stable', 'attractive'
        ]
        
        negative_keywords = [
            'xấu', 'giảm', 'yếu', 'thấp', 'rủi ro', 'tiêu cực', 'kém',
            'bad', 'weak', 'low', 'negative', 'poor', 'decline'
        ]
        
        # Tính điểm dựa trên từ khóa
        positive_count = sum(1 for keyword in positive_keywords if keyword in reasoning_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in reasoning_lower)
        
        # Base score từ sentiment
        base_score = max(0, min(10, 5 + positive_count - negative_count))
        
        # Bonus từ specific criteria
        for criterion, weight in criteria.items():
            if any(term in reasoning_lower for term in criterion.split('_')):
                base_score += weight * 0.5
        
        return min(10.0, base_score)
    
    def calculate_fundamental_score(self, reasoning: str) -> float:
        """Tính điểm phân tích cơ bản"""
        return self.extract_score_from_reasoning(reasoning, self.fundamental_criteria)
    
    def calculate_technical_score(self, reasoning: str) -> float:
        """Tính điểm phân tích kỹ thuật"""
        return self.extract_score_from_reasoning(reasoning, self.technical_criteria)
    
    def calculate_macro_score(self, reasoning: str) -> float:
        """Tính điểm phân tích vĩ mô"""
        if not reasoning or 'không có thông tin' in reasoning.lower():
            return 5.0  # Neutral score
        
        # Simple sentiment analysis for macro
        positive_terms = ['tích cực', 'thuận lợi', 'hỗ trợ', 'tăng trưởng']
        negative_terms = ['tiêu cực', 'bất lợi', 'rủi ro', 'suy thoái']
        
        reasoning_lower = reasoning.lower()
        positive_count = sum(1 for term in positive_terms if term in reasoning_lower)
        negative_count = sum(1 for term in negative_terms if term in reasoning_lower)
        
        return max(0, min(10, 5 + positive_count * 1.5 - negative_count * 1.5))
    
    def calculate_total_score(self, decision_data: Dict) -> float:
        """
        Tính tổng điểm từ dữ liệu phân tích
        
        Args:
            decision_data: Dict chứa kết quả phân tích từ CrewAI
            
        Returns:
            Tổng điểm từ 0-10
        """
        # Extract scores from reasoning
        fund_score = self.calculate_fundamental_score(
            decision_data.get('fund_reasoning', '')
        )
        
        tech_score = self.calculate_technical_score(
            decision_data.get('tech_reasoning', '')
        )
        
        macro_score = self.calculate_macro_score(
            decision_data.get('macro_reasoning', '')
        )
        
        # Sentiment score (placeholder - có thể cải thiện)
        sentiment_score = 5.0  # Neutral default
        
        # Calculate weighted total
        total_score = (
            fund_score * self.weights['fundamental'] +
            tech_score * self.weights['technical'] +
            macro_score * self.weights['macro'] +
            sentiment_score * self.weights['sentiment']
        )
        
        # Apply decision bonus/penalty
        decision = decision_data.get('decision', '').upper()
        if decision == 'MUA':
            total_score += 1.0  # Bonus for BUY
        elif decision == 'BÁN':
            total_score -= 1.0  # Penalty for SELL
        
        return max(0, min(10, total_score))
    
    def rank_stocks(self, analysis_results: List[Dict]) -> List[Dict]:
        """
        Xếp hạng danh sách cổ phiếu
        
        Args:
            analysis_results: List kết quả phân tích
            
        Returns:
            List đã được sắp xếp theo điểm số giảm dần
        """
        # Calculate scores for all stocks
        for result in analysis_results:
            if 'total_score' not in result:
                result['total_score'] = self.calculate_total_score(
                    result.get('raw_data', {})
                )
        
        # Sort by score descending
        ranked_results = sorted(
            analysis_results, 
            key=lambda x: x.get('total_score', 0), 
            reverse=True
        )
        
        # Add ranking position
        for i, result in enumerate(ranked_results, 1):
            result['rank'] = i
        
        return ranked_results
    
    def filter_buy_recommendations(self, 
                                 ranked_results: List[Dict], 
                                 min_score: float = 7.5) -> List[Dict]:
        """
        Lọc chỉ các khuyến nghị MUA với điểm số cao
        
        Args:
            ranked_results: List kết quả đã xếp hạng
            min_score: Điểm tối thiểu
            
        Returns:
            List các khuyến nghị MUA được lọc
        """
        buy_recommendations = []
        
        for result in ranked_results:
            # Check decision
            decision = result.get('decision', '').upper()
            if decision != 'MUA':
                continue
            
            # Check minimum score
            total_score = result.get('total_score', 0)
            if total_score < min_score:
                continue
            
            buy_recommendations.append(result)
        
        return buy_recommendations
    
    def generate_ranking_summary(self, ranked_results: List[Dict]) -> str:
        """
        Tạo báo cáo tóm tắt xếp hạng
        
        Args:
            ranked_results: List kết quả đã xếp hạng
            
        Returns:
            Báo cáo dạng text
        """
        if not ranked_results:
            return "No stocks to rank"
        
        summary = []
        summary.append("📊 STOCK RANKING SUMMARY")
        summary.append("=" * 40)
        
        # Statistics
        total_stocks = len(ranked_results)
        buy_stocks = len([r for r in ranked_results if r.get('decision', '').upper() == 'MUA'])
        avg_score = sum(r.get('total_score', 0) for r in ranked_results) / total_stocks
        
        summary.append(f"Total Stocks Analyzed: {total_stocks}")
        summary.append(f"Buy Recommendations: {buy_stocks}")
        summary.append(f"Average Score: {avg_score:.2f}")
        summary.append("")
        
        # Top performers
        summary.append("🏆 TOP 10 PERFORMERS:")
        summary.append("-" * 30)
        
        for result in ranked_results[:10]:
            rank = result.get('rank', 0)
            symbol = result.get('symbol', 'N/A')
            score = result.get('total_score', 0)
            decision = result.get('decision', 'N/A')
            
            summary.append(f"{rank:2d}. {symbol:>4} | Score: {score:5.2f} | {decision}")
        
        return "\n".join(summary)
