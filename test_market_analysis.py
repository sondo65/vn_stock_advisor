#!/usr/bin/env python3
"""
Demo script để test chức năng Market Analysis
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_news_collector():
    """Test news collector functionality"""
    print("🔍 Testing News Collector...")
    
    try:
        from src.vn_stock_advisor.market_analysis.news_collector import get_market_news_analysis
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return
        
        print(f"✅ Using SERPER API key: {serper_key[:10]}...")
        if gemini_key:
            print(f"✅ Using Gemini API key: {gemini_key[:10]}...")
        if openai_key:
            print(f"✅ Using OpenAI API key: {openai_key[:10]}...")
        
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
        
    except Exception as e:
        print(f"❌ Error testing news collector: {e}")


async def test_vnindex_analyzer():
    """Test VN-Index analyzer functionality"""
    print("\n📈 Testing VN-Index Analyzer...")
    
    try:
        from src.vn_stock_advisor.market_analysis.vnindex_analyzer import get_vnindex_market_analysis
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return
        
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
        
    except Exception as e:
        print(f"❌ Error testing VN-Index analyzer: {e}")


async def test_daily_report():
    """Test daily market report generation"""
    print("\n📰 Testing Daily Market Report...")
    
    try:
        from src.vn_stock_advisor.market_analysis.daily_market_report import get_daily_market_report_message
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return
        
        message = await get_daily_market_report_message(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 Daily Market Report Generated:")
        print("=" * 50)
        print(message)
        print("=" * 50)
        
        print("✅ Daily market report test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing daily market report: {e}")


async def main():
    """Run all tests"""
    print("🚀 Starting Market Analysis Tests...")
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
    await test_news_collector()
    await test_vnindex_analyzer()
    await test_daily_report()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
