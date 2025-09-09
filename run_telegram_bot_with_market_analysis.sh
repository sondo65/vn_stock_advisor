#!/bin/bash

# Script to run Telegram Bot with Market Analysis
echo "🚀 Starting Telegram Bot with Market Analysis..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with required API keys:"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token"
    echo "SERPER_API_KEY=your_serper_key"
    echo "GEMINI_API_KEY=your_gemini_key (optional)"
    echo "OPENAI_API_KEY=your_openai_key (optional)"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check required environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set in .env file"
    exit 1
fi

if [ -z "$SERPER_API_KEY" ]; then
    echo "❌ SERPER_API_KEY not set in .env file"
    echo "Market analysis will not be available"
fi

# Check optional API keys
if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ Gemini API key found - Enhanced sentiment analysis enabled"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API key found - Enhanced sentiment analysis enabled"
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -e . > /dev/null 2>&1

# Run the bot
echo "🤖 Starting Telegram Bot..."
python telegram_portfolio_bot.py
