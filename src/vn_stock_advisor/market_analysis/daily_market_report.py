"""
Daily Market Report Generator for Telegram Bot
"""
import os
from datetime import datetime, time
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

from .vnindex_analyzer import get_vnindex_market_analysis, VNIndexPrediction
from .news_collector import get_market_news_analysis


class DailyMarketReportGenerator:
    """Generate daily market analysis reports for Telegram"""
    
    def __init__(self, serper_api_key: str, gemini_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        self.serper_api_key = serper_api_key
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key
    
    def escape_markdown(self, text: str) -> str:
        """Escape special HTML characters"""
        if not text:
            return ""
        # Escape characters that can break HTML parsing
        return text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
    
    async def generate_market_report(self) -> Dict[str, Any]:
        """Generate comprehensive daily market report"""
        try:
            # Get VN-Index analysis
            vnindex_analysis = await get_vnindex_market_analysis(
                self.serper_api_key, 
                self.gemini_api_key, 
                self.openai_api_key
            )
            
            # Get detailed news analysis
            news_analysis = await get_market_news_analysis(
                self.serper_api_key,
                self.gemini_api_key,
                self.openai_api_key
            )
            
            return {
                "vnindex_analysis": vnindex_analysis,
                "news_analysis": news_analysis,
                "generated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Error generating market report: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def format_telegram_message(self, report_data: Dict[str, Any]) -> str:
        """Format market report for Telegram message"""
        if "error" in report_data:
            return f"❌ **Lỗi tạo báo cáo thị trường:**\n{report_data['error']}"
        
        vnindex_analysis = report_data.get("vnindex_analysis")
        news_analysis = report_data.get("news_analysis", {})
        
        if not vnindex_analysis:
            return "❌ Không thể lấy dữ liệu phân tích VN-Index"
        
        # Header
        current_time = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        message_lines = [
            f"📊 <b>BÁO CÁO THỊ TRƯỜNG SÁNG {current_time.strftime('%d/%m/%Y')}</b>",
            f"⏰ {current_time.strftime('%H:%M')} - Phân tích trước phiên giao dịch",
            ""
        ]
        
        # VN-Index Analysis
        trend_emoji = {
            "BULLISH": "🟢",
            "BULLISH_WEAK": "🟡", 
            "NEUTRAL": "⚪",
            "BEARISH_WEAK": "🟠",
            "BEARISH": "🔴"
        }
        
        trend_text = {
            "BULLISH": "TĂNG MẠNH",
            "BULLISH_WEAK": "TĂNG NHẸ", 
            "NEUTRAL": "TRUNG TÍNH",
            "BEARISH_WEAK": "GIẢM NHẸ",
            "BEARISH": "GIẢM MẠNH"
        }
        
        emoji = trend_emoji.get(vnindex_analysis.trend, "⚪")
        trend_name = trend_text.get(vnindex_analysis.trend, "TRUNG TÍNH")
        confidence_pct = int(vnindex_analysis.confidence * 100)
        
        message_lines.extend([
            f"🎯 <b>DỰ BÁO VN-INDEX:</b> {emoji} {trend_name}",
            f"📈 Độ tin cậy: {confidence_pct}%",
            f"💰 Khoảng giá dự kiến: {vnindex_analysis.target_range[0]:.0f} - {vnindex_analysis.target_range[1]:.0f}",
            f"⚠️ Mức rủi ro: {vnindex_analysis.risk_level}",
            ""
        ])
        
        # Recommendation
        message_lines.extend([
            "💡 <b>KHUYẾN NGHỊ:</b>",
            f"{self.escape_markdown(vnindex_analysis.recommendation)}",
            ""
        ])
        
        # Key Factors
        if vnindex_analysis.key_factors:
            message_lines.extend([
                "🔍 <b>CÁC YẾU TỐ CHÍNH:</b>",
                *[f"• {self.escape_markdown(factor)}" for factor in vnindex_analysis.key_factors[:5]],
                ""
            ])
        
        # News Sentiment
        news_impact = vnindex_analysis.news_impact
        if news_impact:
            domestic_sentiment = news_impact.get("domestic_sentiment", 0.0)
            international_sentiment = news_impact.get("international_sentiment", 0.0)
            overall_sentiment = news_impact.get("overall_sentiment", 0.0)
            
            def sentiment_emoji(score):
                if score > 0.3:
                    return "🟢"
                elif score > 0.1:
                    return "🟡"
                elif score < -0.3:
                    return "🔴"
                elif score < -0.1:
                    return "🟠"
                else:
                    return "⚪"
            
            message_lines.extend([
                "📰 <b>TÁC ĐỘNG TIN TỨC:</b>",
                f"• Trong nước: {sentiment_emoji(domestic_sentiment)} {domestic_sentiment:+.2f}",
                f"• Quốc tế: {sentiment_emoji(international_sentiment)} {international_sentiment:+.2f}",
                f"• Tổng thể: {sentiment_emoji(overall_sentiment)} {overall_sentiment:+.2f}",
                ""
            ])
        
        # Technical Signals
        tech_signals = vnindex_analysis.technical_signals
        if tech_signals:
            message_lines.extend([
                "📊 <b>TÍN HIỆU KỸ THUẬT:</b>",
                f"• Hành động giá: {tech_signals.get('price_action', 'NEUTRAL')}",
                f"• Động lượng: {tech_signals.get('momentum', 'NEUTRAL')}",
                f"• Khối lượng: {tech_signals.get('volume_signal', 'NEUTRAL')}",
                ""
            ])
        
        # News Summary
        news_data = news_analysis.get("news_data", {})
        if news_data:
            domestic_news = news_data.get("domestic", [])
            international_news = news_data.get("international", [])
            
            message_lines.extend([
                "📰 <b>TIN TỨC NỔI BẬT:</b>",
                f"• Tin trong nước: {len(domestic_news)} bài",
                f"• Tin quốc tế: {len(international_news)} bài",
                ""
            ])
            
            # Show top 3 most relevant news
            all_news = domestic_news + international_news
            relevant_news = [news for news in all_news if news.relevance_score and news.relevance_score > 0.5]
            relevant_news.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
            if relevant_news:
                message_lines.append("🔥 <b>TIN QUAN TRỌNG NHẤT:</b>")
                for i, news in enumerate(relevant_news[:3], 1):
                    sentiment_icon = "🟢" if (news.sentiment_score or 0) > 0.1 else "🔴" if (news.sentiment_score or 0) < -0.1 else "⚪"
                    # Escape special characters for HTML
                    safe_title = self.escape_markdown(news.title)
                    message_lines.append(f"{i}. {sentiment_icon} {safe_title[:80]}...")
                message_lines.append("")
        
        # Footer
        message_lines.extend([
            "📝 <b>LƯU Ý:</b>",
            "• Phân tích dựa trên tin tức và dữ liệu kỹ thuật",
            "• Không phải lời khuyên đầu tư, chỉ mang tính tham khảo",
            "• Luôn quản lý rủi ro và đa dạng hóa danh mục",
            "",
            f"🤖 Tự động tạo lúc {current_time.strftime('%H:%M:%S %d/%m/%Y')}"
        ])
        
        return "\n".join(message_lines)
    
    async def generate_and_format_report(self) -> str:
        """Generate market report and format for Telegram"""
        report_data = await self.generate_market_report()
        return self.format_telegram_message(report_data)


# Convenience function for easy integration
async def get_daily_market_report_message(
    serper_api_key: str,
    gemini_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> str:
    """Get formatted daily market report message for Telegram"""
    generator = DailyMarketReportGenerator(serper_api_key, gemini_api_key, openai_api_key)
    return await generator.generate_and_format_report()


if __name__ == "__main__":
    # Test the daily market report
    async def test_daily_report():
        import os
        
        serper_key = os.getenv("SERPER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serper_key:
            print("Please set SERPER_API_KEY environment variable")
            return
        
        message = await get_daily_market_report_message(serper_key, gemini_key, openai_key)
        print(message)
    
    import asyncio
    asyncio.run(test_daily_report())
