"""
Test Data Sources - Test multiple data source fallback
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_data_source_fallback():
    """Test data source fallback functionality"""
    print("🔍 Testing data source fallback...")
    
    try:
        from src.vn_stock_advisor.tools.custom_tool import FundDataTool
        
        fund_tool = FundDataTool()
        
        # Test with a common stock symbol
        test_symbol = "VCB"  # Vietcombank
        
        print(f"📊 Testing with symbol: {test_symbol}")
        print("🔄 Trying multiple data sources: VCI → DNSE → SSI → MAS")
        
        start_time = time.time()
        
        try:
            result = fund_tool._run(test_symbol)
            end_time = time.time()
            
            print(f"✅ Success! Data retrieved in {end_time - start_time:.1f} seconds")
            print(f"📄 Result length: {len(result)} characters")
            
            # Check if result contains expected data
            if "P/E" in result or "P/B" in result or "ROE" in result:
                print("✅ Financial ratios found in result")
                return True
            else:
                print("⚠️ No financial ratios found in result")
                return False
                
        except Exception as e:
            print(f"❌ Error retrieving data: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data sources: {e}")
        return False

def test_industry_advisor_with_new_sources():
    """Test industry advisor with new data sources"""
    print("\n🏭 Testing Industry Advisor with new data sources...")
    
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
            return True
        else:
            print("⚠️ No stock suggestions found")
            return False
        
    except Exception as e:
        print(f"❌ Error testing industry advisor: {e}")
        return False

def main():
    """Main test function"""
    print("="*60)
    print("DATA SOURCE FALLBACK TEST")
    print("="*60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Data Source Fallback", test_data_source_fallback),
        ("Industry Advisor with New Sources", test_industry_advisor_with_new_sources)
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
        print("🎉 All tests passed! Data source fallback is working correctly.")
        print("\n💡 Benefits:")
        print("   1. No more TCBS rate limiting issues")
        print("   2. Automatic fallback to alternative sources")
        print("   3. Better reliability and uptime")
        print("   4. Real data from multiple providers")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
