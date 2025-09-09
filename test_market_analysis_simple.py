#!/usr/bin/env python3
"""
Simple test script for Market Analysis without crewai dependency
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

async def test_news_collector_direct():
    """Test news collector directly without importing main module"""
    print("🔍 Testing News Collector Direct...")
    
    try:
        # Import directly from the module
        from vn_stock_advisor.market_analysis.news_collector import get_market_news_analysis
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            print("Please set SERPER_API_KEY in .env file")
            return
        
        print(f"✅ Using SERPER API key: {serper_key[:10]}...")
        if gemini_key:
            print(f"✅ Using Gemini API key: {gemini_key[:10]}...")
        if openai_key:
            print(f"✅ Using OpenAI API key: {openai_key[:10]}...")
        
        print("\n🔍 Fetching news...")
        result = await get_market_news_analysis(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 News Analysis Results:")
        print(f"• Domestic news: {len(result['news_data']['domestic'])} articles")
        print(f"• International news: {len(result['news_data']['international'])} articles")
        print(f"• Overall sentiment: {result['sentiment_analysis']['overall_sentiment']:.3f}")
        print(f"• Domestic sentiment: {result['sentiment_analysis']['domestic_sentiment']:.3f}")
        print(f"• International sentiment: {result['sentiment_analysis']['international_sentiment']:.3f}")
        
        if result['sentiment_analysis']['key_themes']:
            print(f"• Key themes: {', '.join(result['sentiment_analysis']['key_themes'])}")
        
        print("✅ News collector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing news collector: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_vnindex_analyzer_direct():
    """Test VN-Index analyzer directly"""
    print("\n📈 Testing VN-Index Analyzer Direct...")
    
    try:
        from vn_stock_advisor.market_analysis.vnindex_analyzer import get_vnindex_market_analysis
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return False
        
        print("🔍 Analyzing VN-Index...")
        result = await get_vnindex_market_analysis(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 VN-Index Analysis Results:")
        print(f"• Trend: {result.trend}")
        print(f"• Confidence: {result.confidence:.2f}")
        print(f"• Target Range: {result.target_range[0]:.0f} - {result.target_range[1]:.0f}")
        print(f"• Risk Level: {result.risk_level}")
        print(f"• Recommendation: {result.recommendation}")
        
        if result.key_factors:
            print(f"• Key Factors: {', '.join(result.key_factors)}")
        
        print("✅ VN-Index analyzer test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing VN-Index analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_daily_report_direct():
    """Test daily market report directly"""
    print("\n📰 Testing Daily Market Report Direct...")
    
    try:
        from vn_stock_advisor.market_analysis.daily_market_report import get_daily_market_report_message
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return False
        
        print("🔍 Generating market report...")
        message = await get_daily_market_report_message(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 Daily Market Report Generated:")
        print("=" * 60)
        print(message[:800] + "..." if len(message) > 800 else message)
        print("=" * 60)
        
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
    print("🚀 Starting Simple Market Analysis Tests...")
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
    total_tests = 3
    
    if await test_news_collector_direct():
        success_count += 1
    
    if await test_vnindex_analyzer_direct():
        success_count += 1
    
    if await test_daily_report_direct():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"🎉 Tests completed: {success_count}/{total_tests} passed!")
    
    if success_count == total_tests:
        print("✅ All tests passed! Market Analysis is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
