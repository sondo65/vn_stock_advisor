"""
Validation Metrics for VN Stock Advisor.

This module provides metrics to track and validate the performance
of stock recommendations over time.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class RecommendationRecord:
    """Record of a stock recommendation."""
    stock_symbol: str
    recommendation_date: datetime
    recommendation: str
    confidence_score: float
    target_price: float
    current_price: float
    industry: str
    component_scores: Dict[str, float]
    
@dataclass
class ValidationResult:
    """Result of validation analysis."""
    hit_rate: float
    average_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_recommendations: int
    successful_recommendations: int
    failed_recommendations: int

class ValidationMetrics:
    """
    Track and validate the performance of stock recommendations.
    """
    
    def __init__(self, data_file: str = "recommendation_history.json"):
        self.data_file = data_file
        self.recommendations = self._load_recommendations()
        
    def _load_recommendations(self) -> List[RecommendationRecord]:
        """Load recommendation history from file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [RecommendationRecord(**record) for record in data]
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error loading recommendations: {e}")
            return []
    
    def _save_recommendations(self):
        """Save recommendations to file."""
        try:
            data = []
            for rec in self.recommendations:
                rec_dict = {
                    'stock_symbol': rec.stock_symbol,
                    'recommendation_date': rec.recommendation_date.isoformat(),
                    'recommendation': rec.recommendation,
                    'confidence_score': rec.confidence_score,
                    'target_price': rec.target_price,
                    'current_price': rec.current_price,
                    'industry': rec.industry,
                    'component_scores': rec.component_scores
                }
                data.append(rec_dict)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving recommendations: {e}")
    
    def add_recommendation(self, 
                          stock_symbol: str,
                          recommendation: str,
                          confidence_score: float,
                          target_price: float,
                          current_price: float,
                          industry: str,
                          component_scores: Dict[str, float]):
        """Add a new recommendation to the history."""
        record = RecommendationRecord(
            stock_symbol=stock_symbol,
            recommendation_date=datetime.now(),
            recommendation=recommendation,
            confidence_score=confidence_score,
            target_price=target_price,
            current_price=current_price,
            industry=industry,
            component_scores=component_scores
        )
        
        self.recommendations.append(record)
        self._save_recommendations()
    
    def calculate_hit_rate(self, days_threshold: int = 30) -> float:
        """Calculate hit rate of recommendations within specified days."""
        if not self.recommendations:
            return 0.0
        
        successful = 0
        total = 0
        
        for rec in self.recommendations:
            days_ago = (datetime.now() - rec.recommendation_date).days
            
            if days_ago >= days_threshold:
                total += 1
                
                # Calculate return
                if rec.recommendation in ['BUY', 'STRONG_BUY']:
                    if rec.target_price > rec.current_price:
                        successful += 1
                elif rec.recommendation in ['SELL', 'STRONG_SELL']:
                    if rec.target_price < rec.current_price:
                        successful += 1
                elif rec.recommendation == 'HOLD':
                    # For HOLD, consider it successful if price stays within 10% of current
                    price_change = abs(rec.target_price - rec.current_price) / rec.current_price
                    if price_change <= 0.1:
                        successful += 1
        
        return successful / total if total > 0 else 0.0
    
    def calculate_average_return(self, days_threshold: int = 30) -> float:
        """Calculate average return of recommendations."""
        if not self.recommendations:
            return 0.0
        
        returns = []
        
        for rec in self.recommendations:
            days_ago = (datetime.now() - rec.recommendation_date).days
            
            if days_ago >= days_threshold:
                if rec.recommendation in ['BUY', 'STRONG_BUY']:
                    return_pct = (rec.target_price - rec.current_price) / rec.current_price
                    returns.append(return_pct)
                elif rec.recommendation in ['SELL', 'STRONG_SELL']:
                    return_pct = (rec.current_price - rec.target_price) / rec.current_price
                    returns.append(return_pct)
        
        return np.mean(returns) if returns else 0.0
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.05) -> float:
        """Calculate Sharpe ratio of recommendations."""
        returns = self._get_all_returns()
        
        if not returns:
            return 0.0
        
        excess_returns = np.array(returns) - risk_free_rate
        return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0.0
    
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown of recommendations."""
        returns = self._get_all_returns()
        
        if not returns:
            return 0.0
        
        cumulative = np.cumprod(1 + np.array(returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        return np.min(drawdown)
    
    def _get_all_returns(self) -> List[float]:
        """Get all returns from recommendations."""
        returns = []
        
        for rec in self.recommendations:
            if rec.recommendation in ['BUY', 'STRONG_BUY']:
                return_pct = (rec.target_price - rec.current_price) / rec.current_price
                returns.append(return_pct)
            elif rec.recommendation in ['SELL', 'STRONG_SELL']:
                return_pct = (rec.current_price - rec.target_price) / rec.current_price
                returns.append(return_pct)
        
        return returns
    
    def get_validation_summary(self, days_threshold: int = 30) -> ValidationResult:
        """Get comprehensive validation summary."""
        hit_rate = self.calculate_hit_rate(days_threshold)
        avg_return = self.calculate_average_return(days_threshold)
        sharpe_ratio = self.calculate_sharpe_ratio()
        max_drawdown = self.calculate_max_drawdown()
        
        total = len([r for r in self.recommendations if (datetime.now() - r.recommendation_date).days >= days_threshold])
        successful = int(hit_rate * total)
        failed = total - successful
        
        return ValidationResult(
            hit_rate=hit_rate,
            average_return=avg_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_recommendations=total,
            successful_recommendations=successful,
            failed_recommendations=failed
        )
    
    def export_performance_report(self, output_file: str = "performance_report.md"):
        """Export performance report to markdown file."""
        summary = self.get_validation_summary()
        
        report = f"""# Báo Cáo Hiệu Quả Khuyến Nghị Đầu Tư

