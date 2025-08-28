"""
VN Stock Advisor - Advanced AI-powered Stock Analysis System

This package provides comprehensive stock analysis including:
- Fundamental analysis with industry benchmarking
- Technical analysis with advanced indicators
- Macroeconomic analysis and news sentiment
- Risk assessment and stress testing
- Machine learning-powered insights
- Advanced scoring and confidence calculation
"""

__version__ = "0.6.0"
__author__ = "VN Stock Advisor Team"

# Import main components
from .crew import VnStockAdvisor
from .scoring import WeightedScoringSystem, ConfidenceCalculator, ValidationMetrics
from .risk_analysis import RiskCalculator, StressTesting, RiskMetrics
from .ml import PatternRecognition, AnomalyDetection, SentimentAnalyzer
from .technical import FibonacciCalculator, IchimokuAnalyzer, VolumeAnalyzer, DivergenceDetector

__all__ = [
    'VnStockAdvisor',
    'WeightedScoringSystem',
    'ConfidenceCalculator',
    'ValidationMetrics',
    'RiskCalculator',
    'StressTesting',
    'RiskMetrics',
    'PatternRecognition',
    'AnomalyDetection',
    'SentimentAnalyzer',
    'FibonacciCalculator',
    'IchimokuAnalyzer',
    'VolumeAnalyzer',
    'DivergenceDetector'
]
