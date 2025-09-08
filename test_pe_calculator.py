#!/usr/bin/env python3
"""
Test script for P/E Calculator
"""
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from vn_stock_advisor.tools.pe_calculator import PECalculator

def test_pe_calculator():
    """Test P/E Calculator with MSB"""
    print("=== Test P/E Calculator ===")
    
    calculator = PECalculator()
    
    # Test với MSB
    print("\n1. Testing MSB P/E calculation...")
    result = calculator.calculate_accurate_pe("MSB", use_diluted_eps=True)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"✅ MSB P/E Analysis:")
    print(f"   - Symbol: {result['symbol']}")
    print(f"   - Current Price: {result['current_price']:,.0f} VND")
    print(f"   - Net Income TTM: {result['net_income_ttm']:,.0f} VND")
    print(f"   - Shares Outstanding: {result['shares_outstanding']:,.0f} cp")
    print(f"   - EPS Basic: {result['eps_basic']:,.0f} VND")
    print(f"   - EPS Diluted: {result['eps_diluted']:,.0f} VND")
    print(f"   - EPS Used: {result['eps_used']:,.0f} VND")
    print(f"   - Accurate P/E: {result['pe_ratio']:.2f}")
    print(f"   - Source P/E: {result['source_pe']}")
    print(f"   - P/E Difference: {result['pe_difference']:.2f}")
    print(f"   - Calculation Method: {result['calculation_method']}")
    print(f"   - Last Updated: {result['last_updated']}")
    
    # Test bias detection
    print("\n2. Testing bias detection...")
    bias_result = calculator.detect_pe_bias("MSB")
    
    if "error" in bias_result:
        print(f"❌ Bias detection error: {bias_result['error']}")
    else:
        print(f"✅ Bias Detection Results:")
        print(f"   - Accurate P/E: {bias_result['accurate_pe']}")
        print(f"   - Source P/E: {bias_result['source_pe']}")
        print(f"   - P/E Difference: {bias_result['pe_difference']}")
        print(f"   - Bias Detected: {bias_result['bias_detected']}")
        print(f"   - Recommendations: {bias_result['recommendations']}")
    
    # Test với một cổ phiếu khác
    print("\n3. Testing VIC P/E calculation...")
    vic_result = calculator.calculate_accurate_pe("VIC", use_diluted_eps=True)
    
    if "error" in vic_result:
        print(f"❌ VIC Error: {vic_result['error']}")
    else:
        print(f"✅ VIC P/E Analysis:")
        print(f"   - Accurate P/E: {vic_result['pe_ratio']:.2f}")
        print(f"   - Source P/E: {vic_result['source_pe']}")
        print(f"   - P/E Difference: {vic_result['pe_difference']:.2f}")

if __name__ == "__main__":
    test_pe_calculator()
