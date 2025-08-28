#!/usr/bin/env python3
"""
Test script for Phase 2 ML and Advanced Technical Analysis modules only.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np

def test_pattern_recognition():
    """Test Pattern Recognition module."""
    print("🔍 Testing Pattern Recognition...")
    
    try:
        from vn_stock_advisor.ml.pattern_recognition import PatternRecognition
        
        # Generate sample price data
        np.random.seed(42)
        base_prices = np.linspace(100, 120, 100)
        noise = np.random.normal(0, 2, 100)
        prices = base_prices + noise
        
        # Create double bottom pattern
        prices[40:45] = 95  # First bottom
        prices[60:65] = 96  # Second bottom
        prices[50:55] = 105  # Peak between bottoms
        
        volumes = np.random.randint(1000, 10000, 100)
        
        pattern_analyzer = PatternRecognition()
        patterns = pattern_analyzer.analyze_patterns(prices.tolist(), volumes.tolist())
        summary = pattern_analyzer.get_pattern_summary(patterns)
        
        print(f"✅ Pattern Recognition: Detected {summary['total_patterns']} patterns")
        print(f"   Primary signal: {summary['primary_signal']}")
        print(f"   Recommendation: {summary['recommendation']}")
        return True
    except Exception as e:
        print(f"❌ Pattern Recognition: {e}")
        return False

def test_anomaly_detection():
    """Test Anomaly Detection module."""
    print("🚨 Testing Anomaly Detection...")
    
    try:
        from vn_stock_advisor.ml.anomaly_detection import AnomalyDetection
        
        # Generate normal price data with anomalies
        np.random.seed(42)
        prices = np.random.normal(100, 5, 100)
        volumes = np.random.normal(5000, 1000, 100)
        
        # Add price anomalies
        prices[50] = 150  # Price spike
        prices[75] = 50   # Price drop
        
        # Add volume anomalies
        volumes[30] = 50000  # Volume spike
        volumes[80] = 20000  # Volume spike
        
        anomaly_detector = AnomalyDetection()
        analysis = anomaly_detector.comprehensive_anomaly_analysis(prices.tolist(), volumes.tolist())
        
        print(f"✅ Anomaly Detection: Found {analysis['total_anomalies']} anomalies")
        print(f"   Risk level: {analysis['risk_level']}")
        print(f"   Summary: {analysis['summary']}")
        return True
    except Exception as e:
        print(f"❌ Anomaly Detection: {e}")
        return False

def test_sentiment_analyzer():
    """Test Sentiment Analyzer module."""
    print("💭 Testing Sentiment Analyzer...")
    
    try:
        from vn_stock_advisor.ml.sentiment_analyzer import SentimentAnalyzer
        
        sample_news = [
            {
                "title": "Cổ phiếu ABC tăng mạnh do kết quả kinh doanh tích cực",
                "content": "Công ty ABC báo cáo lợi nhuận tăng 25% so với cùng kỳ năm trước nhờ tăng trưởng doanh thu mạnh mẽ.",
                "source": "VnExpress"
            },
            {
                "title": "Lo ngại về triển vọng kinh tế tác động tiêu cực đến ABC",
                "content": "Các chuyên gia cảnh báo rằng lạm phát cao có thể ảnh hưởng đến biên lợi nhuận của ABC trong quý tới.",
                "source": "CafeF"
            }
        ]
        
        sentiment_analyzer = SentimentAnalyzer()
        result = sentiment_analyzer.analyze_news_batch(sample_news)
        
        print(f"✅ Sentiment Analysis: Analyzed {result['total_articles']} articles")
        print(f"   Average sentiment: {result['average_sentiment']:.2f}")
        print(f"   Market outlook: {result['market_outlook']}")
        print(f"   Recommendation: {result['recommendation']}")
        return True
    except Exception as e:
        print(f"❌ Sentiment Analysis: {e}")
        return False

def test_fibonacci_calculator():
    """Test Fibonacci Calculator module."""
    print("📐 Testing Fibonacci Calculator...")
    
    try:
        from vn_stock_advisor.technical.fibonacci_calculator import FibonacciCalculator
        
        # Generate trending price data
        np.random.seed(42)
        trend = np.linspace(80, 120, 100)
        noise = np.random.normal(0, 2, 100)
        prices = trend + noise
        
        fib_calc = FibonacciCalculator()
        summary = fib_calc.get_fibonacci_summary(prices.tolist())
        
        if 'error' not in summary:
            print(f"✅ Fibonacci Calculator: Analysis completed")
            print(f"   Trend direction: {summary['trend_direction']}")
            print(f"   Swing High: {summary['swing_high']:.2f}")
            print(f"   Swing Low: {summary['swing_low']:.2f}")
            print(f"   Retracement levels: {len(summary['retracement_levels'])}")
            return True
        else:
            print(f"❌ Fibonacci Calculator: {summary['error']}")
            return False
    except Exception as e:
        print(f"❌ Fibonacci Calculator: {e}")
        return False

def test_ichimoku_analyzer():
    """Test Ichimoku Analyzer module."""
    print("☁️ Testing Ichimoku Analyzer...")
    
    try:
        from vn_stock_advisor.technical.ichimoku_analyzer import IchimokuAnalyzer
        
        # Generate OHLC data
        np.random.seed(42)
        closes = np.random.normal(100, 5, 100)
        highs = closes + np.random.uniform(0, 3, 100)
        lows = closes - np.random.uniform(0, 3, 100)
        
        ichimoku_analyzer = IchimokuAnalyzer()
        summary = ichimoku_analyzer.get_ichimoku_summary(highs.tolist(), lows.tolist(), closes.tolist())
        
        if 'error' not in summary:
            signal = summary['trading_signal']
            print(f"✅ Ichimoku Analyzer: Analysis completed")
            print(f"   Signal: {signal['signal']} ({signal['strength']})")
            print(f"   Confidence: {signal['confidence']:.1%}")
            return True
        else:
            print(f"❌ Ichimoku Analyzer: Error in analysis")
            return False
    except Exception as e:
        print(f"❌ Ichimoku Analyzer: {e}")
        return False

def test_volume_analyzer():
    """Test Volume Analyzer module."""
    print("📊 Testing Volume Analyzer...")
    
    try:
        from vn_stock_advisor.technical.volume_analyzer import VolumeAnalyzer
        
        # Generate price and volume data
        np.random.seed(42)
        prices = np.random.normal(100, 5, 100)
        volumes = np.random.normal(5000, 1000, 100)
        highs = prices + np.random.uniform(0, 2, 100)
        lows = prices - np.random.uniform(0, 2, 100)
        
        volume_analyzer = VolumeAnalyzer()
        summary = volume_analyzer.get_volume_summary(
            prices.tolist(), volumes.tolist(), highs.tolist(), lows.tolist()
        )
        
        if 'error' not in summary:
            print(f"✅ Volume Analyzer: Analysis completed")
            print(f"   Price vs VWAP: {summary['price_vs_vwap']}")
            print(f"   Volume profile position: {summary['volume_profile_position']}")
            print(f"   Volume trend: {summary['volume_trend']['volume_assessment']}")
            return True
        else:
            print(f"❌ Volume Analyzer: {summary['error']}")
            return False
    except Exception as e:
        print(f"❌ Volume Analyzer: {e}")
        return False

def test_divergence_detector():
    """Test Divergence Detector module."""
    print("🔄 Testing Divergence Detector...")
    
    try:
        from vn_stock_advisor.technical.divergence_detector import DivergenceDetector
        
        # Generate data with potential divergences
        np.random.seed(42)
        prices = np.random.normal(100, 5, 100)
        volumes = np.random.normal(5000, 1000, 100)
        highs = prices + np.random.uniform(0, 2, 100)
        lows = prices - np.random.uniform(0, 2, 100)
        
        # Create artificial divergence
        prices[80:] = np.linspace(prices[79], prices[79] + 10, 20)  # Rising prices
        
        divergence_detector = DivergenceDetector()
        analysis = divergence_detector.get_comprehensive_divergence_analysis(
            prices.tolist(), volumes.tolist(), highs.tolist(), lows.tolist()
        )
        
        if 'error' not in analysis:
            print(f"✅ Divergence Detector: Analysis completed")
            print(f"   Total divergences: {analysis['total_divergences']}")
            print(f"   Overall signal: {analysis['overall_signal']}")
            return True
        else:
            print(f"❌ Divergence Detector: {analysis['error']}")
            return False
    except Exception as e:
        print(f"❌ Divergence Detector: {e}")
        return False

def main():
    """Run all Phase 2 module tests."""
    print("🚀 PHASE 2 MODULE TESTING - ML & ADVANCED TECHNICAL ANALYSIS")
    print("=" * 60)
    
    tests = [
        test_pattern_recognition,
        test_anomaly_detection,
        test_sentiment_analyzer,
        test_fibonacci_calculator,
        test_ichimoku_analyzer,
        test_volume_analyzer,
        test_divergence_detector
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: Exception - {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL PHASE 2 MODULE TESTS PASSED! ML and Advanced Technical Analysis ready!")
        return True
    else:
        print(f"⚠️  {failed} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
