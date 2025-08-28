"""
Risk analysis module for VN Stock Advisor.

This module provides comprehensive risk assessment including:
- Value at Risk (VaR) calculation
- Beta and correlation analysis
- Stress testing and scenario analysis
- Risk-adjusted return metrics
"""

from .risk_calculator import RiskCalculator
from .stress_testing import StressTesting
from .risk_metrics import RiskMetrics

__all__ = [
    'RiskCalculator',
    'StressTesting',
    'RiskMetrics'
]
