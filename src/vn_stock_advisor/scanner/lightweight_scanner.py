"""
Lightweight Stock Scanner - Scanner tối ưu cho việc quét nhanh cổ phiếu

Tập trung vào:
1. Phân tích kỹ thuật cơ bản (RSI, MACD, MA, Volume)
2. So sánh giá thị trường vs giá trị sổ sách (P/B)
3. Momentum và xu hướng
4. Tối thiểu hóa token usage
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from dataclasses import dataclass
import logging

# Import data tools
try:
    from ..tools.custom_tool import FundDataTool, TechDataTool
    from ..data_integration.cache_manager import CacheManager
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    print("Warning: Tools not available, using mock data")

@dataclass
class LightweightScanResult:
    """Kết quả scan nhẹ cho một cổ phiếu"""
    symbol: str
    company_name: str
    industry: str
    
    # Giá và định giá
    current_price: float
    pb_ratio: float
    pe_ratio: float
    market_cap: float
    
    # Kỹ thuật cơ bản
    rsi: float
    macd_signal: str  # "positive", "negative", "neutral"
    ma_trend: str     # "upward", "downward", "sideways"
    volume_trend: str # "increasing", "decreasing", "normal"
    
    # Đánh giá tổng thể
    value_score: float      # 0-10, so sánh P/B với ngành
    momentum_score: float   # 0-10, momentum kỹ thuật
    overall_score: float    # 0-10, điểm tổng hợp
    
    # Khuyến nghị
    recommendation: str     # "BUY", "HOLD", "SELL", "WATCH"
    confidence: float       # 0-1, độ tin cậy
    
    # Metadata
    scan_time: datetime
    data_quality: str       # "good", "fair", "poor"

class LightweightStockScanner:
    """Scanner tối ưu cho việc quét nhanh nhiều cổ phiếu"""
    
    def __init__(self, max_workers: int = 5, use_cache: bool = True):
        """
        Initialize lightweight scanner.
        
        Args:
            max_workers: Số thread tối đa cho parallel processing
            use_cache: Có sử dụng cache để tối ưu token không
        """
        self.max_workers = max_workers
        self.use_cache = use_cache
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache if available
        self.cache_manager = None
        if use_cache and TOOLS_AVAILABLE:
            try:
                self.cache_manager = CacheManager(
                    max_memory_size=20 * 1024 * 1024,  # 20MB
                    default_ttl=1800  # 30 minutes cache
                )
            except Exception as e:
                self.logger.warning(f"Could not initialize cache: {e}")
        
        # Initialize tools
        if TOOLS_AVAILABLE:
            self.fund_tool = FundDataTool()
            self.tech_tool = TechDataTool()
        
        # Industry P/B benchmarks (simplified)
        self.industry_pb_benchmarks = {
            "Real Estate": 1.9,
            "Banking": 1.3,
            "Technology": 3.0,
            "Manufacturing": 2.0,
            "Retail": 2.5,
            "Energy": 2.1,
            "Healthcare": 2.8,
            "Default": 2.0
        }
        
        # Scoring weights
        self.weights = {
            "value": 0.4,      # 40% - Định giá
            "momentum": 0.35,  # 35% - Momentum kỹ thuật
            "quality": 0.25    # 25% - Chất lượng dữ liệu và cơ bản
        }
    
    def get_popular_stocks(self) -> List[str]:
        """Lấy danh sách cổ phiếu phổ biến để scan."""
        return [
            # VN30 top picks
            'VIC', 'VHM', 'VRE', 'VCB', 'BID', 'CTG', 'TCB', 'MBB', 'ACB',
            'HPG', 'HSG', 'GVR', 'PLX', 'GAS', 'VNM', 'MSN', 'MWG', 'FPT',
            'VJC', 'SAB', 'BVH', 'CTD', 'PDR', 'KDH', 'DXG',
            
            # HNX potential
            'SHB', 'PVS', 'CEO', 'TNG', 'VCS', 'IDC', 'MBS', 'PVC',
            
            # Mid-cap với tiềm năng
            'DGC', 'VGC', 'BCM', 'GMD', 'VPI', 'HAG', 'DCM', 'DPM'
        ]
    
    async def _get_cached_data(self, symbol: str, data_type: str) -> Optional[Dict]:
        """Lấy dữ liệu từ cache nếu có."""
        if not self.cache_manager:
            return None
        
        cache_key = f"lightweight_scan_{symbol}_{data_type}"
        try:
            return await self.cache_manager.get(cache_key)
        except Exception:
            return None
    
    async def _cache_data(self, symbol: str, data_type: str, data: Dict) -> None:
        """Lưu dữ liệu vào cache."""
        if not self.cache_manager:
            return
        
        cache_key = f"lightweight_scan_{symbol}_{data_type}"
        try:
            await self.cache_manager.set(cache_key, data, ttl=1800)  # 30 min
        except Exception as e:
            self.logger.warning(f"Could not cache data for {symbol}: {e}")
    
    def _extract_fundamental_metrics(self, fund_data: str) -> Dict[str, float]:
        """Trích xuất các chỉ số cơ bản từ dữ liệu."""
        metrics = {
            "pe_ratio": None,
            "pb_ratio": None,
            "roe": None,
            "current_price": 0.0,
            "market_cap": 0.0
        }
        
        try:
            lines = fund_data.split('\n')
            for line in lines:
                line = line.strip()
                if 'P/E:' in line or 'Tỷ lệ P/E:' in line:
                    value = line.split(':')[-1].strip()
                    if value != 'N/A' and value != '':
                        try:
                            metrics["pe_ratio"] = float(value)
                        except ValueError:
                            pass
                elif 'P/B:' in line or 'Tỷ lệ P/B:' in line:
                    value = line.split(':')[-1].strip()
                    if value != 'N/A' and value != '':
                        try:
                            metrics["pb_ratio"] = float(value)
                        except ValueError:
                            pass
                elif 'ROE:' in line or 'Tỷ lệ ROE:' in line:
                    value = line.split(':')[-1].strip()
                    if value != 'N/A' and value != '':
                        try:
                            metrics["roe"] = float(value)
                        except ValueError:
                            pass
        except Exception as e:
            self.logger.warning(f"Error extracting fundamental metrics: {e}")
        
        return metrics
    
    def _extract_technical_signals(self, tech_data: str) -> Dict[str, any]:
        """Trích xuất tín hiệu kỹ thuật từ dữ liệu."""
        signals = {
            "rsi": 50.0,
            "macd_signal": "neutral",
            "ma_trend": "sideways",
            "volume_trend": "normal"
        }
        
        try:
            lines = tech_data.split('\n')
            for line in lines:
                line = line.strip().lower()
                
                # RSI
                if 'rsi' in line and ':' in line:
                    try:
                        rsi_value = float(line.split(':')[-1].strip())
                        signals["rsi"] = rsi_value
                    except:
                        pass
                
                # MACD
                if 'macd' in line:
                    if any(word in line for word in ['tích cực', 'positive', 'mua', 'buy']):
                        signals["macd_signal"] = "positive"
                    elif any(word in line for word in ['tiêu cực', 'negative', 'bán', 'sell']):
                        signals["macd_signal"] = "negative"
                
                # Moving Average Trend
                if any(word in line for word in ['xu hướng', 'trend', 'ma']):
                    if any(word in line for word in ['tăng', 'up', 'upward']):
                        signals["ma_trend"] = "upward"
                    elif any(word in line for word in ['giảm', 'down', 'downward']):
                        signals["ma_trend"] = "downward"
                
                # Volume
                if 'volume' in line or 'khối lượng' in line:
                    if any(word in line for word in ['tăng', 'increase', 'cao', 'high']):
                        signals["volume_trend"] = "increasing"
                    elif any(word in line for word in ['giảm', 'decrease', 'thấp', 'low']):
                        signals["volume_trend"] = "decreasing"
        
        except Exception as e:
            self.logger.warning(f"Error extracting technical signals: {e}")
        
        return signals
    
    def _calculate_value_score(self, pb_ratio: float, industry: str) -> float:
        """Tính điểm giá trị dựa trên P/B so với ngành."""
        if pb_ratio is None or pb_ratio <= 0:
            return 5.0  # Neutral score for missing data
        
        # Lấy benchmark của ngành
        benchmark = self.industry_pb_benchmarks.get(industry, self.industry_pb_benchmarks["Default"])
        
        # Tính điểm: P/B thấp hơn benchmark = điểm cao
        if pb_ratio <= benchmark * 0.7:  # Rất rẻ
            return 10.0
        elif pb_ratio <= benchmark * 0.85:  # Rẻ
            return 8.5
        elif pb_ratio <= benchmark:  # Hợp lý
            return 7.0
        elif pb_ratio <= benchmark * 1.2:  # Hơi đắt
            return 5.5
        elif pb_ratio <= benchmark * 1.5:  # Đắt
            return 3.0
        else:  # Rất đắt
            return 1.0
    
    def _calculate_momentum_score(self, signals: Dict[str, any]) -> float:
        """Tính điểm momentum từ các tín hiệu kỹ thuật."""
        score = 5.0  # Base score
        
        # RSI score (30-70 là tốt, <30 quá bán, >70 quá mua)
        rsi = signals.get("rsi", None)
        if rsi is not None:
            if 35 <= rsi <= 65:  # Vùng lành mạnh
                score += 2.0
            elif 30 <= rsi < 35 or 65 < rsi <= 70:  # Gần vùng quá mua/bán
                score += 1.0
            elif rsi < 30:  # Quá bán - có thể là cơ hội
                score += 1.5
            elif rsi > 70:  # Quá mua - rủi ro
                score -= 1.0
        
        # MACD signal
        macd_signal = signals.get("macd_signal", None)
        if macd_signal == "positive":
            score += 2.5
        elif macd_signal == "negative":
            score -= 2.0
        
        # MA Trend
        ma_trend = signals.get("ma_trend", None)
        if ma_trend == "upward":
            score += 2.0
        elif ma_trend == "downward":
            score -= 2.0
        
        # Volume trend
        volume_trend = signals.get("volume_trend", None)
        if volume_trend == "increasing":
            score += 1.5
        elif volume_trend == "decreasing":
            score -= 1.0
        
        return max(0.0, min(10.0, score))
    
    def _calculate_quality_score(self, fundamental_metrics: Dict, technical_signals: Dict) -> float:
        """Tính điểm chất lượng dựa trên độ tin cậy của dữ liệu."""
        score = 5.0
        
        # ROE score
        roe = fundamental_metrics.get("roe", None)
        if roe is not None:
            if roe > 15:  # ROE cao
                score += 2.0
            elif roe > 10:
                score += 1.0
            elif roe < 5:
                score -= 1.0
        
        # P/E reasonable check
        pe = fundamental_metrics.get("pe_ratio", None)
        if pe is not None and pe > 0:
            if 0 < pe < 25:  # P/E hợp lý
                score += 1.5
            elif pe > 50:  # P/E quá cao
                score -= 1.0
        
        # Data completeness - check if we have at least some data
        valid_data_count = sum(1 for v in fundamental_metrics.values() if v is not None and v > 0)
        if valid_data_count >= 2:  # At least 2 valid metrics
            score += 1.0
        
        return max(0.0, min(10.0, score))
    
    def _make_recommendation(self, overall_score: float, value_score: float, momentum_score: float) -> Tuple[str, float]:
        """Đưa ra khuyến nghị dựa trên điểm số."""
        confidence = 0.5  # Base confidence
        
        if overall_score >= 8.5:
            recommendation = "BUY"
            confidence = min(0.95, 0.7 + (overall_score - 8.5) * 0.1)
        elif overall_score >= 7.0:
            if momentum_score >= 7.0:
                recommendation = "BUY"
                confidence = 0.75
            else:
                recommendation = "WATCH"
                confidence = 0.65
        elif overall_score >= 5.5:
            recommendation = "HOLD"
            confidence = 0.55
        elif overall_score >= 4.0:
            recommendation = "WATCH"
            confidence = 0.45
        else:
            recommendation = "SELL"
            confidence = 0.6
        
        return recommendation, confidence
    
    def analyze_single_stock_lightweight(self, symbol: str) -> Optional[LightweightScanResult]:
        """
        Phân tích nhanh một cổ phiếu với token usage tối thiểu.
        
        Args:
            symbol: Mã cổ phiếu
            
        Returns:
            Kết quả phân tích nhẹ hoặc None nếu lỗi
        """
        try:
            start_time = time.time()
            
            # Lấy dữ liệu cơ bản
            if TOOLS_AVAILABLE:
                fund_data = self.fund_tool._run(symbol)
                tech_data = self.tech_tool._run(symbol)
            else:
                # Mock data for testing
                fund_data = f"Mã cổ phiếu: {symbol}\nTỷ lệ P/E: 15.5\nTỷ lệ P/B: 2.1\nTỷ lệ ROE: 12.5"
                tech_data = f"RSI: 58.3\nMACD: tích cực\nXu hướng: tăng\nKhối lượng: tăng"
            
            # Trích xuất metrics
            fundamental_metrics = self._extract_fundamental_metrics(fund_data)
            technical_signals = self._extract_technical_signals(tech_data)
            
            # Xác định ngành (simplified)
            industry = "Default"
            if "real estate" in fund_data.lower() or "bất động sản" in fund_data.lower():
                industry = "Real Estate"
            elif "bank" in fund_data.lower() or "ngân hàng" in fund_data.lower():
                industry = "Banking"
            
            # Tính điểm
            value_score = self._calculate_value_score(fundamental_metrics["pb_ratio"], industry)
            momentum_score = self._calculate_momentum_score(technical_signals)
            quality_score = self._calculate_quality_score(fundamental_metrics, technical_signals)
            
            # Điểm tổng hợp
            overall_score = (
                value_score * self.weights["value"] +
                momentum_score * self.weights["momentum"] +
                quality_score * self.weights["quality"]
            )
            
            # Khuyến nghị
            recommendation, confidence = self._make_recommendation(overall_score, value_score, momentum_score)
            
            # Đánh giá chất lượng dữ liệu
            data_quality = "good"
            if fundamental_metrics["pb_ratio"] == 0 or technical_signals["rsi"] == 50:
                data_quality = "fair"
            if all(v == 0 for v in fundamental_metrics.values()):
                data_quality = "poor"
            
            # Tạo kết quả
            result = LightweightScanResult(
                symbol=symbol,
                company_name=f"Company {symbol}",  # Simplified
                industry=industry,
                current_price=fundamental_metrics.get("current_price", 0),
                pb_ratio=fundamental_metrics["pb_ratio"],
                pe_ratio=fundamental_metrics["pe_ratio"],
                market_cap=fundamental_metrics.get("market_cap", 0),
                rsi=technical_signals["rsi"],
                macd_signal=technical_signals["macd_signal"],
                ma_trend=technical_signals["ma_trend"],
                volume_trend=technical_signals["volume_trend"],
                value_score=value_score,
                momentum_score=momentum_score,
                overall_score=overall_score,
                recommendation=recommendation,
                confidence=confidence,
                scan_time=datetime.now(),
                data_quality=data_quality
            )
            
            scan_time = time.time() - start_time
            self.logger.info(f"✅ {symbol}: {recommendation} (Score: {overall_score:.1f}, Time: {scan_time:.1f}s)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing {symbol}: {e}")
            return None
    
    def scan_stocks_lightweight(self, 
                               stock_list: List[str], 
                               min_score: float = 6.5,
                               only_buy_watch: bool = True,
                               max_results: int = 20) -> List[LightweightScanResult]:
        """
        Quét nhanh danh sách cổ phiếu với token usage tối thiểu.
        
        Args:
            stock_list: Danh sách mã cổ phiếu
            min_score: Điểm tối thiểu để lọc
            only_buy_watch: Chỉ lấy BUY và WATCH
            max_results: Số kết quả tối đa trả về
            
        Returns:
            Danh sách kết quả được sắp xếp theo điểm số
        """
        print(f"🚀 Starting lightweight scan for {len(stock_list)} stocks...")
        print(f"📊 Criteria: min_score={min_score}, only_buy_watch={only_buy_watch}")
        
        results = []
        
        # Parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_single_stock_lightweight, symbol): symbol 
                for symbol in stock_list
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result(timeout=60)  # 1 minute timeout per stock
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"❌ {symbol}: {e}")
        
        # Lọc kết quả
        filtered_results = []
        for result in results:
            # Lọc theo điểm số
            if result.overall_score < min_score:
                continue
            
            # Lọc theo khuyến nghị
            if only_buy_watch and result.recommendation not in ["BUY", "WATCH"]:
                continue
            
            filtered_results.append(result)
        
        # Sắp xếp theo điểm số giảm dần
        filtered_results.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Giới hạn số kết quả
        final_results = filtered_results[:max_results]
        
        print(f"✅ Found {len(final_results)} promising stocks from {len(stock_list)} scanned")
        return final_results
    
    def generate_scan_report(self, results: List[LightweightScanResult]) -> str:
        """Tạo báo cáo scan ngắn gọn."""
        if not results:
            return "📊 **LIGHTWEIGHT SCAN REPORT**\n\nNo stocks found matching criteria."
        
        report = ["📊 **LIGHTWEIGHT SCAN REPORT**"]
        report.append("=" * 50)
        report.append(f"🕒 Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📈 Total stocks found: {len(results)}")
        report.append("")
        
        # Top recommendations
        buy_stocks = [r for r in results if r.recommendation == "BUY"]
        watch_stocks = [r for r in results if r.recommendation == "WATCH"]
        
        if buy_stocks:
            report.append("🟢 **TOP BUY RECOMMENDATIONS:**")
            for stock in buy_stocks[:5]:
                report.append(
                    f"   {stock.symbol}: {stock.overall_score:.1f}/10 "
                    f"(Value: {stock.value_score:.1f}, Momentum: {stock.momentum_score:.1f}, "
                    f"P/B: {stock.pb_ratio:.2f}, RSI: {stock.rsi:.1f})"
                )
            report.append("")
        
        if watch_stocks:
            report.append("🟡 **STOCKS TO WATCH:**")
            for stock in watch_stocks[:3]:
                report.append(
                    f"   {stock.symbol}: {stock.overall_score:.1f}/10 "
                    f"({stock.recommendation}, P/B: {stock.pb_ratio:.2f})"
                )
            report.append("")
        
        # Summary stats
        avg_score = sum(r.overall_score for r in results) / len(results)
        avg_pb = sum(r.pb_ratio for r in results if r.pb_ratio > 0) / len([r for r in results if r.pb_ratio > 0])
        
        report.append("📊 **SUMMARY STATISTICS:**")
        report.append(f"   Average Score: {avg_score:.1f}/10")
        report.append(f"   Average P/B: {avg_pb:.2f}")
        report.append(f"   BUY signals: {len(buy_stocks)}")
        report.append(f"   WATCH signals: {len(watch_stocks)}")
        
        return "\n".join(report)

# Convenience functions
def quick_scan_market(min_score: float = 6.5, max_stocks: int = 30) -> List[LightweightScanResult]:
    """Quét nhanh thị trường để tìm cơ hội."""
    scanner = LightweightStockScanner(max_workers=3)
    stock_list = scanner.get_popular_stocks()[:max_stocks]
    return scanner.scan_stocks_lightweight(stock_list, min_score=min_score)

def scan_custom_list(symbols: List[str], min_score: float = 6.0) -> List[LightweightScanResult]:
    """Quét danh sách cổ phiếu tùy chỉnh."""
    scanner = LightweightStockScanner(max_workers=3)
    return scanner.scan_stocks_lightweight(symbols, min_score=min_score)
