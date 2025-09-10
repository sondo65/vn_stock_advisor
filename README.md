# VN Stock Advisor (v.0.5.0)

## 🇻🇳 Tiếng Việt

### Giới thiệu
VN Stock Advisor là một công cụ phân tích cổ phiếu thông minh sử dụng hệ thống Multi-AI-Agent của CrewAI. 
Công cụ cũng sử dụng trí tuệ nhân tạo được cung cấp bởi Google Gemini.
Hệ thống cung cấp phân tích toàn diện về cổ phiếu, bao gồm tin tức, phân tích cơ bản và phân tích kỹ thuật và đưa ra khuyến nghị.

### Lưu ý:
Dự án này có mục đích chính là học tập và nghiên cứu về Large Language Model, Prompt Engineering và CrewAI framework. Từ đó áp dụng vào phân tích chứng khoán một cách tự động.
Các báo cáo phân tích được VN Stock Advisor thu thập từ những nguồn trên Internet và tổng hợp, phân tích bởi trí tuệ nhân tạo.
Do đó, tất cả các quan điểm, luận điểm, khuyến nghị mua/bán mà VN Stock Advisor đưa ra chỉ mang tính tham khảo. 
VN Stock Advisor không chịu trách nhiệm đối với bất kỳ khoản thua lỗ từ đầu tư nào do sử dụng các báo cáo phân tích này.

### Tính năng
Sử dụng hệ thống 4 AI Agents để thực hiện những công việc sau:
- 🔍 Tự động search google và scrape các trang web để thu thập và phân tích tin tức mới nhất về cổ phiếu
- 📊 Tự động gọi API và RAG để lấy dữ liệu và phân tích cơ bản (P/E, P/B, ROE, EPS,...)
- 📈 Tự động thu thập dữ liệu giá, khối lượng từ VCI hoặc TCBS, tính toán và phân tích kỹ thuật (SMA, EMA, RSI, MACD, OBV...)
- 💡 Tổng hợp dữ liệu và đề xuất quyết định đầu tư (Mua/Bán/Giữ)

### Tính năng nâng cao (v0.8.0)
- 🤖 **Machine Learning Analysis**: Pattern Recognition, Anomaly Detection
- 📊 **Advanced Technical Analysis**: Fibonacci, Ichimoku Cloud, Volume Profile, Divergence Detection  
- 💭 **Sentiment Analysis**: Phân tích tâm lý thị trường từ tin tức và social media
- ⚖️ **Advanced Scoring System**: Hệ thống chấm điểm và tính toán confidence động
- 🎯 **Risk Analysis**: Comprehensive risk assessment và stress testing
- 🔗 **Multi-Source Data Integration**: Tích hợp dữ liệu từ nhiều nguồn với conflict resolution
- 📡 **Real-time Data Collection**: Thu thập dữ liệu real-time với caching và validation

### Tính năng mới (v0.9.0) - Industry Stock Advisor
- 🏭 **Industry-Based Stock Suggestions**: Gợi ý cổ phiếu tiềm năng theo từng ngành cụ thể
- 📈 **Industry Analysis & Comparison**: Phân tích và so sánh hiệu suất giữa các ngành
- 🎯 **Smart Industry Scoring**: Hệ thống chấm điểm thông minh dựa trên benchmark ngành
- 🔍 **Top Investment Opportunities**: Tìm kiếm top cơ hội đầu tư theo ngành
- 📊 **Comprehensive Industry Dashboard**: Giao diện Streamlit hoàn chỉnh cho phân tích ngành
- ⚖️ **Industry Benchmark Integration**: Tích hợp benchmark P/E, P/B cho 40+ ngành

