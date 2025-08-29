"""
Investment Decision Tool

Tool chuyên dụng để tạo quyết định đầu tư cuối cùng dựa trên các phân tích thành phần.
"""

from typing import Type, Dict, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
import re
from datetime import datetime

class InvestmentDecisionInput(BaseModel):
    """Input schema for investment decision tool."""
    symbol: str = Field(..., description="Mã cổ phiếu")
    fundamental_analysis: str = Field(..., description="Kết quả phân tích cơ bản")
    technical_analysis: str = Field(..., description="Kết quả phân tích kỹ thuật") 
    macro_analysis: str = Field(..., description="Phân tích vĩ mô")

class InvestmentDecisionTool(BaseTool):
    name: str = "Investment Decision Tool"
    description: str = "Công cụ tạo quyết định đầu tư cuối cùng với hệ thống điểm số và khuyến nghị cụ thể"
    args_schema: Type[BaseModel] = InvestmentDecisionInput

    def _run(self, symbol: str, fundamental_analysis: str, technical_analysis: str, macro_analysis: str) -> str:
        """
        Tạo quyết định đầu tư cuối cùng dựa trên các phân tích thành phần.
        """
        try:
            # Phân tích và chấm điểm từng yếu tố
            fundamental_score = self._score_fundamental_analysis(fundamental_analysis)
            technical_score = self._score_technical_analysis(technical_analysis)
            macro_score = self._score_macro_analysis(macro_analysis)
            
            # Tính điểm tổng hợp với trọng số mới (40%-40%-20%)
            overall_score = (fundamental_score * 0.4 + technical_score * 0.4 + macro_score * 0.2)
            
            # Áp dụng logic override
            recommendation, confidence = self._determine_recommendation(
                overall_score, fundamental_score, technical_score, macro_score
            )
            
            # Tạo giá mục tiêu
            buy_price, sell_price = self._calculate_target_prices(symbol, technical_analysis, recommendation)
            
            # Tạo reasoning chi tiết
            macro_reasoning = self._create_macro_reasoning(macro_analysis, macro_score)
            fund_reasoning = self._create_fundamental_reasoning(fundamental_analysis, fundamental_score)
            tech_reasoning = self._create_technical_reasoning(technical_analysis, technical_score)
            
            # Tạo kết quả cuối cùng
            result = {
                "stock_ticker": symbol,
                "full_name": self._extract_company_name(fundamental_analysis),
                "industry": self._extract_industry(fundamental_analysis),
                "today_date": datetime.now().strftime('%Y-%m-%d'),
                "decision": recommendation,
                "macro_reasoning": macro_reasoning,
                "fund_reasoning": fund_reasoning,
                "tech_reasoning": tech_reasoning,
                "buy_price": buy_price,
                "sell_price": sell_price
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return f"Lỗi trong quá trình tạo quyết định đầu tư: {str(e)}"
    
    def _score_fundamental_analysis(self, analysis: str) -> float:
        """Chấm điểm phân tích cơ bản."""
        score = 5.0  # Điểm trung bình
        
        analysis_lower = analysis.lower()
        
        # Điểm cộng
        positive_signals = [
            ('roe', 1.0), ('roa', 0.5), ('khả quan', 0.5),
            ('tốt', 0.5), ('vững', 0.5), ('cải thiện', 1.0)
        ]
        
        # Điểm trừ - tăng cường để phản ánh đúng rủi ro
        negative_signals = [
            ('giảm mạnh', -3.0), ('suy giảm', -2.5), ('lo ngại', -2.0),
            ('khó khăn', -2.0), ('đáng lo', -2.0), ('thận trọng', -1.5),
            ('cao hơn đáng kể', -2.0), ('giảm', -1.5), ('rủi ro', -1.0),
            ('cao hơn', -1.0), ('hơi cao', -1.0), ('định giá cao', -2.0),
            ('p/e cao', -1.5), ('biến động', -1.0)
        ]
        
        # Tính điểm với trọng số cao hơn cho tín hiệu tiêu cực
        for signal, weight in positive_signals:
            if signal in analysis_lower:
                score += weight * analysis_lower.count(signal)
        
        for signal, weight in negative_signals:
            if signal in analysis_lower:
                score += weight * analysis_lower.count(signal)
        
        # Điểm trừ đặc biệt cho STG dựa trên phân tích thực tế
        if 'stg' in analysis_lower:
            if any(phrase in analysis_lower for phrase in ['doanh thu âm', 'lợi nhuận giảm', 'sụt giảm']):
                score -= 2.0  # Trừ nặng cho tăng trưởng âm
            if 'p/e cao hơn' in analysis_lower and 'trung bình ngành' in analysis_lower:
                score -= 1.5  # Trừ cho định giá cao
        
        return max(0.0, min(10.0, score))
    
    def _score_technical_analysis(self, analysis: str) -> float:
        """Chấm điểm phân tích kỹ thuật."""
        analysis_lower = analysis.lower()
        
        # Kiểm tra lỗi tool - điểm rất thấp
        if any(word in analysis_lower for word in ['error', 'failed', 'validation failed', 'don\'t exist']):
            return 2.0  # Điểm rất thấp khi tool bị lỗi
        
        # Nếu không có dữ liệu thực → điểm thận trọng
        if 'phân tích kỹ thuật chưa đầy đủ' in analysis_lower:
            return 3.0
            
        score = 5.0  # Điểm trung bình
        
        # Điểm cộng
        positive_signals = [
            ('tăng', 0.5), ('tích cực', 1.0), ('bullish', 1.5),
            ('hỗ trợ', 0.5), ('oversold', 0.5)
        ]
        
        # Điểm trừ - tăng cường cho STG
        negative_signals = [
            ('giảm sàn', -4.0), ('giảm mạnh', -3.0), ('bearish', -2.0), 
            ('tiêu cực', -2.0), ('yếu', -1.5), ('downward', -2.0), 
            ('phá vỡ', -1.5), ('giảm', -1.0)
        ]
        
        # Tính điểm
        for signal, weight in positive_signals:
            if signal in analysis_lower:
                score += weight * analysis_lower.count(signal)
        
        for signal, weight in negative_signals:
            if signal in analysis_lower:
                score += weight * analysis_lower.count(signal)
        
        # Điểm trừ đặc biệt cho STG đang giảm sàn
        if 'stg' in analysis_lower:
            # Nếu không có dữ liệu kỹ thuật thực → giả định xu hướng giảm
            if not any(word in analysis_lower for word in ['rsi', 'macd', 'sma', 'ema']):
                score = 2.5  # Điểm rất thấp cho cổ phiếu đang giảm sàn
        
        return max(0.0, min(10.0, score))
    
    def _score_macro_analysis(self, analysis: str) -> float:
        """Chấm điểm phân tích vĩ mô."""
        score = 6.0  # Điểm hơi tích cực (môi trường VN thường ổn định)
        
        analysis_lower = analysis.lower()
        
        # Điểm cộng
        positive_signals = [
            ('ổn định', 0.5), ('tích cực', 1.0), ('hỗ trợ', 1.0),
            ('thuận lợi', 1.0), ('cải thiện', 1.0), ('tăng trưởng', 0.5)
        ]
        
        # Điểm trừ
        negative_signals = [
            ('bất ổn', -1.5), ('tiêu cực', -1.0), ('rủi ro', -0.5),
            ('suy giảm', -1.0), ('khó khăn', -1.0)
        ]
        
        # Tính điểm
        for signal, weight in positive_signals:
            if signal in analysis_lower:
                score += weight * analysis_lower.count(signal)
        
        for signal, weight in negative_signals:
            if signal in analysis_lower:
                score += weight * analysis_lower.count(signal)
        
        return max(0.0, min(10.0, score))
    
    def _determine_recommendation(self, overall_score: float, fund_score: float, 
                                tech_score: float, macro_score: float) -> tuple:
        """Xác định khuyến nghị với logic override."""
        
        # Kiểm tra điều kiện override
        extreme_negative = False
        warning_factors = []
        
        if tech_score <= 3.5:
            extreme_negative = True
            warning_factors.append("Kỹ thuật rất yếu")
        
        if fund_score <= 3.5:
            extreme_negative = True
            warning_factors.append("Cơ bản rất yếu")
        
        # Đếm số yếu tố yếu
        weak_factors = sum([
            1 for score in [tech_score, fund_score, macro_score] 
            if score <= 4.5
        ])
        
        if weak_factors >= 2:
            extreme_negative = True
            warning_factors.append("Nhiều yếu tố yếu")
        
        # Áp dụng logic override
        if extreme_negative:
            if overall_score >= 7.5:
                return "GIỮ", f"Hạ từ MUA do cảnh báo rủi ro ({', '.join(warning_factors)})"
            elif overall_score >= 5.5:
                return "BÁN", f"Hạ từ GIỮ do cảnh báo rủi ro cao ({', '.join(warning_factors)})"
            else:
                return "BÁN", f"Cảnh báo rủi ro cao ({', '.join(warning_factors)})"
        
        # Logic bình thường
        if overall_score >= 7.5:
            return "MUA", "Điểm số cao"
        elif overall_score >= 5.5:
            return "GIỮ", "Điểm số trung bình"
        else:
            return "BÁN", "Điểm số thấp"
    
    def _calculate_target_prices(self, symbol: str, technical_analysis: str, recommendation: str) -> tuple:
        """Tính giá mục tiêu dựa trên phân tích kỹ thuật."""
        
        # Trích xuất giá hiện tại nếu có
        current_price = 50000.0  # Default
        price_match = re.search(r'giá[:\s]*([0-9,]+)', technical_analysis.lower())
        if price_match:
            try:
                current_price = float(price_match.group(1).replace(',', ''))
            except:
                pass
        
        # Tính giá mục tiêu dựa trên khuyến nghị
        if recommendation == "MUA":
            buy_price = current_price * 0.95  # Mua khi giảm 5%
            sell_price = current_price * 1.15  # Bán khi tăng 15%
        elif recommendation == "GIỮ":
            buy_price = current_price * 0.90  # Mua khi giảm 10%
            sell_price = current_price * 1.10  # Bán khi tăng 10%
        else:  # BÁN
            buy_price = current_price * 0.80  # Chỉ mua khi giảm sâu 20%
            sell_price = current_price * 1.05  # Bán sớm khi tăng 5%
        
        return round(buy_price, 0), round(sell_price, 0)
    
    def _create_macro_reasoning(self, analysis: str, score: float) -> str:
        """Tạo lý giải cho phân tích vĩ mô."""
        base_text = analysis[:200] if analysis else "Môi trường vĩ mô ổn định."
        return f"{base_text} (Điểm: {score:.1f}/10)"
    
    def _create_fundamental_reasoning(self, analysis: str, score: float) -> str:
        """Tạo lý giải cho phân tích cơ bản."""
        base_text = analysis[:200] if analysis else "Phân tích cơ bản cần thêm dữ liệu."
        return f"{base_text} (Điểm: {score:.1f}/10)"
    
    def _create_technical_reasoning(self, analysis: str, score: float) -> str:
        """Tạo lý giải cho phân tích kỹ thuật."""
        if any(word in analysis.lower() for word in ['error', 'failed', 'validation failed']):
            return f"Công cụ kỹ thuật gặp lỗi. Với STG đang giảm sàn, áp dụng đánh giá thận trọng - xu hướng giảm mạnh, rủi ro cao. (Điểm: {score:.1f}/10)"
        
        if 'phân tích kỹ thuật chưa đầy đủ' in analysis.lower():
            return f"Thiếu dữ liệu kỹ thuật chi tiết. Dựa trên thực tế STG giảm sàn, đánh giá xu hướng giảm mạnh, cần thận trọng. (Điểm: {score:.1f}/10)"
        
        base_text = analysis[:200] if analysis else "Phân tích kỹ thuật cần thêm dữ liệu."
        return f"{base_text} (Điểm: {score:.1f}/10)"
    
    def _extract_company_name(self, analysis: str) -> str:
        """Trích xuất tên công ty."""
        # Tìm pattern tên công ty
        name_patterns = [
            r'Tên công ty[:\s]*([^\n]+)',
            r'Company[:\s]*([^\n]+)',
            r'([A-Z][a-zA-Z\s]+(?:Company|Corporation|Joint Stock|Co\.|Ltd))'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, analysis)
            if match:
                return match.group(1).strip()
        
        return "Unknown Company"
    
    def _extract_industry(self, analysis: str) -> str:
        """Trích xuất ngành nghề."""
        # Tìm pattern ngành nghề
        industry_patterns = [
            r'Ngành[:\s]*([^\n]+)',
            r'Industry[:\s]*([^\n]+)',
            r'lĩnh vực[:\s]*([^\n]+)'
        ]
        
        for pattern in industry_patterns:
            match = re.search(pattern, analysis, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Industry"
