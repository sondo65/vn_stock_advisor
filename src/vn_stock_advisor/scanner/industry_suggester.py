"""
Industry Stock Suggester - Gợi ý cổ phiếu tiềm năng theo ngành

Chức năng chính:
1. Phân tích và so sánh cổ phiếu với benchmark ngành
2. Đánh giá tiềm năng tăng trưởng theo từng ngành
3. Suggest top picks cho từng ngành dựa trên phân tích kỹ thuật và cơ bản
4. Tích hợp với hệ thống scoring hiện có
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

from .lightweight_scanner import LightweightStockScanner, LightweightScanResult
from .screening_engine import ScreeningEngine, ScreeningCriteria
from ..tools.custom_tool import FundDataTool, TechDataTool

class IndustryType(Enum):
    """Các ngành chính trong thị trường chứng khoán Việt Nam"""
    BANKING = "Tài chính ngân hàng"
    SECURITIES = "Chứng khoán và ngân hàng đầu tư"
    INSURANCE = "Bảo hiểm"
    REAL_ESTATE = "Bất động sản"
    INFRASTRUCTURE = "Cơ sở hạ tầng giao thông vận tải"
    CONSTRUCTION = "Xây dựng"
    TRANSPORTATION = "Vận chuyển hành khách"
    HEAVY_MACHINERY = "Máy móc, thiết bị nặng và đóng tàu"
    LOGISTICS = "Vận chuyển hàng hóa và giao nhận"
    FOOD_TOBACCO = "Thực phẩm và thuốc lá"
    RETAIL_FOOD = "Bán lẻ thực phẩm và thuốc"
    BEVERAGES = "Đồ uống"
    PERSONAL_CARE = "Sản phẩm cá nhân, gia dụng"
    TELECOMMUNICATIONS = "Dịch vụ viễn thông"
    TECHNOLOGY = "Phần mềm và dịch vụ công nghệ thông tin"
    MEDIA = "Truyền thông và mạng"
    MINING = "Kim loại và khai khoáng"
    CHEMICALS = "Hóa chất"
    BUILDING_MATERIALS = "Vật liệu xây dựng"
    PAPER_FOREST = "Giấy và lâm sản"
    PACKAGING = "Hộp đựng và bao bì"
    SPECIALTY_RETAIL = "Bán lẻ chuyên dụng"
    AUTOMOTIVE = "Ô tô và phụ tùng ô tô"
    CIVIL_CONSTRUCTION = "Xây dựng và vật liệu xây dựng dân dụng"
    TEXTILES = "Dệt may"
    HOUSEHOLD_GOODS = "Hàng gia dụng"
    PUBLISHING = "Truyền thông và xuất bản"
    HOSPITALITY = "Khách sạn và giải trí"
    OIL_GAS = "Dầu và khí đốt"
    COAL = "Than"
    RENEWABLE_ENERGY = "Năng lượng tái tạo"
    ELECTRICITY = "Ngành điện"
    WATER_UTILITIES = "Ngành cấp thoát nước"
    PHARMACEUTICALS = "Dược phẩm"
    HEALTHCARE_SERVICES = "Dịch vụ chăm sóc sức khỏe"
    MEDICAL_EQUIPMENT = "Thiết bị vật tư y tế"

@dataclass
class IndustryBenchmark:
    """Benchmark cho từng ngành"""
    industry: str
    pe_ratio: float
    pb_ratio: float
    roe: float
    roa: Optional[float] = None
    dividend_yield: Optional[float] = None
    volatility: Optional[str] = None
    beta: Optional[float] = None
    key_metrics: List[str] = field(default_factory=list)
    seasonal_factors: List[str] = field(default_factory=list)
    regulatory_impact: Optional[str] = None

@dataclass
class IndustryStockSuggestion:
    """Gợi ý cổ phiếu cho một ngành"""
    symbol: str
    company_name: str
    industry: str
    
    # Điểm số
    value_score: float          # 0-10, so sánh với benchmark ngành
    momentum_score: float       # 0-10, momentum kỹ thuật
    quality_score: float        # 0-10, chất lượng tài chính
    industry_score: float       # 0-10, vị thế trong ngành
    total_score: float          # 0-10, điểm tổng hợp
    
    # Phân tích chi tiết
    valuation_analysis: str     # Phân tích định giá
    technical_analysis: str     # Phân tích kỹ thuật
    industry_position: str      # Vị thế trong ngành
    growth_potential: str       # Tiềm năng tăng trưởng
    
    # Khuyến nghị
    recommendation: str         # "STRONG_BUY", "BUY", "HOLD", "SELL"
    confidence: float           # 0-1, độ tin cậy
    analysis_date: datetime     # Metadata
    data_quality: str           # Metadata
    target_price: Optional[float] = None
    risk_level: str = "MEDIUM"  # "LOW", "MEDIUM", "HIGH"

class IndustryStockSuggester:
    """Hệ thống gợi ý cổ phiếu theo ngành"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize tools with reduced workers to avoid rate limiting
        self.scanner = LightweightStockScanner(max_workers=1, use_cache=True)
        self.screening_engine = ScreeningEngine()
        self.fund_tool = FundDataTool()
        self.tech_tool = TechDataTool()
        
        # Load industry benchmarks
        self.industry_benchmarks = self._load_industry_benchmarks()
        
        # Industry-specific stock lists
        self.industry_stocks = self._load_industry_stocks()
        
        # Scoring weights for different industries
        self.industry_weights = {
            IndustryType.BANKING: {"value": 0.4, "momentum": 0.3, "quality": 0.3},
            IndustryType.REAL_ESTATE: {"value": 0.35, "momentum": 0.4, "quality": 0.25},
            IndustryType.TECHNOLOGY: {"value": 0.3, "momentum": 0.45, "quality": 0.25},
            IndustryType.MINING: {"value": 0.45, "momentum": 0.35, "quality": 0.2},
            IndustryType.PHARMACEUTICALS: {"value": 0.35, "momentum": 0.35, "quality": 0.3},
            "default": {"value": 0.4, "momentum": 0.35, "quality": 0.25}
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.request_delay = 15.0  # 15 seconds between requests
    
    def _rate_limit(self):
        """Rate limiting to avoid too many API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            self.logger.info(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _load_industry_benchmarks(self) -> Dict[str, IndustryBenchmark]:
        """Load industry benchmarks from JSON files"""
        benchmarks = {}
        
        try:
            # Load from PE_PB_industry_average.json
            with open("knowledge/PE_PB_industry_average.json", "r", encoding="utf-8") as f:
                pe_pb_data = json.load(f)
            
            # Load from enhanced_industry_benchmarks.json if available
            enhanced_data = {}
            try:
                with open("knowledge/enhanced_industry_benchmarks.json", "r", encoding="utf-8") as f:
                    enhanced_data = json.load(f)
            except FileNotFoundError:
                self.logger.warning("Enhanced industry benchmarks not found, using basic data")
            
            # Create benchmark objects
            for industry_name, data in pe_pb_data["data"].items():
                enhanced_info = enhanced_data.get("industries", {}).get(industry_name, {})
                
                benchmark = IndustryBenchmark(
                    industry=industry_name,
                    pe_ratio=data["PE"],
                    pb_ratio=data["PB"],
                    roe=enhanced_info.get("ROE", 12.0),
                    roa=enhanced_info.get("ROA"),
                    dividend_yield=enhanced_info.get("dividend_yield"),
                    volatility=enhanced_info.get("volatility"),
                    beta=enhanced_info.get("beta"),
                    key_metrics=enhanced_info.get("key_metrics", []),
                    seasonal_factors=enhanced_info.get("seasonal_factors", []),
                    regulatory_impact=enhanced_info.get("regulatory_impact")
                )
                benchmarks[industry_name] = benchmark
                
        except Exception as e:
            self.logger.error(f"Error loading industry benchmarks: {e}")
            # Fallback to default benchmarks
            benchmarks = self._get_default_benchmarks()
        
        return benchmarks
    
    def _get_default_benchmarks(self) -> Dict[str, IndustryBenchmark]:
        """Fallback default benchmarks"""
        return {
            "Tài chính ngân hàng": IndustryBenchmark(
                industry="Tài chính ngân hàng",
                pe_ratio=7.93,
                pb_ratio=1.32,
                roe=16.8,
                volatility="low",
                beta=0.85
            ),
            "Bất động sản": IndustryBenchmark(
                industry="Bất động sản",
                pe_ratio=19.94,
                pb_ratio=1.90,
                roe=9.5,
                volatility="high",
                beta=1.2
            ),
            "Phần mềm và dịch vụ công nghệ thông tin": IndustryBenchmark(
                industry="Phần mềm và dịch vụ công nghệ thông tin",
                pe_ratio=20.60,
                pb_ratio=5.16,
                roe=15.0,
                volatility="high",
                beta=1.3
            )
        }
    
    def _load_industry_stocks(self) -> Dict[str, List[str]]:
        """Load stock lists by industry"""
        return {
            "Tài chính ngân hàng": [
                'VCB', 'BID', 'CTG', 'TCB', 'MBB', 'ACB', 'TPB', 'STB', 'EIB', 'HDB'
            ],
            "Bất động sản": [
                'VIC', 'VHM', 'VRE', 'KDH', 'DXG', 'PDR', 'NVL', 'HDG', 'CEO', 'IJC'
            ],
            "Phần mềm và dịch vụ công nghệ thông tin": [
                'FPT', 'CMG', 'ELC', 'ITD', 'SAM', 'VGI', 'VNG', 'TMA', 'GTS', 'VTI'
            ],
            "Kim loại và khai khoáng": [
                'HPG', 'HSG', 'NKG', 'SMC', 'DPM', 'DCM', 'VGC', 'DGC', 'GMD', 'VPI'
            ],
            "Dược phẩm": [
                'DHG', 'DP3', 'PME', 'TNH', 'DBD', 'IMP', 'DCL', 'PMG', 'DHT', 'DVP'
            ],
            "Thực phẩm và thuốc lá": [
                'VNM', 'MSN', 'SAB', 'KDC', 'VCF', 'LSS', 'QNS', 'VHC', 'ANV', 'BAL'
            ],
            "Dầu và khí đốt": [
                'GAS', 'PLX', 'PVS', 'PVC', 'BSR', 'OIL', 'PVD', 'PVB', 'PXS', 'PSH'
            ],
            "Ngành điện": [
                'POW', 'GEG', 'NT2', 'PC1', 'SJD', 'QTP', 'BTP', 'SBA', 'GEG', 'PPC'
            ]
        }
    
    def suggest_stocks_by_industry(self, 
                                 industry: str, 
                                 max_stocks: int = 10,
                                 min_score: float = 7.0,
                                 include_analysis: bool = True) -> List[IndustryStockSuggestion]:
        """
        Gợi ý cổ phiếu tiềm năng cho một ngành cụ thể
        
        Args:
            industry: Tên ngành
            max_stocks: Số lượng cổ phiếu tối đa
            min_score: Điểm tối thiểu
            include_analysis: Có bao gồm phân tích chi tiết không
            
        Returns:
            Danh sách gợi ý cổ phiếu được sắp xếp theo điểm số
        """
        self.logger.info(f"Suggesting stocks for industry: {industry}")
        
        # Get stocks in the industry
        industry_stocks = self.industry_stocks.get(industry, [])
        if not industry_stocks:
            self.logger.warning(f"No stocks found for industry: {industry}")
            return []
        
        # Get industry benchmark
        benchmark = self.industry_benchmarks.get(industry)
        if not benchmark:
            self.logger.warning(f"No benchmark found for industry: {industry}")
            benchmark = self.industry_benchmarks.get("Tài chính ngân hàng")  # Fallback
        
        suggestions = []
        candidates = []  # keep best efforts even if below min_score
        
        # Analyze stocks with controlled attempts, stop when enough suggestions are found
        suggestions = []
        attempts = 0
        # Allow up to 5x the requested stocks, capped to 10, to find valid picks
        max_attempts = min(len(industry_stocks), max(max_stocks * 5, max_stocks), 10)
        for symbol in industry_stocks:
            if len(suggestions) >= max_stocks or attempts >= max_attempts:
                break
            attempts += 1
            try:
                suggestion = self._analyze_stock_for_industry(
                    symbol, industry, benchmark, include_analysis
                )
                if suggestion:
                    candidates.append(suggestion)
                    if suggestion.total_score >= min_score:
                        suggestions.append(suggestion)
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {e}")
                continue

        # If not enough suggestions meet min_score, backfill from best candidates
        if len(suggestions) < max_stocks and candidates:
            # sort candidates by total_score desc
            candidates_sorted = sorted(candidates, key=lambda x: x.total_score, reverse=True)
            picked_symbols = set(s.symbol for s in suggestions)
            for cand in candidates_sorted:
                if len(suggestions) >= max_stocks:
                    break
                if cand.symbol in picked_symbols:
                    continue
                suggestions.append(cand)
                picked_symbols.add(cand.symbol)
        
        # Sort by total score and return top picks
        suggestions.sort(key=lambda x: x.total_score, reverse=True)
        return suggestions[:max_stocks]
    
    def _analyze_stock_for_industry(self, 
                                  symbol: str, 
                                  industry: str, 
                                  benchmark: IndustryBenchmark,
                                  include_analysis: bool) -> Optional[IndustryStockSuggestion]:
        """Phân tích một cổ phiếu cho ngành cụ thể"""
        try:
            # Rate limiting
            self._rate_limit()
            
            # Get lightweight scan result
            scan_result = self.scanner.analyze_single_stock_lightweight(symbol)
            if not scan_result:
                return None
            
            # Calculate industry-specific scores
            value_score = self._calculate_industry_value_score(scan_result, benchmark)
            momentum_score = self._calculate_industry_momentum_score(scan_result)
            quality_score = self._calculate_industry_quality_score(scan_result, benchmark)
            industry_score = self._calculate_industry_position_score(scan_result, benchmark)
            
            # Get industry-specific weights
            weights = self.industry_weights.get(industry, self.industry_weights["default"])
            
            # Calculate total score
            total_score = (
                value_score * weights["value"] +
                momentum_score * weights["momentum"] +
                quality_score * weights["quality"]
            )
            
            # Generate analysis if requested
            valuation_analysis = ""
            technical_analysis = ""
            industry_position = ""
            growth_potential = ""
            
            if include_analysis:
                valuation_analysis = self._generate_valuation_analysis(scan_result, benchmark)
                technical_analysis = self._generate_technical_analysis(scan_result)
                industry_position = self._generate_industry_position_analysis(scan_result, benchmark)
                growth_potential = self._generate_growth_potential_analysis(scan_result, benchmark)
            
            # Make recommendation
            recommendation, confidence = self._make_industry_recommendation(
                total_score, value_score, momentum_score, quality_score
            )
            
            # Calculate target price
            target_price = self._calculate_target_price(scan_result, benchmark)
            
            # Determine risk level
            risk_level = self._determine_risk_level(scan_result, benchmark)
            
            return IndustryStockSuggestion(
                symbol=symbol,
                company_name=getattr(scan_result, 'company_name', symbol),
                industry=industry,
                value_score=value_score,
                momentum_score=momentum_score,
                quality_score=quality_score,
                industry_score=industry_score,
                total_score=total_score,
                valuation_analysis=valuation_analysis,
                technical_analysis=technical_analysis,
                industry_position=industry_position,
                growth_potential=growth_potential,
                recommendation=recommendation,
                confidence=confidence,
                target_price=target_price,
                risk_level=risk_level,
                analysis_date=datetime.now(),
                data_quality=scan_result.data_quality
            )
            
        except Exception as e:
            self.logger.error(f"Error in industry analysis for {symbol}: {e}")
            return None
    
    def _calculate_industry_value_score(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> float:
        """Tính điểm định giá so với benchmark ngành"""
        score = 0.0
        
        # P/B comparison
        if scan_result.pb_ratio > 0:
            pb_ratio = scan_result.pb_ratio / benchmark.pb_ratio
            if pb_ratio <= 0.7:  # Undervalued
                score += 4.0
            elif pb_ratio <= 0.9:  # Fairly valued
                score += 3.0
            elif pb_ratio <= 1.1:  # Slightly overvalued
                score += 2.0
            else:  # Overvalued
                score += 1.0
        
        # P/E comparison
        if scan_result.pe_ratio > 0:
            pe_ratio = scan_result.pe_ratio / benchmark.pe_ratio
            if pe_ratio <= 0.8:  # Undervalued
                score += 3.0
            elif pe_ratio <= 1.0:  # Fairly valued
                score += 2.5
            elif pe_ratio <= 1.2:  # Slightly overvalued
                score += 2.0
            else:  # Overvalued
                score += 1.0
        
        # Market cap consideration
        if scan_result.market_cap > 0:
            if scan_result.market_cap > 10000000000000:  # > 10T VND
                score += 1.0  # Large cap premium
            elif scan_result.market_cap > 1000000000000:  # > 1T VND
                score += 0.5  # Mid cap
        
        return min(score, 10.0)
    
    def _calculate_industry_momentum_score(self, scan_result: LightweightScanResult) -> float:
        """Tính điểm momentum kỹ thuật"""
        score = 0.0
        
        # RSI analysis
        if scan_result.rsi > 0:
            if 30 <= scan_result.rsi <= 40:  # Oversold, potential bounce
                score += 3.0
            elif 40 < scan_result.rsi <= 60:  # Neutral, good for entry
                score += 2.5
            elif 60 < scan_result.rsi <= 70:  # Strong momentum
                score += 2.0
            elif scan_result.rsi > 70:  # Overbought
                score += 1.0
        
        # MACD signal
        if scan_result.macd_signal == "positive":
            score += 2.5
        elif scan_result.macd_signal == "neutral":
            score += 1.5
        else:
            score += 0.5
        
        # MA trend
        if scan_result.ma_trend == "upward":
            score += 2.5
        elif scan_result.ma_trend == "sideways":
            score += 1.5
        else:
            score += 0.5
        
        # Volume trend
        if scan_result.volume_trend == "increasing":
            score += 2.0
        elif scan_result.volume_trend == "normal":
            score += 1.0
        
        return min(score, 10.0)
    
    def _calculate_industry_quality_score(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> float:
        """Tính điểm chất lượng tài chính"""
        score = 0.0
        
        # ROE comparison with industry
        if hasattr(scan_result, 'roe') and scan_result.roe > 0:
            roe_ratio = scan_result.roe / benchmark.roe
            if roe_ratio >= 1.2:  # Above industry average
                score += 3.0
            elif roe_ratio >= 1.0:  # At industry average
                score += 2.5
            elif roe_ratio >= 0.8:  # Below but acceptable
                score += 2.0
            else:  # Poor ROE
                score += 1.0
        
        # Data quality
        if scan_result.data_quality == "good":
            score += 2.0
        elif scan_result.data_quality == "fair":
            score += 1.5
        else:
            score += 1.0
        
        # Market cap stability
        if scan_result.market_cap > 5000000000000:  # > 5T VND
            score += 2.0
        elif scan_result.market_cap > 1000000000000:  # > 1T VND
            score += 1.5
        else:
            score += 1.0
        
        # Price stability (simplified)
        if scan_result.current_price > 10000:  # Above 10k VND
            score += 1.5
        elif scan_result.current_price > 5000:  # Above 5k VND
            score += 1.0
        else:
            score += 0.5
        
        return min(score, 10.0)
    
    def _calculate_industry_position_score(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> float:
        """Tính điểm vị thế trong ngành"""
        score = 5.0  # Base score
        
        # Market cap ranking (simplified)
        if scan_result.market_cap > 20000000000000:  # > 20T VND - Large cap leader
            score += 2.0
        elif scan_result.market_cap > 10000000000000:  # > 10T VND - Large cap
            score += 1.5
        elif scan_result.market_cap > 5000000000000:  # > 5T VND - Mid cap
            score += 1.0
        
        # Valuation attractiveness
        if scan_result.pb_ratio > 0 and scan_result.pb_ratio < benchmark.pb_ratio * 0.8:
            score += 1.5  # Undervalued
        elif scan_result.pb_ratio < benchmark.pb_ratio:
            score += 1.0  # Fairly valued
        
        return min(score, 10.0)
    
    def _generate_valuation_analysis(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> str:
        """Tạo phân tích định giá"""
        analysis = []
        
        # P/B analysis
        if scan_result.pb_ratio > 0:
            pb_ratio = scan_result.pb_ratio / benchmark.pb_ratio
            if pb_ratio <= 0.7:
                analysis.append(f"P/B {scan_result.pb_ratio:.2f} thấp hơn {benchmark.pb_ratio:.2f} của ngành, cổ phiếu bị định giá thấp")
            elif pb_ratio <= 1.0:
                analysis.append(f"P/B {scan_result.pb_ratio:.2f} tương đương ngành, định giá hợp lý")
            else:
                analysis.append(f"P/B {scan_result.pb_ratio:.2f} cao hơn ngành, cần thận trọng")
        
        # P/E analysis
        if scan_result.pe_ratio > 0:
            pe_ratio = scan_result.pe_ratio / benchmark.pe_ratio
            if pe_ratio <= 0.8:
                analysis.append(f"P/E {scan_result.pe_ratio:.1f} thấp hơn ngành, tiềm năng tăng giá")
            elif pe_ratio <= 1.2:
                analysis.append(f"P/E {scan_result.pe_ratio:.1f} phù hợp với ngành")
            else:
                analysis.append(f"P/E {scan_result.pe_ratio:.1f} cao hơn ngành")
        
        return ". ".join(analysis) if analysis else "Cần thêm dữ liệu để phân tích định giá"
    
    def _generate_technical_analysis(self, scan_result: LightweightScanResult) -> str:
        """Tạo phân tích kỹ thuật"""
        analysis = []
        
        # RSI analysis
        if scan_result.rsi > 0:
            if scan_result.rsi <= 30:
                analysis.append("RSI quá bán, cơ hội mua vào")
            elif scan_result.rsi <= 40:
                analysis.append("RSI gần quá bán, có thể cân nhắc")
            elif scan_result.rsi <= 60:
                analysis.append("RSI ở vùng trung tính, tín hiệu tích cực")
            elif scan_result.rsi <= 70:
                analysis.append("RSI mạnh, momentum tốt")
            else:
                analysis.append("RSI quá mua, cần thận trọng")
        
        # MACD analysis
        if scan_result.macd_signal == "positive":
            analysis.append("MACD tích cực, xu hướng tăng")
        elif scan_result.macd_signal == "negative":
            analysis.append("MACD tiêu cực, cần theo dõi")
        else:
            analysis.append("MACD trung tính")
        
        # Trend analysis
        if scan_result.ma_trend == "upward":
            analysis.append("Xu hướng tăng rõ ràng")
        elif scan_result.ma_trend == "downward":
            analysis.append("Xu hướng giảm, cần thận trọng")
        else:
            analysis.append("Xu hướng đi ngang")
        
        # Volume analysis
        if scan_result.volume_trend == "increasing":
            analysis.append("Khối lượng tăng, xác nhận xu hướng")
        elif scan_result.volume_trend == "decreasing":
            analysis.append("Khối lượng giảm, cần theo dõi")
        
        return ". ".join(analysis) if analysis else "Tín hiệu kỹ thuật trung tính"
    
    def _generate_industry_position_analysis(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> str:
        """Tạo phân tích vị thế ngành"""
        analysis = []
        
        # Market cap analysis
        if scan_result.market_cap > 20000000000000:  # > 20T
            analysis.append("Cổ phiếu blue-chip, vị thế dẫn đầu ngành")
        elif scan_result.market_cap > 10000000000000:  # > 10T
            analysis.append("Cổ phiếu lớn, vị thế ổn định")
        elif scan_result.market_cap > 5000000000000:  # > 5T
            analysis.append("Cổ phiếu tầm trung, có tiềm năng tăng trưởng")
        else:
            analysis.append("Cổ phiếu nhỏ, rủi ro cao nhưng tiềm năng lớn")
        
        # Competitive position
        if scan_result.pb_ratio > 0 and scan_result.pb_ratio < benchmark.pb_ratio:
            analysis.append("Định giá hấp dẫn so với ngành")
        elif scan_result.pb_ratio > benchmark.pb_ratio * 1.2:
            analysis.append("Định giá cao so với ngành")
        
        return ". ".join(analysis) if analysis else "Vị thế trung bình trong ngành"
    
    def _generate_growth_potential_analysis(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> str:
        """Tạo phân tích tiềm năng tăng trưởng"""
        analysis = []
        
        # ROE analysis
        if hasattr(scan_result, 'roe') and scan_result.roe > 0:
            if scan_result.roe > benchmark.roe * 1.2:
                analysis.append("ROE vượt trội so với ngành, hiệu quả kinh doanh tốt")
            elif scan_result.roe > benchmark.roe:
                analysis.append("ROE trên trung bình ngành")
            else:
                analysis.append("ROE cần cải thiện")
        
        # Market cap growth potential
        if scan_result.market_cap < 10000000000000:  # < 10T
            analysis.append("Tiềm năng tăng trưởng vốn hóa lớn")
        
        # Technical momentum
        if scan_result.macd_signal == "positive" and scan_result.ma_trend == "upward":
            analysis.append("Momentum kỹ thuật tích cực, hỗ trợ tăng trưởng")
        
        return ". ".join(analysis) if analysis else "Tiềm năng tăng trưởng trung bình"
    
    def _make_industry_recommendation(self, total_score: float, value_score: float, 
                                    momentum_score: float, quality_score: float) -> Tuple[str, float]:
        """Tạo khuyến nghị dựa trên điểm số"""
        if total_score >= 8.5:
            recommendation = "STRONG_BUY"
            confidence = min(0.9, 0.6 + (total_score - 8.5) * 0.1)
        elif total_score >= 7.5:
            recommendation = "BUY"
            confidence = min(0.8, 0.5 + (total_score - 7.5) * 0.1)
        elif total_score >= 6.5:
            recommendation = "HOLD"
            confidence = min(0.7, 0.4 + (total_score - 6.5) * 0.1)
        elif total_score >= 5.0:
            recommendation = "WATCH"
            confidence = min(0.6, 0.3 + (total_score - 5.0) * 0.1)
        else:
            recommendation = "SELL"
            confidence = 0.3
        
        # Adjust confidence based on score consistency
        score_variance = abs(value_score - momentum_score) + abs(momentum_score - quality_score)
        if score_variance < 1.0:  # Consistent scores
            confidence += 0.1
        elif score_variance > 3.0:  # Inconsistent scores
            confidence -= 0.1
        
        confidence = max(0.1, min(0.95, confidence))
        
        return recommendation, confidence
    
    def _calculate_target_price(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> Optional[float]:
        """Tính giá mục tiêu"""
        if scan_result.current_price <= 0:
            return None
        
        # Simple target price calculation based on P/B normalization
        if scan_result.pb_ratio > 0 and benchmark.pb_ratio > 0:
            target_pb = benchmark.pb_ratio * 0.9  # 90% of industry average
            target_price = scan_result.current_price * (target_pb / scan_result.pb_ratio)
            return round(target_price, 0)
        
        return None
    
    def _determine_risk_level(self, scan_result: LightweightScanResult, benchmark: IndustryBenchmark) -> str:
        """Xác định mức độ rủi ro"""
        risk_score = 0
        
        # Market cap risk
        if scan_result.market_cap < 1000000000000:  # < 1T
            risk_score += 2
        elif scan_result.market_cap < 5000000000000:  # < 5T
            risk_score += 1
        
        # Valuation risk
        if scan_result.pb_ratio > benchmark.pb_ratio * 1.5:
            risk_score += 2
        elif scan_result.pb_ratio > benchmark.pb_ratio * 1.2:
            risk_score += 1
        
        # Technical risk
        if scan_result.rsi > 80 or scan_result.rsi < 20:
            risk_score += 1
        
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_available_industries(self) -> List[str]:
        """Lấy danh sách các ngành có sẵn"""
        return list(self.industry_stocks.keys())
    
    def get_industry_summary(self, industry: str) -> Dict[str, Any]:
        """Lấy tóm tắt thông tin ngành"""
        benchmark = self.industry_benchmarks.get(industry)
        stocks = self.industry_stocks.get(industry, [])
        
        if not benchmark:
            return {"error": f"Industry {industry} not found"}
        
        return {
            "industry": industry,
            "benchmark": {
                "pe_ratio": benchmark.pe_ratio,
                "pb_ratio": benchmark.pb_ratio,
                "roe": benchmark.roe,
                "volatility": benchmark.volatility,
                "beta": benchmark.beta
            },
            "stock_count": len(stocks),
            "stocks": stocks[:10],  # Top 10 stocks
            "key_metrics": benchmark.key_metrics,
            "seasonal_factors": benchmark.seasonal_factors,
            "regulatory_impact": benchmark.regulatory_impact
        }