### Tính năng User Experience & API (v0.8.0)
- 🌐 **Streamlit Web Interface**: Giao diện web thân thiện với người dùng
- 📱 **Mobile-Responsive Design**: Tối ưu cho thiết bị di động và tablet
- 🔌 **REST API**: API endpoints đầy đủ cho integration với hệ thống khác
- 👤 **User Authentication**: Hệ thống đăng nhập, đăng ký và quản lý người dùng
- 💼 **Portfolio Management**: Quản lý danh mục đầu tư cá nhân
- 📈 **Interactive Dashboard**: Dashboard tương tác với biểu đồ nâng cao
- 📤 **Export Capabilities**: Xuất báo cáo PDF, Excel, JSON
- 🎨 **Advanced Visualization**: Biểu đồ tương tác với Plotly
- 📊 **Sector Analysis**: Phân tích theo ngành chi tiết
- 🔍 **Stock Comparison**: So sánh multiple cổ phiếu

### Tính năng Telegram Bot & Watchlist (v0.9.1)
- 🤖 **Telegram Portfolio Bot**: Bot Telegram hoàn chỉnh cho quản lý danh mục
- 📝 **Smart Watchlist**: Danh sách theo dõi cổ phiếu tiềm năng với gợi ý mua thông minh
- 🎯 **Auto Buy Signals**: Tự động phát hiện tín hiệu mua dựa trên giá mục tiêu, volume, kỹ thuật
- 📊 **Real-time Tracking**: Theo dõi real-time cả portfolio và watchlist
- 🔄 **Auto Portfolio Transfer**: Tự động chuyển từ watchlist sang portfolio khi mua
- 📈 **Advanced Alerts**: Thông báo thông minh với độ tin cậy và phân tích chi tiết
- ⚙️ **Flexible Configuration**: Cấu hình linh hoạt cho stoploss, trailing stop, phong cách đầu tư

### Webdemo
- Update sau

### Cài đặt (nếu muốn chạy local)
```bash
# Cài đặt Python >= 3.10, < 3.13
https://www.python.org/downloads/

# Cài đặt uv package manager
https://docs.astral.sh/uv/getting-started/installation/

# Cài đặt crewai
uv tool install crewai

# Tham khảo hướng dẫn cài đặt crewai nếu gặp lỗi
https://docs.crewai.com/installation

# Cài đặt các dependencies
crewai install
```

### Cấu hình
Tạo file `.env` với các biến môi trường sau:
Có thể thay thế các MODEL bằng các model khác của Google hoặc thậm chí từ OpenAi, Anthropic hay local model như Ollama.
```
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini/gemini-2.0-flash-001
GEMINI_REASONING_MODEL=gemini/gemini-2.5-flash-preview-04-17
SERPER_API_KEY=your_serper_api_key
# Telegram Bot (tuỳ chọn nếu dùng Telegram Portfolio Bot)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# ví dụ: 123456789 hoặc -1001234567890 (group/channel)
DEFAULT_CHAT_ID=
# ví dụ: /Users/you/Documents/portfolio.sqlite3 (để trống sẽ dùng mặc định cạnh script)
TELEGRAM_PORTFOLIO_DB=
```

## 🎯 Cách sử dụng

### 1. Chạy Web Interface
```bash
streamlit run streamlit_app.py
```

### 2. Chạy API Server
```bash
cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Chạy phân tích truyền thống (Command Line)
```bash
# Vào main.py, thay biến symbol bằng mã cổ phiếu muốn phân tích
# Mặc định hiện đang để là "HPG"

