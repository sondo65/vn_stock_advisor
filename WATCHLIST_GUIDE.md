# 📝 Hướng dẫn sử dụng Danh sách theo dõi (Watchlist)

## Tổng quan

Chức năng **Watchlist** cho phép bạn theo dõi các cổ phiếu tiềm năng mà chưa mua. Bot sẽ tự động phân tích và gợi ý mua khi có tín hiệu tốt.

## Các lệnh chính

### 1. Thêm cổ phiếu vào danh sách theo dõi
```
/watch_add <mã_cổ_phiếu> [giá_mục_tiêu] [ghi_chú]
```

**Ví dụ:**
- `/watch_add VIC` - Theo dõi VIC
- `/watch_add VIC 50000` - Theo dõi VIC với giá mục tiêu 50,000
- `/watch_add VIC 50000 Cổ phiếu tiềm năng` - Thêm ghi chú

### 2. Xem danh sách theo dõi
```
/watch_list
```

Hiển thị tất cả cổ phiếu trong danh sách theo dõi với:
- Mã cổ phiếu
- Giá mục tiêu (nếu có)
- Ghi chú (nếu có)
- Thời gian thêm vào

### 3. Xóa cổ phiếu khỏi danh sách
```
/watch_remove <mã_cổ_phiếu>
```

**Ví dụ:** `/watch_remove VIC`

### 4. Xóa toàn bộ danh sách
```
/watch_clear
```

Sẽ yêu cầu xác nhận trước khi xóa.

## Cách hoạt động

### 1. Tích hợp với hệ thống tracking
- Watchlist được tích hợp vào hệ thống tracking hiện tại
- Mỗi khi bot chạy tracking, nó sẽ phân tích cả portfolio và watchlist
- Cổ phiếu trong watchlist được phân tích để tìm tín hiệu mua

### 2. Tín hiệu mua được phát hiện
Bot sẽ gợi ý mua khi có các tín hiệu sau:

#### 🎯 Đạt giá mục tiêu
- Giá hiện tại trong vòng 2% của giá mục tiêu
- Độ tin cậy: +30%

#### 📈 Volume tăng mạnh
- Volume hiện tại > 150% volume trung bình
- Độ tin cậy: +20%

#### 🔮 Tín hiệu kỹ thuật
- Sử dụng PredictionEngine để phân tích
- BUY_MORE: +30% độ tin cậy
- HOLD với confidence > 70%: +10% độ tin cậy

#### 📈 Momentum tích cực
- Tăng giá > 2% trong 2 ngày gần nhất
- Độ tin cậy: +10%

### 3. Ngưỡng gợi ý mua
- **Tối thiểu 40% độ tin cậy** để gửi gợi ý mua
- Bot sẽ gửi thông báo chi tiết với:
  - Giá hiện tại
  - Giá mục tiêu (nếu có)
  - Độ tin cậy
  - Các tín hiệu phát hiện
  - Ghi chú (nếu có)
  - Hướng dẫn mua

### 4. Tự động chuyển sang portfolio
- Khi bạn mua cổ phiếu bằng lệnh `/add`
- Bot sẽ tự động xóa cổ phiếu khỏi watchlist
- Thông báo xác nhận việc chuyển đổi

## Ví dụ sử dụng

### Kịch bản 1: Theo dõi cổ phiếu tiềm năng
```
/watch_add VIC 50000 Cổ phiếu bất động sản hàng đầu
/watch_add VHM 60000 Cổ phiếu bất động sản
/watch_add VCB 80000 Ngân hàng lớn nhất
/watch_list
```

### Kịch bản 2: Nhận gợi ý mua
Khi có tín hiệu tốt, bot sẽ gửi:
```
🚀 GỢI Ý MUA - VIC
💰 Giá hiện tại: 48,500
🎯 Giá mục tiêu: 50,000 (Giảm 3.0%)
📊 Độ tin cậy: 75%

🔍 Tín hiệu:
• 🎯 Đạt giá mục tiêu (50,000)
• 📈 Volume tăng mạnh (+65.2%)
• 🔮 Tín hiệu kỹ thuật: Breakout pattern detected

📝 Ghi chú: Cổ phiếu bất động sản hàng đầu

💡 Dùng /add VIC <số_lượng> <giá> để mua
```

### Kịch bản 3: Mua và chuyển sang portfolio
```
/add VIC 100 48500 0.08
```

Bot sẽ trả lời:
```
✅ Đã mua 100 VIC giá 48,500.
📊 Stoploss đã được đặt: 8% (giá: 44,620)
📝 Đã xóa VIC khỏi danh sách theo dõi (đã mua)
```

## Lưu ý quan trọng

1. **Không trùng lặp**: Cổ phiếu đã có trong portfolio sẽ không thể thêm vào watchlist
2. **Tự động xóa**: Khi mua cổ phiếu, nó sẽ tự động bị xóa khỏi watchlist
3. **Phân tích thông minh**: Bot sử dụng nhiều chỉ báo kỹ thuật để đánh giá
4. **Tần suất tracking**: Watchlist được phân tích cùng với portfolio trong mỗi lần tracking
5. **Độ tin cậy**: Chỉ gửi gợi ý khi có độ tin cậy ≥ 40%

## Tích hợp với các chức năng khác

- **Tracking tự động**: `/track_on` sẽ theo dõi cả portfolio và watchlist
- **Phân tích thị trường**: Watchlist được bao gồm trong báo cáo thị trường
- **Prediction engine**: Sử dụng cùng hệ thống dự đoán với portfolio
- **Volume analysis**: Phân tích volume để xác nhận tín hiệu

## Troubleshooting

### Không nhận được gợi ý mua
- Kiểm tra xem tracking có được bật không: `/track_status`
- Đảm bảo cổ phiếu có dữ liệu giá hợp lệ
- Kiểm tra độ tin cậy có đạt ngưỡng 40% không

### Cổ phiếu không được thêm vào watchlist
- Kiểm tra xem cổ phiếu đã có trong portfolio chưa
- Đảm bảo mã cổ phiếu đúng định dạng (VD: VIC, VHM, VCB)

### Lỗi kết nối dữ liệu
- Bot sẽ tự động fallback sang dữ liệu lịch sử
- Kiểm tra kết nối internet và API vnstock
