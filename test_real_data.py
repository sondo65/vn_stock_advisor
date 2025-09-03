"""
Test Real Data - Test with real data sources
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_single_stock_data():
    """Test getting data for a single stock"""
    print("🔍 Testing single stock data retrieval...")
    
    try:
        from src.vn_stock_advisor.tools.custom_tool import FundDataTool
        
        fund_tool = FundDataTool()
        
        # Test with a common stock symbol
        test_symbol = "VCB"  # Vietcombank
        
        print(f"📊 Testing with symbol: {test_symbol}")
        print("🔄 Using real data sources: VCI → DNSE → SSI")
        
        start_time = time.time()
        
        try:
            result = fund_tool._run(test_symbol)
            end_time = time.time()
            
            print(f"✅ Success! Data retrieved in {end_time - start_time:.1f} seconds")
            print(f"📄 Result length: {len(result)} characters")
            
            # Check if result contains expected data
            if "P/E" in result or "P/B" in result or "ROE" in result:
                print("✅ Financial ratios found in result")
                print("📋 Sample result:")
                print(result[:200] + "..." if len(result) > 200 else result)
                return True
            else:
                print("⚠️ No financial ratios found in result")
                print("📋 Full result:")
                print(result)
                return False
                
        except Exception as e:
            print(f"❌ Error retrieving data: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data retrieval: {e}")
        return False

def test_industry_advisor_with_real_data():
    """Test industry advisor with real data"""
    print("\n🏭 Testing Industry Advisor with real data...")
    
    try:
        from src.vn_stock_advisor.scanner import suggest_industry_stocks
        
        print("📊 Testing with minimal parameters...")
        
        start_time = time.time()
        
        # Test with very small parameters
        stocks = suggest_industry_stocks(
            industry="Tài chính ngân hàng",
            max_stocks=1,  # Only 1 stock
            min_score=5.0  # Low threshold
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Analysis completed in {total_time:.1f} seconds")
        
        if stocks:
            print(f"✅ Found {len(stocks)} stock suggestions")
            for stock in stocks:
                print(f"   • {stock.symbol}: {stock.total_score:.1f}/10")
                print(f"     Company: {stock.company_name}")
                print(f"     Industry: {stock.industry}")
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
    print("REAL DATA TEST")
    print("="*60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Single Stock Data", test_single_stock_data),
        ("Industry Advisor with Real Data", test_industry_advisor_with_real_data)
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
        print("🎉 All tests passed! Real data retrieval is working correctly.")
        print("\n💡 Benefits:")
        print("   1. Using real financial data from VCI, DNSE, SSI")
        print("   2. Random delays to avoid rate limiting")
        print("   3. Better error handling and fallback")
        print("   4. Proper logging for debugging")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
