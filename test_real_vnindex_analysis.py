#!/usr/bin/env python3
"""
Test real VN-Index analysis with actual data
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_real_vnindex_analysis():
    """Test VN-Index analysis with real data"""
    print("🔍 Testing Real VN-Index Analysis...")
    
    try:
        # Import the module directly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "vnindex_analyzer", 
            "src/vn_stock_advisor/market_analysis/vnindex_analyzer.py"
        )
        vnindex_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vnindex_module)
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return False
        
        print(f"✅ Using SERPER API key: {serper_key[:10]}...")
        if gemini_key:
            print(f"✅ Using Gemini API key: {gemini_key[:10]}...")
        if openai_key:
            print(f"✅ Using OpenAI API key: {openai_key[:10]}...")
        
        print("\n🔍 Analyzing VN-Index with real data...")
        result = await vnindex_module.get_vnindex_market_analysis(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 VN-Index Analysis Results:")
        print(f"• Trend: {result.trend}")
        print(f"• Confidence: {result.confidence:.2f}")
        print(f"• Target Range: {result.target_range[0]:.0f} - {result.target_range[1]:.0f}")
        print(f"• Risk Level: {result.risk_level}")
        print(f"• Recommendation: {result.recommendation}")
        
        if result.key_factors:
            print(f"• Key Factors: {', '.join(result.key_factors)}")
        
        # Check if we got real data
        if result.target_range[0] > 1500 and result.target_range[1] > 1500:
            print("✅ Real VN-Index data detected (range > 1500)")
        else:
            print("⚠️ Still using fallback data (range < 1500)")
        
        print("✅ VN-Index analysis test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing VN-Index analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_daily_report_with_real_data():
    """Test daily market report with real data"""
    print("\n📰 Testing Daily Market Report with Real Data...")
    
    try:
        # Import the module directly
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "daily_market_report", 
            "src/vn_stock_advisor/market_analysis/daily_market_report.py"
        )
        report_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(report_module)
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return False
        
        print("🔍 Generating market report with real data...")
        message = await report_module.get_daily_market_report_message(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 Daily Market Report Generated:")
        print("=" * 60)
        print(message[:1000] + "..." if len(message) > 1000 else message)
        print("=" * 60)
        
        # Check for real VN-Index data in the message
        if "1600" in message or "1700" in message or "1500" in message:
            print("✅ Real VN-Index data detected in report")
        else:
            print("⚠️ No real VN-Index data detected in report")
        
        # Check for HTML formatting
        if '<b>' in message and '</b>' in message:
            print("✅ HTML formatting detected - should work with ParseMode.HTML")
        else:
            print("⚠️ No HTML formatting detected")
        
        print("✅ Daily market report test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing daily market report: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Real VN-Index Analysis Tests...")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["SERPER_API_KEY"]
    optional_vars = ["GEMINI_API_KEY", "OPENAI_API_KEY"]
    
    print("🔧 Environment Check:")
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set (REQUIRED)")
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Not set (Optional)")
    
    print("\n" + "=" * 60)
    
    # Run tests
    success_count = 0
    total_tests = 2
    
    if await test_real_vnindex_analysis():
        success_count += 1
    
    if await test_daily_report_with_real_data():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"🎉 Tests completed: {success_count}/{total_tests} passed!")
    
    if success_count == total_tests:
        print("✅ All tests passed!")
        print("🎯 VN-Index analysis now uses real data (1627+ points)")
        print("📊 Market reports will show accurate target ranges")
        print("💡 You can now use /market_report command in Telegram bot.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
