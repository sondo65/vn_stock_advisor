# Industry Stock Advisor - Hướng dẫn sử dụng

## 📋 Tổng quan

Industry Stock Advisor là một hệ thống gợi ý cổ phiếu tiềm năng dựa trên phân tích kỹ thuật và số liệu thực tế theo từng ngành cụ thể. Hệ thống tích hợp với các module hiện có để cung cấp phân tích toàn diện và khuyến nghị đầu tư.

## 🚀 Tính năng chính

### 1. Gợi ý cổ phiếu theo ngành
- Phân tích và so sánh cổ phiếu với benchmark ngành
- Đánh giá tiềm năng tăng trưởng theo từng ngành
- Suggest top picks cho từng ngành dựa trên phân tích kỹ thuật và cơ bản

### 2. Phân tích ngành
- Phân tích xu hướng ngành (bullish, bearish, neutral, volatile)
- So sánh hiệu suất giữa các ngành
- Xác định ngành có tiềm năng nhất
- Phân tích chu kỳ ngành

### 3. Hệ thống scoring thông minh
- Điểm giá trị (value score): So sánh P/B, P/E với benchmark ngành
- Điểm momentum (momentum score): RSI, MACD, xu hướng, khối lượng
- Điểm chất lượng (quality score): ROE, vốn hóa, chất lượng dữ liệu
- Điểm vị thế ngành (industry score): Vị thế trong ngành

### 4. Khuyến nghị đầu tư
- STRONG_BUY, BUY, HOLD, WATCH, SELL
- Độ tin cậy (confidence level)
- Giá mục tiêu (target price)
- Mức độ rủi ro (LOW, MEDIUM, HIGH)

## 📁 Cấu trúc module

```
src/vn_stock_advisor/scanner/
├── industry_suggester.py      # Gợi ý cổ phiếu theo ngành
├── industry_analyzer.py       # Phân tích và so sánh ngành
├── industry_stock_advisor.py  # Hệ thống tích hợp hoàn chỉnh
└── __init__.py               # Export các module
```

## 🛠️ Cài đặt và sử dụng

### 1. Import modules

```python
from src.vn_stock_advisor.scanner import (
    IndustryStockAdvisor,
    suggest_industry_stocks,
    get_top_industry_opportunities,
    compare_industries,
    get_available_industries
)
```

### 2. Sử dụng cơ bản

#### Gợi ý cổ phiếu cho một ngành

```python
# Tạo advisor
advisor = IndustryStockAdvisor()

# Lấy khuyến nghị cho ngành
recommendation = advisor.get_industry_recommendation(
    industry="Tài chính ngân hàng",
    max_stocks=10,
    min_score=7.0,
    include_analysis=True
)

# Hiển thị kết quả
if recommendation:
    print(f"Ngành: {recommendation.industry}")
    print(f"Điểm tổng thể: {recommendation.industry_analysis.overall_score:.1f}/10")
    print(f"Khuyến nghị: {recommendation.industry_analysis.recommendation}")
    
    for stock in recommendation.stock_suggestions:
        print(f"{stock.symbol}: {stock.total_score:.1f}/10 ({stock.recommendation})")
```

#### Sử dụng hàm tiện ích

```python
# Gợi ý nhanh
stocks = suggest_industry_stocks(
    industry="Bất động sản",
    max_stocks=5,
    min_score=7.0
)

# Top cơ hội đầu tư
opportunities = get_top_industry_opportunities(
    max_industries=5,
    max_stocks_per_industry=5
)

# So sánh ngành
comparisons = compare_industries(
    industries=["Tài chính ngân hàng", "Bất động sản", "Công nghệ"],
    max_stocks_per_industry=5
)

# Danh sách ngành có sẵn
industries = get_available_industries()
```

### 3. Giao diện Streamlit

Chạy giao diện web:

```bash
streamlit run industry_stock_advisor_ui.py
```

Giao diện bao gồm:
- **Tab 1**: Gợi ý theo ngành
- **Tab 2**: Top cơ hội đầu tư
- **Tab 3**: So sánh ngành
- **Tab 4**: Danh sách ngành

### 4. Demo script

Chạy demo để test chức năng:

```bash
python demo_industry_advisor.py
```

## 📊 Các ngành được hỗ trợ

Hệ thống hỗ trợ 40+ ngành chính:

- **Tài chính**: Tài chính ngân hàng, Chứng khoán, Bảo hiểm
- **Bất động sản**: Bất động sản, Xây dựng
- **Công nghệ**: Phần mềm và dịch vụ CNTT, Viễn thông
- **Năng lượng**: Dầu khí, Điện, Năng lượng tái tạo
- **Tiêu dùng**: Thực phẩm, Đồ uống, Bán lẻ
- **Công nghiệp**: Kim loại, Hóa chất, Ô tô
- **Y tế**: Dược phẩm, Thiết bị y tế
- **Và nhiều ngành khác...**

## 🎯 Thuật toán scoring

### Điểm giá trị (Value Score)
- So sánh P/B với benchmark ngành
- So sánh P/E với benchmark ngành
- Xem xét vốn hóa thị trường

