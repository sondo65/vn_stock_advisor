"""
Risk Metrics for VN Stock Advisor.

This module provides additional risk metrics and risk-adjusted
performance measures for comprehensive risk assessment.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class RiskAdjustedMetrics:
    """Risk-adjusted performance metrics."""
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    treynor_ratio: float
    jensen_alpha: float

class RiskMetrics:
    """
    Calculate comprehensive risk metrics and risk-adjusted returns.
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate
    
    def calculate_calmar_ratio(self, returns: List[float], max_drawdown: float) -> float:
        """Calculate Calmar ratio (return / max drawdown)."""
        if not returns or max_drawdown == 0:
            return 0.0
        
        annual_return = np.mean(returns) * 252
        return annual_return / abs(max_drawdown)
    
    def calculate_information_ratio(self, 
                                  stock_returns: List[float], 
                                  benchmark_returns: List[float]) -> float:
        """Calculate information ratio (excess return / tracking error)."""
        if len(stock_returns) != len(benchmark_returns) or len(stock_returns) < 2:
            return 0.0
        
        stock_array = np.array(stock_returns)
        benchmark_array = np.array(benchmark_returns)
        
        excess_returns = stock_array - benchmark_array
        tracking_error = np.std(excess_returns)
        
        if tracking_error == 0:
            return 0.0
        
        information_ratio = np.mean(excess_returns) / tracking_error
        return information_ratio * np.sqrt(252)  # Annualized
    
    def calculate_treynor_ratio(self, returns: List[float], beta: float) -> float:
        """Calculate Treynor ratio (excess return / beta)."""
        if not returns or beta == 0:
            return 0.0
        
        excess_return = np.mean(returns) - self.risk_free_rate / 252
        treynor = excess_return / beta
        
        return treynor * np.sqrt(252)  # Annualized
    
    def calculate_jensen_alpha(self, 
                              stock_returns: List[float], 
                              market_returns: List[float], 
                              beta: float) -> float:
        """Calculate Jensen's alpha."""
        if len(stock_returns) != len(market_returns) or len(stock_returns) < 2:
            return 0.0
        
        stock_return = np.mean(stock_returns)
        market_return = np.mean(market_returns)
        
        # CAPM expected return
        expected_return = self.risk_free_rate / 252 + beta * (market_return - self.risk_free_rate / 252)
        
        # Jensen's alpha
        alpha = stock_return - expected_return
        
        return alpha * 252  # Annualized
    
    def calculate_ulcer_index(self, prices: List[float]) -> float:
        """Calculate Ulcer Index (measure of downside risk)."""
        if not prices or len(prices) < 2:
            return 0.0
        
        prices_array = np.array(prices)
        drawdowns = []
        
        for i in range(1, len(prices_array)):
            peak = np.max(prices_array[:i])
            if peak > 0:
                drawdown = (peak - prices_array[i]) / peak
                drawdowns.append(drawdown)
        
        if not drawdowns:
            return 0.0
        
        # Calculate Ulcer Index
        ulcer_index = np.sqrt(np.mean(np.array(drawdowns) ** 2))
        return ulcer_index
    
    def calculate_gain_to_pain_ratio(self, returns: List[float]) -> float:
        """Calculate gain-to-pain ratio."""
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        gains = returns_array[returns_array > 0]
        losses = returns_array[returns_array < 0]
        
        if len(losses) == 0:
            return np.sum(gains) if len(gains) > 0 else 0.0
        
        total_gains = np.sum(gains)
        total_losses = abs(np.sum(losses))
        
        return total_gains / total_losses if total_losses > 0 else 0.0
    
    def calculate_risk_of_ruin(self, 
                               win_rate: float, 
                               avg_win: float, 
                               avg_loss: float) -> float:
        """Calculate risk of ruin probability."""
        if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss <= 0:
            return 0.0
        
        # Kelly Criterion
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        
        if kelly_fraction <= 0:
            return 1.0  # 100% risk of ruin
        
        # Risk of ruin approximation
        risk_of_ruin = ((1 - win_rate) / win_rate) ** (avg_win / avg_loss)
        
        return min(risk_of_ruin, 1.0)
    
    def calculate_comprehensive_risk_score(self, 
                                         volatility: float,
                                         beta: float,
                                         max_drawdown: float,
                                         var_95: float,
                                         sharpe_ratio: float) -> Dict:
        """Calculate comprehensive risk score (0-100, higher = more risky)."""
        risk_score = 0
        
        # Volatility risk (0-25 points)
        if volatility > 0.5:
            risk_score += 25
        elif volatility > 0.4:
            risk_score += 20
        elif volatility > 0.3:
            risk_score += 15
        elif volatility > 0.2:
            risk_score += 10
        elif volatility > 0.1:
            risk_score += 5
        
        # Beta risk (0-20 points)
        if beta > 1.5:
            risk_score += 20
        elif beta > 1.2:
            risk_score += 15
        elif beta > 1.0:
            risk_score += 10
        elif beta > 0.8:
            risk_score += 5
        
        # Drawdown risk (0-20 points)
        if max_drawdown > 0.4:
            risk_score += 20
        elif max_drawdown > 0.3:
            risk_score += 15
        elif max_drawdown > 0.2:
            risk_score += 10
        elif max_drawdown > 0.1:
            risk_score += 5
        
        # VaR risk (0-20 points)
        if var_95 > 0.3:
            risk_score += 20
        elif var_95 > 0.2:
            risk_score += 15
        elif var_95 > 0.1:
            risk_score += 10
        elif var_95 > 0.05:
            risk_score += 5
        
        # Sharpe ratio risk (0-15 points)
        if sharpe_ratio < 0:
            risk_score += 15
        elif sharpe_ratio < 0.5:
            risk_score += 10
        elif sharpe_ratio < 1.0:
            risk_score += 5
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = "EXTREME"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        elif risk_score >= 20:
            risk_level = "LOW"
        else:
            risk_level = "VERY_LOW"
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'volatility_risk': min(25, risk_score),
            'beta_risk': min(20, risk_score),
            'drawdown_risk': min(20, risk_score),
            'var_risk': min(20, risk_score),
            'sharpe_risk': min(15, risk_score)
        }
    
    def generate_risk_report(self, 
                            stock_symbol: str,
                            risk_metrics: Dict,
                            risk_adjusted_metrics: RiskAdjustedMetrics) -> str:
        """Generate comprehensive risk report."""
        report = f"""# Báo Cáo Rủi Ro - {stock_symbol}

## Chỉ Số Rủi Ro Cơ Bản
- **Độ biến động**: {risk_metrics.get('volatility', 0):.2%}
- **Beta**: {risk_metrics.get('beta', 0):.2f}
- **VaR (95%)**: {risk_metrics.get('var_95', 0):.2%}
- **Mức sụt giảm tối đa**: {risk_metrics.get('max_drawdown', 0):.2%}

## Chỉ Số Hiệu Quả Điều Chỉnh Rủi Ro
- **Tỷ lệ Sharpe**: {risk_adjusted_metrics.sharpe_ratio:.2f}
- **Tỷ lệ Sortino**: {risk_adjusted_metrics.sortino_ratio:.2f}
- **Tỷ lệ Calmar**: {risk_adjusted_metrics.calmar_ratio:.2f}
- **Tỷ lệ thông tin**: {risk_adjusted_metrics.information_ratio:.2f}
- **Tỷ lệ Treynor**: {risk_adjusted_metrics.treynor_ratio:.2f}
- **Jensen's Alpha**: {risk_adjusted_metrics.jensen_alpha:.2%}

## Đánh Giá Tổng Quan
- **Điểm rủi ro tổng hợp**: {risk_metrics.get('risk_score', 0)}/100
- **Mức độ rủi ro**: {risk_metrics.get('risk_level', 'Không xác định')}

## Khuyến Nghị Quản Lý Rủi Ro
"""
        
        risk_level = risk_metrics.get('risk_level', 'MEDIUM')
        
        if risk_level == 'EXTREME':
            report += "- **RỦI RO CỰC CAO**: Không nên đầu tư hoặc chỉ đầu tư với số tiền nhỏ\n"
            report += "- Đặt stop-loss rất chặt chẽ (5-10%)\n"
            report += "- Cân nhắc sử dụng các công cụ phòng ngừa rủi ro\n"
        elif risk_level == 'HIGH':
            report += "- **RỦI RO CAO**: Đầu tư thận trọng với số tiền vừa phải\n"
            report += "- Đặt stop-loss chặt chẽ (10-15%)\n"
            report += "- Theo dõi thường xuyên và sẵn sàng thoát khi cần\n"
        elif risk_level == 'MEDIUM':
            report += "- **RỦI RO TRUNG BÌNH**: Có thể đầu tư với số tiền hợp lý\n"
            report += "- Đặt stop-loss vừa phải (15-20%)\n"
            report += "- Theo dõi định kỳ và điều chỉnh khi cần\n"
        elif risk_level == 'LOW':
            report += "- **RỦI RO THẤP**: Có thể đầu tư với số tiền lớn hơn\n"
            report += "- Đặt stop-loss lỏng lẻo (20-25%)\n"
            report += "- Theo dõi ít thường xuyên hơn\n"
        else:
            report += "- **RỦI RO RẤT THẤP**: Có thể đầu tư an toàn\n"
            report += "- Không cần đặt stop-loss quá chặt chẽ\n"
            report += "- Phù hợp với nhà đầu tư thận trọng\n"
        
        return report
