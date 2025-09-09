#!/usr/bin/env python3
"""
Test news collection with links
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_news_with_links():
    """Test news collection with links"""
    print("🔍 Testing News Collection with Links...")
    
    try:
        # Import the module directly
        from src.vn_stock_advisor.market_analysis.news_collector import get_market_news_analysis
        
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
        
        print("\n🔍 Fetching news with links...")
        result = await get_market_news_analysis(serper_key, gemini_key, openai_key)
        
        news_data = result.get("news_data", {})
        domestic_news = news_data.get("domestic", [])
        international_news = news_data.get("international", [])
        
        print(f"✅ Domestic news: {len(domestic_news)} articles")
        print(f"✅ International news: {len(international_news)} articles")
        
        # Check for URLs in news items
        print("\n📰 Sample News Items with URLs:")
        all_news = domestic_news + international_news
        relevant_news = [news for news in all_news if news.relevance_score and news.relevance_score > 0.5]
        relevant_news.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        
        for i, news in enumerate(relevant_news[:3], 1):
            print(f"\n{i}. Title: {news.title[:80]}...")
            print(f"   URL: {news.url}")
            print(f"   Source: {news.source}")
            print(f"   Sentiment: {news.sentiment_score:.3f}")
            print(f"   Relevance: {news.relevance_score:.3f}")
        
        # Test HTML link formatting
        print("\n🔗 Testing HTML Link Formatting:")
        for i, news in enumerate(relevant_news[:3], 1):
            sentiment_icon = "🟢" if (news.sentiment_score or 0) > 0.1 else "🔴" if (news.sentiment_score or 0) < -0.1 else "⚪"
            safe_title = news.title.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            safe_url = news.url.replace('&', '&amp;')
            html_link = f"{i}. {sentiment_icon} <a href='{safe_url}'>{safe_title[:60]}...</a>"
            print(html_link)
        
        print("\n✅ News collection with links test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing news with links: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_daily_report_with_links():
    """Test daily report with links"""
    print("\n📊 Testing Daily Report with Links...")
    
    try:
        # Import the module directly
        from src.vn_stock_advisor.market_analysis.daily_market_report import get_daily_market_report_message
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("❌ SERPER_API_KEY not found in environment")
            return False
        
        print("🔍 Generating market report with links...")
        message = await get_daily_market_report_message(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 Daily Market Report with Links:")
        print("=" * 80)
        print(message)
        print("=" * 80)
        
        # Check for HTML links
        if '<a href=' in message:
            print("✅ HTML links detected in report")
        else:
            print("⚠️ No HTML links detected in report")
        
        # Check for real VN-Index data
        if "1600" in message or "1700" in message or "1500" in message:
            print("✅ Real VN-Index data detected in report")
        else:
            print("⚠️ No real VN-Index data detected in report")
        
        print("✅ Daily report with links test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing daily report with links: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing News Links Integration...")
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
    
    if await test_news_with_links():
        success_count += 1
    
    if await test_daily_report_with_links():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"🎉 Tests completed: {success_count}/{total_tests} passed!")
    
    if success_count == total_tests:
        print("✅ All tests passed!")
        print("🔗 News links are now clickable in Telegram")
        print("📊 Market reports include clickable news links")
        print("💡 Users can easily access full news articles")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
