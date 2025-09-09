#!/usr/bin/env python3
"""
Demo script để minh họa tính năng Trailing Stop trong Telegram Portfolio Bot

Tính năng Trailing Stop (Dừng lỗ động):
- Tự động điều chỉnh mức dừng lỗ theo giá cao nhất
- Bảo vệ lợi nhuận khi giá tăng
- Hạn chế rủi ro khi giá giảm
"""

import asyncio
from datetime import datetime, timezone

# Simulate the trailing stop logic
class TrailingStopDemo:
    def __init__(self, symbol: str, initial_price: float, trailing_pct: float):
        self.symbol = symbol
        self.trailing_pct = trailing_pct
        self.highest_price = initial_price
        self.trailing_stop_price = initial_price * (1 - trailing_pct)
        self.initial_price = initial_price
        
    def update_price(self, current_price: float) -> dict:
        """Cập nhật giá và kiểm tra trailing stop"""
        result = {
            'symbol': self.symbol,
            'current_price': current_price,
            'highest_price': self.highest_price,
            'trailing_stop_price': self.trailing_stop_price,
            'trailing_triggered': False,
            'action': 'HOLD'
        }
        
        # Nếu giá hiện tại cao hơn giá cao nhất, cập nhật trailing stop
        if current_price > self.highest_price:
            self.highest_price = current_price
            self.trailing_stop_price = current_price * (1 - self.trailing_pct)
            result['highest_price'] = self.highest_price
            result['trailing_stop_price'] = self.trailing_stop_price
            result['action'] = 'TRAILING_UPDATED'
            print(f"📈 {self.symbol}: Giá tăng {current_price:.2f} → Cập nhật trailing stop = {self.trailing_stop_price:.2f}")
        
        # Nếu giá chạm trailing stop, kích hoạt bán
        elif current_price <= self.trailing_stop_price:
            result['trailing_triggered'] = True
            result['action'] = 'SELL'
            print(f"🎯 {self.symbol}: TRAILING STOP KÍCH HOẠT! Giá {current_price:.2f} ≤ {self.trailing_stop_price:.2f}")
        
        return result

def demo_trailing_stop():
    """Demo minh họa trailing stop với HPG"""
    print("🎯 DEMO TRAILING STOP - HPG\n")
    print("Kịch bản: Mua HPG giá 30, đặt trailing stop 10%")
    print("=" * 50)
    
    # Khởi tạo trailing stop
    trailing = TrailingStopDemo("HPG", 30.0, 0.10)
    
    # Các mức giá demo
    price_scenarios = [
        30.0,   # Giá mua ban đầu
        28.0,   # Giá giảm ngay
        32.0,   # Giá tăng
        35.0,   # Giá tăng tiếp
        36.0,   # Giá cao nhất
        34.0,   # Giá giảm nhẹ
        32.4,   # Chạm trailing stop
        30.0,   # Giá giảm mạnh
    ]
    
    print(f"💰 Giá mua ban đầu: {trailing.initial_price:.2f}")
    print(f"🎯 Trailing Stop ban đầu: {trailing.trailing_stop_price:.2f} ({trailing.trailing_pct*100:.0f}%)")
    print()
    
    for i, price in enumerate(price_scenarios, 1):
        print(f"Bước {i}: Giá = {price:.2f}")
        result = trailing.update_price(price)
        
        if result['action'] == 'TRAILING_UPDATED':
            print(f"   ✅ Trailing stop cập nhật: {result['trailing_stop_price']:.2f}")
        elif result['action'] == 'SELL':
            pnl_pct = ((price - trailing.initial_price) / trailing.initial_price) * 100
            print(f"   🎯 BÁN! Lãi: {pnl_pct:+.1f}% (từ {trailing.initial_price:.2f} → {price:.2f})")
            break
        else:
            print(f"   ⏳ Chờ (Trailing: {result['trailing_stop_price']:.2f})")
        print()

def demo_comparison():
    """So sánh Stoploss cố định vs Trailing Stop"""
    print("\n" + "=" * 60)
    print("📊 SO SÁNH: STOPLOSS CỐ ĐỊNH vs TRAILING STOP")
    print("=" * 60)
    
    initial_price = 30.0
    stoploss_pct = 0.10
    fixed_stoploss = initial_price * (1 - stoploss_pct)  # 27.0
    
    print(f"💰 Giá mua: {initial_price:.2f}")
    print(f"⛔ Stoploss cố định: {fixed_stoploss:.2f} ({stoploss_pct*100:.0f}%)")
    print()
    
    # Kịch bản: Giá tăng lên 36 rồi giảm
    prices = [30.0, 32.0, 35.0, 36.0, 34.0, 32.0, 30.0, 28.0, 26.0]
    
    print("Kịch bản giá: 30 → 32 → 35 → 36 → 34 → 32 → 30 → 28 → 26")
    print()
    
    # Fixed stoploss
    print("🔴 STOPLOSS CỐ ĐỊNH:")
    for price in prices:
        if price <= fixed_stoploss:
            pnl_pct = ((price - initial_price) / initial_price) * 100
            print(f"   Giá {price:.2f}: BÁN tại {fixed_stoploss:.2f} → Lãi/lỗ: {pnl_pct:+.1f}%")
            break
        else:
            print(f"   Giá {price:.2f}: Chờ (SL: {fixed_stoploss:.2f})")
    
    print()
    
    # Trailing stop
    print("🟢 TRAILING STOP:")
    trailing = TrailingStopDemo("HPG", initial_price, stoploss_pct)
    for price in prices:
        result = trailing.update_price(price)
        if result['action'] == 'SELL':
            pnl_pct = ((price - initial_price) / initial_price) * 100
            print(f"   Giá {price:.2f}: BÁN tại {result['trailing_stop_price']:.2f} → Lãi/lỗ: {pnl_pct:+.1f}%")
            break
        elif result['action'] == 'TRAILING_UPDATED':
            print(f"   Giá {price:.2f}: Cập nhật trailing = {result['trailing_stop_price']:.2f}")
        else:
            print(f"   Giá {price:.2f}: Chờ (Trailing: {result['trailing_stop_price']:.2f})")

if __name__ == "__main__":
    print("🎯 DEMO TÍNH NĂNG TRAILING STOP")
    print("Telegram Portfolio Bot - Dừng lỗ động thông minh")
    print("=" * 60)
    
    # Demo 1: Trailing stop cơ bản
    demo_trailing_stop()
    
    # Demo 2: So sánh với stoploss cố định
    demo_comparison()
    
    print("\n" + "=" * 60)
    print("💡 KẾT LUẬN:")
    print("• Trailing Stop bảo vệ lợi nhuận tốt hơn Stoploss cố định")
    print("• Tự động điều chỉnh theo xu hướng tăng")
    print("• Hạn chế rủi ro khi thị trường đảo chiều")
    print("• Phù hợp cho các cổ phiếu có xu hướng tăng mạnh")
    print("\n🚀 Sử dụng trong bot: /set_trailing_stop <mã> <phần_trăm>")
    print("📊 Xem cấu hình: /trailing_config")
