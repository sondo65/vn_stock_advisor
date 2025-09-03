#!/bin/bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd /Users/dotruongson/Documents/freelancer/vn_stock_advisor || exit 1
# Run directly with venv python, don't rely on shell activation
/Users/dotruongson/Documents/freelancer/vn_stock_advisor/.venv/bin/python /Users/dotruongson/Documents/freelancer/vn_stock_advisor/telegram_portfolio_bot.py >> \
  /Users/dotruongson/Library/Logs/vnstockadvisor.telegrambot.loginitem.out.log 2>> \
  /Users/dotruongson/Library/Logs/vnstockadvisor.telegrambot.loginitem.err.log &
disown