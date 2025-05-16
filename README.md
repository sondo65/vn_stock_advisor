# VN Stock Advisor (v.0.1.2)

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
- 📈 Tự động thu thập giữ liệu giá từ VCI hoặc TCBS, tính toán và phân tích kỹ thuật (SMA, EMA, RSI, MACD,...)
- 💡 Tổng hợp dữ liệu và đề xuất quyết định đầu tư (Mua/Bán/Giữ)

### Webdemo
- Update sau

### Cài đặt (nếu muốn chạy locally)
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
MODEL=gemini/gemini-2.0-flash-001
SERPER_API_KEY=your_serper_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### Sử dụng
```bash
# Vào main.py, thay biến symbol bằng mã cổ phiếu muốn phân tích
# Mặc định hiện đang để là "HPG"

# Sử dụng lệnh sau để chạy chương trình
crewai run
```
### Yêu cầu
- Python >= 3.10, < 3.13
- crewai[tools] >= 0.117.0
- firecrawl-py>=2.5.4
- google-generativeai >= 0.8.4
- vnstock >= 3.2.4
- python-dotenv >= 1.1.0
- Google Gemini API key (đăng kí free từ [Google AI Studio](https://aistudio.google.com/apikey))
- Serper.dev API key (đăng kí free từ [serper.dev](https://serper.dev/api-key))
- Firecrawl.dev API key (đăng kí free từ [firecrawl.dev](https://www.firecrawl.dev/app/api-keys))

### Một số lỗi có thể gặp
- Đã thiết lập JSON knowledge source nhưng có vẻ Agent chưa tận dụng được -> chuyển sang dùng FileReadTool
- Custom tool sử dụng @tool decorator không hoạt động. Phải chuyển sang dùng BaseTool class mới chạy.
- FileReadTool mặc định ko dùng utf-8 encoding. Phải viết lại tool này.

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
- 📈 Automatically collect price data from API, calculate and perform technical analysis of a stock (SMA, EMA, RSI, MACD,...)
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
MODEL=gemini/gemini-2.0-flash-001
SERPER_API_KEY=your_serper_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### Usage
```bash
# In main.py, replace the symbol variable with the stock code you want to analyze
# Currently set to "HPG" by default

# Use the following command to run the program
crewai run
```

### Requirements
- Python >= 3.10, < 3.13
- crewai[tools] >= 0.117.0
- firecrawl-py>=2.5.4
- google-generativeai >= 0.8.4
- vnstock >= 3.2.4
- python-dotenv >= 1.1.0
- Google Gemini API key (register free from [Google AI Studio](https://aistudio.google.com/apikey))
- Serper.dev API key (register free from [serper.dev](https://serper.dev/api-key))
- Firecrawl.dev API key (register free từ [firecrawl.dev](https://www.firecrawl.dev/app/api-keys))

### Known Issues
- Already implemented JSON knowledge source but seems like Agent still not be able to take advantage of. Using FileReadTool instead.
- Custom tool using @tool decorator not working. Using BaseTool class instead.
- FileReadTool not using utf-8 encoding. Need to re-write this tool instead.

### License
MIT License