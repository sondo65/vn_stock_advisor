# Hướng dẫn cấu hình Market Analysis

## Tổng quan
Chức năng Market Analysis tích hợp SERPER API, Gemini, và OpenAI để:
- Thu thập tin tức trong nước và quốc tế
- Phân tích sentiment bằng AI
- Dự báo xu hướng VN-Index
- Gửi báo cáo tự động vào 8h15 hàng ngày

## Cấu hình API Keys

### 1. SERPER API (Bắt buộc)
- Đăng ký tại: https://serper.dev/
- Lấy API key và thêm vào file `.env`:
```bash
SERPER_API_KEY=your_serper_api_key_here
```

### 2. Gemini API (Tùy chọn - để phân tích sentiment nâng cao)
- Đăng ký tại: https://makersuite.google.com/app/apikey
- Thêm vào file `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. OpenAI API (Tùy chọn - để phân tích sentiment nâng cao)
- Đăng ký tại: https://platform.openai.com/api-keys
- Thêm vào file `.env`:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Cài đặt Dependencies

```bash
# Cài đặt dependencies mới
pip install aiohttp>=3.9.0 openai>=1.0.0 pandas>=2.0.0

# Hoặc cài đặt từ pyproject.toml
pip install -e .
```

## Sử dụng

### Lệnh Telegram Bot

1. **Xem báo cáo ngay lập tức:**
   ```
   /market_report
   ```

2. **Lên lịch báo cáo hàng ngày (8h15):**
   ```
   /market_report_schedule
   ```

3. **Tắt báo cáo tự động:**
   ```
   /market_report_off
   ```

### Cấu trúc Module

```
src/vn_stock_advisor/market_analysis/
├── __init__.py
├── news_collector.py          # Thu thập tin tức từ SERPER API
├── vnindex_analyzer.py        # Phân tích VN-Index
└── daily_market_report.py     # Tạo báo cáo hàng ngày
```

## Tính năng

### 1. Thu thập tin tức
- **Trong nước:** VN-Index, kinh tế VN, ngân hàng, lạm phát, doanh nghiệp
- **Quốc tế:** Fed, S&P 500, Trung Quốc, dầu thô, vàng, USD/VND

### 2. Phân tích AI
- **Sentiment Analysis:** Sử dụng Gemini hoặc OpenAI
- **Relevance Scoring:** Đánh giá mức độ liên quan đến thị trường VN
- **Theme Detection:** Xác định các chủ đề chính

### 3. Dự báo VN-Index
- **Technical Analysis:** Price action, momentum, volume
- **News Impact:** Kết hợp sentiment từ tin tức
- **Trend Prediction:** BULLISH, BEARISH, NEUTRAL với confidence score
- **Target Range:** Khoảng giá dự kiến trong ngày

### 4. Báo cáo tự động
- **Thời gian:** 8h15 sáng hàng ngày (giờ VN)
- **Nội dung:** Dự báo, khuyến nghị, tin tức nổi bật, tín hiệu kỹ thuật
- **Format:** Markdown với emoji và cấu trúc rõ ràng

## Lưu ý

1. **API Limits:** SERPER có giới hạn requests, cân nhắc tối ưu hóa
2. **Rate Limiting:** Gemini và OpenAI có rate limits
3. **Fallback:** Nếu không có AI API, sẽ dùng keyword-based analysis
4. **Timezone:** Tất cả thời gian đều theo giờ Việt Nam (Asia/Ho_Chi_Minh)

## Troubleshooting

### Lỗi thường gặp:

1. **"Chức năng phân tích thị trường chưa khả dụng"**
   - Kiểm tra import module
   - Cài đặt dependencies

2. **"Thiếu SERPER_API_KEY"**
   - Thêm SERPER_API_KEY vào .env
   - Restart bot

3. **"Lỗi khi tạo báo cáo thị trường"**
   - Kiểm tra API keys
   - Xem logs để debug chi tiết

### Debug:

```python
# Test news collector
python -m src.vn_stock_advisor.market_analysis.news_collector

# Test VN-Index analyzer  
python -m src.vn_stock_advisor.market_analysis.vnindex_analyzer

# Test daily report
python -m src.vn_stock_advisor.market_analysis.daily_market_report
```
