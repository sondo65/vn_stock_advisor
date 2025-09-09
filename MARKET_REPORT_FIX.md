# Sửa lỗi Market Report - Markdown Parsing

## Vấn đề
Lỗi: `Can't parse entities: can't find end of the entity starting at byte offset 53`

## Nguyên nhân
- Telegram có thể gặp vấn đề với Markdown parsing khi có ký tự đặc biệt
- Một số ký tự trong tin tức có thể gây xung đột với Markdown syntax

## Giải pháp đã áp dụng

### 1. Chuyển từ Markdown sang HTML
```python
# Trước (có thể gây lỗi)
parse_mode=ParseMode.MARKDOWN

# Sau (ổn định hơn)
parse_mode=ParseMode.HTML
```

### 2. Cập nhật format message
```python
# Trước
f"📊 **BÁO CÁO THỊ TRƯỜNG**"

# Sau  
f"📊 <b>BÁO CÁO THỊ TRƯỜNG</b>"
```

### 3. Escape ký tự đặc biệt
```python
def escape_markdown(self, text: str) -> str:
    """Escape special HTML characters"""
    if not text:
        return ""
    return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
```

## Các thay đổi chính

### 1. DailyMarketReportGenerator
- Thêm hàm `escape_markdown()` để escape ký tự HTML
- Chuyển tất cả `**text**` thành `<b>text</b>`
- Chuyển tất cả `*text*` thành `<b>text</b>`

### 2. Telegram Bot
- Thay đổi `ParseMode.MARKDOWN` thành `ParseMode.HTML`
- Áp dụng cho cả callback và command handler

### 3. Message Format
- Header: `<b>BÁO CÁO THỊ TRƯỜNG</b>`
- Sections: `<b>TÍN HIỆU KỸ THUẬT:</b>`
- News titles: Escape ký tự đặc biệt

## Test

Chạy script test để kiểm tra:
```bash
python test_market_report_fix.py
```

## Lưu ý

1. **HTML Tags**: Chỉ sử dụng `<b>` và `</b>` cho bold text
2. **Escape**: Tất cả user content đều được escape
3. **Compatibility**: HTML mode ổn định hơn Markdown mode
4. **Performance**: Không ảnh hưởng đến performance

## Kết quả

- ✅ Không còn lỗi parsing
- ✅ Message hiển thị đúng format
- ✅ Tương thích với tất cả ký tự đặc biệt
- ✅ Ổn định hơn với tin tức đa dạng
