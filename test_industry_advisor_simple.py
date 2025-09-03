"""
Simple test for Industry Stock Advisor - Test without API calls
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test importing modules"""
    print("🔍 Testing imports...")
    
    try:
        from src.vn_stock_advisor.scanner import get_available_industries
        print("✅ Import get_available_industries successful")
        
        from src.vn_stock_advisor.scanner import IndustryStockAdvisor
        print("✅ Import IndustryStockAdvisor successful")
        
        from src.vn_stock_advisor.scanner import IndustryStockSuggester
        print("✅ Import IndustryStockSuggester successful")
        
        from src.vn_stock_advisor.scanner import IndustryAnalyzer
        print("✅ Import IndustryAnalyzer successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_available_industries():
    """Test getting available industries"""
    print("\n📋 Testing available industries...")
    
    try:
        from src.vn_stock_advisor.scanner import get_available_industries
        
        industries = get_available_industries()
        print(f"✅ Found {len(industries)} industries:")
        
        for i, industry in enumerate(industries, 1):
            print(f"   {i}. {industry}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting industries: {e}")
        return False

def test_industry_summary():
    """Test getting industry summary"""
    print("\n📊 Testing industry summary...")
    
    try:
        from src.vn_stock_advisor.scanner import IndustryStockAdvisor
        
        advisor = IndustryStockAdvisor()
        summary = advisor.get_industry_summary("Tài chính ngân hàng")
        
        if "error" not in summary:
            print("✅ Industry summary retrieved successfully:")
            print(f"   Industry: {summary['industry']}")
            print(f"   Stock count: {summary['stock_count']}")
            print(f"   PE ratio: {summary['benchmark']['pe_ratio']}")
            print(f"   PB ratio: {summary['benchmark']['pb_ratio']}")
            return True
        else:
            print(f"❌ Error in summary: {summary['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting summary: {e}")
        return False

def test_industry_benchmarks():
    """Test industry benchmarks"""
    print("\n⚖️ Testing industry benchmarks...")
    
    try:
        from src.vn_stock_advisor.scanner import IndustryStockSuggester
        
        suggester = IndustryStockSuggester()
        benchmarks = suggester.industry_benchmarks
        
        print(f"✅ Loaded {len(benchmarks)} industry benchmarks:")
        
        for i, (industry, benchmark) in enumerate(list(benchmarks.items())[:5], 1):
            print(f"   {i}. {industry}: PE={benchmark.pe_ratio}, PB={benchmark.pb_ratio}")
        
        if len(benchmarks) > 5:
            print(f"   ... and {len(benchmarks) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading benchmarks: {e}")
        return False

def test_industry_stocks():
    """Test industry stock lists"""
    print("\n📈 Testing industry stock lists...")
    
    try:
        from src.vn_stock_advisor.scanner import IndustryStockSuggester
        
        suggester = IndustryStockSuggester()
        industry_stocks = suggester.industry_stocks
        
        print(f"✅ Loaded stock lists for {len(industry_stocks)} industries:")
        
        for industry, stocks in list(industry_stocks.items())[:3]:
            print(f"   {industry}: {len(stocks)} stocks")
            print(f"      Top 3: {', '.join(stocks[:3])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading stock lists: {e}")
        return False

def main():
    """Main test function"""
    print("="*60)
    print("INDUSTRY STOCK ADVISOR - SIMPLE TEST")
    print("="*60)
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Import Test", test_imports),
        ("Available Industries", test_available_industries),
        ("Industry Summary", test_industry_summary),
        ("Industry Benchmarks", test_industry_benchmarks),
        ("Industry Stocks", test_industry_stocks)
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
        print("🎉 All tests passed! Industry Stock Advisor is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Run: streamlit run industry_stock_advisor_ui.py")
        print("   2. Run: python demo_industry_advisor.py")
        print("   3. Check: INDUSTRY_STOCK_ADVISOR_GUIDE.md")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
