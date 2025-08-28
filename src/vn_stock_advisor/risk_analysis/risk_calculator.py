"""
Risk Calculator for VN Stock Advisor.

This module provides comprehensive risk assessment including:
- Value at Risk (VaR) calculation
- Beta and correlation analysis
- Volatility analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class RiskMetrics:
    """Risk metrics for a stock."""
    volatility: float
    beta: float
    var_95: float
    var_99: float
    correlation_vnindex: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float

class RiskCalculator:
    """
    Calculate various risk metrics for stock analysis.
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate
    
    def calculate_volatility(self, returns: List[float]) -> float:
        """Calculate annualized volatility from returns."""
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        daily_vol = np.std(returns_array)
        annual_vol = daily_vol * np.sqrt(252)  # 252 trading days per year
        
        return annual_vol
    
    def calculate_beta(self, stock_returns: List[float], market_returns: List[float]) -> float:
        """Calculate beta relative to market (VN-Index)."""
        if len(stock_returns) != len(market_returns) or len(stock_returns) < 2:
            return 1.0
        
        stock_array = np.array(stock_returns)
        market_array = np.array(market_returns)
        
        # Calculate covariance and variance
        covariance = np.cov(stock_array, market_array)[0, 1]
        market_variance = np.var(market_array)
        
        if market_variance == 0:
            return 1.0
        
        beta = covariance / market_variance
        return beta
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)."""
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        
        if confidence_level == 0.95:
            var = np.percentile(returns_array, 5)
        elif confidence_level == 0.99:
            var = np.percentile(returns_array, 1)
        else:
            var = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        return abs(var)
    
    def calculate_correlation(self, stock_returns: List[float], market_returns: List[float]) -> float:
        """Calculate correlation with market returns."""
        if len(stock_returns) != len(market_returns) or len(stock_returns) < 2:
            return 0.0
        
        stock_array = np.array(stock_returns)
        market_array = np.array(market_returns)
        
        correlation = np.corrcoef(stock_array, market_array)[0, 1]
        return correlation if not np.isnan(correlation) else 0.0
    
    def calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio."""
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - self.risk_free_rate / 252  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe * np.sqrt(252)  # Annualized
    
    def calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - self.risk_free_rate / 252
        
        # Calculate downside deviation
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0
        
        sortino = np.mean(excess_returns) / np.std(downside_returns)
        return sortino * np.sqrt(252)  # Annualized
    
    def calculate_max_drawdown(self, prices: List[float]) -> float:
        """Calculate maximum drawdown from price series."""
        if not prices or len(prices) < 2:
            return 0.0
        
        prices_array = np.array(prices)
        peak = prices_array[0]
        max_dd = 0.0
        
        for price in prices_array[1:]:
            if price > peak:
                peak = price
            else:
                drawdown = (peak - price) / peak
                max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def calculate_comprehensive_risk(self, 
                                   stock_returns: List[float],
                                   market_returns: List[float],
                                   stock_prices: List[float]) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        volatility = self.calculate_volatility(stock_returns)
        beta = self.calculate_beta(stock_returns, market_returns)
        var_95 = self.calculate_var(stock_returns, 0.95)
        var_99 = self.calculate_var(stock_returns, 0.99)
        correlation = self.calculate_correlation(stock_returns, market_returns)
        sharpe = self.calculate_sharpe_ratio(stock_returns)
        sortino = self.calculate_sortino_ratio(stock_returns)
        max_dd = self.calculate_max_drawdown(stock_prices)
        
        return RiskMetrics(
            volatility=volatility,
            beta=beta,
            var_95=var_95,
            var_99=var_99,
            correlation_vnindex=correlation,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd
        )
    
    def get_risk_assessment(self, risk_metrics: RiskMetrics) -> Dict:
        """Get risk assessment based on calculated metrics."""
        assessment = {
            'overall_risk': 'MEDIUM',
            'volatility_risk': 'MEDIUM',
            'market_risk': 'MEDIUM',
            'downside_risk': 'MEDIUM',
            'recommendations': []
        }
        
        # Volatility risk assessment
        if risk_metrics.volatility > 0.4:
            assessment['volatility_risk'] = 'HIGH'
            assessment['recommendations'].append('Cổ phiếu có độ biến động cao, cần quản lý rủi ro chặt chẽ')
        elif risk_metrics.volatility < 0.2:
            assessment['volatility_risk'] = 'LOW'
            assessment['recommendations'].append('Cổ phiếu có độ biến động thấp, phù hợp với nhà đầu tư thận trọng')
        
        # Market risk assessment (Beta)
        if risk_metrics.beta > 1.2:
            assessment['market_risk'] = 'HIGH'
            assessment['recommendations'].append('Cổ phiếu nhạy cảm với biến động thị trường (Beta > 1.2)')
        elif risk_metrics.beta < 0.8:
            assessment['market_risk'] = 'LOW'
            assessment['recommendations'].append('Cổ phiếu ít nhạy cảm với biến động thị trường (Beta < 0.8)')
        
        # Downside risk assessment
        if risk_metrics.max_drawdown > 0.3:
            assessment['downside_risk'] = 'HIGH'
            assessment['recommendations'].append('Cổ phiếu có mức sụt giảm tối đa cao, cần đặt stop-loss')
        elif risk_metrics.max_drawdown < 0.15:
            assessment['downside_risk'] = 'LOW'
            assessment['recommendations'].append('Cổ phiếu có mức sụt giảm tối đa thấp, tương đối an toàn')
        
        # Overall risk assessment
        high_risk_count = sum([
            assessment['volatility_risk'] == 'HIGH',
            assessment['market_risk'] == 'HIGH',
            assessment['downside_risk'] == 'HIGH'
        ])
        
        if high_risk_count >= 2:
            assessment['overall_risk'] = 'HIGH'
        elif high_risk_count == 1:
            assessment['overall_risk'] = 'MEDIUM'
        else:
            assessment['overall_risk'] = 'LOW'
        
        return assessment
