"""
Enhanced Data Tool - Phase 3

Advanced data tool integrating:
- Multi-source data aggregation
- Real-time data collection
- Enhanced knowledge base
- Data validation and caching
"""

from crewai.tools import BaseTool
from pydantic import BaseModel
from typing import Type, Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime

try:
    from ..data_integration import (
        RealtimeDataCollector,
        DataValidator,
        CacheManager,
        MultiSourceAggregator
    )
    DATA_INTEGRATION_AVAILABLE = True
except ImportError:
    DATA_INTEGRATION_AVAILABLE = False
    print("Warning: Data integration modules not available")

class EnhancedDataInput(BaseModel):
    """Input schema for enhanced data tool."""
    symbol: str

class EnhancedDataTool(BaseTool):
    """Enhanced data collection tool with multi-source aggregation."""
    
    name: str = "Enhanced Multi-Source Financial Data Tool"
    description: str = (
        "Advanced tool for collecting comprehensive financial data from multiple sources "
        "with real-time updates, data validation, and quality assurance. "
        "Provides aggregated, validated data with confidence scores."
    )
    args_schema: Type[BaseModel] = EnhancedDataInput
    
    def __init__(self):
        """Initialize enhanced data tool."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.cache_manager = None
        self.aggregator = None
        self.validator = None
        self._initialized = False
        
        # Load enhanced knowledge base
        self.industry_benchmarks = self._load_industry_benchmarks()
    
    async def _initialize_components(self):
        """Initialize data integration components."""
        if not DATA_INTEGRATION_AVAILABLE or self._initialized:
            return
        
        try:
            # Initialize cache manager
            self.cache_manager = CacheManager(
                max_memory_size=50 * 1024 * 1024,  # 50MB
                default_ttl=300  # 5 minutes
            )
            
            # Initialize aggregator
            self.aggregator = MultiSourceAggregator(self.cache_manager)
            await self.aggregator.initialize()
            
            # Initialize validator
            self.validator = DataValidator()
            
            self._initialized = True
            self.logger.info("Enhanced data tool components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
    
    def _run(self, symbol: str) -> str:
        """
        Collect enhanced financial data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Comprehensive financial data analysis
        """
        try:
            # Run async data collection
            return asyncio.run(self._run_async(symbol))
            
        except Exception as e:
            self.logger.error(f"Error in enhanced data collection: {e}")
            return f"Lỗi khi thu thập dữ liệu nâng cao cho {symbol}: {str(e)}"
    
    async def _run_async(self, symbol: str) -> str:
        """Async implementation of data collection."""
        try:
            await self._initialize_components()
            
            # Collect data from multiple sources
            if self.aggregator:
                aggregated_data = await self.aggregator.aggregate_stock_data(
                    symbol, 
                    data_types=['price', 'ratios', 'sentiment']
                )
                
                if aggregated_data:
                    return self._format_enhanced_output(symbol, aggregated_data)
            
            # Fallback to basic data collection
            return self._get_basic_data(symbol)
            
        except Exception as e:
            self.logger.error(f"Error in async data collection: {e}")
            return self._get_basic_data(symbol)
    
    def _format_enhanced_output(self, symbol: str, data) -> str:
        """Format enhanced data output."""
        try:
            output = f"""=== PHÂN TÍCH DỮ LIỆU NÂNG CAO - {symbol.upper()} ===

📊 THÔNG TIN CƠ BẢN:
• Mã cổ phiếu: {symbol.upper()}
• Thời gian cập nhật: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
• Điểm chất lượng dữ liệu: {data.data_quality_score:.1%}
• Số nguồn dữ liệu: {len(data.source_data)}

💰 DỮ LIỆU GIÁ (MULTI-SOURCE):
"""
            
            # Price data
            if 'price' in data.primary_data:
                price = data.primary_data['price']
                change = data.primary_data.get('change', 0)
                change_pct = data.primary_data.get('change_percent', 0)
                volume = data.primary_data.get('volume', 0)
                
                output += f"""• Giá hiện tại: {price:,.0f} VND
• Thay đổi: {change:+,.0f} VND ({change_pct:+.2f}%)
• Khối lượng: {volume:,} cổ phiếu
"""
            
            # Data sources used
            output += f"\n🔗 NGUỒN DỮ LIỆU SỬ DỤNG:\n"
            for source_name, source_data in data.source_data.items():
                confidence = data.confidence_scores.get(source_name, 0)
                output += f"• {source_name.upper()}: Độ tin cậy {confidence:.1%}\n"
            
            # Conflicts and quality
            if data.conflicts_detected:
                output += f"\n⚠️ XUNG ĐỘT DỮ LIỆU PHÁT HIỆN:\n"
                for conflict in data.conflicts_detected:
                    output += f"• {conflict}\n"
            
            # Sentiment analysis
            if 'sentiment_score' in data.primary_data:
                sentiment = data.primary_data['sentiment_score']
                sentiment_trend = data.primary_data.get('sentiment_trend', 'neutral')
                
                output += f"""