# Sử dụng lệnh sau để chạy chương trình
crewai run
```

### 5. Telegram Portfolio Bot (local-first)
Bot Telegram quản lý danh mục chạy trên máy Mac (local), lưu SQLite, có đặt lịch phân tích hàng ngày.

Tính năng:
- Bot asyncio `python-telegram-bot` v21
- Lưu `positions`, `transactions`, `settings` vào SQLite
- Decision engine plug-point: BUY_MORE / HOLD / SELL
- Đặt lịch hằng ngày bằng JobQueue (máy phải bật, process đang chạy)
- Lệnh: add/sell, portfolio, pnl, analyze_now, set_schedule

Cài đặt nhanh:
```bash
pip install python-telegram-bot==21.6 aiosqlite pydantic python-dotenv
```
Tạo biến môi trường (hoặc thêm vào `.env`):
```bash
export TELEGRAM_BOT_TOKEN="<your_bot_token>"
# tuỳ chọn: chat id để bot gửi thông báo khi khởi động
export DEFAULT_CHAT_ID="<your_chat_id>"
# tuỳ chọn: đường dẫn DB
# export TELEGRAM_PORTFOLIO_DB="/absolute/path/portfolio.sqlite3"
```
Chạy bot:
```bash
python telegram_portfolio_bot.py
```

Các lệnh Telegram:
- `/start` — đăng ký user, khởi tạo
- `/help` — hướng dẫn
- `/add <mã> <sl> <giá>` — mua/thêm vị thế
- `/sell <mã> <sl> <giá>` — bán
- `/portfolio` — xem danh mục
- `/pnl` — PnL theo giá hiện tại
- `/analyze_now` — phân tích ngay và gợi ý hành động
- `/set_schedule <HH:MM>` — đặt giờ chạy hàng ngày theo giờ máy

Điểm tích hợp (mở `telegram_portfolio_bot.py`):
- `PredictionEngine.predict(symbol)` — gọi mô hình/advisor hiện có để trả về quyết định
- `MarketData.get_price(symbol)` — lấy giá hiện tại (mặc định thử `vnstock`)

### 4. Chạy Industry Stock Advisor (Gợi ý cổ phiếu theo ngành)
```bash
# Giao diện Streamlit chính (đã tích hợp Industry Stock Advisor)
streamlit run streamlit_app.py

# Giao diện riêng cho Industry Stock Advisor
streamlit run industry_stock_advisor_ui.py

# Demo script
python demo_industry_advisor.py
```
### Yêu cầu
- Python >= 3.10, < 3.13
- crewai[tools] >= 0.117.0
- google-generativeai >= 0.8.4
- vnstock >= 3.2.4
- python-dotenv >= 1.1.0
- Google Gemini API key (đăng kí free từ [Google AI Studio](https://aistudio.google.com/apikey))
- Serper.dev API key (đăng kí free từ [serper.dev](https://serper.dev/api-key))

### Một số lỗi có thể gặp
- Đôi khi agent sẽ chạy lâu hơn bình thường do giới hạn về API call mỗi phút (hiện tại là rpm đang set là 5)
- Đôi khi server Gemini quá tải dẫn đến agent bị lỗi, thường là vào buổi tối. Có thể thử lại vào 1 thời điểm khác
- Cũng do giới hạn của API free nên chỉ search và scrape tối đa 3 nguồn tin.
- Do thử nghiệm prompting bằng tiếng Việt nên có khả năng Gemini vẫn chưa hiểu và tuân thủ 100% prompt
- 1 số trang web sử dụng nhiều JavaScript hoặc chặn bot nên bị lỗi khi scrape dữ liệu (ví dụ như vietstock.vn)

### Bản quyền
MIT License

## 🇺🇸 English

### Introduction
VN Stock Advisor is an intelligent stock analysis tool utilizing CrewAI's Multi-AI-Agent system.
The tool also leverages artificial intelligence provided by Google Gemini.
The system provides comprehensive stock analysis, including news, fundamental analysis, technical analysis, and recommendations.

### Note:
This project's main purpose is to study and research Large Language Models, Prompt Engineering, and the CrewAI framework, applying them to automated stock analysis.
The analysis reports are collected by VN Stock Advisor from Internet sources and synthesized, analyzed by artificial intelligence.
Therefore, all viewpoints, arguments, and buy/sell recommendations provided by VN Stock Advisor are for reference only.
VN Stock Advisor is not responsible for any investment losses resulting from the use of these analysis reports.

### Features
Uses a system of 4 AI Agents to perform the following tasks:
- 🔍 Automatically search Google and scrape websites to collect and analyze the latest stock news
- 📊 Automatically call APIs and RAG to retrieve data and perform fundamental analysis of a stock (P/E, P/B, ROE, EPS,...)
- 📈 Automatically collect price, volume data from API, calculate and perform technical analysis of a stock (SMA, EMA, RSI, MACD, OBV...)
- 💡 Synthesize data and propose investment decisions (Buy/Sell/Hold)

### Webdemo
- To be updated later

### Installation (for running locally)
```bash
# Install Python >= 3.10, < 3.13
https://www.python.org/downloads/

