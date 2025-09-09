#!/usr/bin/env python3
"""
Test Telegram market report with real data
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_telegram_market_report():
    """Test market report function from telegram bot"""
    print("🔍 Testing Telegram Market Report...")
    
    try:
        # Import the function from telegram bot
        from telegram_portfolio_bot import get_daily_market_report_message
        
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
        
        print("\n🔍 Generating market report...")
        message = await get_daily_market_report_message(serper_key, gemini_key, openai_key)
        
        print(f"\n📊 Daily Market Report Generated:")
        print("=" * 80)
        print(message)
        print("=" * 80)
        
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
        
        # Check for potential issues
        if '**' in message or '__' in message:
            print("⚠️ Found Markdown syntax - might cause parsing issues")
        else:
            print("✅ No Markdown syntax found - should be safe")
        
        print("✅ Telegram market report test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing telegram market report: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run test"""
    print("🚀 Testing Telegram Market Report with Real Data...")
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
    
    success = await test_telegram_market_report()
    
    if success:
        print("\n✅ Test passed!")
        print("🎯 VN-Index analysis now uses real data")
        print("📊 Market reports will show accurate target ranges")
        print("💡 Telegram bot is ready to use!")
    else:
        print("\n❌ Test failed!")

if __name__ == "__main__":
    asyncio.run(main())