💭 PHÂN TÍCH TÂM LÝ THỊ TRƯỜNG:
• Điểm sentiment: {sentiment:.2f}
• Xu hướng: {sentiment_trend.upper()}
"""
            
            # Industry benchmarks
            industry_data = self._get_industry_context(symbol)
            if industry_data:
                output += f"\n🏭 THÔNG TIN NGÀNH:\n{industry_data}"
            
            # Data quality assessment
            output += f"""
✅ ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU:
• Tổng điểm chất lượng: {data.data_quality_score:.1%}
• Phương pháp xử lý xung đột: {data.resolution_method.value if data.resolution_method else 'N/A'}
• Độ tin cậy tổng thể: {'CAO' if data.data_quality_score > 0.8 else 'TRUNG BÌNH' if data.data_quality_score > 0.6 else 'THẤP'}

📈 KHUYẾN NGHỊ SỬ DỤNG:
"""
            
            if data.data_quality_score > 0.8:
                output += "• Dữ liệu có độ tin cậy cao, phù hợp cho phân tích và ra quyết định\n"
            elif data.data_quality_score > 0.6:
                output += "• Dữ liệu có độ tin cậy trung bình, nên kết hợp với các nguồn khác\n"
            else:
                output += "• Dữ liệu có độ tin cậy thấp, cần thận trọng khi sử dụng\n"
            
            if data.conflicts_detected:
                output += "• Phát hiện xung đột dữ liệu, đã được xử lý tự động\n"
            
            output += f"\n⏱️ Dữ liệu được thu thập và xử lý lúc: {datetime.now().strftime('%H:%M:%S')}"
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error formatting enhanced output: {e}")
            return f"Lỗi định dạng dữ liệu nâng cao cho {symbol}: {str(e)}"
    
    def _get_basic_data(self, symbol: str) -> str:
        """Fallback basic data collection."""
        try:
            # This would use the original vnstock integration
            output = f"""=== DỮ LIỆU CƠ BẢN - {symbol.upper()} ===

⚠️ Chế độ dữ liệu cơ bản (Enhanced features không khả dụng)

• Mã cổ phiếu: {symbol.upper()}
• Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 Để sử dụng đầy đủ tính năng nâng cao, vui lòng cài đặt:
- Multi-source data integration
- Real-time data collectors
- Data validation system
"""
            
            # Add industry context if available
            industry_data = self._get_industry_context(symbol)
            if industry_data:
                output += f"\n🏭 THÔNG TIN NGÀNH:\n{industry_data}"
            
            return output
            
        except Exception as e:
            return f"Lỗi thu thập dữ liệu cơ bản cho {symbol}: {str(e)}"
    
    def _load_industry_benchmarks(self) -> Dict[str, Any]:
        """Load enhanced industry benchmarks."""
        try:
            import os
            benchmark_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', '..', 
                'knowledge', 
                'enhanced_industry_benchmarks.json'
            )
            
            if os.path.exists(benchmark_path):
                with open(benchmark_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return {}
            
        except Exception as e:
            self.logger.warning(f"Could not load industry benchmarks: {e}")
            return {}
    
    def _get_industry_context(self, symbol: str) -> str:
        """Get industry context for symbol."""
        try:
            if not self.industry_benchmarks:
                return ""
            
            # Map common symbols to industries (simplified)
            symbol_industry_map = {
                'HPG': 'Kim loại và khai khoáng',
                'VIC': 'Bất động sản',
                'VCB': 'Tài chính ngân hàng',
                'FPT': 'Phần mềm và dịch vụ công nghệ thông tin',
                'MSN': 'Bất động sản',
                'VHM': 'Bất động sản',
                'TCB': 'Tài chính ngân hàng',
                'SSI': 'Chứng khoán và ngân hàng đầu tư'
            }
            
            industry = symbol_industry_map.get(symbol.upper())
            if not industry:
                return "• Thông tin ngành: Chưa xác định"
            
            industries_data = self.industry_benchmarks.get('industries', {})
            industry_info = industries_data.get(industry, {})
            
            if not industry_info:
                return f"• Ngành: {industry} (Chưa có dữ liệu benchmark)"
            
            context = f"• Ngành: {industry}\n"
            context += f"• P/E trung bình ngành: {industry_info.get('PE', 'N/A')}\n"
            context += f"• P/B trung bình ngành: {industry_info.get('PB', 'N/A')}\n"
            context += f"• ROE trung bình ngành: {industry_info.get('ROE', 'N/A')}%\n"
            
            volatility = industry_info.get('volatility', 'unknown')
            context += f"• Độ biến động: {volatility.upper()}\n"
            
            regulatory_impact = industry_info.get('regulatory_impact', 'unknown')
            context += f"• Tác động chính sách: {regulatory_impact.upper()}\n"
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting industry context: {e}")
            return "• Lỗi khi lấy thông tin ngành"

# Example usage
def test_enhanced_data_tool():
    """Test the enhanced data tool."""
    tool = EnhancedDataTool()
    result = tool._run("HPG")
    print(result)

if __name__ == "__main__":
    test_enhanced_data_tool()