### Điểm momentum (Momentum Score)
- RSI: 30-40 (oversold), 40-60 (neutral), 60-70 (strong)
- MACD: positive, negative, neutral
- Xu hướng MA: upward, downward, sideways
- Khối lượng: increasing, decreasing, normal

### Điểm chất lượng (Quality Score)
- ROE so với benchmark ngành
- Chất lượng dữ liệu
- Vốn hóa thị trường
- Độ ổn định giá

### Điểm vị thế ngành (Industry Score)
- Vị thế trong ngành (large cap, mid cap, small cap)
- Tính hấp dẫn định giá
- Khả năng cạnh tranh

## 📈 Khuyến nghị đầu tư

### Mức khuyến nghị
- **STRONG_BUY**: Điểm ≥ 8.5, tiềm năng cao
- **BUY**: Điểm ≥ 7.5, tiềm năng tốt
- **HOLD**: Điểm ≥ 6.5, giữ nguyên
- **WATCH**: Điểm ≥ 5.0, theo dõi
- **SELL**: Điểm < 5.0, nên bán

### Độ tin cậy
- Dựa trên tính nhất quán của các điểm số
- Chất lượng dữ liệu
- Số lượng cổ phiếu được phân tích

### Mức độ rủi ro
- **LOW**: Vốn hóa lớn, định giá hợp lý
- **MEDIUM**: Vốn hóa trung bình, định giá vừa phải
- **HIGH**: Vốn hóa nhỏ, định giá cao

## 🔧 Tùy chỉnh

### Thay đổi trọng số scoring

```python
# Trong industry_suggester.py
self.industry_weights = {
    "Tài chính ngân hàng": {"value": 0.4, "momentum": 0.3, "quality": 0.3},
    "Bất động sản": {"value": 0.35, "momentum": 0.4, "quality": 0.25},
    # ...
}
```

### Thêm ngành mới

```python
# Trong industry_suggester.py
self.industry_stocks["Ngành mới"] = [
    'MÃ1', 'MÃ2', 'MÃ3'
]
```

### Thay đổi benchmark

Cập nhật file `knowledge/PE_PB_industry_average.json` hoặc `knowledge/enhanced_industry_benchmarks.json`

## 📝 Ví dụ sử dụng

### Ví dụ 1: Tìm cơ hội đầu tư ngành ngân hàng

```python
from src.vn_stock_advisor.scanner import IndustryStockAdvisor

advisor = IndustryStockAdvisor()

# Phân tích ngành ngân hàng
recommendation = advisor.get_industry_recommendation(
    industry="Tài chính ngân hàng",
    max_stocks=10,
    min_score=7.0
)

if recommendation:
    print(f"Ngành ngân hàng có điểm {recommendation.industry_analysis.overall_score:.1f}/10")
    print(f"Khuyến nghị: {recommendation.industry_analysis.recommendation}")
    
    # Top 3 cổ phiếu
    for stock in recommendation.stock_suggestions[:3]:
        print(f"{stock.symbol}: {stock.total_score:.1f}/10 - {stock.recommendation}")
```

### Ví dụ 2: So sánh các ngành

```python
from src.vn_stock_advisor.scanner import compare_industries

# So sánh 3 ngành
comparisons = compare_industries([
    "Tài chính ngân hàng",
    "Bất động sản", 
    "Phần mềm và dịch vụ công nghệ thông tin"
])

# Sắp xếp theo điểm số
for comp in comparisons:
    print(f"{comp.industry}: {comp.industry_analysis.overall_score:.1f}/10")
```

### Ví dụ 3: Tìm top cơ hội

```python
from src.vn_stock_advisor.scanner import get_top_industry_opportunities

# Top 5 cơ hội đầu tư
opportunities = get_top_industry_opportunities(
    max_industries=5,
    max_stocks_per_industry=5
)

for i, opp in enumerate(opportunities, 1):
    print(f"#{i} {opp.industry}: {opp.industry_analysis.overall_score:.1f}/10")
```

## 🚨 Lưu ý quan trọng

1. **Dữ liệu**: Hệ thống phụ thuộc vào chất lượng dữ liệu từ các nguồn bên ngoài
2. **Cache**: Kết quả được cache 30 phút để tối ưu hiệu suất
3. **Rủi ro**: Khuyến nghị chỉ mang tính tham khảo, không phải lời khuyên đầu tư
4. **Cập nhật**: Benchmark ngành cần được cập nhật định kỳ

## 🔄 Cập nhật và bảo trì

### Cập nhật benchmark ngành
```bash
# Cập nhật file knowledge/PE_PB_industry_average.json
# Cập nhật file knowledge/enhanced_industry_benchmarks.json
```

### Xóa cache
```python
advisor = IndustryStockAdvisor()
advisor.clear_cache()
```

### Kiểm tra thống kê cache
```python
stats = advisor.get_cache_stats()
print(f"Cache size: {stats['cache_size']}")
```

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra log lỗi
2. Xóa cache và thử lại
3. Kiểm tra kết nối dữ liệu
4. Cập nhật benchmark ngành

---

**Lưu ý**: Hệ thống này chỉ mang tính tham khảo và không thay thế cho việc nghiên cứu đầu tư chuyên sâu. Luôn thực hiện due diligence trước khi đầu tư.
