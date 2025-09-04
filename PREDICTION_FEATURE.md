# 🔮 Chức năng Dự đoán Giá - Telegram Portfolio Bot

## Tổng quan

Bot Telegram đã được bổ sung chức năng dự đoán giá dựa trên phân tích kỹ thuật từ dữ liệu lịch sử. Hệ thống sử dụng các chỉ báo kỹ thuật phổ biến để đưa ra các kịch bản dự đoán với xác suất.

## 🎯 Tính năng chính

### 1. Phân tích kỹ thuật tự động
- **Moving Averages (MA)**: SMA 20, SMA 50
- **RSI (Relative Strength Index)**: Phát hiện oversold/overbought
- **MACD**: Phân tích xu hướng và momentum
- **Bollinger Bands**: Xác định vùng hỗ trợ/kháng cự
- **ATR (Average True Range)**: Đo lường biến động

### 2. Dự đoán với kịch bản xác suất
- **Tăng mạnh/nhẹ**: Dựa trên ATR và tín hiệu bullish
- **Giảm mạnh/nhẹ**: Dựa trên ATR và tín hiệu bearish  
- **Sideway**: Biến động trong biên độ hẹp
- **Xác suất**: Mỗi kịch bản có xác suất riêng

### 3. Quyết định đầu tư
- **BUY_MORE**: Tín hiệu mua mạnh
- **HOLD**: Tín hiệu trung tính
- **SELL**: Tín hiệu bán mạnh
- **Độ tin cậy**: Từ 30% đến 90%

## 📱 Lệnh mới

### `/predict <mã cổ phiếu>`
Dự đoán chi tiết cho một cổ phiếu cụ thể.

**Ví dụ:**
```
/predict VIC
```

**Kết quả:**
```
📈 Dự đoán cho VIC:
🎯 Quyết định: BUY_MORE
📊 Độ tin cậy: 75.2%
💡 Lý do: Tín hiệu mua mạnh (RSI: 45.2, MACD: +)

🎲 Các kịch bản có thể:
  • Tăng mạnh (+3.2%): 45.0%
  • Tăng nhẹ (+1.1%): 30.0%
  • Sideway (±0.8%): 25.0%

📊 Chỉ báo kỹ thuật:
  • Giá hiện tại: 45.20
  • MA20: 44.80
  • RSI: 45.2 (Neutral)
  • MACD: Bullish
```

### `/analyze_now` (đã cập nhật)
Phân tích toàn bộ danh mục với dự đoán cho từng cổ phiếu.

**Kết quả mẫu:**
```
📊 Kết quả phân tích danh mục:
- VIC: BUY_MORE (conf 75%), Giá=45.20, SL=100, Giá vốn=44.50, Lãi/lỗ=70.00 | Kịch bản: Tăng mạnh (+3.2%) (45%)
- VCB: HOLD (conf 60%), Giá=78.50, SL=50, Giá vốn=77.80, Lãi/lỗ=35.00 | Kịch bản: Sideway (±1.2%) (60%)
```

## 🔧 Cách hoạt động

### 1. Thu thập dữ liệu
- Sử dụng vnstock để lấy dữ liệu OHLCV 60 ngày gần nhất
- Hỗ trợ nhiều nguồn: VCI, TCBS, DNSE, SSI
- Fallback sang phương thức legacy nếu cần

### 2. Tính toán chỉ báo
```python
# Ví dụ tính RSI
rsi = TechnicalIndicators.rsi(prices, 14)

# Ví dụ tính MACD
macd_data = TechnicalIndicators.macd(prices, 12, 26, 9)
```

### 3. Phân tích tín hiệu
- **Xu hướng**: So sánh giá với MA20, MA50
- **Momentum**: RSI oversold/overbought
- **Trend**: MACD bullish/bearish
- **Volatility**: Bollinger Bands position

### 4. Tạo kịch bản
- Tính điểm cho từng kịch bản (bullish/bearish/neutral)
- Chuẩn hóa thành xác suất
- Tạo target price dựa trên ATR

### 5. Đưa ra quyết định
- Tổng hợp tất cả tín hiệu
- Tính độ tin cậy
- Đưa ra lý do chi tiết

## 📊 Ví dụ phân tích

### Trường hợp 1: Tín hiệu mua mạnh
```
Điều kiện:
- Giá > MA20 > MA50 (xu hướng tăng)
- RSI < 35 (oversold)
- MACD > Signal và > 0 (bullish)
- Giá gần Bollinger Lower Band

Kết quả:
- Decision: BUY_MORE
- Confidence: 85%
- Scenarios: Tăng mạnh (60%), Tăng nhẹ (40%)
```

### Trường hợp 2: Tín hiệu bán
```
Điều kiện:
- Giá < MA20 < MA50 (xu hướng giảm)
- RSI > 70 (overbought)
- MACD < Signal và < 0 (bearish)
- Giá gần Bollinger Upper Band

Kết quả:
- Decision: SELL
- Confidence: 80%
- Scenarios: Giảm mạnh (55%), Giảm nhẹ (45%)
```

### Trường hợp 3: Tín hiệu trung tính
```
Điều kiện:
- Giá gần MA20
- RSI 40-60 (neutral)
- MACD mixed signals
- Giá trong Bollinger Bands

Kết quả:
- Decision: HOLD
- Confidence: 65%
- Scenarios: Sideway (70%), Tăng nhẹ (15%), Giảm nhẹ (15%)
```

## ⚠️ Lưu ý quan trọng

### 1. Giới hạn dự đoán
- **Không chính xác 100%**: Dự đoán chỉ mang tính tham khảo
- **Dựa trên lịch sử**: Không tính đến tin tức, sự kiện bất ngờ
- **Thời gian ngắn hạn**: Phù hợp cho giao dịch 1-5 ngày

### 2. Rủi ro
- **Thị trường biến động**: Có thể thay đổi nhanh chóng
- **Dữ liệu không đầy đủ**: Một số mã có thể thiếu dữ liệu
- **Lỗi kỹ thuật**: API có thể tạm thời không khả dụng

### 3. Khuyến nghị sử dụng
- **Kết hợp với phân tích cơ bản**: Không chỉ dựa vào kỹ thuật
- **Quản lý rủi ro**: Luôn đặt stoploss
- **Đa dạng hóa**: Không tập trung vào một mã
- **Cập nhật thường xuyên**: Theo dõi thay đổi thị trường

## 🚀 Cách sử dụng

### 1. Khởi động bot
```bash
python telegram_portfolio_bot.py
```

### 2. Test chức năng
```bash
python test_prediction_demo.py
```

### 3. Sử dụng trong Telegram
```
/start
/predict VIC
/analyze_now
/help
```

## 🔮 Tương lai

### Các cải tiến có thể:
1. **Machine Learning**: Tích hợp LSTM, Transformer
2. **Sentiment Analysis**: Phân tích tin tức, mạng xã hội
3. **Macro Data**: Dữ liệu kinh tế vĩ mô
4. **Sector Analysis**: Phân tích theo ngành
5. **Real-time Updates**: Cập nhật liên tục trong phiên

### Tích hợp với hệ thống hiện tại:
- **Auto-trading**: Tự động giao dịch dựa trên tín hiệu
- **Risk Management**: Điều chỉnh stoploss tự động
- **Portfolio Optimization**: Tối ưu hóa danh mục
- **Alert System**: Cảnh báo khi có tín hiệu mạnh

---

**Lưu ý**: Đây là công cụ hỗ trợ quyết định, không phải lời khuyên đầu tư. Luôn thực hiện nghiên cứu riêng và quản lý rủi ro cẩn thận.
