"""
Machine Learning module for VN Stock Advisor.

This module provides advanced ML-powered analysis including:
- Pattern recognition for price patterns
- Anomaly detection for outlier identification
- Sentiment analysis for news and social media
- Predictive modeling for price forecasting
"""

from .pattern_recognition import PatternRecognition
from .anomaly_detection import AnomalyDetection
from .sentiment_analyzer import SentimentAnalyzer

__all__ = [
    'PatternRecognition',
    'AnomalyDetection',
    'SentimentAnalyzer'
]
