"""
Stress Testing for VN Stock Advisor.

This module provides stress testing capabilities to evaluate
stock performance under various adverse market conditions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class StressTestScenario:
    """Scenario for stress testing."""
    name: str
    market_shock: float  # Market decline percentage
    volatility_increase: float  # Volatility multiplier
    correlation_increase: float  # Correlation increase
    description: str

@dataclass
class StressTestResult:
    """Result of stress testing."""
    scenario_name: str
    expected_return: float
    worst_case_return: float
    probability_of_loss: float
    var_stressed: float
    max_drawdown_stressed: float
    risk_level: str

class StressTesting:
    """
    Perform stress testing on stock portfolios and individual stocks.
    """
    
    def __init__(self):
        self.default_scenarios = self._create_default_scenarios()
    
    def _create_default_scenarios(self) -> List[StressTestScenario]:
        """Create default stress test scenarios."""
        return [
            StressTestScenario(
                name="Mild Recession",
                market_shock=-0.15,
                volatility_increase=1.5,
                correlation_increase=0.2,
                description="Thị trường suy thoái nhẹ với giảm 15%"
            ),
            StressTestScenario(
                name="Moderate Recession",
                market_shock=-0.25,
                volatility_increase=2.0,
                correlation_increase=0.4,
                description="Thị trường suy thoái vừa phải với giảm 25%"
            ),
            StressTestScenario(
                name="Severe Recession",
                market_shock=-0.40,
                volatility_increase=2.5,
                correlation_increase=0.6,
                description="Thị trường suy thoái nghiêm trọng với giảm 40%"
            ),
            StressTestScenario(
                name="Market Crash",
                market_shock=-0.50,
                volatility_increase=3.0,
                correlation_increase=0.8,
                description="Thị trường sụp đổ với giảm 50%"
            ),
            StressTestScenario(
                name="Interest Rate Shock",
                market_shock=-0.10,
                volatility_increase=1.8,
                correlation_increase=0.3,
                description="Sốc lãi suất với giảm thị trường 10%"
            ),
            StressTestScenario(
                name="Currency Crisis",
                market_shock=-0.20,
                volatility_increase=2.2,
                correlation_increase=0.5,
                description="Khủng hoảng tiền tệ với giảm thị trường 20%"
            )
        ]
    
    def run_stress_test(self, 
                        stock_returns: List[float],
                        market_returns: List[float],
                        stock_beta: float,
                        scenario: StressTestScenario = None) -> StressTestResult:
        """
        Run stress test on a stock.
        
        Args:
            stock_returns: Historical stock returns
            market_returns: Historical market returns
            stock_beta: Stock beta relative to market
            scenario: Stress test scenario (uses default if None)
            
        Returns:
            StressTestResult object
        """
        if scenario is None:
            scenario = self.default_scenarios[1]  # Default to moderate recession
        
        # Calculate base metrics
        base_return = np.mean(stock_returns)
        base_volatility = np.std(stock_returns)
        
        # Apply stress factors
        stressed_return = self._calculate_stressed_return(
            base_return, stock_beta, scenario
        )
        
        stressed_volatility = base_volatility * scenario.volatility_increase
        
        # Calculate stressed VaR
        var_stressed = self._calculate_stressed_var(
            stressed_return, stressed_volatility
        )
        
        # Calculate worst case return
        worst_case_return = stressed_return - 2 * stressed_volatility
        
        # Calculate probability of loss
        probability_of_loss = self._calculate_loss_probability(
            stressed_return, stressed_volatility
        )
        
        # Calculate stressed max drawdown
        max_drawdown_stressed = self._calculate_stressed_drawdown(
            stressed_return, stressed_volatility
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            stressed_return, var_stressed, probability_of_loss
        )
        
        return StressTestResult(
            scenario_name=scenario.name,
            expected_return=stressed_return,
            worst_case_return=worst_case_return,
            probability_of_loss=probability_of_loss,
            var_stressed=var_stressed,
            max_drawdown_stressed=max_drawdown_stressed,
            risk_level=risk_level
        )
    
    def _calculate_stressed_return(self, 
                                 base_return: float, 
                                 beta: float, 
                                 scenario: StressTestScenario) -> float:
        """Calculate expected return under stress scenario."""
        # CAPM model with stress adjustment
        risk_free_rate = 0.05  # Assume 5% risk-free rate
        market_premium = 0.08  # Assume 8% market risk premium
        
        # Apply market shock
        stressed_market_return = scenario.market_shock
        
        # Calculate stressed return using CAPM
        stressed_return = risk_free_rate + beta * (stressed_market_return - risk_free_rate)
        
        return stressed_return
    
    def _calculate_stressed_var(self, 
                               expected_return: float, 
                               volatility: float, 
                               confidence: float = 0.95) -> float:
        """Calculate VaR under stress conditions."""
        if confidence == 0.95:
            z_score = 1.645
        elif confidence == 0.99:
            z_score = 2.326
        else:
            z_score = 1.645  # Default to 95% confidence
        
        var = expected_return - z_score * volatility
        return abs(var)
    
    def _calculate_loss_probability(self, 
                                   expected_return: float, 
                                   volatility: float) -> float:
        """Calculate probability of negative return."""
        if volatility == 0:
            return 0.5 if expected_return < 0 else 0.0
        
        # Using normal distribution approximation
        z_score = -expected_return / volatility
        probability = 0.5 * (1 - self._erf(z_score / np.sqrt(2)))
        
        return probability
    
    def _erf(self, x: float) -> float:
        """Error function approximation."""
        # Simple approximation of error function
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911
        
        sign = 1 if x >= 0 else -1
        x = abs(x)
        
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)
        
        return sign * y
    
    def _calculate_stressed_drawdown(self, 
                                    expected_return: float, 
                                    volatility: float) -> float:
        """Calculate expected maximum drawdown under stress."""
        # Simplified drawdown calculation
        if expected_return >= 0:
            # If expected return is positive, drawdown is limited
            max_dd = min(0.3, volatility * 2)  # Cap at 30%
        else:
            # If expected return is negative, drawdown can be significant
            max_dd = abs(expected_return) + volatility * 1.5
        
        return min(max_dd, 0.8)  # Cap at 80%
    
    def _determine_risk_level(self, 
                             expected_return: float, 
                             var: float, 
                             loss_probability: float) -> str:
        """Determine risk level based on stress test results."""
        risk_score = 0
        
        # Return risk
        if expected_return < -0.2:
            risk_score += 3
        elif expected_return < -0.1:
            risk_score += 2
        elif expected_return < 0:
            risk_score += 1
        
        # VaR risk
        if var > 0.3:
            risk_score += 3
        elif var > 0.2:
            risk_score += 2
        elif var > 0.1:
            risk_score += 1
        
        # Loss probability risk
        if loss_probability > 0.7:
            risk_score += 3
        elif loss_probability > 0.5:
            risk_score += 2
        elif loss_probability > 0.3:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 7:
            return "EXTREME"
        elif risk_score >= 5:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        elif risk_score >= 1:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def run_multiple_scenarios(self, 
                              stock_returns: List[float],
                              market_returns: List[float],
                              stock_beta: float) -> List[StressTestResult]:
        """Run stress tests on multiple scenarios."""
        results = []
        
        for scenario in self.default_scenarios:
            result = self.run_stress_test(
                stock_returns, market_returns, stock_beta, scenario
            )
            results.append(result)
        
        return results
    
    def generate_stress_report(self, results: List[StressTestResult]) -> str:
        """Generate comprehensive stress test report."""
        report = "# Báo Cáo Stress Test\n\n"
        
        for result in results:
            report += f"## {result.scenario_name}\n"
            report += f"- **Mô tả**: {result.description}\n"
            report += f"- **Lợi nhuận kỳ vọng**: {result.expected_return:.2%}\n"
            report += f"- **Trường hợp xấu nhất**: {result.worst_case_return:.2%}\n"
            report += f"- **Xác suất thua lỗ**: {result.probability_of_loss:.2%}\n"
            report += f"- **VaR (95%)**: {result.var_stressed:.2%}\n"
            report += f"- **Mức sụt giảm tối đa**: {result.max_drawdown_stressed:.2%}\n"
            report += f"- **Mức độ rủi ro**: {result.risk_level}\n\n"
        
        # Summary
        high_risk_scenarios = [r for r in results if r.risk_level in ['HIGH', 'EXTREME']]
        report += f"## Tóm Tắt\n"
        report += f"- **Tổng số kịch bản**: {len(results)}\n"
        report += f"- **Kịch bản rủi ro cao**: {len(high_risk_scenarios)}\n"
        report += f"- **Khuyến nghị**: "
        
        if len(high_risk_scenarios) > len(results) / 2:
            report += "Cổ phiếu có rủi ro cao trong nhiều kịch bản, cần quản lý rủi ro chặt chẽ\n"
        else:
            report += "Cổ phiếu có khả năng chống chịu tốt trong hầu hết kịch bản\n"
        
        return report
