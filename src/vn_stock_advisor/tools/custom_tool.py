from typing import Type, Optional, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from vnstock import Vnstock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

try:
    import talib as ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    print("Warning: TA-Lib not available. Some technical indicators may not work.")

# Import ML and Technical Analysis modules
try:
    from ..ml.pattern_recognition import PatternRecognition
    from ..ml.anomaly_detection import AnomalyDetection
    from ..ml.sentiment_analyzer import SentimentAnalyzer
    from ..technical.fibonacci_calculator import FibonacciCalculator
    from ..technical.ichimoku_analyzer import IchimokuAnalyzer
    from ..technical.volume_analyzer import VolumeAnalyzer
    from ..technical.divergence_detector import DivergenceDetector
except ImportError as e:
    print(f"Warning: Could not import ML/Technical modules: {e}")
    PatternRecognition = None
    AnomalyDetection = None
    SentimentAnalyzer = None
    FibonacciCalculator = None
    IchimokuAnalyzer = None
    VolumeAnalyzer = None
    DivergenceDetector = None

# Import Phase 3 Data Integration modules
try:
    from ..data_integration import (
        RealtimeDataCollector,
        DataValidator,
        CacheManager,
        MultiSourceAggregator
    )
    DATA_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Data Integration modules: {e}")
    RealtimeDataCollector = None
    DataValidator = None
    CacheManager = None
    MultiSourceAggregator = None
    DATA_INTEGRATION_AVAILABLE = False

class MyToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Mã cổ phiếu.")

class FundDataTool(BaseTool):
    name: str = "Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích cơ bản."
    description: str = "Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích cơ bản, cung cấp các chỉ số tài chính như P/E, P/B, ROE, ROA, EPS, D/E, biên lợi nhuận và EV/EBITDA."
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, argument: str) -> str:
        try:
            # Use real data with better error handling and caching
            import time
            import random
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            # Try multiple sources with proper error handling
            sources = ["VCI", "DNSE", "SSI"]
            stock = None
            company = None
            
            for source in sources:
                try:
                    print(f"Trying {source} for {argument}...")
                    stock = Vnstock().stock(symbol=argument, source=source)
                    company = Vnstock().stock(symbol=argument, source=source).company
                    print(f"Successfully got data from {source}")
                    break
                except Exception as e:
                    print(f"Source {source} failed: {str(e)[:100]}...")
                    continue
            
            if stock is None:
                raise Exception("All data sources failed")
                
            financial_ratios = stock.finance.ratio(period="quarter")
            income_df = stock.finance.income_statement(period="quarter")

            # Get company full name & industry with error handling
            try:
                profile_data = company.profile().get("company_name")
                full_name = profile_data.iloc[0] if not profile_data.empty else f"Company {argument}"
            except (IndexError, AttributeError):
                full_name = f"Company {argument}"
            
            try:
                overview_data = company.overview().get("industry")
                industry = overview_data.iloc[0] if not overview_data.empty else "Unknown"
            except (IndexError, AttributeError):
                industry = "Unknown"

            # Get data from the latest row of DataFrame for financial ratios with error handling
            if financial_ratios.empty:
                return f"Không có dữ liệu tài chính cho cổ phiếu {argument}"
            
            latest_ratios = financial_ratios.iloc[0]

            # Get last 4 quarters of income statement with error handling
            if income_df.empty:
                quarterly_trends = ["Không có dữ liệu báo cáo thu nhập"]
            else:
                last_4_quarters = income_df.head(4)
            
            # Extract financial ratios data - handle both TCBS and VCI formats
            try:
                # Try VCI format first (multi-level columns)
                pe_ratio = latest_ratios.get(('Chỉ tiêu định giá', 'P/E'), "N/A")
                pb_ratio = latest_ratios.get(('Chỉ tiêu định giá', 'P/B'), "N/A")
                roe = latest_ratios.get(('Chỉ tiêu khả năng sinh lợi', 'ROE (%)'), "N/A")
                roa = latest_ratios.get(('Chỉ tiêu khả năng sinh lợi', 'ROA (%)'), "N/A")
                eps = latest_ratios.get(('Chỉ tiêu định giá', 'EPS (VND)'), "N/A")
                de = latest_ratios.get(('Chỉ tiêu cơ cấu nguồn vốn', 'Debt/Equity'), "N/A")
                profit_margin = latest_ratios.get(('Chỉ tiêu khả năng sinh lợi', 'Gross Profit Margin (%)'), "N/A")
                evebitda = latest_ratios.get(('Chỉ tiêu định giá', 'EV/EBITDA'), "N/A")
            except:
                # Fallback to TCBS format
                pe_ratio = latest_ratios.get("price_to_earning", "N/A")
                pb_ratio = latest_ratios.get("price_to_book", "N/A")
                roe = latest_ratios.get("roe", "N/A")
                roa = latest_ratios.get("roa", "N/A")
                eps = latest_ratios.get("earning_per_share", "N/A")
                de = latest_ratios.get("debt_on_equity", "N/A")
                profit_margin = latest_ratios.get("gross_profit_margin", "N/A")
                evebitda = latest_ratios.get("value_before_ebitda", "N/A")

                        # Format quarterly income data only if we have data
            if 'last_4_quarters' in locals() and not last_4_quarters.empty:
                quarterly_trends = []
                for i, (_, quarter) in enumerate(last_4_quarters.iterrows()):
                    try:
                        # Handle formatting of values properly - VCI format
                        revenue = quarter.get("Revenue (Bn. VND)", "N/A")
                        revenue_formatted = f"{revenue:,.0f}" if isinstance(revenue, (int, float)) and revenue != "N/A" else revenue
                        
                        gross_profit = quarter.get("Gross Profit", "N/A")
                        gross_profit_formatted = f"{gross_profit:,.0f}" if isinstance(gross_profit, (int, float)) and gross_profit != "N/A" else gross_profit
                        
                        post_tax_profit = quarter.get("Net Profit For the Year", "N/A")
                        post_tax_profit_formatted = f"{post_tax_profit:,.0f}" if isinstance(post_tax_profit, (int, float)) and post_tax_profit != "N/A" else post_tax_profit
                        
                        quarter_info = f"""
                        Quý T - {i + 1}:
                        - Doanh thu thuần: {revenue_formatted} tỉ đồng
                        - Lợi nhuận gộp: {gross_profit_formatted} tỉ đồng
                        - Lợi nhuận sau thuế: {post_tax_profit_formatted} tỉ đồng
                        """
                        quarterly_trends.append(quarter_info)
                    except Exception as quarter_error:
                        quarterly_trends.append(f"Quý T - {i + 1}: Lỗi dữ liệu")
            else:
                quarterly_trends = ["Không có dữ liệu báo cáo thu nhập"]
            
            return f"""Mã cổ phiếu: {argument}
            Tên công ty: {full_name}
            Ngành: {industry}
            Ngày phân tích: {datetime.now().strftime('%Y-%m-%d')}
            
            Tỷ lệ P/E: {pe_ratio}
            Tỷ lệ P/B: {pb_ratio}
            Tỷ lệ ROE: {roe}
            Tỷ lệ ROA: {roa}
            Biên lợi nhuận: {profit_margin}
            Lợi nhuận trên mỗi cổ phiếu EPS (VND): {eps}
            Hệ số nợ trên vốn chủ sở hữu D/E: {de}
            Tỷ lệ EV/EBITDA: {evebitda}

            XU HƯỚNG 4 QUÝ GẦN NHẤT:
            {"".join(quarterly_trends)}
            """
        except Exception as e:
            return f"Lỗi khi lấy dữ liệu: {e}"
        
