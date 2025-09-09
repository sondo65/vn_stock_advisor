"""
VN-Index Market Analysis combining news sentiment and technical data
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd

from .news_collector import get_market_news_analysis, NewsItem


class MarketTrend(str, Enum):
    BULLISH = "BULLISH"  # Tăng mạnh
    BULLISH_WEAK = "BULLISH_WEAK"  # Tăng nhẹ
    NEUTRAL = "NEUTRAL"  # Trung tính
    BEARISH_WEAK = "BEARISH_WEAK"  # Giảm nhẹ
    BEARISH = "BEARISH"  # Giảm mạnh


@dataclass
class VNIndexPrediction:
    trend: MarketTrend
    confidence: float  # 0-1
    target_range: Tuple[float, float]  # (min, max) expected range
    key_factors: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH
    recommendation: str
    technical_signals: Dict[str, Any]
    news_impact: Dict[str, Any]
    timestamp: str


class VNIndexAnalyzer:
    """Analyze VN-Index based on news sentiment and technical data"""
    
    def __init__(self):
        self.current_vnindex = None
        self.previous_close = None
        self.volume_data = None
    
    async def get_vnindex_data(self) -> Dict[str, Any]:
        """Get current VN-Index data from vnstock"""
        try:
            from vnstock import Vnstock
            
            # Try to get VN-Index data
            for source in ("VCI", "TCBS", "MSN"):
                try:
                    vnindex = Vnstock().stock(symbol="VNINDEX", source=source)
                    
                    # Get historical data to get latest price
                    try:
                        today = datetime.now().date()
                        start_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
                        end_date = today.strftime("%Y-%m-%d")
                        
                        hist_data = vnindex.quote.history(
                            start=start_date,
                            end=end_date,
                            interval="1D"
                        )
                        
                        if hist_data is not None and not hist_data.empty:
                            # Get latest data (most recent)
                            latest_data = hist_data.iloc[-1]
                            current_price = float(latest_data["close"])
                            volume = float(latest_data["volume"]) if "volume" in latest_data else None
                            
                            # Get previous close (second to last)
                            if len(hist_data) > 1:
                                previous_data = hist_data.iloc[-2]
                                previous_close = float(previous_data["close"])
                            else:
                                previous_close = current_price
                            
                            return {
                                "current_price": current_price,
                                "previous_close": previous_close,
                                "volume": volume,
                                "change": current_price - previous_close,
                                "change_pct": ((current_price - previous_close) / previous_close * 100) if previous_close else 0,
                                "source": source
                            }
                    except Exception:
                        continue
                except Exception:
                    continue
            
            return None
        except Exception as e:
            print(f"Error getting VN-Index data: {e}")
            return None
    
    def analyze_technical_signals(self, vnindex_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical signals for VN-Index"""
        if not vnindex_data:
            return {}
        
        current_price = vnindex_data.get("current_price", 0)
        previous_close = vnindex_data.get("previous_close", 0)
        change_pct = vnindex_data.get("change_pct", 0)
        volume = vnindex_data.get("volume", 0)
        
        signals = {
            "price_action": "NEUTRAL",
            "volume_signal": "NEUTRAL", 
            "momentum": "NEUTRAL",
            "support_resistance": "NEUTRAL"
        }
        
        # Price action analysis
        if change_pct > 1.0:
            signals["price_action"] = "BULLISH"
        elif change_pct > 0.3:
            signals["price_action"] = "BULLISH_WEAK"
        elif change_pct < -1.0:
            signals["price_action"] = "BEARISH"
        elif change_pct < -0.3:
            signals["price_action"] = "BEARISH_WEAK"
        
        # Volume analysis (simplified)
        if volume and volume > 1000000:  # High volume threshold
            signals["volume_signal"] = "HIGH_VOLUME"
        elif volume and volume < 500000:  # Low volume threshold
            signals["volume_signal"] = "LOW_VOLUME"
        
        # Momentum analysis
        if change_pct > 0.5:
            signals["momentum"] = "BULLISH"
        elif change_pct < -0.5:
            signals["momentum"] = "BEARISH"
        
        return signals
    
    def calculate_news_impact_score(self, sentiment_analysis: Dict[str, Any]) -> float:
        """Calculate overall news impact score (-1 to 1)"""
        overall_sentiment = sentiment_analysis.get("overall_sentiment", 0.0)
        domestic_sentiment = sentiment_analysis.get("domestic_sentiment", 0.0)
        international_sentiment = sentiment_analysis.get("international_sentiment", 0.0)
        
        # Weight domestic news more heavily for VN market
        weighted_sentiment = (domestic_sentiment * 0.7 + international_sentiment * 0.3)
        
        # Combine with overall sentiment
        final_score = (weighted_sentiment + overall_sentiment) / 2
        
        return max(-1.0, min(1.0, final_score))
    
    def determine_market_trend(
        self, 
        technical_signals: Dict[str, Any], 
        news_impact: float,
        vnindex_data: Dict[str, Any]
    ) -> Tuple[MarketTrend, float]:
        """Determine overall market trend based on technical and news analysis"""
        
        # Technical score
        tech_score = 0.0
        price_action = technical_signals.get("price_action", "NEUTRAL")
        momentum = technical_signals.get("momentum", "NEUTRAL")
        volume_signal = technical_signals.get("volume_signal", "NEUTRAL")
        
        # Price action scoring
        if price_action == "BULLISH":
            tech_score += 0.4
        elif price_action == "BULLISH_WEAK":
            tech_score += 0.2
        elif price_action == "BEARISH":
            tech_score -= 0.4
        elif price_action == "BEARISH_WEAK":
            tech_score -= 0.2
        
        # Momentum scoring
        if momentum == "BULLISH":
            tech_score += 0.3
        elif momentum == "BEARISH":
            tech_score -= 0.3
        
        # Volume confirmation
        if volume_signal == "HIGH_VOLUME" and tech_score > 0:
            tech_score += 0.1
        elif volume_signal == "HIGH_VOLUME" and tech_score < 0:
            tech_score -= 0.1
        
        # Combine technical and news analysis
        combined_score = (tech_score * 0.6) + (news_impact * 0.4)
        
        # Determine trend
        if combined_score > 0.6:
            trend = MarketTrend.BULLISH
            confidence = min(0.9, 0.6 + abs(combined_score) * 0.3)
        elif combined_score > 0.2:
            trend = MarketTrend.BULLISH_WEAK
            confidence = min(0.8, 0.5 + abs(combined_score) * 0.3)
        elif combined_score < -0.6:
            trend = MarketTrend.BEARISH
            confidence = min(0.9, 0.6 + abs(combined_score) * 0.3)
        elif combined_score < -0.2:
            trend = MarketTrend.BEARISH_WEAK
            confidence = min(0.8, 0.5 + abs(combined_score) * 0.3)
        else:
            trend = MarketTrend.NEUTRAL
            confidence = 0.5
        
        return trend, confidence
    
    def calculate_target_range(
        self, 
        trend: MarketTrend, 
        current_price: float, 
        confidence: float
    ) -> Tuple[float, float]:
        """Calculate expected price range for the day"""
        
        # Base volatility assumption (1-3% daily range)
        base_volatility = 0.02  # 2%
        
        # Adjust based on trend and confidence
        if trend in [MarketTrend.BULLISH, MarketTrend.BEARISH]:
            volatility_multiplier = 1.5 + confidence
        elif trend in [MarketTrend.BULLISH_WEAK, MarketTrend.BEARISH_WEAK]:
            volatility_multiplier = 1.0 + confidence
        else:
            volatility_multiplier = 0.8 + confidence * 0.4
        
        daily_range = current_price * base_volatility * volatility_multiplier
        
        if trend in [MarketTrend.BULLISH, MarketTrend.BULLISH_WEAK]:
            min_price = current_price - daily_range * 0.3
            max_price = current_price + daily_range * 0.7
        elif trend in [MarketTrend.BEARISH, MarketTrend.BEARISH_WEAK]:
            min_price = current_price - daily_range * 0.7
            max_price = current_price + daily_range * 0.3
        else:
            min_price = current_price - daily_range * 0.5
            max_price = current_price + daily_range * 0.5
        
        return (min_price, max_price)
    
    def generate_recommendation(
        self, 
        trend: MarketTrend, 
        confidence: float,
        key_factors: List[str]
    ) -> str:
        """Generate trading recommendation based on analysis"""
        
        if trend == MarketTrend.BULLISH and confidence > 0.7:
            return "Mạnh: Có thể mua vào với kỳ vọng tăng giá. Theo dõi khối lượng giao dịch."
        elif trend == MarketTrend.BULLISH_WEAK and confidence > 0.6:
            return "Nhẹ: Cân nhắc mua vào với vị thế nhỏ. Chờ tín hiệu xác nhận."
        elif trend == MarketTrend.BEARISH and confidence > 0.7:
            return "Mạnh: Nên bán ra hoặc giảm vị thế. Tránh mua vào mới."
        elif trend == MarketTrend.BEARISH_WEAK and confidence > 0.6:
            return "Nhẹ: Thận trọng với vị thế mua. Có thể giảm vị thế."
        elif trend == MarketTrend.NEUTRAL:
            return "Trung tính: Chờ tín hiệu rõ ràng. Có thể giao dịch trong phạm vi hẹp."
        else:
            return "Không rõ: Cần thêm thông tin để đưa ra quyết định."
    
    def assess_risk_level(self, confidence: float, volatility: float) -> str:
        """Assess risk level based on confidence and market volatility"""
        if confidence > 0.8 and volatility < 0.03:
            return "LOW"
        elif confidence > 0.6 and volatility < 0.05:
            return "MEDIUM"
        else:
            return "HIGH"
    
    async def analyze_vnindex_market(
        self, 
        serper_api_key: str,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ) -> VNIndexPrediction:
        """Main analysis function for VN-Index market prediction"""
        
        # Get news analysis
        news_analysis = await get_market_news_analysis(serper_api_key, gemini_api_key, openai_api_key)
        sentiment_analysis = news_analysis["sentiment_analysis"]
        
        # Get VN-Index data
        vnindex_data = await self.get_vnindex_data()
        
        # Analyze technical signals
        technical_signals = self.analyze_technical_signals(vnindex_data)
        
        # Calculate news impact
        news_impact = self.calculate_news_impact_score(sentiment_analysis)
        
        # Determine market trend
        trend, confidence = self.determine_market_trend(technical_signals, news_impact, vnindex_data)
        
        # Calculate target range
        current_price = vnindex_data.get("current_price", 1000) if vnindex_data else 1000
        target_range = self.calculate_target_range(trend, current_price, confidence)
        
        # Generate key factors
        key_factors = []
        if sentiment_analysis.get("key_themes"):
            key_factors.extend(sentiment_analysis["key_themes"][:3])
        
        if technical_signals.get("price_action") != "NEUTRAL":
            key_factors.append(f"Tín hiệu giá: {technical_signals['price_action']}")
        
        if technical_signals.get("volume_signal") != "NEUTRAL":
            key_factors.append(f"Khối lượng: {technical_signals['volume_signal']}")
        
        # Generate recommendation
        recommendation = self.generate_recommendation(trend, confidence, key_factors)
        
        # Assess risk level
        volatility = abs(vnindex_data.get("change_pct", 0) / 100) if vnindex_data else 0.02
        risk_level = self.assess_risk_level(confidence, volatility)
        
        return VNIndexPrediction(
            trend=trend,
            confidence=confidence,
            target_range=target_range,
            key_factors=key_factors,
            risk_level=risk_level,
            recommendation=recommendation,
            technical_signals=technical_signals,
            news_impact={
                "overall_sentiment": sentiment_analysis.get("overall_sentiment", 0.0),
                "domestic_sentiment": sentiment_analysis.get("domestic_sentiment", 0.0),
                "international_sentiment": sentiment_analysis.get("international_sentiment", 0.0),
                "news_count": sentiment_analysis.get("news_count", {}),
                "impact_score": news_impact
            },
            timestamp=datetime.now().isoformat()
        )


async def get_vnindex_market_analysis(
    serper_api_key: str,
    gemini_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> VNIndexPrediction:
    """Main function to get VN-Index market analysis"""
    analyzer = VNIndexAnalyzer()
    return await analyzer.analyze_vnindex_market(serper_api_key, gemini_api_key, openai_api_key)


if __name__ == "__main__":
    # Test the VN-Index analyzer
    async def test_vnindex_analyzer():
        import os
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("Please set SERPER_API_KEY environment variable")
            return
        
        result = await get_vnindex_market_analysis(serper_key, gemini_key, openai_key)
        print(f"VN-Index Analysis:")
        print(f"Trend: {result.trend}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Target Range: {result.target_range[0]:.2f} - {result.target_range[1]:.2f}")
        print(f"Risk Level: {result.risk_level}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Key Factors: {', '.join(result.key_factors)}")
    
    asyncio.run(test_vnindex_analyzer())
