"""
Sentiment Analyzer for VN Stock Advisor.

This module analyzes sentiment from news articles, social media,
and other text sources to gauge market sentiment.
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from textblob import TextBlob
import warnings

warnings.filterwarnings('ignore')

@dataclass
class SentimentSignal:
    """Sentiment analysis result."""
    text_source: str
    sentiment_score: float  # -1 (very negative) to 1 (very positive)
    sentiment_label: str    # 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
    confidence: float
    key_phrases: List[str]
    market_impact: str      # 'BULLISH', 'BEARISH', 'NEUTRAL'
    recommendation: str

class SentimentAnalyzer:
    """
    Sentiment analysis for financial news and social media.
    """
    
    def __init__(self):
        # Financial keywords and their sentiment weights
        self.positive_keywords = {
            'tăng': 0.8, 'tăng trưởng': 0.9, 'lợi nhuận': 0.7, 'thành công': 0.8,
            'tích cực': 0.6, 'khả quan': 0.7, 'thuận lợi': 0.6, 'cải thiện': 0.7,
            'phục hồi': 0.8, 'bứt phá': 0.9, 'đột phá': 0.9, 'kỷ lục': 0.8,
            'mạnh mẽ': 0.7, 'vững chắc': 0.6, 'ổn định': 0.5, 'tăng cao': 0.9,
            'lạc quan': 0.7, 'tin tưởng': 0.6, 'hỗ trợ': 0.5, 'thúc đẩy': 0.6,
            'nâng hạng': 0.8, 'khuyến nghị mua': 0.9, 'mục tiêu giá': 0.6,
            'doanh thu tăng': 0.8, 'lợi nhuận tăng': 0.9, 'thị phần tăng': 0.7
        }
        
        self.negative_keywords = {
            'giảm': -0.8, 'sụt giảm': -0.9, 'thua lỗ': -0.9, 'thất bại': -0.8,
            'tiêu cực': -0.6, 'xấu': -0.7, 'bất lợi': -0.6, 'suy thoái': -0.9,
            'khủng hoảng': -0.9, 'rủi ro': -0.6, 'lo ngại': -0.7, 'giảm mạnh': -0.9,
            'sụp đổ': -0.9, 'thảm họa': -0.9, 'bi quan': -0.7, 'hoài nghi': -0.6,
            'áp lực': -0.6, 'khó khăn': -0.7, 'thách thức': -0.5, 'cảnh báo': -0.7,
            'hạ bậc': -0.8, 'khuyến nghị bán': -0.9, 'cắt lỗ': -0.8,
            'doanh thu giảm': -0.8, 'lợi nhuận giảm': -0.9, 'thị phần giảm': -0.7
        }
        
        self.neutral_keywords = {
            'dự kiến': 0.0, 'kỳ vọng': 0.1, 'theo dõi': 0.0, 'quan sát': 0.0,
            'phân tích': 0.0, 'đánh giá': 0.0, 'nhận định': 0.0, 'dự báo': 0.1,
            'ước tính': 0.0, 'thống kê': 0.0, 'báo cáo': 0.0, 'công bố': 0.0
        }
        
        # Market impact keywords
        self.bullish_phrases = [
            'tăng giá', 'xu hướng tăng', 'đà tăng', 'tín hiệu tích cực',
            'triển vọng khả quan', 'thúc đẩy tăng trưởng', 'hỗ trợ giá',
            'đột phá kỹ thuật', 'vượt kháng cự', 'thanh khoản tốt'
        ]
        
        self.bearish_phrases = [
            'giảm giá', 'xu hướng giảm', 'đà giảm', 'tín hiệu tiêu cực',
            'triển vọng ảm đạm', 'gây áp lực giảm', 'phá vỡ hỗ trợ',
            'suy yếu kỹ thuật', 'thanh khoản kém', 'bán tháo'
        ]
    
    def analyze_text_sentiment(self, text: str, source: str = "unknown") -> SentimentSignal:
        """Analyze sentiment of a single text."""
        if not text or not text.strip():
            return SentimentSignal(
                text_source=source,
                sentiment_score=0.0,
                sentiment_label='NEUTRAL',
                confidence=0.0,
                key_phrases=[],
                market_impact='NEUTRAL',
                recommendation='Không có thông tin để phân tích'
            )
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Calculate sentiment using multiple methods
        textblob_sentiment = self._textblob_sentiment(cleaned_text)
        keyword_sentiment = self._keyword_sentiment(cleaned_text)
        
        # Combine sentiments (weighted average)
        combined_sentiment = (textblob_sentiment * 0.4 + keyword_sentiment * 0.6)
        
        # Determine sentiment label and confidence
        sentiment_label, confidence = self._determine_sentiment_label(combined_sentiment)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(cleaned_text)
        
        # Determine market impact
        market_impact = self._determine_market_impact(cleaned_text, combined_sentiment)
        
        # Generate recommendation
        recommendation = self._generate_sentiment_recommendation(
            combined_sentiment, market_impact, confidence
        )
        
        return SentimentSignal(
            text_source=source,
            sentiment_score=combined_sentiment,
            sentiment_label=sentiment_label,
            confidence=confidence,
            key_phrases=key_phrases,
            market_impact=market_impact,
            recommendation=recommendation
        )
    
    def analyze_news_batch(self, news_articles: List[Dict]) -> Dict:
        """Analyze sentiment for a batch of news articles."""
        if not news_articles:
            return self._empty_sentiment_result()
        
        sentiments = []
        for article in news_articles:
            text = article.get('content', article.get('title', ''))
            source = article.get('source', 'unknown')
            sentiment = self.analyze_text_sentiment(text, source)
            sentiments.append(sentiment)
        
        return self._aggregate_sentiments(sentiments)
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep Vietnamese characters
        text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _textblob_sentiment(self, text: str) -> float:
        """Calculate sentiment using TextBlob."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            return polarity
        except:
            return 0.0
    
    def _keyword_sentiment(self, text: str) -> float:
        """Calculate sentiment based on financial keywords."""
        sentiment_score = 0.0
        word_count = 0
        
        words = text.split()
        
        for word in words:
            # Check positive keywords
            for keyword, weight in self.positive_keywords.items():
                if keyword in word or word in keyword:
                    sentiment_score += weight
                    word_count += 1
            
            # Check negative keywords
            for keyword, weight in self.negative_keywords.items():
                if keyword in word or word in keyword:
                    sentiment_score += weight
                    word_count += 1
            
            # Check neutral keywords
            for keyword, weight in self.neutral_keywords.items():
                if keyword in word or word in keyword:
                    sentiment_score += weight
                    word_count += 1
        
        # Normalize by word count
        if word_count > 0:
            sentiment_score = sentiment_score / word_count
        
        # Clip to [-1, 1] range
        sentiment_score = np.clip(sentiment_score, -1, 1)
        
        return sentiment_score
    
    def _determine_sentiment_label(self, sentiment_score: float) -> Tuple[str, float]:
        """Determine sentiment label and confidence."""
        abs_score = abs(sentiment_score)
        
        if abs_score >= 0.6:
            confidence = min(0.9, abs_score)
            if sentiment_score > 0:
                return 'POSITIVE', confidence
            else:
                return 'NEGATIVE', confidence
        elif abs_score >= 0.2:
            confidence = abs_score * 0.7
            if sentiment_score > 0:
                return 'POSITIVE', confidence
            else:
                return 'NEGATIVE', confidence
        else:
            confidence = 0.8 - abs_score
            return 'NEUTRAL', confidence
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text."""
        key_phrases = []
        
        # Find bullish phrases
        for phrase in self.bullish_phrases:
            if phrase in text:
                key_phrases.append(phrase)
        
        # Find bearish phrases
        for phrase in self.bearish_phrases:
            if phrase in text:
                key_phrases.append(phrase)
        
        # Find keyword matches
        words = text.split()
        for word in words:
            for keyword in list(self.positive_keywords.keys()) + list(self.negative_keywords.keys()):
                if keyword in word and len(keyword) > 3:
                    key_phrases.append(keyword)
        
        # Remove duplicates and limit to top 5
        key_phrases = list(set(key_phrases))[:5]
        
        return key_phrases
    
    def _determine_market_impact(self, text: str, sentiment_score: float) -> str:
        """Determine market impact based on text content and sentiment."""
        # Check for explicit bullish/bearish phrases
        bullish_count = sum(1 for phrase in self.bullish_phrases if phrase in text)
        bearish_count = sum(1 for phrase in self.bearish_phrases if phrase in text)
        
        if bullish_count > bearish_count and sentiment_score > 0.2:
            return 'BULLISH'
        elif bearish_count > bullish_count and sentiment_score < -0.2:
            return 'BEARISH'
        elif abs(sentiment_score) >= 0.4:
            return 'BULLISH' if sentiment_score > 0 else 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _generate_sentiment_recommendation(self, sentiment_score: float, market_impact: str, confidence: float) -> str:
        """Generate recommendation based on sentiment analysis."""
        if confidence < 0.3:
            return "Thông tin không đủ rõ ràng để đưa ra khuyến nghị"
        
        if market_impact == 'BULLISH' and sentiment_score > 0.5:
            if confidence > 0.7:
                return "Tin tức tích cực mạnh - Có thể cân nhắc mua vào"
            else:
                return "Tin tức có xu hướng tích cực - Theo dõi thêm"
        elif market_impact == 'BEARISH' and sentiment_score < -0.5:
            if confidence > 0.7:
                return "Tin tức tiêu cực mạnh - Cân nhắc bán hoặc tránh mua"
            else:
                return "Tin tức có xu hướng tiêu cực - Cẩn trọng"
        elif abs(sentiment_score) < 0.3:
            return "Tin tức trung tính - Tác động hạn chế đến giá"
        else:
            return "Tín hiệu sentiment không rõ ràng - Cần phân tích thêm"
    
    def _aggregate_sentiments(self, sentiments: List[SentimentSignal]) -> Dict:
        """Aggregate multiple sentiment signals."""
        if not sentiments:
            return self._empty_sentiment_result()
        
        # Calculate averages
        sentiment_scores = [s.sentiment_score for s in sentiments]
        confidences = [s.confidence for s in sentiments]
        
        avg_sentiment = np.mean(sentiment_scores)
        avg_confidence = np.mean(confidences)
        
        # Count sentiment types
        positive_count = len([s for s in sentiments if s.sentiment_label == 'POSITIVE'])
        negative_count = len([s for s in sentiments if s.sentiment_label == 'NEGATIVE'])
        neutral_count = len([s for s in sentiments if s.sentiment_label == 'NEUTRAL'])
        
        # Count market impacts
        bullish_count = len([s for s in sentiments if s.market_impact == 'BULLISH'])
        bearish_count = len([s for s in sentiments if s.market_impact == 'BEARISH'])
        
        # Determine overall sentiment
        if avg_sentiment > 0.3 and positive_count > negative_count:
            overall_sentiment = 'POSITIVE'
            market_outlook = 'BULLISH'
        elif avg_sentiment < -0.3 and negative_count > positive_count:
            overall_sentiment = 'NEGATIVE'
            market_outlook = 'BEARISH'
        else:
            overall_sentiment = 'NEUTRAL'
            market_outlook = 'NEUTRAL'
        
        # Collect all key phrases
        all_key_phrases = []
        for s in sentiments:
            all_key_phrases.extend(s.key_phrases)
        
        # Get most common phrases
        phrase_counts = {}
        for phrase in all_key_phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        top_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_phrases = [phrase for phrase, count in top_phrases]
        
        # Generate overall recommendation
        overall_recommendation = self._generate_overall_recommendation(
            avg_sentiment, market_outlook, avg_confidence, len(sentiments)
        )
        
        return {
            'total_articles': len(sentiments),
            'average_sentiment': avg_sentiment,
            'average_confidence': avg_confidence,
            'overall_sentiment': overall_sentiment,
            'market_outlook': market_outlook,
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'neutral_articles': neutral_count,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'top_key_phrases': top_phrases,
            'recommendation': overall_recommendation,
            'sentiment_distribution': {
                'positive': positive_count / len(sentiments),
                'negative': negative_count / len(sentiments),
                'neutral': neutral_count / len(sentiments)
            }
        }
    
    def _generate_overall_recommendation(self, avg_sentiment: float, market_outlook: str, 
                                       avg_confidence: float, article_count: int) -> str:
        """Generate overall recommendation from aggregated sentiment."""
        if article_count < 3:
            return "Không đủ dữ liệu để đưa ra khuyến nghị đáng tin cậy"
        
        if avg_confidence < 0.4:
            return "Sentiment analysis có độ tin cậy thấp - Cần thêm thông tin"
        
        if market_outlook == 'BULLISH' and avg_sentiment > 0.4:
            return f"Sentiment tổng thể tích cực ({avg_sentiment:.2f}) - Môi trường tin tức hỗ trợ cho xu hướng tăng"
        elif market_outlook == 'BEARISH' and avg_sentiment < -0.4:
            return f"Sentiment tổng thể tiêu cực ({avg_sentiment:.2f}) - Môi trường tin tức tạo áp lực giảm"
        elif abs(avg_sentiment) < 0.3:
            return "Sentiment trung tính - Tin tức không tạo ra tác động rõ ràng đến giá"
        else:
            return f"Sentiment hỗn hợp ({avg_sentiment:.2f}) - Cần theo dõi diễn biến thêm"
    
    def _empty_sentiment_result(self) -> Dict:
        """Return empty sentiment result when no data available."""
        return {
            'total_articles': 0,
            'average_sentiment': 0.0,
            'average_confidence': 0.0,
            'overall_sentiment': 'NEUTRAL',
            'market_outlook': 'NEUTRAL',
            'positive_articles': 0,
            'negative_articles': 0,
            'neutral_articles': 0,
            'bullish_signals': 0,
            'bearish_signals': 0,
            'top_key_phrases': [],
            'recommendation': 'Không có dữ liệu tin tức để phân tích sentiment',
            'sentiment_distribution': {
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0
            }
        }