## Tổng Quan
- **Tổng số khuyến nghị**: {summary.total_recommendations}
- **Khuyến nghị thành công**: {summary.successful_recommendations}
- **Khuyến nghị thất bại**: {summary.failed_recommendations}

## Chỉ Số Hiệu Quả
- **Tỷ lệ thành công**: {summary.hit_rate:.2%}
- **Lợi nhuận trung bình**: {summary.average_return:.2%}
- **Tỷ lệ Sharpe**: {summary.sharpe_ratio:.2f}
- **Mức sụt giảm tối đa**: {summary.max_drawdown:.2%}

## Phân Tích Theo Ngành
"""
        
        # Group by industry
        industry_stats = {}
        for rec in self.recommendations:
            if rec.industry not in industry_stats:
                industry_stats[rec.industry] = []
            industry_stats[rec.industry].append(rec)
        
        for industry, recs in industry_stats.items():
            industry_hit_rate = self._calculate_industry_hit_rate(recs)
            report += f"- **{industry}**: {industry_hit_rate:.2%}\n"
        
        report += f"""
## Khuyến Nghị Cải Tiến
- Tập trung vào các ngành có tỷ lệ thành công cao
- Cải thiện mô hình dự đoán cho các ngành có hiệu quả thấp
- Theo dõi và điều chỉnh trọng số các yếu tố phân tích

*Báo cáo được tạo vào: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report
    
    def _calculate_industry_hit_rate(self, recommendations: List[RecommendationRecord]) -> float:
        """Calculate hit rate for a specific industry."""
        if not recommendations:
            return 0.0
        
        successful = 0
        total = 0
        
        for rec in recommendations:
            days_ago = (datetime.now() - rec.recommendation_date).days
            
            if days_ago >= 30:  # 30 days threshold
                total += 1
                
                if rec.recommendation in ['BUY', 'STRONG_BUY']:
                    if rec.target_price > rec.current_price:
                        successful += 1
                elif rec.recommendation in ['SELL', 'STRONG_SELL']:
                    if rec.target_price < rec.current_price:
                        successful += 1
                elif rec.recommendation == 'HOLD':
                    price_change = abs(rec.target_price - rec.current_price) / rec.current_price
                    if price_change <= 0.1:
                        successful += 1
        
        return successful / total if total > 0 else 0.0
