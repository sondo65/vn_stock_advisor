#!/usr/bin/env python3
"""
Test Pattern Recognition module independently.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np

# Direct import without going through __init__.py
from vn_stock_advisor.ml.pattern_recognition import PatternRecognition

def test_pattern_recognition():
    """Test Pattern Recognition module."""
    print("🔍 Testing Pattern Recognition...")
    
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

if __name__ == "__main__":
    try:
        success = test_pattern_recognition()
        print(f"Result: {'PASS' if success else 'FAIL'}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
