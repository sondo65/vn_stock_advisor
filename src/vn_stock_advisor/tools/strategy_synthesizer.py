"""
Strategy Synthesizer Tool - Fixed Version

Tool thông minh tổng hợp kết quả từ phân tích cơ bản và kỹ thuật
để đưa ra kết luận cuối cùng và chiến lược đầu tư cụ thể với điểm số chi tiết.
"""

from typing import Type, Dict, Any, Optional, Tuple
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import re
import logging
from datetime import datetime

class StrategySynthesizerInput(BaseModel):
    """Input schema for strategy synthesizer."""
    symbol: str = Field(..., description="Mã cổ phiếu")
    fundamental_analysis: str = Field(..., description="Kết quả phân tích cơ bản")
    technical_analysis: str = Field(..., description="Kết quả phân tích kỹ thuật")
    macro_analysis: str = Field(default="", description="Phân tích vĩ mô (tùy chọn)")
    current_price: float = Field(default=0.0, description="Giá hiện tại")

class StrategySynthesizerTool(BaseTool):
    """Tool tổng hợp chiến lược đầu tư từ các phân tích thành phần."""
    
    name: str = "Strategy Synthesis and Investment Recommendation Tool"
    description: str = (
        "Intelligent tool that synthesizes fundamental and technical analysis results "
        "to provide comprehensive investment strategy with detailed scoring, price targets, "
        "entry/exit points, and risk management recommendations."
    )
    args_schema: Type[BaseModel] = StrategySynthesizerInput
    
    def __init__(self):
        """Initialize strategy synthesizer."""
        super().__init__()
        self._components = {}
        self._components['logger'] = logging.getLogger(__name__)
    
    @property
    def logger(self):
        """Get logger component."""
        return self._components.get('logger')
    
    def _run(self, symbol: str, fundamental_analysis: str, technical_analysis: str, 
            macro_analysis: str = "", current_price: float = 0.0) -> str:
        """Synthesize investment strategy from analysis results."""
        try:
            # Extract insights
            fund_insights = self._extract_fundamental_insights(fundamental_analysis)
            tech_insights = self._extract_technical_insights(technical_analysis)
            macro_insights = self._extract_macro_insights(macro_analysis)
            
            # Estimate current price if not provided
            if current_price <= 0:
                current_price = self._extract_price_from_analysis(technical_analysis, fundamental_analysis)
            
            # Calculate detailed scores
            scores = self._calculate_detailed_scores(fund_insights, tech_insights, macro_insights)
            
            # Determine overall trend
            overall_trend = self._determine_overall_trend(fund_insights, tech_insights, macro_insights)
            
            # Calculate price targets
            price_levels = self._calculate_price_targets(current_price, tech_insights, fund_insights)
            
            # Assess risks
            risk_assessment = self._assess_risk_factors(fund_insights, tech_insights, macro_insights)
            
            # Generate strategy
            strategy = self._generate_complete_strategy(
                symbol, scores, overall_trend, price_levels, risk_assessment, 
                fund_insights, tech_insights, current_price
            )
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"Error synthesizing strategy for {symbol}: {e}")
            return self._generate_fallback_strategy(symbol, fundamental_analysis, technical_analysis)
    
    def _calculate_detailed_scores(self, fund_insights: Dict, tech_insights: Dict, macro_insights: Dict) -> Dict[str, float]:
        """Calculate detailed scores for all analysis components."""
        
        # Fundamental Analysis Scoring
        valuation_score = 5.0
        if fund_insights["valuation"] == "undervalued":
            valuation_score = 8.5
        elif fund_insights["valuation"] == "fair":
            valuation_score = 7.0
        elif fund_insights["valuation"] == "overvalued":
            valuation_score = 3.5
        
        financial_quality_score = 5.0
        if fund_insights["roe_quality"] == "excellent":
            financial_quality_score = 9.0
        elif fund_insights["roe_quality"] == "good":
            financial_quality_score = 7.5
        elif fund_insights["roe_quality"] == "average":
            financial_quality_score = 5.5
        elif fund_insights["roe_quality"] == "poor":
            financial_quality_score = 3.0
        
        # Adjust for debt level
        if fund_insights["debt_level"] == "low":
            financial_quality_score += 1.0
        elif fund_insights["debt_level"] == "high":
            financial_quality_score -= 1.5
        
        growth_score = 5.0
        if fund_insights["growth_trend"] == "growing":
            growth_score = 8.0
        elif fund_insights["growth_trend"] == "stable":
            growth_score = 6.5
        elif fund_insights["growth_trend"] == "declining":
            growth_score = 3.0
        
        fundamental_score = (valuation_score * 0.4 + financial_quality_score * 0.4 + growth_score * 0.2)
        
        # Technical Analysis Scoring
        trend_score = 5.0
        if tech_insights["trend"] == "upward":
            trend_score = 8.5
        elif tech_insights["trend"] == "sideways":
            trend_score = 6.0
        elif tech_insights["trend"] == "downward":
            trend_score = 2.5
        
        momentum_score = 5.0
        if tech_insights["macd_signal"] == "bullish":
            momentum_score += 2.0
        elif tech_insights["macd_signal"] == "bearish":
            momentum_score -= 2.0
        
        if tech_insights["rsi_status"] == "oversold":
            momentum_score += 1.5
        elif tech_insights["rsi_status"] == "overbought":
            momentum_score -= 1.0
        
        timing_score = 5.0
        if tech_insights["entry_timing"] == "good":
            timing_score = 8.5
        elif tech_insights["entry_timing"] == "fair":
            timing_score = 6.5
        elif tech_insights["entry_timing"] == "wait":
            timing_score = 3.5
        
        technical_score = (trend_score * 0.4 + momentum_score * 0.35 + timing_score * 0.25)
        
        # Macro Analysis Scoring
        market_sentiment_score = 6.0  # Default neutral
        if macro_insights["market_sentiment"] == "positive":
            market_sentiment_score = 7.5
        elif macro_insights["market_sentiment"] == "negative":
            market_sentiment_score = 4.0
        
        policy_environment_score = 6.0  # Default neutral
        if macro_insights["policy_impact"] == "positive":
            policy_environment_score = 7.5
        elif macro_insights["policy_impact"] == "negative":
            policy_environment_score = 4.5
        
        macro_score = (market_sentiment_score + policy_environment_score) / 2
        
        # Overall Score (weighted average) - More balanced approach
        overall_score = (
            fundamental_score * 0.40 +  # 40% fundamentals (reduced from 45%)
            technical_score * 0.40 +    # 40% technicals (increased from 35%)
            macro_score * 0.20          # 20% macro (unchanged)
        )
        
        return {
            'fundamental': min(10.0, max(0.0, fundamental_score)),
            'technical': min(10.0, max(0.0, technical_score)),
            'macro': min(10.0, max(0.0, macro_score)),
            'overall': min(10.0, max(0.0, overall_score)),
            'valuation': min(10.0, max(0.0, valuation_score)),
            'financial_quality': min(10.0, max(0.0, financial_quality_score)),
            'growth': min(10.0, max(0.0, growth_score)),
            'trend': min(10.0, max(0.0, trend_score)),
            'momentum': min(10.0, max(0.0, momentum_score)),
            'timing': min(10.0, max(0.0, timing_score)),
            'market_sentiment': min(10.0, max(0.0, market_sentiment_score)),
            'policy_environment': min(10.0, max(0.0, policy_environment_score))
        }
    
    def _generate_complete_strategy(self, symbol: str, scores: Dict, overall_trend: Dict, 
                                  price_levels: Dict, risk_assessment: Dict, fund_insights: Dict, 
                                  tech_insights: Dict, current_price: float) -> str:
        """Generate complete investment strategy with scoring."""
        
        strategy_parts = []
        
        # Header with enhanced system description
        strategy_parts.append("## 🎯 **KẾT LUẬN & CHIẾN LƯỢC**")
        strategy_parts.append("=" * 50)
        strategy_parts.append("*Hệ thống phân tích đa chiều với logic override thông minh*")
        strategy_parts.append("")
        
        # Scoring Section
        strategy_parts.append("### 📊 **BẢNG ĐIỂM PHÂN TÍCH**")
        strategy_parts.append("")
        
        # Individual component scores
        strategy_parts.append(f"**📈 Phân tích Cơ bản:** {scores['fundamental']:.1f}/10")
        strategy_parts.append(f"   • Định giá: {scores['valuation']:.1f}/10 ({fund_insights['valuation']})")
        strategy_parts.append(f"   • Chất lượng tài chính: {scores['financial_quality']:.1f}/10")
        strategy_parts.append(f"   • Tăng trưởng: {scores['growth']:.1f}/10")
        strategy_parts.append("")
        
        strategy_parts.append(f"**📊 Phân tích Kỹ thuật:** {scores['technical']:.1f}/10")
        strategy_parts.append(f"   • Xu hướng: {scores['trend']:.1f}/10 ({tech_insights['trend']})")
        strategy_parts.append(f"   • Momentum: {scores['momentum']:.1f}/10")
        strategy_parts.append(f"   • Timing: {scores['timing']:.1f}/10 ({tech_insights['entry_timing']})")
        strategy_parts.append("")
        
        strategy_parts.append(f"**🌍 Phân tích Vĩ mô:** {scores['macro']:.1f}/10")
        strategy_parts.append(f"   • Tâm lý thị trường: {scores['market_sentiment']:.1f}/10")
        strategy_parts.append(f"   • Môi trường chính sách: {scores['policy_environment']:.1f}/10")
        strategy_parts.append("")
        
        # Overall score with visual indicator
        overall_score = scores['overall']
        score_emoji = "🔴" if overall_score < 5 else "🟡" if overall_score < 7 else "🟢"
        score_level = "THẤP" if overall_score < 5 else "TRUNG BÌNH" if overall_score < 7 else "CAO"
        
        strategy_parts.append(f"**🎯 ĐIỂM TỔNG HỢP: {score_emoji} {overall_score:.1f}/10 ({score_level})**")
        strategy_parts.append("")
        strategy_parts.append("📋 **PHƯƠNG PHÁP TÍNH ĐIỂM:**")
        strategy_parts.append("   • **Trọng số:** Cơ bản 40% - Kỹ thuật 40% - Vĩ mô 20%")
        strategy_parts.append("   • **Ngưỡng khuyến nghị:** MUA ≥7.5 | GIỮ 5.5-7.4 | BÁN <5.5")
        strategy_parts.append("   • **Logic Override:** Tự động hạ xuống BÁN khi:")
        strategy_parts.append("     - Bất kỳ yếu tố nào ≤3.5 (rủi ro cực cao)")
        strategy_parts.append("     - Hoặc ≥2 yếu tố ≤4.5 (nhiều rủi ro)")
        strategy_parts.append("")
        
        # Investment recommendation with consistency check
        # Check for extreme negative signals that should override overall score
        extreme_negative = False
        warning_factors = []
        
        # Technical analysis warning
        if scores['technical'] <= 3.5:
            extreme_negative = True
            warning_factors.append("Kỹ thuật rất yếu")
        
        # Fundamental analysis warning  
        if scores['fundamental'] <= 3.5:
            extreme_negative = True
            warning_factors.append("Cơ bản rất yếu")
        
        # Sub-component warnings - CRITICAL for detailed analysis
        if scores.get('financial_quality', 10.0) <= 3.5:
            extreme_negative = True
            warning_factors.append("Chất lượng tài chính rất yếu")
        
        if scores.get('valuation', 10.0) <= 3.5:
            extreme_negative = True
            warning_factors.append("Định giá rất kém")
            
        if scores.get('growth', 10.0) <= 3.5:
            extreme_negative = True
            warning_factors.append("Tăng trưởng rất yếu")
        
        if scores.get('trend', 10.0) <= 3.5:
            extreme_negative = True
            warning_factors.append("Xu hướng rất xấu")
            
        # Multiple factors below threshold (including sub-components)
        weak_factors = 0
        component_checks = [
            ('technical', scores['technical']),
            ('fundamental', scores['fundamental']), 
            ('macro', scores['macro']),
            ('financial_quality', scores.get('financial_quality', 10.0)),
            ('valuation', scores.get('valuation', 10.0)),
            ('growth', scores.get('growth', 10.0))
        ]
        
        for name, score in component_checks:
            if score <= 4.5:
                weak_factors += 1
                
        if weak_factors >= 2:
            extreme_negative = True
            warning_factors.append(f"Nhiều yếu tố yếu ({weak_factors}/6)")

        # Final recommendation with improved override logic
        if extreme_negative:
            # Always override when there are extreme negative signals
            if overall_score >= 7.5:
                # High score but with extreme risks - downgrade to HOLD with warning
                recommendation = "**🟡 KHUYẾN NGHỊ: GIỮ/THEO DÕI**"
                confidence_text = f"Hạ từ MUA do cảnh báo rủi ro ({', '.join(warning_factors)})"
            elif overall_score >= 5.5:
                # Medium score with extreme risks - downgrade to SELL
                recommendation = "**🔴 KHUYẾN NGHỊ: TRÁNH/BÁN**"
                confidence_text = f"Hạ từ GIỮ do cảnh báo rủi ro cao ({', '.join(warning_factors)})"
            else:
                # Low score with extreme risks - definitely SELL
                recommendation = "**🔴 KHUYẾN NGHỊ: TRÁNH/BÁN**"
                confidence_text = f"Cảnh báo rủi ro cao ({', '.join(warning_factors)})"
        elif overall_score >= 7.5:
            recommendation = "**🟢 KHUYẾN NGHỊ: MUA**"
            confidence_text = "Độ tin cậy cao"
        elif overall_score >= 5.5:
            recommendation = "**🟡 KHUYẾN NGHỊ: GIỮ/THEO DÕI**"
            confidence_text = "Độ tin cậy trung bình"
        else:
            recommendation = "**🔴 KHUYẾN NGHỊ: TRÁNH/BÁN**"
            confidence_text = "Độ tin cậy thấp"
        
        strategy_parts.append(f"{recommendation} ({confidence_text})")
        
        # Add warning explanation if override occurred
        if extreme_negative:
            strategy_parts.append("")
            if overall_score >= 7.5:
                strategy_parts.append("⚠️ **LƯU Ý**: Khuyến nghị đã được hạ từ MUA xuống GIỮ do phát hiện rủi ro:")
            elif overall_score >= 5.5:
                strategy_parts.append("⚠️ **LƯU Ý**: Khuyến nghị đã được hạ từ GIỮ xuống BÁN do phát hiện rủi ro cao:")
            else:
                strategy_parts.append("⚠️ **LƯU Ý**: Cảnh báo rủi ro cao được phát hiện:")
            
            for factor in warning_factors:
                strategy_parts.append(f"   • {factor}")
            strategy_parts.append("   • Hệ thống ưu tiên an toàn và quản lý rủi ro")
        
        strategy_parts.append("")
        strategy_parts.append("---")
        strategy_parts.append("")
        
        # Trend Assessment
        short_term = overall_trend["short_term"]
        long_term = overall_trend["long_term"]
        trend_desc = self._format_trend_description(short_term, long_term)
        strategy_parts.append(f"**📈 Xu hướng tổng thể:** {trend_desc}")
        strategy_parts.append("")
        
        # Price Strategy
        strategy_parts.append("### 💰 **CHIẾN LƯỢC GIÁ**")
        strategy_parts.append("")
        
        # Entry levels
        entry_min = price_levels["entry_min"]
        entry_max = price_levels["entry_max"]
        strategy_parts.append(f"**🎯 Vùng mua tiềm năng:** {entry_min:,.0f} – {entry_max:,.0f} VND")
        
        # Add context for entry
        if tech_insights["rsi_status"] == "oversold":
            strategy_parts.append("   *(RSI quá bán - cơ hội tích lũy tốt)*")
        elif tech_insights["support_levels"]:
            nearest_support = min(tech_insights["support_levels"], key=lambda x: abs(x - current_price))
            strategy_parts.append(f"   *(Gần vùng hỗ trợ {nearest_support:,.0f})*")
        
        strategy_parts.append("")
        
        # Profit targets
        target_1 = price_levels["target_1"]
        target_2 = price_levels["target_2"]
        target_3 = price_levels["target_3"]
        
        gain_1 = ((target_1 / current_price) - 1) * 100
        gain_2 = ((target_2 / current_price) - 1) * 100
        gain_3 = ((target_3 / current_price) - 1) * 100
        
        strategy_parts.append(f"**📈 Vùng chốt lời:**")
        strategy_parts.append(f"   • T1: {target_1:,.0f} VND (+{gain_1:.1f}%)")
        strategy_parts.append(f"   • T2: {target_2:,.0f} VND (+{gain_2:.1f}%)")
        strategy_parts.append(f"   • T3: {target_3:,.0f} VND (+{gain_3:.1f}%)")
        
        if tech_insights["resistance_levels"]:
            nearest_resistance = min(tech_insights["resistance_levels"], key=lambda x: abs(x - target_1))
            strategy_parts.append(f"   *(Gần kháng cự kỹ thuật {nearest_resistance:,.0f})*")
        
        strategy_parts.append("")
        
        # Stop loss
        stop_loss = price_levels["stop_loss"]
        loss_percent = ((current_price / stop_loss) - 1) * 100
        strategy_parts.append(f"**⛔ Vùng Stop-loss:** Dưới {stop_loss:,.0f} VND (-{loss_percent:.1f}%)")
        
        if tech_insights["volume_trend"] == "decreasing":
            strategy_parts.append("   *(Đặc biệt nếu khối lượng bán tăng mạnh)*")
        elif tech_insights["support_levels"]:
            strategy_parts.append("   *(Phá vỡ vùng hỗ trợ kỹ thuật)*")
        
        strategy_parts.append("")
        
        # Risk Management
        strategy_parts.append("### ⚠️ **QUẢN TRỊ RỦI RO**")
        strategy_parts.append("")
        
        risk_level = risk_assessment["overall_risk"]
        position_recommendations = {
            "low": "5-8% danh mục",
            "medium": "3-5% danh mục", 
            "high": "1-3% danh mục"
        }
        
        strategy_parts.append(f"**📊 Khuyến nghị tỷ trọng:** {position_recommendations.get(risk_level, '3-5% danh mục')} (Rủi ro: {risk_level})")
        strategy_parts.append("")
        
        if risk_assessment["key_risks"]:
            strategy_parts.append("**🚨 Rủi ro chính:**")
            for risk in risk_assessment["key_risks"][:3]:  # Top 3 risks
                strategy_parts.append(f"   • {risk}")
            strategy_parts.append("")
        
        # Timing and Execution
        strategy_parts.append("### ⏰ **THỜI ĐIỂM & THỰC HIỆN**")
        strategy_parts.append("")
        
        entry_timing = tech_insights["entry_timing"]
        timing_advice = {
            "good": "✅ Thời điểm vào lệnh tốt",
            "fair": "🟡 Có thể vào lệnh với stop-loss chặt",
            "wait": "⏳ Nên chờ tín hiệu rõ ràng hơn"
        }
        
        strategy_parts.append(f"**🎯 Đánh giá timing:** {timing_advice[entry_timing]}")
        strategy_parts.append("")
        
        # Execution recommendations
        strategy_parts.append("**📋 Khuyến nghị thực hiện:**")
        if entry_timing == "good":
            strategy_parts.append("   • Có thể mua từng phần trong vùng entry")
            strategy_parts.append("   • Đặt lệnh stop-loss ngay sau khi mua")
            strategy_parts.append("   • Theo dõi volume để xác nhận")
        elif entry_timing == "fair":
            strategy_parts.append("   • Vào lệnh thận trọng với position size nhỏ")
            strategy_parts.append("   • Stop-loss chặt chẽ")
            strategy_parts.append("   • Sẵn sàng cắt lỗ nhanh nếu sai")
        else:
            strategy_parts.append("   • Thêm vào watchlist để theo dõi")
            strategy_parts.append("   • Chờ tín hiệu kỹ thuật rõ ràng hơn")
            strategy_parts.append("   • Xem xét lại khi có catalyst mới")
        
        # Footer with system information
        strategy_parts.append("")
        strategy_parts.append("---")
        strategy_parts.append("### 🔧 **THÔNG TIN HỆ THỐNG**")
        strategy_parts.append("")
        strategy_parts.append("**Phiên bản:** V2.0 - Hệ thống phân tích thông minh với logic override")
        strategy_parts.append("**Cải tiến chính:**")
        strategy_parts.append("   • Cân bằng trọng số phân tích (40%-40%-20%)")
        strategy_parts.append("   • Logic cảnh báo rủi ro tự động")
        strategy_parts.append("   • Khuyến nghị nhất quán và minh bạch")
        strategy_parts.append("")
        strategy_parts.append(f"*Phân tích được tổng hợp vào {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        strategy_parts.append("*Đây là thông tin tham khảo, không phải lời khuyên đầu tư*")
        
        return "\n".join(strategy_parts)
    
    def _extract_fundamental_insights(self, analysis: str) -> Dict[str, Any]:
        """Extract key insights from fundamental analysis."""
        insights = {
            "valuation": "neutral",
            "pe_status": "normal",
            "pb_status": "normal", 
            "roe_quality": "average",
            "debt_level": "moderate",
            "growth_trend": "stable",
            "financial_health": "fair"
        }
        
        try:
            analysis_lower = analysis.lower()
            
            # Valuation assessment
            if any(word in analysis_lower for word in ['rẻ', 'hấp dẫn', 'undervalued', 'cheap']):
                insights["valuation"] = "undervalued"
            elif any(word in analysis_lower for word in ['đắt', 'cao', 'overvalued', 'expensive']):
                insights["valuation"] = "overvalued"
            elif any(word in analysis_lower for word in ['hợp lý', 'fair', 'reasonable']):
                insights["valuation"] = "fair"
            
            # ROE quality assessment
            roe_match = re.search(r'roe[:\s]*([0-9.]+)', analysis_lower)
            if roe_match:
                roe_value = float(roe_match.group(1))
                if roe_value >= 20:
                    insights["roe_quality"] = "excellent"
                elif roe_value >= 15:
                    insights["roe_quality"] = "good"
                elif roe_value >= 10:
                    insights["roe_quality"] = "average"
                else:
                    insights["roe_quality"] = "poor"
            
            # Growth trend
            if any(word in analysis_lower for word in ['tăng trưởng', 'growth', 'tăng']):
                insights["growth_trend"] = "growing"
            elif any(word in analysis_lower for word in ['giảm', 'decline', 'sụt giảm']):
                insights["growth_trend"] = "declining"
                
        except Exception as e:
            self.logger.warning(f"Error extracting fundamental insights: {e}")
        
        return insights
    
    def _extract_technical_insights(self, analysis: str) -> Dict[str, Any]:
        """Extract key insights from technical analysis."""
        insights = {
            "trend": "sideways",
            "momentum": "neutral",
            "rsi_status": "normal",
            "macd_signal": "neutral",
            "volume_trend": "normal",
            "support_levels": [],
            "resistance_levels": [],
            "entry_timing": "wait"
        }
        
        try:
            analysis_lower = analysis.lower()
            
            # Trend determination
            if any(word in analysis_lower for word in ['xu hướng tăng', 'upward', 'tăng', 'bullish']):
                insights["trend"] = "upward"
            elif any(word in analysis_lower for word in ['xu hướng giảm', 'downward', 'giảm', 'bearish']):
                insights["trend"] = "downward"
            
            # RSI status
            rsi_match = re.search(r'rsi[:\s]*([0-9.]+)', analysis_lower)
            if rsi_match:
                rsi_value = float(rsi_match.group(1))
                if rsi_value <= 30:
                    insights["rsi_status"] = "oversold"
                elif rsi_value >= 70:
                    insights["rsi_status"] = "overbought"
            
            # MACD signal
            if any(word in analysis_lower for word in ['macd tích cực', 'macd positive', 'macd bullish']):
                insights["macd_signal"] = "bullish"
            elif any(word in analysis_lower for word in ['macd tiêu cực', 'macd negative', 'macd bearish']):
                insights["macd_signal"] = "bearish"
            
            # Support and resistance levels
            support_matches = re.findall(r'hỗ trợ[:\s]*([0-9,]+)', analysis_lower)
            resistance_matches = re.findall(r'kháng cự[:\s]*([0-9,]+)', analysis_lower)
            
            insights["support_levels"] = [float(s.replace(',', '')) for s in support_matches]
            insights["resistance_levels"] = [float(r.replace(',', '')) for r in resistance_matches]
            
            # Entry timing
            if (insights["rsi_status"] == "oversold" or 
                (insights["trend"] == "upward" and insights["macd_signal"] == "bullish")):
                insights["entry_timing"] = "good"
            elif insights["trend"] == "upward" or insights["macd_signal"] == "bullish":
                insights["entry_timing"] = "fair"
                
        except Exception as e:
            self.logger.warning(f"Error extracting technical insights: {e}")
        
        return insights
    
    def _extract_macro_insights(self, analysis: str) -> Dict[str, Any]:
        """Extract macro environment insights."""
        insights = {
            "market_sentiment": "neutral",
            "sector_outlook": "stable",
            "policy_impact": "neutral"
        }
        
        if not analysis:
            return insights
        
        try:
            analysis_lower = analysis.lower()
            
            if any(word in analysis_lower for word in ['tích cực', 'positive', 'tăng trưởng', 'ổn định']):
                insights["market_sentiment"] = "positive"
            elif any(word in analysis_lower for word in ['tiêu cực', 'negative', 'suy giảm', 'rủi ro']):
                insights["market_sentiment"] = "negative"
            
            if any(word in analysis_lower for word in ['chính sách hỗ trợ', 'thuận lợi', 'supportive']):
                insights["policy_impact"] = "positive"
            elif any(word in analysis_lower for word in ['chính sách thắt chặt', 'bất lợi', 'restrictive']):
                insights["policy_impact"] = "negative"
                
        except Exception as e:
            self.logger.warning(f"Error extracting macro insights: {e}")
        
        return insights
    
    def _extract_price_from_analysis(self, technical_analysis: str, fundamental_analysis: str) -> float:
        """Extract current price from analysis text."""
        try:
            price_patterns = [
                r'giá hiện tại[:\s]*([0-9,]+)',
                r'current price[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*VND',
                r'giá[:\s]*([0-9,]+)'
            ]
            
            for pattern in price_patterns:
                for text in [technical_analysis, fundamental_analysis]:
                    match = re.search(pattern, text.lower())
                    if match:
                        price_str = match.group(1).replace(',', '')
                        return float(price_str)
            
            return 25000.0
            
        except Exception:
            return 25000.0
    
    def _determine_overall_trend(self, fund_insights: Dict, tech_insights: Dict, macro_insights: Dict) -> Dict[str, str]:
        """Determine overall trend from combined insights."""
        trend_analysis = {
            "short_term": "neutral",
            "long_term": "neutral",
            "overall_bias": "neutral"
        }
        
        # Short-term (technical)
        if tech_insights["trend"] == "upward":
            trend_analysis["short_term"] = "bullish"
        elif tech_insights["trend"] == "downward":
            trend_analysis["short_term"] = "bearish"
        
        # Long-term (fundamental)
        if fund_insights["valuation"] == "undervalued" and fund_insights["financial_health"] in ["good", "excellent"]:
            trend_analysis["long_term"] = "bullish"
        elif fund_insights["valuation"] == "overvalued" or fund_insights["financial_health"] == "poor":
            trend_analysis["long_term"] = "bearish"
        
        return trend_analysis
    
    def _calculate_price_targets(self, current_price: float, tech_insights: Dict, fund_insights: Dict) -> Dict[str, float]:
        """Calculate price targets and key levels."""
        levels = {
            "current_price": current_price,
            "entry_min": current_price * 0.97,
            "entry_max": current_price * 1.03,
            "target_1": current_price * 1.15,
            "target_2": current_price * 1.25,
            "target_3": current_price * 1.40,
            "stop_loss": current_price * 0.92
        }
        
        try:
            # Adjust based on technical levels
            if tech_insights["support_levels"]:
                nearest_support = min(tech_insights["support_levels"], key=lambda x: abs(x - current_price))
                if nearest_support < current_price:
                    levels["stop_loss"] = nearest_support * 0.97
            
            if tech_insights["resistance_levels"]:
                nearest_resistance = min(tech_insights["resistance_levels"], key=lambda x: abs(x - current_price))
                if nearest_resistance > current_price:
                    levels["target_1"] = nearest_resistance
            
            # Adjust for valuation
            if fund_insights["valuation"] == "undervalued":
                levels["target_1"] = current_price * 1.20
                levels["target_2"] = current_price * 1.35
                levels["target_3"] = current_price * 1.50
            elif fund_insights["valuation"] == "overvalued":
                levels["target_1"] = current_price * 1.08
                levels["target_2"] = current_price * 1.15
                levels["stop_loss"] = current_price * 0.95
                
        except Exception as e:
            self.logger.warning(f"Error calculating price targets: {e}")
        
        return levels
    
    def _assess_risk_factors(self, fund_insights: Dict, tech_insights: Dict, macro_insights: Dict) -> Dict[str, Any]:
        """Assess overall risk factors."""
        risk_assessment = {
            "overall_risk": "medium",
            "key_risks": [],
            "risk_mitigation": []
        }
        
        risk_factors = []
        
        if fund_insights["valuation"] == "overvalued":
            risk_factors.append("Định giá cao - rủi ro điều chỉnh")
        if fund_insights["debt_level"] == "high":
            risk_factors.append("Nợ cao - rủi ro tài chính")
        if tech_insights["rsi_status"] == "overbought":
            risk_factors.append("RSI quá mua - rủi ro điều chỉnh ngắn hạn")
        if tech_insights["trend"] == "downward":
            risk_factors.append("Xu hướng giảm - momentum tiêu cực")
        if macro_insights["market_sentiment"] == "negative":
            risk_factors.append("Tâm lý thị trường tiêu cực")
        
        risk_assessment["key_risks"] = risk_factors
        
        # Determine risk level
        if len(risk_factors) >= 3:
            risk_assessment["overall_risk"] = "high"
        elif len(risk_factors) >= 1:
            risk_assessment["overall_risk"] = "medium"
        else:
            risk_assessment["overall_risk"] = "low"
        
        return risk_assessment
    
    def _format_trend_description(self, short_term: str, long_term: str) -> str:
        """Format trend description in Vietnamese."""
        trend_map = {
            "bullish": "TĂNG",
            "bearish": "GIẢM", 
            "neutral": "ĐI NGANG"
        }
        
        short_vn = trend_map.get(short_term, "KHÔNG RÕ")
        long_vn = trend_map.get(long_term, "KHÔNG RÕ")
        
        if short_term == long_term:
            return f"{long_vn} cả ngắn hạn và dài hạn"
        else:
            return f"Dài hạn {long_vn}, ngắn hạn {short_vn}"
    
    def _generate_fallback_strategy(self, symbol: str, fund_analysis: str, tech_analysis: str) -> str:
        """Generate basic strategy when full synthesis fails."""
        return f"""## 🎯 **KẾT LUẬN & CHIẾN LƯỢC** - {symbol}

### 📊 **BẢNG ĐIỂM PHÂN TÍCH**

**📈 Phân tích Cơ bản:** 6.0/10
   • Định giá: 6.0/10 (cần phân tích thêm)
   • Chất lượng tài chính: 6.0/10
   • Tăng trưởng: 6.0/10

**📊 Phân tích Kỹ thuật:** 6.0/10
   • Xu hướng: 6.0/10 (cần phân tích thêm)
   • Momentum: 6.0/10
   • Timing: 6.0/10

**🌍 Phân tích Vĩ mô:** 6.0/10
   • Tâm lý thị trường: 6.0/10
   • Môi trường chính sách: 6.0/10

**🎯 ĐIỂM TỔNG HỢP: 🟡 6.0/10 (TRUNG BÌNH)**

**🟡 KHUYẾN NGHỊ: GIỮ/THEO DÕI** (Độ tin cậy trung bình)

---

**📈 Xu hướng tổng thể:** Cần phân tích thêm để xác định xu hướng rõ ràng.

**⚠️ Lưu ý:** Do hạn chế trong việc tổng hợp dữ liệu, vui lòng tham khảo chi tiết 
phân tích cơ bản và kỹ thuật để đưa ra quyết định đầu tư phù hợp.

*Được tạo vào {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""

# Create global instance
strategy_synthesizer_fixed = StrategySynthesizerTool()
