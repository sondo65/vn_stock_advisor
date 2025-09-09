#!/usr/bin/env python3
"""
Test script để kiểm tra fix lỗi Markdown parsing
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_market_report_fix():
    """Test market report with HTML formatting"""
    print("🔍 Testing Market Report Fix...")
    
    try:
        from src.vn_stock_advisor.market_analysis.daily_market_report import get_daily_market_report_message
        
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
        
        print("\n🔍 Generating market report...")
        message = await get_daily_market_report_message(serper_key, gemini_key, openai_key)
        
        print("\n📊 Generated Message Preview:")
        print("=" * 60)
        print(message[:500] + "..." if len(message) > 500 else message)
        print("=" * 60)
        
        # Check for potential HTML parsing issues
        if '<' in message and '>' in message:
            print("✅ HTML tags detected - should work with ParseMode.HTML")
        else:
            print("⚠️ No HTML tags detected - using plain text")
        
        # Check for special characters that might cause issues
        problematic_chars = ['*', '_', '`', '[', ']', '(', ')']
        found_chars = [char for char in problematic_chars if char in message]
        if found_chars:
            print(f"⚠️ Found potentially problematic characters: {found_chars}")
        else:
            print("✅ No problematic characters found")
        
        print("\n✅ Market report test completed successfully!")
        print("📝 Message length:", len(message), "characters")
        
    except Exception as e:
        print(f"❌ Error testing market report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_market_report_fix())