# Install uv package manager
https://docs.astral.sh/uv/getting-started/installation/

# Install crewai
uv tool install crewai

# Refer to crewai installation guide if you encounter errors
https://docs.crewai.com/installation

# Install dependencies
crewai install
```

### Configuration
Create a `.env` file with the following environment variables:
You can replace the MODELs with other Google models or even from OpenAi, Anthropic, xAI, Ollama...
```
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini/gemini-2.0-flash-001
GEMINI_REASONING_MODEL=gemini/gemini-2.5-flash-preview-04-17
SERPER_API_KEY=your_serper_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
# Telegram Bot (optional if you use Telegram Portfolio Bot)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# example: 123456789 or -1001234567890 (group/channel)
DEFAULT_CHAT_ID=
# example: /Users/you/Documents/portfolio.sqlite3 (leave empty to use default next to the script)
TELEGRAM_PORTFOLIO_DB=
```

### Usage
```bash
# In main.py, replace the symbol variable with the stock code you want to analyze
# Currently set to "HPG" by default

# Use the following command to run the program
crewai run
```

### Telegram Bot & Watchlist Usage

#### Khởi động Telegram Bot
```bash
# Chạy bot Telegram với phân tích thị trường
python telegram_portfolio_bot.py

# Hoặc sử dụng script có sẵn
./run_telegram_bot_with_market_analysis.sh
```

#### Các lệnh Watchlist chính
```bash
# Thêm cổ phiếu vào danh sách theo dõi
/watch_add VIC 50000 Cổ phiếu tiềm năng

# Xem danh sách theo dõi
/watch_list

# Xóa cổ phiếu khỏi danh sách
/watch_remove VIC

# Xóa toàn bộ danh sách
/watch_clear
```

#### Tính năng Watchlist
- 📝 **Theo dõi cổ phiếu tiềm năng**: Thêm cổ phiếu chưa mua vào danh sách theo dõi
- 🎯 **Gợi ý mua thông minh**: Bot tự động phân tích và gợi ý mua khi có tín hiệu tốt
- 📊 **Tích hợp tracking**: Watchlist được phân tích cùng với portfolio trong mỗi lần tracking
- 🔄 **Tự động chuyển đổi**: Khi mua cổ phiếu, nó tự động chuyển từ watchlist sang portfolio

#### Các tín hiệu mua được phát hiện
- 🎯 **Đạt giá mục tiêu**: Giá hiện tại trong vòng 2% của giá mục tiêu
- 📈 **Volume tăng mạnh**: Volume > 150% volume trung bình
- 🔮 **Tín hiệu kỹ thuật**: Sử dụng PredictionEngine để phân tích
- 📈 **Momentum tích cực**: Tăng giá > 2% trong 2 ngày gần nhất

Chi tiết hướng dẫn sử dụng: [WATCHLIST_GUIDE.md](WATCHLIST_GUIDE.md)

### Requirements
- Python >= 3.10, < 3.13
- crewai[tools] >= 0.117.0
- google-generativeai >= 0.8.4
- vnstock >= 3.2.4
- python-dotenv >= 1.1.0
- Google Gemini API key (register free from [Google AI Studio](https://aistudio.google.com/apikey))
- Serper.dev API key (register free from [serper.dev](https://serper.dev/api-key))

### Known Issues
- Occasionally, the agent system may run longer than usual due to the API call limit per minute (currently set to 5 rpm). 
- Sometimes, the Gemini server may be overloaded, resulting in agent errors; it may be advisable to try again at a later time.
- Also, due to the limit of free API, only search and scrape maximum of 3 news sources.
- Due to Vietnamese prompting, Gemini model may not follow 100% as instructed
- Due to heavy JavaScript or bot blocking, some website scraping may lead to error (notably vietstock.vn)

### License
MIT License
