"""
News Collector using SERPER API, Gemini, and OpenAI for Vietnamese and International Market Analysis
"""
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import google.generativeai as genai
import openai


class NewsCategory(str, Enum):
    DOMESTIC = "domestic"  # Tin tức trong nước
    INTERNATIONAL = "international"  # Tin tức quốc tế
    ECONOMIC = "economic"  # Tin tức kinh tế
    POLITICAL = "political"  # Tin tức chính trị
    MARKET = "market"  # Tin tức thị trường


@dataclass
class NewsItem:
    title: str
    snippet: str
    url: str
    source: str
    published_date: Optional[str] = None
    category: NewsCategory = NewsCategory.MARKET
    sentiment_score: Optional[float] = None  # -1 to 1, negative to positive
    relevance_score: Optional[float] = None  # 0 to 1, how relevant to VN market


class AISentimentAnalyzer:
    """AI-powered sentiment analysis using Gemini and OpenAI"""
    
    def __init__(self, gemini_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key
        
        # Initialize Gemini
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize OpenAI
        if openai_api_key:
            openai.api_key = openai_api_key
    
    async def analyze_sentiment_with_gemini(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Analyze sentiment using Gemini AI"""
        if not self.gemini_api_key or not self.gemini_model:
            return news_items
        
        try:
            for item in news_items:
                text = f"Title: {item.title}\nContent: {item.snippet}"
                
                prompt = f"""
                Phân tích tác động của tin tức sau đây đến thị trường chứng khoán Việt Nam:
                
                {text}
                
                Hãy đánh giá:
                1. Sentiment score từ -1 (rất tiêu cực) đến 1 (rất tích cực)
                2. Relevance score từ 0 (không liên quan) đến 1 (rất liên quan) đến thị trường VN
                3. Tóm tắt ngắn gọn tác động (1-2 câu)
                
                Trả về kết quả theo format JSON:
                {{
                    "sentiment_score": 0.5,
                    "relevance_score": 0.8,
                    "impact_summary": "Mô tả tác động ngắn gọn"
                }}
                """
                
                response = self.gemini_model.generate_content(prompt)
                result = self._parse_ai_response(response.text)
                
                if result:
                    item.sentiment_score = result.get("sentiment_score", 0.0)
                    item.relevance_score = result.get("relevance_score", 0.0)
                    item.impact_summary = result.get("impact_summary", "")
        
        except Exception as e:
            print(f"Error in Gemini sentiment analysis: {e}")
        
        return news_items
    
    async def analyze_sentiment_with_openai(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Analyze sentiment using OpenAI GPT"""
        if not self.openai_api_key:
            return news_items
        
        try:
            for item in news_items:
                text = f"Title: {item.title}\nContent: {item.snippet}"
                
                prompt = f"""
                Analyze the impact of this news on Vietnamese stock market:
                
                {text}
                
                Provide:
                1. Sentiment score from -1 (very negative) to 1 (very positive)
                2. Relevance score from 0 (not relevant) to 1 (highly relevant) to VN market
                3. Brief impact summary (1-2 sentences)
                
                Return JSON format:
                {{
                    "sentiment_score": 0.5,
                    "relevance_score": 0.8,
                    "impact_summary": "Brief impact description"
                }}
                """
                
                response = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                
                result = self._parse_ai_response(response.choices[0].message.content)
                
                if result:
                    item.sentiment_score = result.get("sentiment_score", 0.0)
                    item.relevance_score = result.get("relevance_score", 0.0)
                    item.impact_summary = result.get("impact_summary", "")
        
        except Exception as e:
            print(f"Error in OpenAI sentiment analysis: {e}")
        
        return news_items
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response and extract JSON"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing AI response: {e}")
        
        return None


class SerperNewsCollector:
    """Collect news using SERPER API for market analysis"""
    
    def __init__(self, api_key: str, gemini_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/news"
        self.session: Optional[aiohttp.ClientSession] = None
        self.ai_analyzer = AISentimentAnalyzer(gemini_api_key, openai_api_key)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_news(
        self, 
        query: str, 
        num_results: int = 10,
        language: str = "vi",
        country: str = "vn"
    ) -> List[NewsItem]:
        """Search for news using SERPER API"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results,
            "gl": country,  # Country code
            "hl": language,  # Language code
            "safe": "off"
        }
        
        try:
            async with self.session.post(
                self.base_url, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_news_results(data)
                else:
                    print(f"SERPER API error: {response.status}")
                    return []
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def _parse_news_results(self, data: Dict[str, Any]) -> List[NewsItem]:
        """Parse SERPER API response into NewsItem objects"""
        news_items = []
        
        if "news" not in data:
            return news_items
        
        for item in data["news"]:
            try:
                news_item = NewsItem(
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    url=item.get("link", ""),
                    source=item.get("source", ""),
                    published_date=item.get("date", ""),
                    category=NewsCategory.MARKET
                )
                news_items.append(news_item)
            except Exception as e:
                print(f"Error parsing news item: {e}")
                continue
        
        return news_items
    
    async def collect_vietnamese_market_news(self) -> List[NewsItem]:
        """Collect Vietnamese market-specific news"""
        queries = [
            "VN-Index thị trường chứng khoán Việt Nam",
            "chứng khoán Việt Nam hôm nay",
            "thị trường chứng khoán Việt Nam tin tức",
            "VN-Index phân tích dự báo",
            "kinh tế Việt Nam GDP tăng trưởng",
            "ngân hàng nhà nước Việt Nam chính sách",
            "lạm phát Việt Nam CPI",
            "doanh nghiệp Việt Nam báo cáo tài chính"
        ]
        
        all_news = []
        for query in queries:
            news = await self.search_news(query, num_results=5, language="vi", country="vn")
            all_news.extend(news)
        
        # Remove duplicates and add AI-powered sentiment analysis
        unique_news = self._remove_duplicates(all_news)
        
        # Try AI analysis first, fallback to keyword-based
        if self.ai_analyzer.gemini_api_key:
            unique_news = await self.ai_analyzer.analyze_sentiment_with_gemini(unique_news)
        elif self.ai_analyzer.openai_api_key:
            unique_news = await self.ai_analyzer.analyze_sentiment_with_openai(unique_news)
        else:
            unique_news = self._analyze_sentiment(unique_news)
        
        return unique_news
    
    async def collect_international_market_news(self) -> List[NewsItem]:
        """Collect international market news that affects Vietnam"""
        queries = [
            "US Federal Reserve interest rate decision",
            "US stock market S&P 500 NASDAQ",
            "China economy GDP growth",
            "oil prices crude oil WTI Brent",
            "gold prices precious metals",
            "USD VND exchange rate",
            "global inflation economic outlook",
            "US China trade war tensions",
            "European Central Bank policy",
            "Asian stock markets performance"
        ]
        
        all_news = []
        for query in queries:
            news = await self.search_news(query, num_results=3, language="en", country="us")
            all_news.extend(news)
        
        # Remove duplicates and add AI-powered sentiment analysis
        unique_news = self._remove_duplicates(all_news)
        
        # Try AI analysis first, fallback to keyword-based
        if self.ai_analyzer.gemini_api_key:
            unique_news = await self.ai_analyzer.analyze_sentiment_with_gemini(unique_news)
        elif self.ai_analyzer.openai_api_key:
            unique_news = await self.ai_analyzer.analyze_sentiment_with_openai(unique_news)
        else:
            unique_news = self._analyze_sentiment(unique_news)
        
        return unique_news
    
    def _remove_duplicates(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Remove duplicate news items based on title similarity"""
        unique_items = []
        seen_titles = set()
        
        for item in news_items:
            # Simple deduplication based on title
            title_key = item.title.lower().strip()
            if title_key not in seen_titles and len(title_key) > 10:
                seen_titles.add(title_key)
                unique_items.append(item)
        
        return unique_items
    
    def _analyze_sentiment(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Simple sentiment analysis based on keywords"""
        positive_keywords = [
            "tăng", "tăng trưởng", "phục hồi", "khởi sắc", "tích cực", "lạc quan",
            "tốt", "mạnh", "cao", "vượt", "thành công", "tăng trưởng", "tăng giá",
            "bullish", "growth", "recovery", "positive", "strong", "rise", "gain"
        ]
        
        negative_keywords = [
            "giảm", "sụt", "yếu", "tiêu cực", "bi quan", "khó khăn", "thấp",
            "sụt giảm", "mất giá", "khủng hoảng", "suy thoái", "rủi ro",
            "bearish", "decline", "fall", "drop", "crisis", "recession", "risk"
        ]
        
        for item in news_items:
            text = (item.title + " " + item.snippet).lower()
            
            positive_count = sum(1 for keyword in positive_keywords if keyword in text)
            negative_count = sum(1 for keyword in negative_keywords if keyword in text)
            
            total_keywords = positive_count + negative_count
            if total_keywords > 0:
                item.sentiment_score = (positive_count - negative_count) / total_keywords
            else:
                item.sentiment_score = 0.0
            
            # Calculate relevance score (simple keyword matching)
            vn_keywords = ["việt nam", "vietnam", "vn", "hồ chí minh", "hanoi", "vietnam"]
            relevance_count = sum(1 for keyword in vn_keywords if keyword in text)
            item.relevance_score = min(relevance_count / 3.0, 1.0)
        
        return news_items
    
    async def collect_comprehensive_news(self) -> Dict[str, List[NewsItem]]:
        """Collect comprehensive news for market analysis"""
        vietnamese_news = await self.collect_vietnamese_market_news()
        international_news = await self.collect_international_market_news()
        
        return {
            "domestic": vietnamese_news,
            "international": international_news,
            "all": vietnamese_news + international_news
        }


class MarketNewsAnalyzer:
    """Analyze collected news for market insights"""
    
    def __init__(self):
        self.news_collector: Optional[SerperNewsCollector] = None
    
    async def analyze_market_sentiment(self, news_data: Dict[str, List[NewsItem]]) -> Dict[str, Any]:
        """Analyze overall market sentiment from news"""
        domestic_news = news_data.get("domestic", [])
        international_news = news_data.get("international", [])
        
        # Calculate sentiment scores
        domestic_sentiment = self._calculate_sentiment_score(domestic_news)
        international_sentiment = self._calculate_sentiment_score(international_news)
        
        # Calculate weighted overall sentiment
        total_news = len(domestic_news) + len(international_news)
        if total_news > 0:
            overall_sentiment = (
                domestic_sentiment * len(domestic_news) + 
                international_sentiment * len(international_news)
            ) / total_news
        else:
            overall_sentiment = 0.0
        
        # Identify key themes
        key_themes = self._identify_key_themes(domestic_news + international_news)
        
        return {
            "overall_sentiment": overall_sentiment,
            "domestic_sentiment": domestic_sentiment,
            "international_sentiment": international_sentiment,
            "key_themes": key_themes,
            "news_count": {
                "domestic": len(domestic_news),
                "international": len(international_news),
                "total": total_news
            }
        }
    
    def _calculate_sentiment_score(self, news_items: List[NewsItem]) -> float:
        """Calculate average sentiment score for news items"""
        if not news_items:
            return 0.0
        
        valid_scores = [item.sentiment_score for item in news_items if item.sentiment_score is not None]
        if not valid_scores:
            return 0.0
        
        return sum(valid_scores) / len(valid_scores)
    
    def _identify_key_themes(self, news_items: List[NewsItem]) -> List[str]:
        """Identify key themes from news headlines"""
        theme_keywords = {
            "Lãi suất": ["lãi suất", "interest rate", "fed", "ngân hàng nhà nước"],
            "Lạm phát": ["lạm phát", "inflation", "cpi", "giá cả"],
            "Dầu thô": ["dầu thô", "oil", "crude", "giá dầu"],
            "USD/VND": ["usd", "vnd", "tỷ giá", "exchange rate", "đô la"],
            "Trung Quốc": ["trung quốc", "china", "bắc kinh", "thương mại"],
            "Mỹ": ["mỹ", "usa", "america", "federal reserve"],
            "Ngân hàng": ["ngân hàng", "bank", "tín dụng", "cho vay"],
            "Bất động sản": ["bất động sản", "real estate", "nhà đất", "property"]
        }
        
        theme_counts = {theme: 0 for theme in theme_keywords.keys()}
        
        for item in news_items:
            text = (item.title + " " + item.snippet).lower()
            for theme, keywords in theme_keywords.items():
                if any(keyword in text for keyword in keywords):
                    theme_counts[theme] += 1
        
        # Return top 5 themes
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:5] if count > 0]


async def get_market_news_analysis(
    serper_api_key: str, 
    gemini_api_key: Optional[str] = None, 
    openai_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Main function to get comprehensive market news analysis"""
    async with SerperNewsCollector(serper_api_key, gemini_api_key, openai_api_key) as collector:
        news_data = await collector.collect_comprehensive_news()
        
        analyzer = MarketNewsAnalyzer()
        sentiment_analysis = await analyzer.analyze_market_sentiment(news_data)
        
        return {
            "news_data": news_data,
            "sentiment_analysis": sentiment_analysis,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test the news collector
    async def test_news_collector():
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("Please set SERPER_API_KEY environment variable")
            return
        
        result = await get_market_news_analysis(serper_key, gemini_key, openai_key)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test_news_collector())
