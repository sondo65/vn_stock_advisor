#!/usr/bin/env python3
"""
Demo script để test chức năng dự đoán giá mới được thêm vào bot Telegram.
"""

import asyncio
import sys
import os

# Thêm thư mục gốc vào path để import module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_portfolio_bot import PredictionEngine, TechnicalIndicators


async def test_technical_indicators():
    """Test các chỉ báo kỹ thuật với dữ liệu mẫu"""
    print("🧪 Testing Technical Indicators...")
    
    # Dữ liệu mẫu (giá tăng dần với một số biến động)
    sample_prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 
                     111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
                     119, 121, 123, 122, 124, 126, 125, 127, 129, 128]
    
    # Test SMA
    sma_20 = TechnicalIndicators.sma(sample_prices, 20)
    print(f"📊 SMA(20) cuối: {sma_20[-1]:.2f}")
    
    # Test RSI
    rsi = TechnicalIndicators.rsi(sample_prices, 14)
    print(f"📈 RSI(14) cuối: {rsi[-1]:.1f}")
    
    # Test MACD
    macd_data = TechnicalIndicators.macd(sample_prices)
    macd_val = macd_data['macd'][-1]
    signal_val = macd_data['signal'][-1]
    print(f"📉 MACD cuối: {macd_val:.3f}" if macd_val is not None else "📉 MACD cuối: N/A")
    print(f"📉 Signal cuối: {signal_val:.3f}" if signal_val is not None else "📉 Signal cuối: N/A")
    
    # Test Bollinger Bands
    bb_data = TechnicalIndicators.bollinger_bands(sample_prices, 20)
    print(f"📊 BB Upper: {bb_data['upper'][-1]:.2f}")
    print(f"📊 BB Lower: {bb_data['lower'][-1]:.2f}")
    
    print("✅ Technical Indicators test completed!\n")


async def test_prediction_engine():
    """Test PredictionEngine với các mã cổ phiếu thực tế"""
    print("🔮 Testing Prediction Engine...")
    
    # Test với một số mã cổ phiếu phổ biến
    test_symbols = ["VIC", "VCB", "VHM", "HPG", "GAS"]
    
    for symbol in test_symbols:
        print(f"\n📈 Analyzing {symbol}...")
        try:
            pred = await PredictionEngine.predict(symbol)
            
            print(f"  🎯 Decision: {pred.decision}")
            print(f"  📊 Confidence: {pred.confidence*100:.1f}%")
            print(f"  💡 Rationale: {pred.rationale}")
            
            if pred.scenarios:
                print("  🎲 Scenarios:")
                for scenario, prob in sorted(pred.scenarios.items(), key=lambda x: x[1], reverse=True):
                    print(f"    • {scenario}: {prob*100:.1f}%")
            
            if pred.technical_signals:
                signals = pred.technical_signals
                print("  📊 Technical Signals:")
                if signals.get('current_price'):
                    print(f"    • Current Price: {signals['current_price']:.2f}")
                if signals.get('rsi'):
                    rsi_val = signals['rsi']
                    rsi_status = "Oversold" if rsi_val < 30 else "Overbought" if rsi_val > 70 else "Neutral"
                    print(f"    • RSI: {rsi_val:.1f} ({rsi_status})")
                if signals.get('sma_20'):
                    print(f"    • SMA20: {signals['sma_20']:.2f}")
                    
        except Exception as e:
            print(f"  ❌ Error analyzing {symbol}: {str(e)}")
    
    print("\n✅ Prediction Engine test completed!")


async def test_data_retrieval():
    """Test việc lấy dữ liệu từ vnstock"""
    print("📊 Testing Data Retrieval...")
    
    symbol = "VIC"
    print(f"🔍 Fetching historical data for {symbol}...")
    
    try:
        data = await PredictionEngine.get_historical_data(symbol, days=30)
        if data:
            print(f"  ✅ Data retrieved successfully!")
            print(f"  📈 Data points: {len(data['close'])}")
            print(f"  📊 Price range: {min(data['close']):.2f} - {max(data['close']):.2f}")
            print(f"  📉 Latest close: {data['close'][-1]:.2f}")
        else:
            print(f"  ❌ No data retrieved for {symbol}")
    except Exception as e:
        print(f"  ❌ Error fetching data: {str(e)}")
    
    print("✅ Data retrieval test completed!\n")


async def main():
    """Chạy tất cả các test"""
    print("🚀 Starting Prediction System Demo...\n")
    
    # Test 1: Technical Indicators
    await test_technical_indicators()
    
    # Test 2: Data Retrieval
    await test_data_retrieval()
    
    # Test 3: Prediction Engine
    await test_prediction_engine()
    
    print("\n🎉 All tests completed!")
    print("\n📝 Usage in Telegram Bot:")
    print("  /predict VIC - Dự đoán giá cho VIC")
    print("  /analyze_now - Phân tích toàn bộ danh mục với dự đoán")
    print("  /help - Xem tất cả lệnh khả dụng")


if __name__ == "__main__":
    asyncio.run(main())