class TechDataTool(BaseTool):
    name: str = "Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật."
    description: str = "Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật, cung cấp các chỉ số như SMA, EMA, RSI, MACD, Bollinger Bands, và vùng hỗ trợ/kháng cự."
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, argument: str) -> str:
        try:
            # Use real data with better error handling and caching
            import time
            import random
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            # Try multiple sources with proper error handling
            sources = ["VCI", "DNSE", "SSI"]
            stock = None
            company = None
            
            for source in sources:
                try:
                    print(f"Trying {source} for {argument}...")
                    stock = Vnstock().stock(symbol=argument, source=source)
                    company = Vnstock().stock(symbol=argument, source=source).company
                    print(f"Successfully got data from {source}")
                    break
                except Exception as e:
                    print(f"Source {source} failed: {str(e)[:100]}...")
                    continue
            
            if stock is None:
                raise Exception("All data sources failed")

            # Get company full name & industry with error handling
            try:
                profile_data = company.profile().get("company_name")
                full_name = profile_data.iloc[0] if not profile_data.empty else f"Company {argument}"
            except (IndexError, AttributeError):
                full_name = f"Company {argument}"
            
            try:
                overview_data = company.overview().get("industry")
                industry = overview_data.iloc[0] if not overview_data.empty else "Unknown"
            except (IndexError, AttributeError):
                industry = "Unknown"
            
            # Phase 3: Initialize data validation if available
            data_validator = None
            if DATA_INTEGRATION_AVAILABLE and DataValidator:
                data_validator = DataValidator()
            
            # Get price data for the last 200 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=200)
            price_data = stock.quote.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval="1D"  # Daily data
            )
            
            if price_data.empty:
                return f"Không tìm thấy dữ liệu lịch sử cho cổ phiếu {argument}"
            
            # Calculate technical indicators
            tech_data = self._calculate_indicators(price_data)
            
            # Identify support and resistance levels
            support_resistance = self._find_support_resistance(price_data)
            
            # Get recent price and volume data with error handling
            if len(price_data) == 0:
                return f"Không có dữ liệu giá cho cổ phiếu {argument}"
            
            current_price = price_data['close'].iloc[-1]
            recent_prices = price_data['close'].iloc[-5:-1] if len(price_data) >= 5 else price_data['close']
            current_volume = price_data['volume'].iloc[-1]
            recent_volumes = price_data['volume'].iloc[-5:-1] if len(price_data) >= 5 else price_data['volume']
            
            # Format result
            latest_indicators = tech_data.iloc[-1]
            
            result = f"""Mã cổ phiếu: {argument}
            Tên công ty: {full_name}
            Ngành: {industry}
            Ngày phân tích: {datetime.now().strftime('%Y-%m-%d')}
            Giá hiện tại: {(current_price*1000):,.0f} VND
            Khối lượng giao dịch: {current_volume:,.0f} cp

            GIÁ ĐÓNG CỬA GẦN NHẤT:
            - T-1: {(recent_prices.iloc[-1]*1000):,.0f} VND (KL: {recent_volumes.iloc[-1]:,.0f} cp)
            - T-2: {(recent_prices.iloc[-2]*1000):,.0f} VND (KL: {recent_volumes.iloc[-2]:,.0f} cp)
            - T-3: {(recent_prices.iloc[-3]*1000):,.0f} VND (KL: {recent_volumes.iloc[-3]:,.0f} cp)
            - T-4: {(recent_prices.iloc[-4]*1000):,.0f} VND (KL: {recent_volumes.iloc[-4]:,.0f} cp)
            
            CHỈ SỐ KỸ THUẬT:
            - SMA (20): {(latest_indicators['SMA_20']*1000):,.0f}
            - SMA (50): {(latest_indicators['SMA_50']*1000):,.0f}
            - SMA (200): {(latest_indicators['SMA_200']*1000):,.0f}
            - EMA (12): {(latest_indicators['EMA_12']*1000):,.0f}
            - EMA (26): {(latest_indicators['EMA_26']*1000):,.0f}
            
            - RSI (14): {latest_indicators['RSI_14']:.2f}
            - MACD: {latest_indicators['MACD']:.2f}
            - MACD Signal: {latest_indicators['MACD_Signal']:.2f}
            - MACD Histogram: {latest_indicators['MACD_Hist']:.2f}
            
            - Bollinger Upper: {(latest_indicators['BB_Upper']*1000):,.0f}
            - Bollinger Middle: {(latest_indicators['BB_Middle']*1000):,.0f}
            - Bollinger Lower: {(latest_indicators['BB_Lower']*1000):,.0f}

            CHỈ SỐ KHỐI LƯỢNG:
            - Khối lượng hiện tại: {current_volume:,.0f} cp
            - Trung bình 10 phiên: {latest_indicators['Volume_SMA_10']:,.0f} cp
            - Trung bình 20 phiên: {latest_indicators['Volume_SMA_20']:,.0f} cp
            - Trung bình 50 phiên: {latest_indicators['Volume_SMA_50']:,.0f} cp
            - Tỷ lệ Khối lượng / Trung bình 20: {latest_indicators['Volume_Ratio_20']:.2f}
            - On-Balance Volume (OBV): {latest_indicators['OBV']:,.0f}
            
            VÙNG HỖ TRỢ VÀ KHÁNG CỰ:
            {support_resistance}
            
            NHẬN ĐỊNH KỸ THUẬT:
            {self._get_technical_analysis(latest_indicators, current_price, support_resistance)}
            
            PHÂN TÍCH MACHINE LEARNING:
            {self._run_ml_analysis(tech_data)}
            
            PHÂN TÍCH KỸ THUẬT NÂNG CAO:
            {self._run_advanced_technical_analysis(tech_data)}
            
            {self._get_data_quality_assessment(data_validator, current_price, current_volume, latest_indicators)}
            """
            return result
            
        except Exception as e:
            return f"Lỗi khi lấy dữ liệu kỹ thuật: {e}"
    
    def _calculate_indicators(self, df):
        """Calculate various technical indicators."""
        # Make a copy to avoid modifying original data
        data = df.copy()
        
        # Simple Moving Averages
        data['SMA_20'] = data['close'].rolling(window=20).mean()
        data['SMA_50'] = data['close'].rolling(window=50).mean()
        data['SMA_200'] = data['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        data['EMA_12'] = data['close'].ewm(span=12, adjust=False).mean()
        data['EMA_26'] = data['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Avoid division by zero
        rs = gain / loss.replace(0, np.nan)
        data['RSI_14'] = 100 - (100 / (1 + rs))
        data['RSI_14'] = data['RSI_14'].fillna(50)  # Fill NaN values with neutral RSI
        
        # Bollinger Bands
        data['BB_Middle'] = data['close'].rolling(window=20).mean()
        std_dev = data['close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (std_dev * 2)
        data['BB_Lower'] = data['BB_Middle'] - (std_dev * 2)

        # Calculate volume moving averages
        data['Volume_SMA_10'] = data['volume'].rolling(window=10).mean()
        data['Volume_SMA_20'] = data['volume'].rolling(window=20).mean()
        data['Volume_SMA_50'] = data['volume'].rolling(window=50).mean()
        
        # Calculate volume ratio compared to average
        data['Volume_Ratio_10'] = data['volume'] / data['Volume_SMA_10']
        data['Volume_Ratio_20'] = data['volume'] / data['Volume_SMA_20']
        
        # On-Balance Volume (OBV)
        data['OBV'] = 0
        data.loc[0, 'OBV'] = data.loc[0, 'volume']
        for i in range(1, len(data)):
            if data.loc[i, 'close'] > data.loc[i-1, 'close']:
                data.loc[i, 'OBV'] = data.loc[i-1, 'OBV'] + data.loc[i, 'volume']
            elif data.loc[i, 'close'] < data.loc[i-1, 'close']:
                data.loc[i, 'OBV'] = data.loc[i-1, 'OBV'] - data.loc[i, 'volume']
            else:
                data.loc[i, 'OBV'] = data.loc[i-1, 'OBV']
        
        return data
    
    def _find_support_resistance(self, df, window=10, threshold=0.03):
        """Find support and resistance levels."""
        data = df.copy()
        
        # Find potential pivot points
        data['local_max'] = data['high'].rolling(window=window, center=True).apply(
            lambda x: x.iloc[len(x)//2] == max(x), raw=False
        )
        data['local_min'] = data['low'].rolling(window=window, center=True).apply(
            lambda x: x.iloc[len(x)//2] == min(x), raw=False
        )
        
        # Get pivot high/low points
        resistance_levels = data[data['local_max'] == 1]['high'].values
        support_levels = data[data['local_min'] == 1]['low'].values
        
        # Group close resistance/support levels
        if len(data) == 0:
            return {"support_levels": [], "resistance_levels": []}
        
        current_price = data['close'].iloc[-1]
        
        # Function to cluster price levels
        def cluster_levels(levels, threshold_pct):
            if len(levels) == 0:
                return []
                
            levels = sorted(levels)
            clusters = [[levels[0]]]
            
            for level in levels[1:]:
                last_cluster = clusters[-1]
                last_value = last_cluster[-1]
                
                # If this level is within threshold% of the last value, add to the same cluster
                if abs((level - last_value) / last_value) < threshold_pct:
                    last_cluster.append(level)
                else:
                    clusters.append([level])
            
            # Calculate average for each cluster
            return [np.mean(cluster) for cluster in clusters]
        
        # Cluster and filter resistance levels
        resistance_levels = cluster_levels(resistance_levels, threshold)
        resistance_levels = [r for r in resistance_levels if r > current_price]
        resistance_levels = sorted(resistance_levels)[:3]  # Get nearest 3 levels
        
        # Cluster and filter support levels
        support_levels = cluster_levels(support_levels, threshold)
        support_levels = [s for s in support_levels if s < current_price]
        support_levels = sorted(support_levels, reverse=True)[:3]  # Get nearest 3 levels
        
        # Format result
        result = "Vùng kháng cự:\n"
        for i, level in enumerate(resistance_levels, 1):
            result += f"- R{i}: {level*1000:,.0f} VND\n"
        
        result += "\nVùng hỗ trợ:\n"
        for i, level in enumerate(support_levels, 1):
            result += f"- S{i}: {level*1000:,.0f} VND\n"
            
        return result
    
    def _get_technical_analysis(self, indicators, current_price, support_resistance):
        """Generate technical analysis text based on indicators."""
        analysis = []
        
        # Trend analysis based on SMAs
        if current_price > indicators['SMA_200'] and indicators['SMA_50'] > indicators['SMA_200']:
            analysis.append("- Xu hướng dài hạn: TĂNG (Giá trên SMA 200, SMA 50 trên SMA 200)")
        elif current_price < indicators['SMA_200'] and indicators['SMA_50'] < indicators['SMA_200']:
            analysis.append("- Xu hướng dài hạn: GIẢM (Giá dưới SMA 200, SMA 50 dưới SMA 200)")
        else:
            analysis.append("- Xu hướng dài hạn: TRUNG LẬP (Tín hiệu trái chiều giữa các SMA)")
        
        # Short-term trend
        if current_price > indicators['SMA_20'] and indicators['SMA_20'] > indicators['SMA_50']:
            analysis.append("- Xu hướng ngắn hạn: TĂNG (Giá trên SMA 20, SMA 20 trên SMA 50)")
        elif current_price < indicators['SMA_20'] and indicators['SMA_20'] < indicators['SMA_50']:
            analysis.append("- Xu hướng ngắn hạn: GIẢM (Giá dưới SMA 20, SMA 20 dưới SMA 50)")
        else:
            analysis.append("- Xu hướng ngắn hạn: TRUNG LẬP (Tín hiệu trái chiều giữa SMA ngắn hạn)")
        
        # RSI analysis
        if indicators['RSI_14'] > 70:
            analysis.append("- RSI: QUÁ MUA (RSI > 70), có khả năng điều chỉnh giảm")
        elif indicators['RSI_14'] < 30:
            analysis.append("- RSI: QUÁ BÁN (RSI < 30), có khả năng hồi phục")
        else:
            analysis.append(f"- RSI: TRUNG TÍNH ({indicators['RSI_14']:.2f})")
        
        # MACD analysis
        if indicators['MACD'] > indicators['MACD_Signal']:
            analysis.append("- MACD: TÍCH CỰC (MACD trên Signal Line)")
        else:
            analysis.append("- MACD: TIÊU CỰC (MACD dưới Signal Line)")
        
        # Bollinger Bands analysis
        if current_price > indicators['BB_Upper']:
            analysis.append("- Bollinger Bands: QUÁ MUA (Giá trên dải trên BB)")
        elif current_price < indicators['BB_Lower']:
            analysis.append("- Bollinger Bands: QUÁ BÁN (Giá dưới dải dưới BB)")
        else:
            position = (current_price - indicators['BB_Lower']) / (indicators['BB_Upper'] - indicators['BB_Lower'])
            if position > 0.8:
                analysis.append("- Bollinger Bands: GẦN VÙNG QUÁ MUA (Giá gần dải trên BB)")
            elif position < 0.2:
                analysis.append("- Bollinger Bands: GẦN VÙNG QUÁ BÁN (Giá gần dải dưới BB)")
            else:
                analysis.append("- Bollinger Bands: TRUNG TÍNH (Giá trong khoảng giữa dải BB)")
        
        # Volume ratio analysis
        volume_ratio_20 = indicators['Volume_Ratio_20']
        if volume_ratio_20 > 2.0:
            analysis.append("- Khối lượng: RẤT CAO (>200% trung bình 20 phiên)")
        elif volume_ratio_20 > 1.5:
            analysis.append("- Khối lượng: CAO (150-200% trung bình 20 phiên)")
        elif volume_ratio_20 < 0.5:
            analysis.append("- Khối lượng: THẤP (<50% trung bình 20 phiên)")
        else:
            analysis.append("- Khối lượng: BÌNH THƯỜNG (50-150% trung bình 20 phiên)")

        # Volume trend analysis
        if (indicators['Volume_SMA_10'] > indicators['Volume_SMA_20'] and 
            indicators['Volume_SMA_20'] > indicators['Volume_SMA_50']):
            analysis.append("- Xu hướng khối lượng: TĂNG (SMA 10 > SMA 20 > SMA 50)")
        elif (indicators['Volume_SMA_10'] < indicators['Volume_SMA_20'] and 
            indicators['Volume_SMA_20'] < indicators['Volume_SMA_50']):
            analysis.append("- Xu hướng khối lượng: GIẢM (SMA 10 < SMA 20 < SMA 50)")
        else:
            analysis.append("- Xu hướng khối lượng: TRUNG LẬP")

        # OBV trend analysis
        current_volume = indicators['volume']
        if current_volume > indicators['Volume_SMA_20'] * 1.5:
            if current_price > indicators['SMA_20']:
                analysis.append("- Tín hiệu khối lượng: TÍCH CỰC (Khối lượng cao kèm giá tăng)")
            else:
                analysis.append("- Tín hiệu khối lượng: TIÊU CỰC (Khối lượng cao kèm giá giảm)")

        return "\n".join(analysis)
    
    def _run_ml_analysis(self, data_with_indicators):
        """Run ML analysis on the data."""
        try:
            if not all([PatternRecognition, AnomalyDetection]):
                return "ML modules không khả dụng"
            
            prices = data_with_indicators['close'].tolist()
            volumes = data_with_indicators['volume'].tolist()
            
            ml_results = []
            
            # Pattern Recognition
            pattern_analyzer = PatternRecognition()
            patterns = pattern_analyzer.analyze_patterns(prices, volumes)
            if patterns:
                pattern_summary = pattern_analyzer.get_pattern_summary(patterns)
                ml_results.append(f"📊 PATTERN RECOGNITION:")
                ml_results.append(f"- Phát hiện {pattern_summary['total_patterns']} patterns")
                ml_results.append(f"- Tín hiệu chính: {pattern_summary['primary_signal']}")
                ml_results.append(f"- Khuyến nghị: {pattern_summary['recommendation']}")
            
            # Anomaly Detection
            anomaly_detector = AnomalyDetection()
            anomaly_analysis = anomaly_detector.comprehensive_anomaly_analysis(prices, volumes)
            if anomaly_analysis.get('total_anomalies', 0) > 0:
                ml_results.append(f"🚨 ANOMALY DETECTION:")
                ml_results.append(f"- Phát hiện {anomaly_analysis['total_anomalies']} bất thường")
                ml_results.append(f"- Mức độ rủi ro: {anomaly_analysis['risk_level']}")
                ml_results.append(f"- Tóm tắt: {anomaly_analysis['summary']}")
            
            return "\n".join(ml_results) if ml_results else "Không phát hiện pattern hoặc anomaly đáng kể"
            
        except Exception as e:
            return f"Lỗi ML analysis: {str(e)}"
    
    def _run_advanced_technical_analysis(self, data_with_indicators):
        """Run advanced technical analysis."""
        try:
            if not all([FibonacciCalculator, IchimokuAnalyzer, VolumeAnalyzer, DivergenceDetector]):
                return "Advanced technical modules không khả dụng"
            
            prices = data_with_indicators['close'].tolist()
            highs = data_with_indicators['high'].tolist()
            lows = data_with_indicators['low'].tolist()
            volumes = data_with_indicators['volume'].tolist()
            
            advanced_results = []
            
            # Fibonacci Analysis
            fib_calc = FibonacciCalculator()
            fib_summary = fib_calc.get_fibonacci_summary(prices)
            if 'error' not in fib_summary:
                advanced_results.append(f"📐 FIBONACCI ANALYSIS:")
                advanced_results.append(f"- Xu hướng: {fib_summary['trend_direction']}")
                advanced_results.append(f"- Swing High: {fib_summary['swing_high']:,.0f}")
                advanced_results.append(f"- Swing Low: {fib_summary['swing_low']:,.0f}")
                if fib_summary.get('price_analysis', {}).get('recommendation'):
                    advanced_results.append(f"- Khuyến nghị: {fib_summary['price_analysis']['recommendation']}")
            
            # Ichimoku Analysis
            ichimoku_analyzer = IchimokuAnalyzer()
            ichimoku_summary = ichimoku_analyzer.get_ichimoku_summary(highs, lows, prices)
            if 'error' not in ichimoku_summary:
                trading_signal = ichimoku_summary['trading_signal']
                advanced_results.append(f"☁️ ICHIMOKU ANALYSIS:")
                advanced_results.append(f"- Tín hiệu: {trading_signal['signal']} ({trading_signal['strength']})")
                advanced_results.append(f"- Độ tin cậy: {trading_signal['confidence']:.1%}")
                advanced_results.append(f"- Mô tả: {trading_signal['description']}")
            
            # Volume Profile Analysis
            volume_analyzer = VolumeAnalyzer()
            volume_summary = volume_analyzer.get_volume_summary(prices, volumes, highs, lows)
            if 'error' not in volume_summary:
                advanced_results.append(f"📊 VOLUME PROFILE:")
                advanced_results.append(f"- Vị trí vs VWAP: {volume_summary['price_vs_vwap']}")
                advanced_results.append(f"- Vị trí vs Value Area: {volume_summary['volume_profile_position']}")
                volume_trend = volume_summary['volume_trend']
                advanced_results.append(f"- Xu hướng volume: {volume_trend['volume_assessment']}")
            
            # Divergence Analysis
            divergence_detector = DivergenceDetector()
            divergence_analysis = divergence_detector.get_comprehensive_divergence_analysis(prices, volumes, highs, lows)
            if divergence_analysis.get('total_divergences', 0) > 0:
                advanced_results.append(f"🔄 DIVERGENCE ANALYSIS:")
                advanced_results.append(f"- Tổng divergences: {divergence_analysis['total_divergences']}")
                advanced_results.append(f"- Tín hiệu tổng thể: {divergence_analysis['overall_signal']}")
                advanced_results.append(f"- Tóm tắt: {divergence_analysis['summary']}")
            
            return "\n".join(advanced_results) if advanced_results else "Không có tín hiệu advanced technical đáng kể"
            
        except Exception as e:
            return f"Lỗi advanced technical analysis: {str(e)}"
    
    def _get_data_quality_assessment(self, data_validator, current_price, current_volume, latest_indicators):
        """Get data quality assessment for Phase 3."""
        try:
            if not data_validator or not DATA_INTEGRATION_AVAILABLE:
                return ""
            
            # Prepare data for validation
            price_data = {
                'price': current_price,
                'volume': current_volume,
                'change_percent': latest_indicators.get('Price_Change_Pct', 0),
                'open': latest_indicators.get('Open', current_price),
                'high': latest_indicators.get('High', current_price),
                'low': latest_indicators.get('Low', current_price),
                'close': current_price
            }
            
            # Validate price data
            validation_results = data_validator.validate_price_data(price_data)
            
            if not validation_results:
                return """
📊 ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU (PHASE 3):
✅ Dữ liệu đã qua kiểm tra - Không phát hiện vấn đề
• Độ tin cậy: CAO
• Trạng thái: SẴN SÀNG SỬ DỤNG
"""
            
            # Analyze validation results
            errors = [r for r in validation_results if r.level.value == 'error']
            warnings = [r for r in validation_results if r.level.value == 'warning']
            critical = [r for r in validation_results if r.level.value == 'critical']
            
            quality_assessment = ["📊 ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU (PHASE 3):"]
            
            if critical:
                quality_assessment.append("🚨 VẤN ĐỀ NGHIÊM TRỌNG:")
                for issue in critical:
                    quality_assessment.append(f"  • {issue.message}")
                quality_assessment.append("• Trạng thái: CẦN KIỂM TRA NGAY")
            
            elif errors:
                quality_assessment.append("⚠️ LỖI DỮ LIỆU:")
                for error in errors:
                    quality_assessment.append(f"  • {error.message}")
                quality_assessment.append("• Trạng thái: CẦN THẬN TRỌNG")
            
            elif warnings:
                quality_assessment.append("💡 CẢNH BÁO:")
                for warning in warnings:
                    quality_assessment.append(f"  • {warning.message}")
                quality_assessment.append("• Trạng thái: CHẤP NHẬN ĐƯỢC")
            
            # Overall assessment
            total_issues = len(critical) + len(errors) + len(warnings)
            if total_issues == 0:
                quality_assessment.append("• Độ tin cậy: CAO")
            elif len(critical) > 0 or len(errors) > 2:
                quality_assessment.append("• Độ tin cậy: THẤP")
            else:
                quality_assessment.append("• Độ tin cậy: TRUNG BÌNH")
            
            quality_assessment.append(f"• Tổng vấn đề phát hiện: {total_issues}")
            quality_assessment.append("• Hệ thống: Enhanced Data Validation v0.6.0")
            
            return "\n".join(quality_assessment)
            
        except Exception as e:
            return f"\n📊 ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU: Lỗi kiểm tra - {str(e)}"

class SentimentAnalysisTool(BaseTool):
    name: str = "Công cụ phân tích sentiment từ tin tức và social media."
    description: str = "Công cụ phân tích sentiment từ tin tức, báo cáo, và social media để đánh giá tâm lý thị trường đối với cổ phiếu."
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, argument: str) -> str:
        try:
            if not SentimentAnalyzer:
                return "Sentiment Analysis module không khả dụng"
            
            # Initialize sentiment analyzer
            sentiment_analyzer = SentimentAnalyzer()
            
            # Sample news articles (in real implementation, this would fetch from news APIs)
            sample_news = [
                {
                    "title": f"Cổ phiếu {argument.upper()} có triển vọng tích cực trong quý tới",
                    "content": f"Các chuyên gia dự báo {argument.upper()} sẽ có kết quả kinh doanh khả quan nhờ tăng trưởng doanh thu và cải thiện biên lợi nhuận.",
                    "source": "VnExpress"
                },
                {
                    "title": f"Áp lực bán tháo trên {argument.upper()} do lo ngại về tình hình kinh tế",
                    "content": f"Nhà đầu tư lo ngại về tác động của lạm phát đến kết quả kinh doanh của {argument.upper()}, gây áp lực bán mạnh.",
                    "source": "CafeF"
                },
                {
                    "title": f"Khuyến nghị mua {argument.upper()} với mục tiêu giá cao hơn",
                    "content": f"Công ty chứng khoán ABC nâng hạng {argument.upper()} lên MUA với mục tiêu giá tăng 20% so với hiện tại.",
                    "source": "Đầu tư Chứng khoán"
                }
            ]
            
            # Analyze sentiment
            sentiment_result = sentiment_analyzer.analyze_news_batch(sample_news)
            
            result = f"""
=== PHÂN TÍCH SENTIMENT CHO MÃ {argument.upper()} ===

📊 TỔNG QUAN SENTIMENT:
- Tổng số bài báo phân tích: {sentiment_result['total_articles']}
- Sentiment trung bình: {sentiment_result['average_sentiment']:.2f}
- Độ tin cậy trung bình: {sentiment_result['average_confidence']:.1%}
- Outlook thị trường: {sentiment_result['market_outlook']}

📈 PHÂN BỐ SENTIMENT:
- Bài báo tích cực: {sentiment_result['positive_articles']} ({sentiment_result['sentiment_distribution']['positive']:.1%})
- Bài báo tiêu cực: {sentiment_result['negative_articles']} ({sentiment_result['sentiment_distribution']['negative']:.1%})
- Bài báo trung tính: {sentiment_result['neutral_articles']} ({sentiment_result['sentiment_distribution']['neutral']:.1%})

🎯 TÍN HIỆU SENTIMENT:
- Tín hiệu bullish: {sentiment_result['bullish_signals']}
- Tín hiệu bearish: {sentiment_result['bearish_signals']}

🔑 TỪ KHÓA QUAN TRỌNG:
{', '.join(sentiment_result['top_key_phrases']) if sentiment_result['top_key_phrases'] else 'Không có từ khóa nổi bật'}

💡 KHUYẾN NGHỊ:
{sentiment_result['recommendation']}

⚠️ LƯU Ý: Đây là phân tích mẫu với dữ liệu giả lập. Trong thực tế cần tích hợp với API tin tức thực tế.
"""
            
            return result
            
        except Exception as e:
            return f"Lỗi khi phân tích sentiment cho mã {argument}: {str(e)}"
    
# Re-write basic FileReadTool but with utf-8 encoding
class FileReadToolSchema(BaseModel):
    """Input for FileReadTool."""

    file_path: str = Field(..., description="Mandatory file full path to read the file")
    start_line: Optional[int] = Field(1, description="Line number to start reading from (1-indexed)")
    line_count: Optional[int] = Field(None, description="Number of lines to read. If None, reads the entire file")


class FileReadTool(BaseTool):
    """A tool for reading file contents.

    This tool inherits its schema handling from BaseTool to avoid recursive schema
    definition issues. The args_schema is set to FileReadToolSchema which defines
    the required file_path parameter. The schema should not be overridden in the
    constructor as it would break the inheritance chain and cause infinite loops.

    The tool supports two ways of specifying the file path:
    1. At construction time via the file_path parameter
    2. At runtime via the file_path parameter in the tool's input

    Args:
        file_path (Optional[str]): Path to the file to be read. If provided,
            this becomes the default file path for the tool.
        **kwargs: Additional keyword arguments passed to BaseTool.

    Example:
        >>> tool = FileReadTool(file_path="/path/to/file.txt")
        >>> content = tool.run()  # Reads /path/to/file.txt
        >>> content = tool.run(file_path="/path/to/other.txt")  # Reads other.txt
        >>> content = tool.run(file_path="/path/to/file.txt", start_line=100, line_count=50)  # Reads lines 100-149
    """

    name: str = "Read a file's content"
    description: str = "A tool that reads the content of a file. To use this tool, provide a 'file_path' parameter with the path to the file you want to read. Optionally, provide 'start_line' to start reading from a specific line and 'line_count' to limit the number of lines read."
    args_schema: Type[BaseModel] = FileReadToolSchema
    file_path: Optional[str] = None

    def __init__(self, file_path: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize the FileReadTool.

        Args:
            file_path (Optional[str]): Path to the file to be read. If provided,
                this becomes the default file path for the tool.
            **kwargs: Additional keyword arguments passed to BaseTool.
        """
        if file_path is not None:
            kwargs["description"] = (
                f"A tool that reads file content. The default file is {file_path}, but you can provide a different 'file_path' parameter to read another file. You can also specify 'start_line' and 'line_count' to read specific parts of the file."
            )

        super().__init__(**kwargs)
        self.file_path = file_path

    def _run(
        self,
        **kwargs: Any,
    ) -> str:
        file_path = kwargs.get("file_path", self.file_path)
        start_line = kwargs.get("start_line", 1)
        line_count = kwargs.get("line_count", None)

        if file_path is None:
            return (
                "Error: No file path provided. Please provide a file path either in the constructor or as an argument."
            )

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                if start_line == 1 and line_count is None:
                    return file.read()

                start_idx = max(start_line - 1, 0)

                selected_lines = [
                    line
                    for i, line in enumerate(file)
                    if i >= start_idx and (line_count is None or i < start_idx + line_count)
                ]

                if not selected_lines and start_idx > 0:
                    return f"Error: Start line {start_line} exceeds the number of lines in the file."

                return "".join(selected_lines)
        except FileNotFoundError:
            return f"Error: File not found at path: {file_path}"
        except PermissionError:
            return f"Error: Permission denied when trying to read file: {file_path}"
        except Exception as e:
            return f"Error: Failed to read file {file_path}. {str(e)}"