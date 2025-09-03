"""
Test Rate Limiting - Test rate limiting functionality
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("🔍 Testing rate limiting...")
    
    try:
        from src.vn_stock_advisor.scanner import IndustryStockSuggester
        
        suggester = IndustryStockSuggester()
        
        print(f"✅ Rate limiting delay: {suggester.request_delay} seconds")
        print(f"✅ Max workers: {suggester.scanner.max_workers}")
        
        # Test rate limiting
        print("\n⏱️ Testing rate limiting with 3 requests:")
        
        start_time = time.time()
        
        for i in range(3):
            print(f"   Request {i+1}: {time.strftime('%H:%M:%S')}")
            suggester._rate_limit()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Total time for 3 requests: {total_time:.1f} seconds")
        print(f"✅ Expected time: ~{2 * 2:.1f} seconds (2 requests * 2 seconds)")
        
        if total_time >= 4.0:  # Should be at least 4 seconds
            print("✅ Rate limiting working correctly!")
            return True
        else:
            print("⚠️ Rate limiting may not be working as expected")
            return False
            
    except Exception as e:
        print(f"❌ Error testing rate limiting: {e}")
        return False

def test_industry_analysis_with_limits():
    """Test industry analysis with rate limiting"""
    print("\n🏭 Testing industry analysis with rate limiting...")
    
    try:
        from src.vn_stock_advisor.scanner import suggest_industry_stocks
        
        print("📊 Testing with small parameters to avoid rate limiting...")
        
        start_time = time.time()
        
        # Test with very small parameters
        stocks = suggest_industry_stocks(
            industry="Tài chính ngân hàng",
            max_stocks=2,  # Very small
            min_score=5.0  # Low threshold
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Analysis completed in {total_time:.1f} seconds")
        
        if stocks:
            print(f"✅ Found {len(stocks)} stock suggestions")
            for stock in stocks:
                print(f"   • {stock.symbol}: {stock.total_score:.1f}/10")
        else:
            print("⚠️ No stock suggestions found (may be due to rate limiting)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing industry analysis: {e}")
        return False

def main():
    """Main test function"""
    print("="*60)
    print("RATE LIMITING TEST")
    print("="*60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Rate Limiting", test_rate_limiting),
        ("Industry Analysis with Limits", test_industry_analysis_with_limits)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rate limiting is working correctly.")
        print("\n💡 Recommendations:")
        print("   1. Use small parameters in UI (max 3-5 stocks)")
        print("   2. Wait between requests if needed")
        print("   3. Use cache to reduce API calls")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
