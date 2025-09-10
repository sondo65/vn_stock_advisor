import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
from collections import deque
import math
import pandas as pd

import aiosqlite
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    Defaults,
    JobQueue,
)
from telegram.request import HTTPXRequest
from telegram.error import TimedOut

# Import P/E Calculator
try:
    from src.vn_stock_advisor.tools.pe_calculator import PECalculator
    PE_CALCULATOR_AVAILABLE = True
except ImportError:
    PE_CALCULATOR_AVAILABLE = False
    print("Warning: P/E Calculator not available in Telegram bot")

# Import Market Analysis
try:
    from src.vn_stock_advisor.market_analysis.daily_market_report import get_daily_market_report_message
    MARKET_ANALYSIS_AVAILABLE = True
except ImportError:
    MARKET_ANALYSIS_AVAILABLE = False
    print("Warning: Market Analysis not available in Telegram bot")


load_dotenv()


_env_db = os.getenv("TELEGRAM_PORTFOLIO_DB")
DB_PATH = (
    _env_db if (_env_db is not None and _env_db.strip() != "") else os.path.join(os.path.dirname(__file__), "portfolio.sqlite3")
)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_CHAT_ID = os.getenv("DEFAULT_CHAT_ID")
# Test mode: if set to 1, schedule tracking every minute and send status every minute
TEST_EVERY_MINUTE = os.getenv("TRACKING_TEST_MINUTE", "0") == "1"

# Market Analysis API Keys
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Vietnam timezone for all scheduling
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class MarketData:
    @staticmethod
    async def get_price(symbol: str) -> Optional[float]:
        """Fetch latest price for a symbol. Try real-time first, then fallback to historical.

        Default implementation tries vnstock real-time quote first, then historical data.
        """
        # First try real-time quote from vnstock
        try:
            from vnstock import Vnstock

            for source in ("VCI", "TCBS", "DNSE", "SSI"):
                try:
                    stock = Vnstock().stock(symbol=symbol, source=source)
                    # Try to get real-time quote
                    try:
                        quote_data = stock.quote.live()
                        if quote_data is not None and not quote_data.empty:
                            # Try different price columns
                            for price_col in ["price", "lastPrice", "close", "currentPrice"]:
                                if price_col in quote_data.columns:
                                    price_val = quote_data[price_col].iloc[0]
                                    if price_val is not None and not pd.isna(price_val):
                                        return float(price_val)
                    except Exception:
                        # If live() fails, try quote() method
                        try:
                            quote_data = stock.quote()
                            if quote_data is not None and not quote_data.empty:
                                for price_col in ["price", "lastPrice", "close", "currentPrice"]:
                                    if price_col in quote_data.columns:
                                        price_val = quote_data[price_col].iloc[0]
                                        if price_val is not None and not pd.isna(price_val):
                                            return float(price_val)
                        except Exception:
                            pass
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback to historical data (last trading day)
        try:
            from vnstock import Vnstock

            today = datetime.now().date()
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            for source in ("VCI", "TCBS", "DNSE", "SSI"):
                try:
                    stock = Vnstock().stock(symbol=symbol, source=source)
                    price_df = stock.quote.history(
                        start=start_date,
                        end=end_date,
                        interval="1D",
                    )
                    if price_df is not None and not price_df.empty:
                        # use last non-null close
                        closes = price_df["close"].dropna()
                        if not closes.empty:
                            return float(closes.iloc[-1])
                except Exception:
                    continue
        except Exception:
            pass

        # Final fallback to legacy helper stock_historical_data
        try:
            from vnstock import stock_historical_data

            today = datetime.now().date()
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            data = stock_historical_data(
                symbol=symbol,
                start=start_date,
                end=end_date,
                resolution="1D",
            )
            if data is None or len(data) == 0:
                return None
            last_close = None
            for idx in range(len(data) - 1, -1, -1):
                try:
                    val = float(data.iloc[idx]["close"])  # type: ignore[index]
                    last_close = val
                    break
                except Exception:
                    continue
            if last_close is None:
                return None
            return last_close
        except Exception:
            return None


class PredictionDecision(str, Enum):
    BUY_MORE = "BUY_MORE"
    HOLD = "HOLD"
    SELL = "SELL"


class InvestmentStyle(str, Enum):
    SHORT_TERM = "SHORT_TERM"  # Trading T+, 1-2 weeks
    MEDIUM_TERM = "MEDIUM_TERM"  # 1-6 months
    LONG_TERM = "LONG_TERM"  # 6+ months, value investing


class PredictionResult(BaseModel):
    symbol: str
    decision: PredictionDecision
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: Optional[str] = None
    scenarios: Optional[Dict[str, float]] = None  # Kịch bản với xác suất
    technical_signals: Optional[Dict[str, Any]] = None  # Tín hiệu kỹ thuật
    investment_style: Optional[InvestmentStyle] = None  # Phong cách đầu tư
    timeframe: Optional[str] = None  # Khung thời gian phân tích


class TechnicalIndicators:
    """Tính toán các chỉ báo kỹ thuật từ dữ liệu giá lịch sử."""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return [None] * len(prices)
        
        sma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                sma_values.append(None)
            else:
                sma_values.append(sum(prices[i-period+1:i+1]) / period)
        return sma_values
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return [None] * len(prices)
        
        multiplier = 2 / (period + 1)
        ema_values = [None] * len(prices)
        ema_values[period-1] = sum(prices[:period]) / period
        
        for i in range(period, len(prices)):
            ema_values[i] = (prices[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        rsi_values = [None] * len(prices)
        gains = []
        losses = []
        
        # Tính thay đổi giá
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        # Tính RSI cho từng điểm
        for i in range(period, len(prices)):
            avg_gain = sum(gains[i-period:i]) / period
            avg_loss = sum(losses[i-period:i]) / period
            
            if avg_loss == 0:
                rsi_values[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100 - (100 / (1 + rs))
        
        return rsi_values
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        
        macd_line = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line.append(ema_fast[i] - ema_slow[i])
            else:
                macd_line.append(None)
        
        # Signal line (EMA của MACD line)
        macd_values = [x for x in macd_line if x is not None]
        if len(macd_values) >= signal:
            signal_line = TechnicalIndicators.ema(macd_values, signal)
            # Pad với None để match length
            signal_line = [None] * (len(macd_line) - len(signal_line)) + signal_line
        else:
            signal_line = [None] * len(macd_line)
        
        # Histogram
        histogram = []
        for i in range(len(macd_line)):
            if macd_line[i] is not None and i < len(signal_line) and signal_line[i] is not None:
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(None)
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, List[float]]:
        """Bollinger Bands"""
        sma_values = TechnicalIndicators.sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if sma_values[i] is not None and i >= period - 1:
                # Tính độ lệch chuẩn
                period_prices = prices[i-period+1:i+1]
                mean = sma_values[i]
                variance = sum((x - mean) ** 2 for x in period_prices) / period
                std = math.sqrt(variance)
                
                upper_band.append(mean + (std_dev * std))
                lower_band.append(mean - (std_dev * std))
            else:
                upper_band.append(None)
                lower_band.append(None)
        
        return {
            'upper': upper_band,
            'middle': sma_values,
            'lower': lower_band
        }
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float]:
        """Average True Range"""
        if len(highs) < period + 1:
            return [None] * len(highs)
        
        true_ranges = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        atr_values = [None] * len(highs)
        for i in range(period, len(highs)):
            atr_values[i] = sum(true_ranges[i-period:i]) / period
        
        return atr_values


class PredictionEngine:
    @staticmethod
    def get_data_period_for_style(style: InvestmentStyle) -> int:
        """Get the number of days to fetch data based on investment style."""
        if style == InvestmentStyle.SHORT_TERM:
            return 90  # 3 months for short-term trading
        elif style == InvestmentStyle.MEDIUM_TERM:
            return 365  # 1 year for medium-term
        else:  # LONG_TERM
            return 1095  # 3 years for long-term value investing
    
    @staticmethod
    def get_indicators_for_style(style: InvestmentStyle) -> Dict[str, int]:
        """Get technical indicator periods based on investment style."""
        if style == InvestmentStyle.SHORT_TERM:
            return {
                'sma_short': 5, 'sma_medium': 10, 'sma_long': 20,
                'ema_short': 5, 'ema_medium': 10, 'ema_long': 20,
                'rsi_period': 14, 'macd_fast': 8, 'macd_slow': 17, 'macd_signal': 9,
                'bb_period': 20, 'bb_std': 2, 'atr_period': 14
            }
        elif style == InvestmentStyle.MEDIUM_TERM:
            return {
                'sma_short': 20, 'sma_medium': 50, 'sma_long': 100,
                'ema_short': 20, 'ema_medium': 50, 'ema_long': 100,
                'rsi_period': 14, 'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
                'bb_period': 20, 'bb_std': 2, 'atr_period': 14
            }
        else:  # LONG_TERM
            return {
                'sma_short': 50, 'sma_medium': 100, 'sma_long': 200,
                'ema_short': 50, 'ema_medium': 100, 'ema_long': 200,
                'rsi_period': 21, 'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
                'bb_period': 50, 'bb_std': 2, 'atr_period': 21
            }

    @staticmethod
    async def get_historical_data(symbol: str, days: int = 60) -> Optional[Dict[str, List[float]]]:
        """Lấy dữ liệu lịch sử từ vnstock"""
        try:
            from vnstock import Vnstock
            
            today = datetime.now().date()
            start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            
            # Thử các nguồn dữ liệu khác nhau
            for source in ("VCI", "TCBS", "DNSE", "SSI"):
                try:
                    stock = Vnstock().stock(symbol=symbol, source=source)
                    df = stock.quote.history(
                        start=start_date,
                        end=end_date,
                        interval="1D",
                    )
                    if df is not None and not df.empty and len(df) >= 20:
                        return {
                            'close': df['close'].tolist(),
                            'high': df['high'].tolist(),
                            'low': df['low'].tolist(),
                            'volume': df['volume'].tolist(),
                            'time': df['time'].tolist()
                        }
                except Exception:
                    continue
            
            # Fallback to legacy method
            from vnstock import stock_historical_data
            df = stock_historical_data(
                symbol=symbol,
                start=start_date,
                end=end_date,
                resolution="1D",
            )
            if df is not None and len(df) >= 20:
                return {
                    'close': df['close'].tolist(),
                    'high': df['high'].tolist(),
                    'low': df['low'].tolist(),
                    'volume': df['volume'].tolist(),
                    'time': df['time'].tolist() if 'time' in df.columns else []
                }
        except Exception:
            pass
        return None
    
    @staticmethod
    def analyze_technical_signals(data: Dict[str, List[float]], style: InvestmentStyle = InvestmentStyle.MEDIUM_TERM) -> Dict[str, Any]:
        """Phân tích tín hiệu kỹ thuật từ dữ liệu giá theo phong cách đầu tư"""
        closes = data['close']
        highs = data['high']
        lows = data['low']
        volumes = data['volume']
        
        if len(closes) < 20:
            return {}
        
        # Lấy thông số chỉ báo theo phong cách đầu tư
        indicators = PredictionEngine.get_indicators_for_style(style)
        
        # Tính các chỉ báo
        sma_short = TechnicalIndicators.sma(closes, indicators['sma_short'])
        sma_medium = TechnicalIndicators.sma(closes, indicators['sma_medium'])
        sma_long = TechnicalIndicators.sma(closes, indicators['sma_long'])
        ema_short = TechnicalIndicators.ema(closes, indicators['ema_short'])
        ema_medium = TechnicalIndicators.ema(closes, indicators['ema_medium'])
        ema_long = TechnicalIndicators.ema(closes, indicators['ema_long'])
        rsi = TechnicalIndicators.rsi(closes, indicators['rsi_period'])
        macd_data = TechnicalIndicators.macd(closes, indicators['macd_fast'], indicators['macd_slow'], indicators['macd_signal'])
        bb_data = TechnicalIndicators.bollinger_bands(closes, indicators['bb_period'], indicators['bb_std'])
        atr = TechnicalIndicators.atr(highs, lows, closes, indicators['atr_period'])
        
        # Lấy giá trị cuối cùng
        current_price = closes[-1]
        sma_short_val = sma_short[-1] if sma_short[-1] is not None else None
        sma_medium_val = sma_medium[-1] if sma_medium[-1] is not None else None
        sma_long_val = sma_long[-1] if sma_long[-1] is not None else None
        ema_short_val = ema_short[-1] if ema_short[-1] is not None else None
        ema_medium_val = ema_medium[-1] if ema_medium[-1] is not None else None
        ema_long_val = ema_long[-1] if ema_long[-1] is not None else None
        rsi_val = rsi[-1] if rsi[-1] is not None else None
        macd_val = macd_data['macd'][-1] if macd_data['macd'][-1] is not None else None
        signal_val = macd_data['signal'][-1] if macd_data['signal'][-1] is not None else None
        bb_upper = bb_data['upper'][-1] if bb_data['upper'][-1] is not None else None
        bb_lower = bb_data['lower'][-1] if bb_data['lower'][-1] is not None else None
        atr_val = atr[-1] if atr[-1] is not None else None
        
        # Phân tích tín hiệu
        signals = {
            'current_price': current_price,
            'sma_short': sma_short_val,
            'sma_medium': sma_medium_val,
            'sma_long': sma_long_val,
            'ema_short': ema_short_val,
            'ema_medium': ema_medium_val,
            'ema_long': ema_long_val,
            'rsi': rsi_val,
            'macd': macd_val,
            'macd_signal': signal_val,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'atr': atr_val,
            'volume_avg': sum(volumes[-10:]) / 10 if len(volumes) >= 10 else None,
            'volume_current': volumes[-1] if volumes else None,
            'investment_style': style.value
        }
        
        return signals
    
    @staticmethod
    def generate_scenarios(signals: Dict[str, Any]) -> Dict[str, float]:
        """Tạo các kịch bản dự đoán với xác suất"""
        current_price = signals.get('current_price', 0)
        sma_short = signals.get('sma_short')
        sma_medium = signals.get('sma_medium')
        sma_long = signals.get('sma_long')
        rsi = signals.get('rsi')
        macd = signals.get('macd')
        signal = signals.get('macd_signal')
        bb_upper = signals.get('bb_upper')
        bb_lower = signals.get('bb_lower')
        atr = signals.get('atr')
        investment_style = signals.get('investment_style', 'MEDIUM_TERM')
        
        if not current_price or not atr:
            return {"Không đủ dữ liệu": 1.0}
        
        # Tính điểm cho từng kịch bản
        bullish_score = 0
        bearish_score = 0
        neutral_score = 0
        
        # Phân tích xu hướng (sử dụng MA phù hợp với timeframe)
        if sma_short and sma_medium and sma_long:
            if current_price > sma_short > sma_medium > sma_long:
                bullish_score += 3  # Xu hướng tăng mạnh
            elif current_price > sma_short > sma_medium:
                bullish_score += 2  # Xu hướng tăng
            elif current_price < sma_short < sma_medium < sma_long:
                bearish_score += 3  # Xu hướng giảm mạnh
            elif current_price < sma_short < sma_medium:
                bearish_score += 2  # Xu hướng giảm
            else:
                neutral_score += 1
        
        # Phân tích RSI (điều chỉnh ngưỡng theo timeframe)
        if rsi:
            if investment_style == 'SHORT_TERM':
                # Ngắn hạn: nhạy cảm hơn
                if rsi < 25:
                    bullish_score += 2
                elif rsi > 75:
                    bearish_score += 2
                elif 35 <= rsi <= 65:
                    neutral_score += 1
            else:
                # Trung/dài hạn: ổn định hơn
                if rsi < 30:
                    bullish_score += 1.5
                elif rsi > 70:
                    bearish_score += 1.5
                elif 40 <= rsi <= 60:
                    neutral_score += 1
        
        # Phân tích MACD
        if macd and signal:
            if macd > signal and macd > 0:
                bullish_score += 1.5
            elif macd < signal and macd < 0:
                bearish_score += 1.5
            else:
                neutral_score += 0.5
        
        # Phân tích Bollinger Bands
        if bb_upper and bb_lower:
            if current_price <= bb_lower:
                bullish_score += 1
            elif current_price >= bb_upper:
                bearish_score += 1
            else:
                neutral_score += 0.5
        
        # Chuẩn hóa điểm số thành xác suất
        total_score = bullish_score + bearish_score + neutral_score
        if total_score == 0:
            return {"Không đủ tín hiệu": 1.0}
        
        bullish_prob = bullish_score / total_score
        bearish_prob = bearish_score / total_score
        neutral_prob = neutral_score / total_score
        
        # Tạo kịch bản chi tiết theo timeframe
        scenarios = {}
        
        # Điều chỉnh target theo investment style
        if investment_style == 'SHORT_TERM':
            atr_multiplier_strong = 1.0
            atr_multiplier_weak = 0.3
        elif investment_style == 'MEDIUM_TERM':
            atr_multiplier_strong = 1.5
            atr_multiplier_weak = 0.5
        else:  # LONG_TERM
            atr_multiplier_strong = 2.0
            atr_multiplier_weak = 0.7
        
        if bullish_prob > 0.3:
            target_up_strong = current_price + (atr * atr_multiplier_strong)
            target_up_weak = current_price + (atr * atr_multiplier_weak)
            scenarios[f"Tăng mạnh (+{((target_up_strong/current_price-1)*100):.1f}%)"] = bullish_prob * 0.6
            scenarios[f"Tăng nhẹ (+{((target_up_weak/current_price-1)*100):.1f}%)"] = bullish_prob * 0.4
        
        if bearish_prob > 0.3:
            target_down_strong = current_price - (atr * atr_multiplier_strong)
            target_down_weak = current_price - (atr * atr_multiplier_weak)
            scenarios[f"Giảm mạnh ({((target_down_strong/current_price-1)*100):.1f}%)"] = bearish_prob * 0.6
            scenarios[f"Giảm nhẹ ({((target_down_weak/current_price-1)*100):.1f}%)"] = bearish_prob * 0.4
        
        if neutral_prob > 0.2:
            scenarios[f"Sideway (±{((atr*0.3)/current_price*100):.1f}%)"] = neutral_prob
        
        # Chuẩn hóa xác suất
        total_prob = sum(scenarios.values())
        if total_prob > 0:
            scenarios = {k: v/total_prob for k, v in scenarios.items()}
        
        return scenarios
    
    @staticmethod
    def make_decision(signals: Dict[str, Any], scenarios: Dict[str, float]) -> Tuple[PredictionDecision, float, str]:
        """Đưa ra quyết định dựa trên tín hiệu kỹ thuật"""
        current_price = signals.get('current_price', 0)
        sma_short = signals.get('sma_short')
        sma_medium = signals.get('sma_medium')
        sma_long = signals.get('sma_long')
        rsi = signals.get('rsi')
        macd = signals.get('macd')
        signal = signals.get('macd_signal')
        investment_style = signals.get('investment_style', 'MEDIUM_TERM')
        
        if not current_price:
            return PredictionDecision.HOLD, 0.3, "Không đủ dữ liệu để phân tích"
        
        # Tính điểm quyết định
        buy_score = 0
        sell_score = 0
        hold_score = 0
        
        # Xu hướng (sử dụng MA phù hợp)
        if sma_short and sma_medium:
            if current_price > sma_short > sma_medium:
                buy_score += 2  # Xu hướng tăng rõ ràng
            elif current_price < sma_short < sma_medium:
                sell_score += 2  # Xu hướng giảm rõ ràng
            elif current_price > sma_short:
                buy_score += 1  # Tín hiệu tăng yếu
            elif current_price < sma_short:
                sell_score += 1  # Tín hiệu giảm yếu
            else:
                hold_score += 1
        
        # RSI (điều chỉnh ngưỡng theo timeframe)
        if rsi:
            if investment_style == 'SHORT_TERM':
                # Ngắn hạn: nhạy cảm hơn
                if rsi < 30:
                    buy_score += 2
                elif rsi > 70:
                    sell_score += 2
                elif 40 <= rsi <= 60:
                    hold_score += 1
            else:
                # Trung/dài hạn: ổn định hơn
                if rsi < 35:
                    buy_score += 1.5
                elif rsi > 65:
                    sell_score += 1.5
                elif 40 <= rsi <= 60:
                    hold_score += 0.5
        
        # MACD
        if macd and signal:
            if macd > signal and macd > 0:
                buy_score += 1
            elif macd < signal and macd < 0:
                sell_score += 1
            else:
                hold_score += 0.5
        
        # Kịch bản
        bullish_scenarios = sum(prob for scenario, prob in scenarios.items() if "Tăng" in scenario)
        bearish_scenarios = sum(prob for scenario, prob in scenarios.items() if "Giảm" in scenario)
        
        if bullish_scenarios > 0.4:
            buy_score += 1
        elif bearish_scenarios > 0.4:
            sell_score += 1
        else:
            hold_score += 0.5
        
        # Quyết định cuối cùng
        total_score = buy_score + sell_score + hold_score
        if total_score == 0:
            return PredictionDecision.HOLD, 0.3, "Không đủ tín hiệu"
        
        buy_prob = buy_score / total_score
        sell_prob = sell_score / total_score
        hold_prob = hold_score / total_score
        
        # Tạo rationale chi tiết
        rationale_parts = []
        if rsi:
            rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
            rationale_parts.append(f"RSI: {rsi:.1f} ({rsi_status})")
        
        if macd and signal:
            macd_status = "Bullish" if macd > signal else "Bearish"
            rationale_parts.append(f"MACD: {macd_status}")
        
        if sma_short and sma_medium:
            trend_status = "Uptrend" if current_price > sma_short > sma_medium else "Downtrend" if current_price < sma_short < sma_medium else "Sideways"
            rationale_parts.append(f"Trend: {trend_status}")
        
        rationale = f"Tín hiệu {'mua' if buy_prob > sell_prob and buy_prob > hold_prob else 'bán' if sell_prob > buy_prob and sell_prob > hold_prob else 'trung tính'} ({', '.join(rationale_parts)})"
        
        if buy_prob > sell_prob and buy_prob > hold_prob:
            confidence = min(buy_prob + 0.2, 0.9)
            return PredictionDecision.BUY_MORE, confidence, rationale
        elif sell_prob > buy_prob and sell_prob > hold_prob:
            confidence = min(sell_prob + 0.2, 0.9)
            return PredictionDecision.SELL, confidence, rationale
        else:
            confidence = min(hold_prob + 0.1, 0.7)
            return PredictionDecision.HOLD, confidence, rationale
    
    @staticmethod
    async def predict(symbol: str, investment_style: InvestmentStyle = InvestmentStyle.MEDIUM_TERM) -> PredictionResult:
        """Dự đoán dựa trên phân tích kỹ thuật từ dữ liệu lịch sử theo phong cách đầu tư"""
        try:
            # Lấy dữ liệu lịch sử theo timeframe phù hợp
            days = PredictionEngine.get_data_period_for_style(investment_style)
            data = await PredictionEngine.get_historical_data(symbol, days=days)
            if not data:
                return PredictionResult(
                    symbol=symbol,
                    decision=PredictionDecision.HOLD,
                    confidence=0.3,
                    rationale="Không thể lấy dữ liệu lịch sử",
                    investment_style=investment_style,
                    timeframe=f"{days} ngày"
                )
            
            # Phân tích tín hiệu kỹ thuật theo phong cách đầu tư
            signals = PredictionEngine.analyze_technical_signals(data, investment_style)
            if not signals:
                return PredictionResult(
                    symbol=symbol,
                    decision=PredictionDecision.HOLD,
                    confidence=0.3,
                    rationale="Không đủ dữ liệu để tính toán chỉ báo kỹ thuật",
                    investment_style=investment_style,
                    timeframe=f"{days} ngày"
                )
            
            # Tạo kịch bản
            scenarios = PredictionEngine.generate_scenarios(signals)
            
            # Thêm phân tích cơ bản cho đầu tư dài hạn
            fundamental_signals = {}
            if investment_style == InvestmentStyle.LONG_TERM:
                fundamental_data = await PredictionEngine.get_fundamental_data(symbol)
                if fundamental_data:
                    fundamental_signals = PredictionEngine.analyze_fundamental_signals(fundamental_data)
                    # Cập nhật signals với thông tin cơ bản
                    signals.update(fundamental_signals)
            
            # Đưa ra quyết định
            decision, confidence, rationale = PredictionEngine.make_decision(signals, scenarios)
            
            # Tạo timeframe description
            timeframe_desc = f"{days} ngày"
            if investment_style == InvestmentStyle.SHORT_TERM:
                timeframe_desc = "3 tháng (ngắn hạn)"
            elif investment_style == InvestmentStyle.MEDIUM_TERM:
                timeframe_desc = "1 năm (trung hạn)"
            else:
                timeframe_desc = "3 năm (dài hạn)"
            
            return PredictionResult(
                symbol=symbol,
                decision=decision,
                confidence=confidence,
                rationale=rationale,
                scenarios=scenarios,
                technical_signals=signals,
                investment_style=investment_style,
                timeframe=timeframe_desc
            )
            
        except Exception as e:
            return PredictionResult(
                symbol=symbol,
                decision=PredictionDecision.HOLD,
                confidence=0.3,
                rationale=f"Lỗi phân tích: {str(e)}",
                investment_style=investment_style,
                timeframe=f"{PredictionEngine.get_data_period_for_style(investment_style)} ngày"
            )
    
    @staticmethod
    async def get_fundamental_data(symbol: str) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu cơ bản cho phân tích dài hạn"""
        try:
            from vnstock import Vnstock
            
            # Thử lấy dữ liệu cơ bản từ vnstock
            for source in ("VCI", "TCBS", "DNSE", "SSI"):
                try:
                    stock = Vnstock().stock(symbol=symbol, source=source)
                    
                    # Lấy thông tin cơ bản
                    company_info = stock.company_info
                    financial_ratios = stock.financial_ratios
                    
                    if company_info is not None and not company_info.empty:
                        # Lấy các chỉ số cơ bản
                        pe_ratio = None
                        pb_ratio = None
                        roe = None
                        market_cap = None
                        
                        # Thử lấy P/E, P/B từ financial_ratios
                        if financial_ratios is not None and not financial_ratios.empty:
                            try:
                                latest_ratios = financial_ratios.iloc[-1]
                                pe_ratio = latest_ratios.get('pe', None)
                                pb_ratio = latest_ratios.get('pb', None)
                                roe = latest_ratios.get('roe', None)
                            except Exception:
                                pass
                        
                        # Sử dụng P/E Calculator để tính P/E chính xác
                        if PE_CALCULATOR_AVAILABLE:
                            try:
                                pe_calculator = PECalculator()
                                accurate_pe_data = pe_calculator.calculate_accurate_pe(symbol, use_diluted_eps=True)
                                
                                if accurate_pe_data and "pe_ratio" in accurate_pe_data and accurate_pe_data["pe_ratio"]:
                                    pe_ratio = accurate_pe_data["pe_ratio"]
                                    print(f"Using accurate P/E for {symbol}: {pe_ratio}")
                            except Exception as e:
                                print(f"Warning: Could not calculate accurate P/E for {symbol}: {e}")
                        
                        # Thử lấy market cap từ company_info
                        try:
                            if 'market_cap' in company_info.columns:
                                market_cap = company_info['market_cap'].iloc[-1]
                        except Exception:
                            pass
                        
                        return {
                            'pe_ratio': pe_ratio,
                            'pb_ratio': pb_ratio,
                            'roe': roe,
                            'market_cap': market_cap,
                            'company_name': company_info.get('company_name', [symbol])[0] if 'company_name' in company_info.columns else symbol
                        }
                        
                except Exception:
                    continue
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def analyze_fundamental_signals(fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích tín hiệu cơ bản cho đầu tư dài hạn"""
        if not fundamental_data:
            return {}
        
        pe_ratio = fundamental_data.get('pe_ratio')
        pb_ratio = fundamental_data.get('pb_ratio')
        roe = fundamental_data.get('roe')
        market_cap = fundamental_data.get('market_cap')
        
        signals = {
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'roe': roe,
            'market_cap': market_cap,
            'valuation_score': 0,
            'quality_score': 0,
            'fundamental_analysis': []
        }
        
        # Đánh giá định giá (P/E, P/B)
        if pe_ratio is not None:
            if pe_ratio < 10:
                signals['valuation_score'] += 2  # Rất rẻ
                signals['fundamental_analysis'].append(f"P/E thấp ({pe_ratio:.1f}) - Cổ phiếu rẻ")
            elif pe_ratio < 15:
                signals['valuation_score'] += 1  # Rẻ
                signals['fundamental_analysis'].append(f"P/E hợp lý ({pe_ratio:.1f})")
            elif pe_ratio > 25:
                signals['valuation_score'] -= 1  # Đắt
                signals['fundamental_analysis'].append(f"P/E cao ({pe_ratio:.1f}) - Có thể đắt")
        
        if pb_ratio is not None:
            if pb_ratio < 1:
                signals['valuation_score'] += 2  # Rất rẻ
                signals['fundamental_analysis'].append(f"P/B thấp ({pb_ratio:.1f}) - Giá trị sổ sách tốt")
            elif pb_ratio < 2:
                signals['valuation_score'] += 1  # Rẻ
                signals['fundamental_analysis'].append(f"P/B hợp lý ({pb_ratio:.1f})")
            elif pb_ratio > 3:
                signals['valuation_score'] -= 1  # Đắt
                signals['fundamental_analysis'].append(f"P/B cao ({pb_ratio:.1f}) - Có thể đắt")
        
        # Đánh giá chất lượng (ROE)
        if roe is not None:
            if roe > 20:
                signals['quality_score'] += 2  # Rất tốt
                signals['fundamental_analysis'].append(f"ROE cao ({roe:.1f}%) - Hiệu quả kinh doanh tốt")
            elif roe > 15:
                signals['quality_score'] += 1  # Tốt
                signals['fundamental_analysis'].append(f"ROE tốt ({roe:.1f}%)")
            elif roe < 10:
                signals['quality_score'] -= 1  # Kém
                signals['fundamental_analysis'].append(f"ROE thấp ({roe:.1f}%) - Cần cải thiện")
        
        return signals


CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        chat_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        quantity REAL NOT NULL,
        avg_cost REAL NOT NULL,
        UNIQUE(user_id, symbol),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL, -- BUY / SELL
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        ts TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        user_id INTEGER PRIMARY KEY,
        schedule_hhmm TEXT, -- e.g., 08:15 (24h format, local time)
        timezone_offset_min INTEGER DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tracking_settings (
        user_id INTEGER PRIMARY KEY,
        enabled INTEGER NOT NULL DEFAULT 0,
        sl_pct REAL NOT NULL DEFAULT 0.05,
        tp_pct REAL NOT NULL DEFAULT 0.07,
        vol_ma_days INTEGER NOT NULL DEFAULT 10,
        last_config_ts TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_stoploss (
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        stoploss_pct REAL NOT NULL DEFAULT 0.05,
        PRIMARY KEY (user_id, symbol)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_investment_style (
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        investment_style TEXT NOT NULL DEFAULT 'MEDIUM_TERM',
        last_updated TEXT NOT NULL,
        PRIMARY KEY (user_id, symbol),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tracking_trailing_stop (
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 0,
        trailing_pct REAL NOT NULL DEFAULT 0.10,
        highest_price REAL NOT NULL DEFAULT 0.0,
        trailing_stop_price REAL NOT NULL DEFAULT 0.0,
        last_updated TEXT NOT NULL,
        PRIMARY KEY (user_id, symbol),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS watchlist (
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        target_price REAL,
        notes TEXT,
        added_at TEXT NOT NULL,
        PRIMARY KEY (user_id, symbol),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
]


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        for sql in CREATE_TABLES_SQL:
            await db.execute(sql)
        await db.commit()


async def upsert_user(user_id: int, chat_id: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, chat_id, created_at) VALUES (?, ?, ?)",
            (user_id, chat_id, now),
        )
        await db.commit()


async def get_user_chat_id(user_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            if row:
                try:
                    return int(row[0])
                except (ValueError, TypeError):
                    return None
            return None


async def get_tracking_settings(user_id: int) -> tuple[bool, float, float, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT enabled, sl_pct, tp_pct, vol_ma_days FROM tracking_settings WHERE user_id=?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return (False, 0.05, 0.07, 10)
            enabled = bool(int(row[0]))
            return (enabled, float(row[1]), float(row[2]), int(row[3]))


async def set_tracking_settings(
    user_id: int,
    enabled: Optional[bool] = None,
    sl_pct: Optional[float] = None,
    tp_pct: Optional[float] = None,
    vol_ma_days: Optional[int] = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO tracking_settings (user_id, enabled, sl_pct, tp_pct, vol_ma_days, last_config_ts) VALUES (?, 0, 0.05, 0.07, 10, ?)",
            (user_id, datetime.now(timezone.utc).isoformat()),
        )
        fields = []
        vals = []
        if enabled is not None:
            fields.append("enabled=?")
            vals.append(1 if enabled else 0)
        if sl_pct is not None:
            fields.append("sl_pct=?")
            vals.append(sl_pct)
        if tp_pct is not None:
            fields.append("tp_pct=?")
            vals.append(tp_pct)
        if vol_ma_days is not None:
            fields.append("vol_ma_days=?")
            vals.append(vol_ma_days)
        fields.append("last_config_ts=?")
        vals.append(datetime.now(timezone.utc).isoformat())
        vals.append(user_id)
        await db.execute(
            f"UPDATE tracking_settings SET {', '.join(fields)} WHERE user_id=?",
            vals,
        )
        await db.commit()


async def get_stock_stoploss(user_id: int, symbol: str) -> float:
    """Get individual stoploss percentage for a specific stock."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT stoploss_pct FROM stock_stoploss WHERE user_id=? AND symbol=?",
            (user_id, symbol),
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0.05  # Default 5%


async def set_stock_stoploss(user_id: int, symbol: str, stoploss_pct: float) -> None:
    """Set individual stoploss percentage for a specific stock."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO stock_stoploss (user_id, symbol, stoploss_pct) VALUES (?, ?, ?)",
            (user_id, symbol, stoploss_pct),
        )
        await db.commit()


async def get_stock_investment_style(user_id: int, symbol: str) -> InvestmentStyle:
    """Get investment style for a specific stock."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT investment_style FROM stock_investment_style WHERE user_id=? AND symbol=?",
            (user_id, symbol),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return InvestmentStyle.MEDIUM_TERM
            try:
                return InvestmentStyle(row[0])
            except ValueError:
                return InvestmentStyle.MEDIUM_TERM


async def set_stock_investment_style(user_id: int, symbol: str, style: InvestmentStyle) -> None:
    """Set investment style for a specific stock."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO stock_investment_style (user_id, symbol, investment_style, last_updated) VALUES (?, ?, ?, ?)",
            (user_id, symbol, style.value, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def get_all_stock_styles(user_id: int) -> Dict[str, InvestmentStyle]:
    """Get investment styles for all stocks in user's portfolio."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT symbol, investment_style FROM stock_investment_style WHERE user_id=?",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
            result = {}
            for symbol, style_str in rows:
                try:
                    result[symbol] = InvestmentStyle(style_str)
                except ValueError:
                    result[symbol] = InvestmentStyle.MEDIUM_TERM
            return result


async def get_trailing_stop_settings(user_id: int, symbol: str) -> Optional[Dict[str, Any]]:
    """Get trailing stop settings for a specific stock."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT enabled, trailing_pct, highest_price, trailing_stop_price, last_updated FROM tracking_trailing_stop WHERE user_id=? AND symbol=?",
            (user_id, symbol),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return {
                'enabled': bool(row[0]),
                'trailing_pct': float(row[1]),
                'highest_price': float(row[2]),
                'trailing_stop_price': float(row[3]),
                'last_updated': row[4]
            }


async def set_trailing_stop_settings(
    user_id: int, 
    symbol: str, 
    enabled: bool, 
    trailing_pct: float,
    highest_price: Optional[float] = None,
    trailing_stop_price: Optional[float] = None
) -> None:
    """Set trailing stop settings for a specific stock."""
    now = datetime.now(timezone.utc).isoformat()
    
    # If highest_price and trailing_stop_price not provided, calculate from current price
    if highest_price is None or trailing_stop_price is None:
        current_price = await MarketData.get_price(symbol)
        if current_price is None:
            raise ValueError(f"Không thể lấy giá hiện tại cho {symbol}")
        
        if highest_price is None:
            highest_price = current_price
        if trailing_stop_price is None:
            trailing_stop_price = highest_price * (1 - trailing_pct)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO tracking_trailing_stop (user_id, symbol, enabled, trailing_pct, highest_price, trailing_stop_price, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, symbol, 1 if enabled else 0, trailing_pct, highest_price, trailing_stop_price, now),
        )
        await db.commit()


async def update_trailing_stop_price(user_id: int, symbol: str, current_price: float) -> Optional[float]:
    """Update trailing stop price based on current price. Returns new trailing stop price if updated."""
    settings = await get_trailing_stop_settings(user_id, symbol)
    if not settings or not settings['enabled']:
        return None
    
    trailing_pct = settings['trailing_pct']
    current_highest = settings['highest_price']
    current_trailing_stop = settings['trailing_stop_price']
    
    # If current price is higher than highest price, update both
    if current_price > current_highest:
        new_trailing_stop = current_price * (1 - trailing_pct)
        await set_trailing_stop_settings(
            user_id, symbol, True, trailing_pct, 
            current_price, new_trailing_stop
        )
        return new_trailing_stop
    
    # If current price is still above trailing stop, no update needed
    if current_price > current_trailing_stop:
        return current_trailing_stop
    
    # Price has fallen below trailing stop - return current trailing stop for sell signal
    return current_trailing_stop


async def get_all_trailing_stops(user_id: int) -> Dict[str, Dict[str, Any]]:
    """Get trailing stop settings for all stocks in user's portfolio."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT symbol, enabled, trailing_pct, highest_price, trailing_stop_price, last_updated FROM tracking_trailing_stop WHERE user_id=?",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
            result = {}
            for row in rows:
                result[row[0]] = {
                    'enabled': bool(row[1]),
                    'trailing_pct': float(row[2]),
                    'highest_price': float(row[3]),
                    'trailing_stop_price': float(row[4]),
                    'last_updated': row[5]
                }
            return result


# Watchlist management functions
async def add_to_watchlist(user_id: int, symbol: str, target_price: Optional[float] = None, notes: Optional[str] = None) -> bool:
    """Add a symbol to user's watchlist."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO watchlist (user_id, symbol, target_price, notes, added_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, symbol.upper(), target_price, notes, now)
            )
            await db.commit()
            return True
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return False


async def remove_from_watchlist(user_id: int, symbol: str) -> bool:
    """Remove a symbol from user's watchlist."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND symbol = ?",
                (user_id, symbol.upper())
            )
            await db.commit()
            return True
    except Exception as e:
        print(f"Error removing from watchlist: {e}")
        return False


async def get_watchlist(user_id: int) -> List[Tuple[str, Optional[float], Optional[str], str]]:
    """Get user's watchlist with symbol, target_price, notes, added_at."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT symbol, target_price, notes, added_at FROM watchlist WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [(row[0], row[1], row[2], row[3]) for row in rows]


async def is_in_watchlist(user_id: int, symbol: str) -> bool:
    """Check if symbol is in user's watchlist."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND symbol = ?",
            (user_id, symbol.upper())
        ) as cur:
            row = await cur.fetchone()
            return row is not None


async def clear_watchlist(user_id: int) -> bool:
    """Clear user's entire watchlist."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
            await db.commit()
            return True
    except Exception as e:
        print(f"Error clearing watchlist: {e}")
        return False


async def get_price_and_volume(symbol: str, vol_ma_days: int) -> tuple[Optional[float], Optional[float], Optional[float]]:
    # Get real-time price and volume data
    try:
        from vnstock import Quote
        
        # Get real-time data
        quote = Quote(source='VCI', symbol=symbol)
        realtime_data = quote.intraday()
        
        if realtime_data is not None and len(realtime_data) > 0:
            # Get latest real-time price and volume
            latest_data = realtime_data.iloc[-1]
            price = float(latest_data.get('close', latest_data.get('price', 0)))
            volume = float(latest_data.get('volume', 0))
            
            print(f"    🔍 Getting realtime data for {symbol}")
            print(f"    📊 Realtime: Price={price:.2f}, Volume={volume:.0f}")
            
            if price > 0 and volume > 0:
                # Get historical volume data for MA calculation
                try:
                    today = datetime.now().date()
                    start_date = (today - timedelta(days=max(20, vol_ma_days * 2))).strftime("%Y-%m-%d")
                    end_date = today.strftime("%Y-%m-%d")
                    
                    df = quote.history(
                        start=start_date,
                        end=end_date,
                        interval="1D"
                    )
                    
                    if df is not None and len(df) > 0:
                        print(f"    📊 Historical data: {len(df)} rows for MA calculation")
                        df = df.dropna(subset=["volume"])  # type: ignore[attr-defined]
                        if len(df) > 0:
                            if len(df) >= vol_ma_days:
                                ma_vol = float(df["volume"].tail(vol_ma_days).mean())  # type: ignore[attr-defined]
                            else:
                                ma_vol = float(df["volume"].mean())  # type: ignore[attr-defined]
                            print(f"    ✅ Volume MA: {ma_vol:.0f}")
                            return (price, volume, ma_vol)
                        else:
                            print(f"    ❌ No volume data after dropna")
                    else:
                        print(f"    ❌ No historical data for MA")
                except Exception as e:
                    print(f"    ❌ Error getting volume MA: {e}")
                
                # Return real-time data even without MA
                print(f"    ✅ Using realtime volume without MA")
                return (price, volume, None)
            else:
                print(f"    ❌ Invalid realtime data: price={price}, volume={volume}")
        else:
            print(f"    ❌ No realtime data returned")
            
    except Exception as e:
        print(f"    ❌ Error getting realtime data: {e}")
    
    # Fallback to historical data for both price and volume
    try:
        from vnstock import Quote
        today = datetime.now().date()
        start_date = (today - timedelta(days=max(20, vol_ma_days * 2))).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        quote = Quote(source='VCI', symbol=symbol)
        df = quote.history(
            start=start_date,
            end=end_date,
            interval="1D"
        )
        
        if df is not None and len(df) > 0:
            df = df.dropna(subset=["close", "volume"])  # type: ignore[attr-defined]
            if len(df) > 0:
                last_close = float(df["close"].iloc[-1])  # type: ignore[index]
                last_vol = float(df["volume"].iloc[-1])  # type: ignore[index]
                if len(df) >= vol_ma_days:
                    ma_vol = float(df["volume"].tail(vol_ma_days).mean())  # type: ignore[attr-defined]
                else:
                    ma_vol = float(df["volume"].mean())  # type: ignore[attr-defined]
                print(f"    ✅ Fallback historical: Price={last_close:.2f}, Volume={last_vol:.0f}, MA={ma_vol:.0f}")
                return (last_close, last_vol, ma_vol)
        
        # Final fallback - just get price
        price = await MarketData.get_price(symbol)
        return (price, None, None)
    except Exception as e:
        print(f"    ❌ Error in fallback: {e}")
        price = await MarketData.get_price(symbol)
        return (price, None, None)


async def check_positions_and_alert(app: Application, user_id: int, chat_id: str, *, force_status: bool = False) -> None:
    enabled, sl_pct, tp_pct, vol_ma_days = await get_tracking_settings(user_id)
    if not enabled:
        print(f"Tracking disabled for user {user_id}")
        return
    positions = await get_positions(user_id)
    if not positions:
        print(f"No positions found for user {user_id}")
        return

    print(f"Checking {len(positions)} positions for user {user_id}")
    
    # Check if we should send detailed or compact status
    current_time = datetime.now(VN_TZ)
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # Determine if this is a key time for detailed status
    is_key_time = (
        (current_hour == 9 and current_minute == 5) or  # ATO
        (current_hour == 14 and current_minute == 35) or  # ATC
        (current_hour == 14 and current_minute == 40) or  # Summary
        (current_hour == 9 and current_minute in [15, 30, 45]) or  # Morning key times
        (current_hour == 10 and current_minute in [0, 15, 30]) or  # Morning key times
        (current_hour == 13 and current_minute in [30, 45]) or  # Afternoon key times
        (current_hour == 14 and current_minute in [0, 15, 30])  # Afternoon key times
    )
    
    # Always send portfolio status for traditional tracking
    status_lines = [
        f"📊 **Portfolio Status - {current_time.strftime('%H:%M:%S')}**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    total_pnl = 0.0
    total_cost = 0.0
    any_price_available = False
    any_signal = False
    
    for symbol, qty, avg_cost in positions:
        price, vol, vol_ma = await get_price_and_volume(symbol, vol_ma_days)
        
        if price is not None:
            any_price_available = True
            pnl = (price - avg_cost) * qty
            pnl_pct = ((price - avg_cost) / avg_cost) * 100
            cost_value = avg_cost * qty
            current_value = price * qty
            
            total_pnl += pnl
            total_cost += cost_value
            
            # Price change indicator
            if pnl > 0:
                price_indicator = "📈"
            elif pnl < 0:
                price_indicator = "📉"
            else:
                price_indicator = "➡️"
            
            # Get individual stoploss for this stock
            individual_sl_pct = await get_stock_stoploss(user_id, symbol)
            sl_price = avg_cost * (1 - individual_sl_pct)
            tp_price = avg_cost * (1 + tp_pct)
            
            # Check for signals
            signal_text = ""
            
            # Check trailing stop first (if enabled)
            trailing_settings = await get_trailing_stop_settings(user_id, symbol)
            if trailing_settings and trailing_settings['enabled']:
                # Update trailing stop price based on current price
                new_trailing_stop = await update_trailing_stop_price(user_id, symbol, price)
                if new_trailing_stop is not None:
                    trailing_stop_price = new_trailing_stop
                    if price <= trailing_stop_price:
                        any_signal = True
                        signal_text = f" 🎯 TRAILING STOP!"
                        print(f"  {symbol}: TRAILING STOP TRIGGERED! Price={price:.2f} <= TrailingStop={trailing_stop_price:.2f}")
            else:
                # Check regular stoploss
                if price <= sl_price:
                    any_signal = True
                    signal_text = f" ⛔ STOPLOSS!"
                    print(f"  {symbol}: STOPLOSS TRIGGERED!")
                elif price >= tp_price:
                    vol_ok = (vol is not None and vol_ma is not None and vol > vol_ma) or (vol is None or vol_ma is None)
                    if vol_ok:
                        any_signal = True
                        signal_text = f" ✅ BREAKOUT!"
                        print(f"  {symbol}: BREAKOUT CONFIRMED!")
                    else:
                        signal_text = f" ⚠️ TP nhưng vol chưa xác nhận"
                        print(f"  {symbol}: Breakout but volume not confirmed")
            
            # Format PnL with better visual indicators
            pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            pnl_text = f"{pnl_emoji} {pnl:+.0f} ({pnl_pct:+.1f}%)"
            
            # Add to status lines with improved formatting
            status_lines.extend([
                "",
                f"{price_indicator} **{symbol}**",
                f"   💰 Giá: {price:.2f}",
                f"   📊 SL: {qty:g} | Cost: {avg_cost:.2f}",
                f"   {pnl_text}{signal_text}"
            ])
            
            # Add trailing stop info if enabled
            if trailing_settings and trailing_settings['enabled']:
                trailing_stop_price = await update_trailing_stop_price(user_id, symbol, price)
                if trailing_stop_price is not None:
                    status_lines.append(f"   🎯 Trailing: {trailing_stop_price:.2f} (Highest: {trailing_settings['highest_price']:.2f})")
        else:
            status_lines.extend([
                "",
                f"❓ **{symbol}**",
                f"   📊 SL: {qty:g} | Cost: {avg_cost:.2f}",
                f"   ❌ Giá: N/A"
            ])
    
    # Add summary section with better formatting
    if any_price_available and total_cost > 0:
        total_pnl_pct = (total_pnl / total_cost) * 100
        summary_emoji = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
        status_lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"💰 **Tổng PnL**: {summary_emoji} {total_pnl:+.0f} ({total_pnl_pct:+.1f}%)"
        ])
    
    # Add signal summary if any
    if any_signal:
        status_lines.extend([
            "",
            "🚨 **Có tín hiệu quan trọng!**"
        ])
    
    # Create compact format for frequent updates
    if not is_key_time and not any_signal and not force_status:
        # Only send compact format for non-key times
        compact_lines = [
            f"📊 **Portfolio Update - {current_time.strftime('%H:%M:%S')}**",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        
        # Add all positions in compact format
        for symbol, qty, avg_cost in positions:
            price, vol, vol_ma = await get_price_and_volume(symbol, vol_ma_days)
            if price is not None:
                pnl = (price - avg_cost) * qty
                pnl_pct = ((price - avg_cost) / avg_cost) * 100
                
                # Show all positions in compact format
                pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                price_indicator = "📈" if pnl > 0 else "📉" if pnl < 0 else "➡️"
                compact_lines.append(f"{price_indicator} **{symbol}**: {price:.2f} {pnl_emoji} {pnl:+.0f} ({pnl_pct:+.1f}%)")
        
        # Add total PnL
        if any_price_available and total_cost > 0:
            total_pnl_pct = (total_pnl / total_cost) * 100
            summary_emoji = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
            compact_lines.extend([
                "",
                f"💰 **Tổng PnL**: {summary_emoji} {total_pnl:+.0f} ({total_pnl_pct:+.1f}%)"
            ])
        
        # Send if there are positions to show
        if len(compact_lines) > 2:  # More than just header and separator
            try:
                print(f"🔍 Sending compact portfolio update to user {user_id}")
                await app.bot.send_message(chat_id=chat_id, text="\n".join(compact_lines))
                print(f"✅ Sent compact portfolio update to user {user_id}")
            except Exception as e:
                print(f"❌ Failed to send compact portfolio update to user {user_id}: {e}")
        else:
            print(f"📊 No significant changes to report for user {user_id}")
    else:
        # Send full detailed status for key times or when there are signals
        try:
            print(f"🔍 Sending detailed portfolio status to user {user_id}")
            await app.bot.send_message(chat_id=chat_id, text="\n".join(status_lines))
            print(f"✅ Sent detailed portfolio status to user {user_id}")
        except Exception as e:
            print(f"❌ Failed to send detailed portfolio status to user {user_id}: {e}")
            print(f"🔍 Chat ID type: {type(chat_id)}, value: {chat_id}")
    
    # Check watchlist for buy signals
    await check_watchlist_and_alert(app, user_id, chat_id, vol_ma_days)


async def check_watchlist_and_alert(app: Application, user_id: int, chat_id: str, vol_ma_days: int) -> None:
    """Check watchlist for potential buy signals."""
    try:
        watchlist = await get_watchlist(user_id)
        if not watchlist:
            return
        
        print(f"Checking {len(watchlist)} watchlist items for user {user_id}")
        
        alerts = []
        any_alert = False
        
        for symbol, target_price, notes, added_at in watchlist:
            try:
                # Get current price and volume
                price, vol, vol_ma = await get_price_and_volume(symbol, vol_ma_days)
                
                if price is None:
                    print(f"    ❓ {symbol}: No price data available")
                    continue
                
                print(f"    📊 {symbol}: Price={price:.2f}, Volume={vol:,.0f if vol else 'N/A'}")
                
                # Check for buy signals
                buy_signals = []
                confidence = 0.0
                
                # 1. Target price reached
                if target_price and price <= target_price * 1.02:  # Within 2% of target
                    buy_signals.append(f"🎯 Đạt giá mục tiêu ({target_price:,.0f})")
                    confidence += 0.3
                
                # 2. Volume spike (if volume data available)
                if vol and vol_ma and vol > vol_ma * 1.5:
                    buy_signals.append(f"📈 Volume tăng mạnh (+{((vol/vol_ma-1)*100):.1f}%)")
                    confidence += 0.2
                
                # 3. Technical analysis using prediction engine
                try:
                    prediction = await PredictionEngine.predict(symbol, InvestmentStyle.MEDIUM_TERM)
                    
                    if prediction.decision == PredictionDecision.BUY_MORE:
                        buy_signals.append(f"🔮 Tín hiệu kỹ thuật: {prediction.rationale or 'Mua thêm'}")
                        confidence += prediction.confidence * 0.3
                    elif prediction.decision == PredictionDecision.HOLD and prediction.confidence > 0.7:
                        buy_signals.append(f"📊 Tín hiệu tích cực: {prediction.rationale or 'Giữ vị thế'}")
                        confidence += prediction.confidence * 0.1
                        
                except Exception as e:
                    print(f"    ⚠️ {symbol}: Prediction error: {e}")
                
                # 4. Price momentum (simple check)
                try:
                    from vnstock import Quote
                    quote = Quote(source='VCI', symbol=symbol)
                    today = datetime.now().date()
                    start_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
                    end_date = today.strftime("%Y-%m-%d")
                    
                    df = quote.history(start=start_date, end=end_date, interval="1D")
                    if df is not None and len(df) >= 2:
                        recent_prices = df['close'].tail(2).values
                        if len(recent_prices) == 2:
                            price_change = (recent_prices[1] - recent_prices[0]) / recent_prices[0]
                            if price_change > 0.02:  # 2% increase
                                buy_signals.append(f"📈 Tăng giá gần đây (+{price_change*100:.1f}%)")
                                confidence += 0.1
                except Exception as e:
                    print(f"    ⚠️ {symbol}: Momentum check error: {e}")
                
                # Generate alert if confidence is high enough
                if confidence >= 0.4 and buy_signals:  # Minimum 40% confidence
                    any_alert = True
                    alert_text = f"🚀 **GỢI Ý MUA - {symbol}**\n"
                    alert_text += f"💰 Giá hiện tại: {price:,.0f}\n"
                    
                    if target_price:
                        discount_pct = ((target_price - price) / target_price) * 100
                        alert_text += f"🎯 Giá mục tiêu: {target_price:,.0f} (Giảm {discount_pct:.1f}%)\n"
                    
                    alert_text += f"📊 Độ tin cậy: {confidence*100:.0f}%\n\n"
                    alert_text += "🔍 **Tín hiệu:**\n"
                    for signal in buy_signals:
                        alert_text += f"• {signal}\n"
                    
                    if notes:
                        alert_text += f"\n📝 Ghi chú: {notes}"
                    
                    alert_text += f"\n\n💡 Dùng `/add {symbol} <số_lượng> <giá>` để mua"
                    alerts.append(alert_text)
                    
                    print(f"    🚀 BUY SIGNAL: {symbol} - Confidence: {confidence*100:.0f}%")
                
            except Exception as e:
                print(f"    ❌ Error analyzing {symbol}: {e}")
        
        # Send alerts if any
        if any_alert and alerts:
            try:
                alert_message = "📝 **Danh sách theo dõi - Tín hiệu mua**\n"
                alert_message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                alert_message += "\n\n".join(alerts)
                
                print(f"🔍 Sending watchlist alerts to user {user_id}")
                await app.bot.send_message(chat_id=chat_id, text=alert_message)
                print(f"✅ Sent watchlist alerts to user {user_id}")
            except Exception as e:
                print(f"❌ Failed to send watchlist alerts to user {user_id}: {e}")
        else:
            print(f"📊 No watchlist alerts for user {user_id}")
            
    except Exception as e:
        print(f"❌ Error in watchlist analysis: {e}")


async def summarize_eod_and_outlook(app: Application, user_id: int, chat_id: str) -> None:
    positions = await get_positions(user_id)
    if not positions:
        try:
            await app.bot.send_message(chat_id=chat_id, text="📊 **Tổng kết EOD:** Danh mục trống.")
            print(f"✅ Sent empty portfolio summary to user {user_id}")
        except Exception as e:
            print(f"❌ Failed to send empty portfolio summary to user {user_id}: {e}")
        return

    current_time = datetime.now(VN_TZ)
    lines: List[str] = [f"📊 **Tổng kết cuối phiên - {current_time.strftime('%H:%M:%S %d/%m/%Y')}**\n"]
    
    total_pnl = 0.0
    total_cost = 0.0
    any_price = False
    any_signal = False

    for symbol, qty, avg_cost in positions:
        price, vol, vol_ma = await get_price_and_volume(symbol, vol_ma_days=10)
        
        if price is not None:
            any_price = True
            pnl = (price - avg_cost) * qty
            pnl_pct = ((price - avg_cost) / avg_cost) * 100
            cost_value = avg_cost * qty
            current_value = price * qty
            
            total_pnl += pnl
            total_cost += cost_value
            
            # Price change indicator
            if pnl > 0:
                price_indicator = "📈"
            elif pnl < 0:
                price_indicator = "📉"
            else:
                price_indicator = "➡️"
            
            # Get individual stoploss for this stock
            individual_sl_pct = await get_stock_stoploss(user_id, symbol)
            sl_price = avg_cost * (1 - individual_sl_pct)
            tp_price = avg_cost * (1 + 0.10)  # Default TP 10%
            
            # Check for signals
            signal_text = ""
            if price <= sl_price:
                any_signal = True
                signal_text = f" ⛔ STOPLOSS!"
            elif price >= tp_price:
                vol_ok = (vol is not None and vol_ma is not None and vol > vol_ma) or (vol is None or vol_ma is None)
                if vol_ok:
                    any_signal = True
                    signal_text = f" ✅ BREAKOUT!"
                else:
                    signal_text = f" ⚠️ TP nhưng vol chưa xác nhận"
            
            # Simple next-day outlook heuristic
            outlook: str
            if vol is not None and vol_ma is not None and vol > vol_ma and pnl_pct > 3:
                outlook = "Xu hướng tích cực, có thể theo dõi mua gia tăng nếu xác nhận."
            elif pnl_pct < -3:
                outlook = "Áp lực bán, cân nhắc giảm tỷ trọng nếu thủng hỗ trợ."
            else:
                outlook = "Trung tính, chờ tín hiệu rõ ràng."
            
            lines.append(
                f"{price_indicator} **{symbol}**: {price:.2f} "
                f"(SL: {qty:g}, Cost: {avg_cost:.2f}) "
                f"PnL: {pnl:+.0f} ({pnl_pct:+.1f}%){signal_text}"
            )
            lines.append(f"   📊 SL: {sl_price:.2f} | TP: {tp_price:.2f} | Outlook: {outlook}")
        else:
            lines.append(f"❓ **{symbol}**: N/A (SL: {qty:g}, Cost: {avg_cost:.2f})")

    # Add summary
    if any_price and total_cost > 0:
        total_pnl_pct = (total_pnl / total_cost) * 100
        lines.append(f"\n💰 **Tổng PnL**: {total_pnl:+.0f} ({total_pnl_pct:+.1f}%)")
    
    # Add signal summary if any
    if any_signal:
        lines.append(f"\n🚨 **Có tín hiệu quan trọng cần chú ý!**")
    
    # Add next day outlook
    lines.append(f"\n🔮 **Dự báo ngày mai:**")
    if any_price:
        if total_pnl > 0:
            lines.append("• Xu hướng tích cực, tiếp tục theo dõi")
        elif total_pnl < 0:
            lines.append("• Cần thận trọng, cân nhắc điều chỉnh danh mục")
        else:
            lines.append("• Trung tính, chờ tín hiệu rõ ràng")
    else:
        lines.append("• Thiếu dữ liệu, cần theo dõi thêm")

    try:
        await app.bot.send_message(chat_id=chat_id, text="\n".join(lines))
        print(f"✅ Sent EOD summary to user {user_id}")
    except Exception as e:
        print(f"❌ Failed to send EOD summary to user {user_id}: {e}")


def _vn_time(hh: int, mm: int) -> time:
    # tz-aware time for Vietnam timezone
    return time(hour=hh, minute=mm, tzinfo=VN_TZ)


def _track_job_name(user_id: int, tag: str) -> str:
    return f"track_{tag}_{user_id}"


# Callback functions for tracking jobs
async def tracking_callback(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for tracking jobs - extracts user_id and chat_id from job data."""
    try:
        job = ctx.job
        user_id = job.data.get('user_id')
        chat_id = job.data.get('chat_id')
        job_type = job.data.get('job_type', 'check_positions')
        
        print(f"🔥 TRACKING CALLBACK TRIGGERED! Job: {job.name}, Type: {job_type}, User: {user_id}")
        
        if not user_id or not chat_id:
            print(f"Tracking callback: Missing user_id or chat_id in job data")
            return
        
        print(f"Running tracking job: {job_type} for user {user_id}")
        
        # Check if bot can send messages to this chat first
        try:
            # Try to get chat info to verify we can send messages
            chat = await ctx.application.bot.get_chat(chat_id)
            print(f"Chat info retrieved successfully for user {user_id}")
        except Exception as e:
            print(f"Cannot access chat for user {user_id}: {e}")
            return
        
        if job_type == 'check_positions':
            await check_positions_and_alert(ctx.application, user_id, chat_id)
        elif job_type == 'summary':
            await summarize_eod_and_outlook(ctx.application, user_id, chat_id)
            
        print(f"✅ Tracking job completed successfully for user {user_id}")
        
    except Exception as e:
        print(f"❌ Error in tracking callback: {e}")
        # Try to send error message to user if possible
        try:
            job = ctx.job
            user_id = job.data.get('user_id')
            chat_id = job.data.get('chat_id')
            if user_id and chat_id:
                await ctx.application.bot.send_message(
                    chat_id=chat_id, 
                    text=f"❌ Lỗi trong tracking tự động: {str(e)}"
                )
        except Exception as e2:
            print(f"❌ Error sending error message: {e2}")


async def daily_market_report_callback(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for daily market report job."""
    try:
        job = ctx.job
        user_id = job.data.get('user_id')
        chat_id = job.data.get('chat_id')
        
        print(f"📊 DAILY MARKET REPORT CALLBACK TRIGGERED! User: {user_id}")
        
        if not user_id or not chat_id:
            print(f"Market report callback: Missing user_id or chat_id in job data")
            return
        
        # Check if market analysis is available
        if not MARKET_ANALYSIS_AVAILABLE:
            await ctx.application.bot.send_message(
                chat_id=chat_id,
                text="❌ Chức năng phân tích thị trường chưa khả dụng. Vui lòng kiểm tra cài đặt API keys."
            )
            return
        
        # Check if we have required API keys
        if not SERPER_API_KEY:
            await ctx.application.bot.send_message(
                chat_id=chat_id,
                text="❌ Thiếu SERPER_API_KEY. Vui lòng cấu hình API key để sử dụng chức năng phân tích thị trường."
            )
            return
        
        # Generate and send market report
        try:
            message = await get_daily_market_report_message(
                SERPER_API_KEY, 
                GEMINI_API_KEY if GEMINI_API_KEY else None, 
                OPENAI_API_KEY if OPENAI_API_KEY else None
            )
            
            await ctx.application.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            
            print(f"✅ Daily market report sent successfully to user {user_id}")
            
        except Exception as e:
            print(f"❌ Error generating market report: {e}")
            await ctx.application.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Lỗi khi tạo báo cáo thị trường: {str(e)}"
            )
            
    except Exception as e:
        print(f"❌ Error in daily market report callback: {e}")
        # Try to send error message to user if possible
        try:
            job = ctx.job
            user_id = job.data.get('user_id')
            chat_id = job.data.get('chat_id')
            if user_id and chat_id:
                await ctx.application.bot.send_message(
                    chat_id=chat_id, 
                    text=f"❌ Lỗi trong báo cáo thị trường hàng ngày: {str(e)}"
                )
        except Exception as e2:
            print(f"❌ Error sending error message: {e2}")


async def schedule_tracking_jobs(app: Application, user_id: int) -> None:
    try:
        # Check if job queue exists
        if app.job_queue is None:
            print(f"Schedule tracking: JobQueue is None for user {user_id}")
            return
            
        chat_id = await get_user_chat_id(user_id)
        if not chat_id:
            print(f"Schedule tracking: No chat_id found for user {user_id}")
            return
        enabled, _, _, _ = await get_tracking_settings(user_id)
        print(f"Schedule tracking: User {user_id}, enabled={enabled}")
        
        # Remove old tracking jobs
        for tag in ["ato_once", "morning_5m", "mid_5m", "late_5m", "atc_once", "summary_once"]:
            for job in app.job_queue.get_jobs_by_name(_track_job_name(user_id, tag)):
                job.schedule_removal()
        
        if not enabled:
            print(f"Schedule tracking: Tracking disabled for user {user_id}")
            return

        # Job data to pass to callback
        job_data = {'user_id': user_id, 'chat_id': chat_id}
        
        # Get current VN time to determine which jobs to schedule
        now = datetime.now(VN_TZ)
        current_time = now.timetz()
        
        print(f"Current time: {current_time}, scheduling jobs for user {user_id}")

        # Schedule jobs based on current time
        jobs_scheduled = 0
        
        # 09:05 ATO (once) - only if current time is before 09:05
        if current_time < _vn_time(9, 5):
            app.job_queue.run_daily(
                name=_track_job_name(user_id, "ato_once"),
                time=_vn_time(9, 5),
                callback=tracking_callback,
                data={**job_data, 'job_type': 'check_positions'},
            )
            jobs_scheduled += 1
            print(f"Scheduled ATO job for user {user_id}")
        
        # 09:15–10:30: repeating checks
        if current_time < _vn_time(10, 30):
            start_dt = datetime.combine(now.date(), _vn_time(9, 15))
            end_dt = datetime.combine(now.date(), _vn_time(10, 30))
            if now < start_dt:
                first_dt = start_dt
            else:
                # if already in window, trigger soon
                first_dt = now + timedelta(seconds=2)
            app.job_queue.run_repeating(
                name=_track_job_name(user_id, "morning_5m"),
                interval=timedelta(minutes=1) if TEST_EVERY_MINUTE else timedelta(minutes=5),
                first=first_dt,
                last=end_dt,
                callback=tracking_callback,
                data={**job_data, 'job_type': 'check_positions'},
            )
            jobs_scheduled += 1
            print(f"Scheduled morning job for user {user_id} (first={first_dt}, last={end_dt})")
        
        # 10:30–13:30: repeating checks
        if current_time < _vn_time(13, 30):
            start_dt = datetime.combine(now.date(), _vn_time(10, 30))
            end_dt = datetime.combine(now.date(), _vn_time(13, 30))
            if now < start_dt:
                first_dt = start_dt
            else:
                first_dt = now + timedelta(seconds=2)
            app.job_queue.run_repeating(
                name=_track_job_name(user_id, "mid_5m"),
                interval=timedelta(minutes=1) if TEST_EVERY_MINUTE else timedelta(minutes=5),
                first=first_dt,
                last=end_dt,
                callback=tracking_callback,
                data={**job_data, 'job_type': 'check_positions'},
            )
            jobs_scheduled += 1
            print(f"Scheduled mid job for user {user_id} (first={first_dt}, last={end_dt})")
        
        # 13:30–14:30: repeating checks
        if current_time < _vn_time(14, 30):
            start_dt = datetime.combine(now.date(), _vn_time(13, 30))
            end_dt = datetime.combine(now.date(), _vn_time(14, 30))
            if now < start_dt:
                first_dt = start_dt
            else:
                first_dt = now + timedelta(seconds=2)
            app.job_queue.run_repeating(
                name=_track_job_name(user_id, "late_5m"),
                interval=timedelta(minutes=1) if TEST_EVERY_MINUTE else timedelta(minutes=5),
                first=first_dt,
                last=end_dt,
                callback=tracking_callback,
                data={**job_data, 'job_type': 'check_positions'},
            )
            jobs_scheduled += 1
            print(f"Scheduled late job for user {user_id} (first={first_dt}, last={end_dt})")
        
        # 14:35 ATC (once)
        if current_time < _vn_time(14, 35):
            atc_dt = datetime.combine(now.date(), _vn_time(14, 35))
            # Use one-off for same-day to avoid daily edge cases
            app.job_queue.run_once(
                name=_track_job_name(user_id, "atc_once"),
                when=atc_dt,
                callback=tracking_callback,
                data={**job_data, 'job_type': 'check_positions'},
            )
            jobs_scheduled += 1
            print(f"Scheduled ATC job for user {user_id} at {atc_dt}")
        
        # 14:40 Summary (once)
        if current_time < _vn_time(14, 40):
            sum_dt = datetime.combine(now.date(), _vn_time(14, 40))
            # Use one-off for same-day to avoid daily edge cases
            app.job_queue.run_once(
                name=_track_job_name(user_id, "summary_once"),
                when=sum_dt,
                callback=tracking_callback,
                data={**job_data, 'job_type': 'summary'},
            )
            jobs_scheduled += 1
            print(f"Scheduled summary job for user {user_id} at {sum_dt}")
        
        print(f"Schedule tracking: Successfully scheduled {jobs_scheduled} jobs for user {user_id}")
    except Exception as e:
        print(f"Error scheduling tracking jobs for user {user_id}: {e}")


async def schedule_daily_market_report(app: Application, user_id: int) -> None:
    """Schedule daily market report at 8:15 AM VN time"""
    try:
        if app.job_queue is None:
            print(f"Schedule market report: JobQueue is None for user {user_id}")
            return
            
        chat_id = await get_user_chat_id(user_id)
        if not chat_id:
            print(f"Schedule market report: No chat_id found for user {user_id}")
            return
        
        # Remove old market report jobs
        job_name = f"daily_market_report_{user_id}"
        for job in app.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        
        # Schedule daily market report at 8:15 AM VN time
        job_data = {'user_id': user_id, 'chat_id': chat_id}
        
        app.job_queue.run_daily(
            name=job_name,
            time=_vn_time(8, 15),
            callback=daily_market_report_callback,
            data=job_data,
        )
        
        print(f"✅ Scheduled daily market report for user {user_id} at 8:15 AM VN time")
        
    except Exception as e:
        print(f"Error scheduling daily market report for user {user_id}: {e}")


async def bootstrap_tracking(app: Application) -> None:
    try:
        print("Bootstrap tracking: Starting...")
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM tracking_settings WHERE enabled=1") as cur:
                rows = await cur.fetchall()
                print(f"Bootstrap tracking: Found {len(rows)} users with tracking enabled")
                for (uid,) in rows:
                    await schedule_tracking_jobs(app, int(uid))
        print("Bootstrap tracking: Completed")
    except Exception as e:
        print(f"Error in bootstrap_tracking: {e}")


async def bootstrap_market_reports(app: Application) -> None:
    """Bootstrap daily market reports for all users"""
    try:
        print("Bootstrap market reports: Starting...")
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT DISTINCT user_id FROM users") as cur:
                rows = await cur.fetchall()
                print(f"Bootstrap market reports: Found {len(rows)} users")
                for (uid,) in rows:
                    await schedule_daily_market_report(app, int(uid))
        print("Bootstrap market reports: Completed")
    except Exception as e:
        print(f"Error in bootstrap_market_reports: {e}")


async def add_transaction_and_update_position(
    user_id: int,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
) -> None:
    symbol = symbol.upper().strip()
    ts = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO transactions (user_id, symbol, side, quantity, price, ts) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, symbol, side, quantity, price, ts),
        )

        # Fetch current position
        async with db.execute(
            "SELECT quantity, avg_cost FROM positions WHERE user_id=? AND symbol=?",
            (user_id, symbol),
        ) as cur:
            row = await cur.fetchone()

        if side.upper() == "BUY":
            if row:
                old_qty, old_avg = float(row[0]), float(row[1])
                new_qty = old_qty + quantity
                new_avg = (old_qty * old_avg + quantity * price) / new_qty if new_qty != 0 else 0.0
                await db.execute(
                    "UPDATE positions SET quantity=?, avg_cost=? WHERE user_id=? AND symbol=?",
                    (new_qty, new_avg, user_id, symbol),
                )
            else:
                await db.execute(
                    "INSERT INTO positions (user_id, symbol, quantity, avg_cost) VALUES (?, ?, ?, ?)",
                    (user_id, symbol, quantity, price),
                )
        elif side.upper() == "SELL":
            if row:
                old_qty, old_avg = float(row[0]), float(row[1])
                new_qty = old_qty - quantity
                if new_qty < 0:
                    new_qty = 0.0
                if new_qty == 0:
                    await db.execute(
                        "DELETE FROM positions WHERE user_id=? AND symbol=?",
                        (user_id, symbol),
                    )
                else:
                    # Average cost unchanged on sell
                    await db.execute(
                        "UPDATE positions SET quantity=? WHERE user_id=? AND symbol=?",
                        (new_qty, user_id, symbol),
                    )
            else:
                # Selling without position: record transaction only
                pass
        else:
            raise ValueError("side must be BUY or SELL")

        await db.commit()


async def get_positions(user_id: int) -> List[Tuple[str, float, float]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT symbol, quantity, avg_cost FROM positions WHERE user_id=? ORDER BY symbol",
            (user_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [(str(r[0]), float(r[1]), float(r[2])) for r in rows]


async def get_pnl_report(user_id: int) -> List[Tuple[str, float, float, Optional[float], Optional[float]]]:
    positions = await get_positions(user_id)
    report: List[Tuple[str, float, float, Optional[float], Optional[float]]] = []
    for symbol, qty, avg_cost in positions:
        price = await MarketData.get_price(symbol)
        pnl = None
        if price is not None:
            pnl = (price - avg_cost) * qty
        report.append((symbol, qty, avg_cost, price, pnl))
    return report


async def get_transactions(user_id: int, symbol: str) -> List[Tuple[str, float, float, str]]:
    """Return list of transactions for a symbol ordered by timestamp.

    Each item: (side, quantity, price, ts)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT side, quantity, price, ts FROM transactions WHERE user_id=? AND symbol=? ORDER BY ts ASC",
            (user_id, symbol),
        ) as cur:
            rows = await cur.fetchall()
            return [
                (str(r[0]), float(r[1]), float(r[2]), str(r[3])) for r in rows
            ]


async def compute_fifo_lots(user_id: int, symbol: str) -> List[Tuple[float, float]]:
    """Compute remaining lots using FIFO from transactions.

    Returns list of (quantity, unit_cost) for remaining holdings.
    """
    txs = await get_transactions(user_id, symbol)
    lots: deque[Tuple[float, float]] = deque()
    for side, qty, price, _ in txs:
        if side.upper() == "BUY":
            lots.append((qty, price))
        elif side.upper() == "SELL":
            remaining = qty
            while remaining > 0 and lots:
                lot_qty, lot_price = lots[0]
                if lot_qty > remaining:
                    lots[0] = (lot_qty - remaining, lot_price)
                    remaining = 0
                else:
                    remaining -= lot_qty
                    lots.popleft()
            # If selling more than held, ignore excess
        else:
            continue
    return list(lots)


async def compute_effective_avg_cost_fifo(user_id: int, symbol: str) -> Optional[float]:
    lots = await compute_fifo_lots(user_id, symbol)
    if not lots:
        return None
    total_qty = sum(q for q, _ in lots)
    if total_qty <= 0:
        return None
    total_cost = sum(q * p for q, p in lots)
    return total_cost / total_qty


def parse_hhmm(hhmm: str) -> Optional[time]:
    try:
        parts = hhmm.strip().split(":")
        if len(parts) != 2:
            return None
        hh, mm = int(parts[0]), int(parts[1])
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            return None
        return time(hour=hh, minute=mm)
    except Exception:
        return None


async def set_schedule(user_id: int, hhmm: str) -> bool:
    t = parse_hhmm(hhmm)
    if t is None:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO settings (user_id, schedule_hhmm) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET schedule_hhmm=excluded.schedule_hhmm",
            (user_id, hhmm),
        )
        await db.commit()
    return True


async def get_schedule(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT schedule_hhmm FROM settings WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return str(row[0]) if row and row[0] else None


async def analyze_and_notify(application: Application, user_id: int, chat_id: str) -> None:
    positions = await get_positions(user_id)
    if not positions:
        await application.bot.send_message(chat_id=chat_id, text="Danh mục trống.")
        return

    # Lấy phong cách đầu tư cho từng cổ phiếu
    stock_styles = await get_all_stock_styles(user_id)
    style_text = {"SHORT_TERM": "ngắn hạn", "MEDIUM_TERM": "trung hạn", "LONG_TERM": "dài hạn"}

    lines: List[str] = ["📊 Kết quả phân tích danh mục:"]
    for symbol, qty, avg_cost in positions:
        # Lấy phong cách đầu tư cho cổ phiếu này
        investment_style = stock_styles.get(symbol, InvestmentStyle.MEDIUM_TERM)
        
        price = await MarketData.get_price(symbol)
        pred = await PredictionEngine.predict(symbol, investment_style)
        decision = pred.decision
        conf_pct = int(pred.confidence * 100)
        price_str = f"{price:.2f} (real-time)" if price is not None else "N/A"
        pnl_val = (price - avg_cost) * qty if price is not None else None
        pnl_str = f"{pnl_val:.2f}" if pnl_val is not None else "N/A"
        
        # Thêm kịch bản dự đoán
        scenario_text = ""
        if pred.scenarios:
            top_scenario = max(pred.scenarios.items(), key=lambda x: x[1])
            scenario_text = f" | Kịch bản: {top_scenario[0]} ({top_scenario[1]*100:.0f}%)"
        
        lines.append(
            f"- {symbol} ({style_text[investment_style.value]}): {decision} (conf {conf_pct}%), Giá={price_str}, SL={qty:g}, Giá vốn={avg_cost:.2f}, Lãi/lỗ={pnl_str}{scenario_text}"
        )
    await application.bot.send_message(chat_id=chat_id, text="\n".join(lines))


async def reset_user_data(application: Application, user_id: int) -> None:
    """Delete user's positions, transactions, and settings. Keep user row for chat mapping.

    Also remove any scheduled jobs for this user.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM positions WHERE user_id=?", (user_id,))
        await db.execute("DELETE FROM transactions WHERE user_id=?", (user_id,))
        await db.execute("DELETE FROM settings WHERE user_id=?", (user_id,))
        await db.commit()
    # Remove scheduled jobs if JobQueue is available
    if application.job_queue is not None:
        job_name = f"daily_analysis_{user_id}"
        for job in application.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()


# Telegram command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await upsert_user(user_id, chat_id)
    await update.message.reply_text(
        f"🚀 **Chào mừng đến với VN Stock Advisor Bot!**\n\n"
        f"✅ **Đã kích hoạt bot cho user {user_id}**\n"
        f"📱 **Chat ID: {chat_id}**\n\n"
        "Bây giờ bot có thể gửi thông báo tự động cho bạn!\n"
        "Dùng /help để xem hướng dẫn đầy đủ."
    )


async def test_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test notification command."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await upsert_user(user_id, chat_id)
    
    test_message = (
        "🧪 **Test Notification**\n\n"
        f"✅ User ID: {user_id}\n"
        f"📱 Chat ID: {chat_id}\n"
        f"⏰ Time: {datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%H:%M:%S')}\n\n"
        "Nếu bạn thấy tin nhắn này, bot đã hoạt động bình thường!" 
    )
    
    await update.message.reply_text(test_message)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Lệnh khả dụng:\n"
        "/start — khởi động bot và kích hoạt thông báo\n"
        "/test_notification — test khả năng gửi thông báo\n"
        "/add <mã> <số_lượng> <giá> <stoploss%> — mua thêm\n"
        "/sell <mã> <số_lượng> <giá> — bán\n"
        "/set_stoploss <mã> <phần trăm> — đặt stoploss cho từng cổ phiếu\n"
        "/set_cost <mã> <giá_vốn> — cập nhật giá vốn cổ phiếu\n"
        "/set_trailing_stop <mã> <phần_trăm> [on/off] — đặt trailing stop động\n"
        "/trailing_config — xem cấu hình trailing stop\n"
        "/portfolio — xem danh mục\n"
        "/pnl — thống kê lãi lỗ theo giá hiện tại\n"
        "/analyze_now — phân tích ngay và gợi ý hành động\n"
        "/predict <mã> — dự đoán giá với phân tích kỹ thuật chi tiết\n"
        "\n"
        "🎯 Phong cách đầu tư (theo từng cổ phiếu):\n"
        "/set_style <mã> <SHORT_TERM|MEDIUM_TERM|LONG_TERM> — đặt phong cách đầu tư cho cổ phiếu\n"
        "/my_style — xem phong cách đầu tư cho tất cả cổ phiếu\n"
        "\n"
        "📝 Danh sách theo dõi (Watchlist):\n"
        "/watch_add <mã> [giá_mục_tiêu] [ghi_chú] — thêm cổ phiếu vào danh sách theo dõi\n"
        "/watch_remove <mã> — xóa cổ phiếu khỏi danh sách theo dõi\n"
        "/watch_list — xem danh sách theo dõi\n"
        "/watch_clear — xóa toàn bộ danh sách theo dõi\n"
        "💡 Bot sẽ phân tích và gợi ý mua khi có tín hiệu tốt\n"
        "\n"
        "⚙️ Quản lý:\n"
        "/reset — xóa toàn bộ dữ liệu danh mục (cần xác nhận)\n"
        "/confirm_reset — xác nhận xóa dữ liệu\n"
        "/cancel_reset — hủy yêu cầu xóa\n"
        "/restart — khởi động lại bot (nạp thay đổi mới)\n"
        "\n"
        "📊 Tracking tự động:\n"
        "/track_on — bật tracking tự động\n"
        "/track_off — tắt tracking tự động\n"
        "/track_now — tracking ngay lập tức\n"
        "/track_ping — kiểm tra tracking\n"
        "/track_now_summary — tracking ngay lập tức và tóm tắt cuối ngày\n"
        "/track_bind — gắn tracking với chat\n"
        "/track_config — xem cấu hình tracking\n"
        "⛔ Stoploss: tự động theo dõi từng cổ phiếu\n"
        "🎯 Trailing Stop: dừng lỗ động, bảo vệ lợi nhuận\n"
        "🚀 Breakout: gợi ý mua thêm khi xác nhận\n"
        "🔮 Dự đoán: phân tích kỹ thuật với kịch bản xác suất\n"
        "\n"
        "📈 Phân tích thị trường:\n"
        "/market_report — báo cáo thị trường ngay lập tức\n"
        "/market_report_schedule — lên lịch báo cáo 8h15 hàng ngày\n"
        "/market_report_off — tắt báo cáo tự động\n"
        "🔍 Tích hợp SERPER + Gemini/OpenAI cho phân tích tin tức\n"
        "📊 Dự báo VN-Index dựa trên sentiment + kỹ thuật\n"
        "\n"
        "🧪 Test & Debug:\n"
        "/test_notification — gửi thông báo test ngay lập tức\n"
        "/test_15s — bắt đầu test gửi thông báo mỗi 15 giây\n"
        "/test_15s_stop — dừng test 15 giây\n"
        "/test_job_status — xem trạng thái các job đang chạy\n"
        "/test_price <mã> — test lấy giá real-time\n"
        "/debug_pnl — debug tính toán lãi/lỗ chi tiết\n"
        "\n"
        "📊 Tracking 15s (Real-time):\n"
        "/track_15s — bắt đầu tracking portfolio mỗi 15 giây\n"
        "/track_15s_stop — dừng tracking 15 giây\n"
        "🔄 Hiển thị giá real-time, PnL, và tổng kết danh mục\n"
        "📈 Chỉ báo xu hướng: 📈 tăng, 📉 giảm, ➡️ không đổi\n"
        "\n"
        "🧠 Smart Tracking (Chỉ cảnh báo quan trọng):\n"
        "/smart_track — bắt đầu smart tracking 15s\n"
        "/smart_track_stop — dừng smart tracking\n"
        "🚨 Chỉ gửi thông báo khi: Stoploss, Take Profit, Volume bất thường\n"
        "💡 Gợi ý hành động cụ thể cho từng tình huống\n"
        "\n"
        "💡 Phong cách đầu tư (theo từng cổ phiếu):\n"
        "• SHORT_TERM: 1-2 tuần, trading T+, dữ liệu 3 tháng\n"
        "• MEDIUM_TERM: 1-6 tháng, xu hướng trung hạn, dữ liệu 1 năm\n"
        "• LONG_TERM: 6+ tháng, value investing, dữ liệu 3 năm + P/E/P/B/ROE\n"
        "\n"
        "📝 Ví dụ: /set_style VIC LONG_TERM (đầu tư dài hạn VIC)\n"
        "📝 Ví dụ: /set_style FPT SHORT_TERM (trading ngắn hạn FPT)\n"
        "\n"
        "🎯 Trailing Stop (Dừng lỗ động):\n"
        "• Mua HPG 30, đặt trailing stop 10%\n"
        "• Giá tăng 36 → trailing stop = 32.4 (36-10%)\n"
        "• Giá giảm 32.4 → bán chốt lời +8%\n"
        "• Bảo vệ lợi nhuận, hạn chế rủi ro\n"
        "📝 Ví dụ: /set_trailing_stop HPG 0.10 (10% trailing stop)\n"
    )
    await update.message.reply_text(text)


async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if len(context.args) != 4:
        await update.message.reply_text("Cú pháp: /add <mã> <số_lượng> <giá> <stoploss%>\nVí dụ: /add VIC 100 50000 0.08 (8%)")
        return
    symbol = context.args[0].upper()
    try:
        qty = float(context.args[1])
        price = float(context.args[2])
        stoploss_pct = float(context.args[3])
        if stoploss_pct <= 0 or stoploss_pct > 1:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Số lượng, giá và stoploss phải là số hợp lệ. Stoploss từ 0.01 đến 1.0 (1% đến 100%)")
        return
    
    await add_transaction_and_update_position(user_id, symbol, "BUY", qty, price)
    
    # Tự động set stoploss cho cổ phiếu này
    await set_stock_stoploss(user_id, symbol, stoploss_pct)
    
    # Check if symbol was in watchlist and remove it
    was_in_watchlist = await is_in_watchlist(user_id, symbol)
    if was_in_watchlist:
        await remove_from_watchlist(user_id, symbol)
        print(f"✅ Removed {symbol} from watchlist after purchase")
    
    # Prepare response message
    response_msg = f"✅ Đã mua {qty:g} {symbol} giá {price:.2f}.\n"
    response_msg += f"📊 Stoploss đã được đặt: {stoploss_pct*100:.0f}% (giá: {price*(1-stoploss_pct):.2f})"
    
    if was_in_watchlist:
        response_msg += f"\n📝 Đã xóa {symbol} khỏi danh sách theo dõi (đã mua)"
    
    await update.message.reply_text(response_msg)
    
    # Tự động đặt phong cách đầu tư mặc định nếu chưa có
    current_style = await get_stock_investment_style(user_id, symbol)
    if current_style == InvestmentStyle.MEDIUM_TERM:
        # Chỉ hiển thị prompt nếu chưa được đặt
        await update.message.reply_text(
            f"💡 Để tùy chỉnh phân tích cho {symbol}:\n"
            f"• Đặt stoploss: /set_stoploss {symbol} <phần trăm>\n"
            f"• Đặt phong cách đầu tư: /set_style {symbol} <SHORT_TERM|MEDIUM_TERM|LONG_TERM>\n"
            f"• Mặc định: MEDIUM_TERM (trung hạn)"
        )


async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if len(context.args) != 3:
        await update.message.reply_text("Cú pháp: /sell <mã> <số_lượng> <giá>")
        return
    symbol = context.args[0].upper()
    try:
        qty = float(context.args[1])
        price = float(context.args[2])
    except ValueError:
        await update.message.reply_text("Số lượng và giá phải là số.")
        return
    await add_transaction_and_update_position(user_id, symbol, "SELL", qty, price)
    await update.message.reply_text(f"Đã bán {qty:g} {symbol} giá {price:.2f}.")


async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    positions = await get_positions(user_id)
    if not positions:
        await update.message.reply_text("Danh mục trống.")
        return
    # Build a simple monospaced table
    rows = []
    header = ("Mã", "Số lượng", "Giá vốn", "Giá RT", "Lãi/lỗ", "Stoploss/Trailing")
    rows.append(header)
    for symbol, qty, avg_cost in positions:
        # Recompute avg_cost using FIFO for accuracy after sells
        fifo_avg = await compute_effective_avg_cost_fifo(user_id, symbol)
        effective_avg = fifo_avg if fifo_avg is not None else avg_cost
        price = await MarketData.get_price(symbol)
        price_str = f"{price:.2f} (RT)" if price is not None else "N/A"
        pnl_val = ((price - effective_avg) * qty) if price is not None else None
        pnl_str = f"{pnl_val:.2f}" if pnl_val is not None else "N/A"
        
        # Check if trailing stop is enabled
        trailing_settings = await get_trailing_stop_settings(user_id, symbol)
        if trailing_settings and trailing_settings['enabled']:
            # Update trailing stop to get current values
            trailing_stop_price = await update_trailing_stop_price(user_id, symbol, price) if price else None
            if trailing_stop_price:
                trailing_str = f"T:{trailing_stop_price:.2f} ({trailing_settings['trailing_pct']*100:.0f}%)"
            else:
                trailing_str = f"T:Active ({trailing_settings['trailing_pct']*100:.0f}%)"
        else:
            # Regular stoploss
            stoploss_pct = await get_stock_stoploss(user_id, symbol)
            stoploss_val = effective_avg * (1 - stoploss_pct)
            trailing_str = f"SL:{stoploss_val:.2f} ({stoploss_pct*100:.0f}%)"
        
        rows.append((symbol, f"{qty:g}", f"{effective_avg:.2f}", price_str, pnl_str, trailing_str))

    # Column widths
    col_widths = [0, 0, 0, 0, 0, 0]
    for r in rows:
        for i, val in enumerate(r):
            col_widths[i] = max(col_widths[i], len(str(val)))

    def fmt_row(r: tuple) -> str:
        return (
            f"{str(r[0]).ljust(col_widths[0])}  "
            f"{str(r[1]).rjust(col_widths[1])}  "
            f"{str(r[2]).rjust(col_widths[2])}  "
            f"{str(r[3]).rjust(col_widths[3])}  "
            f"{str(r[4]).rjust(col_widths[4])}  "
            f"{str(r[5]).rjust(col_widths[5])}"
        )

    table_lines = [
        fmt_row(rows[0]),
        fmt_row((
            "-" * col_widths[0],
            "-" * col_widths[1],
            "-" * col_widths[2],
            "-" * col_widths[3],
            "-" * col_widths[4],
            "-" * col_widths[5],
        )),
    ]
    for r in rows[1:]:
        table_lines.append(fmt_row(r))

    msg_lines = ["Danh mục hiện tại:", *table_lines]
    await update.message.reply_text("\n".join(msg_lines))


async def pnl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    report = await get_pnl_report(user_id)
    if not report:
        await update.message.reply_text("Danh mục trống.")
        return
    lines = ["PnL theo giá real-time:"]
    total_pnl = 0.0
    for symbol, qty, avg_cost, price, pnl in report:
        price_str = f"{price:.2f} (RT)" if price is not None else "N/A"
        pnl_str = f"{pnl:.2f}" if pnl is not None else "N/A"
        if pnl is not None:
            total_pnl += pnl
        lines.append(
            f"- {symbol}: Giá={price_str}, SL={qty:g}, Giá vốn={avg_cost:.2f}, Lãi/lỗ={pnl_str}"
        )
    lines.append(f"Tổng lãi/lỗ: {total_pnl:.2f}")
    await update.message.reply_text("\n".join(lines))


async def analyze_now_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    await analyze_and_notify(context.application, user_id, chat_id)


async def predict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dự đoán giá cho một cổ phiếu cụ thể theo phong cách đầu tư của cổ phiếu đó"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    if len(context.args) != 1:
        await update.message.reply_text("Cú pháp: /predict <mã cổ phiếu>\nVí dụ: /predict VIC")
        return
    
    symbol = context.args[0].upper().strip()
    
    # Lấy phong cách đầu tư cho cổ phiếu này
    investment_style = await get_stock_investment_style(user_id, symbol)
    
    # Gửi thông báo đang xử lý
    style_text = {"SHORT_TERM": "ngắn hạn", "MEDIUM_TERM": "trung hạn", "LONG_TERM": "dài hạn"}
    processing_msg = await update.message.reply_text(f"🔍 Đang phân tích {symbol} ({style_text[investment_style.value]})...")
    
    try:
        # Lấy giá real-time trước
        real_time_price = await MarketData.get_price(symbol)
        
        # Lấy dự đoán theo phong cách đầu tư
        pred = await PredictionEngine.predict(symbol, investment_style)
        
        # Tạo thông báo chi tiết
        lines = [f"📈 Dự đoán cho {symbol} ({style_text[investment_style.value]}):"]
        lines.append(f"🎯 Quyết định: {pred.decision}")
        lines.append(f"📊 Độ tin cậy: {pred.confidence*100:.1f}%")
        lines.append(f"💡 Lý do: {pred.rationale}")
        lines.append(f"⏰ Khung thời gian: {pred.timeframe}")
        
        # Hiển thị giá real-time
        if real_time_price is not None:
            lines.append(f"💰 Giá real-time: {real_time_price:.2f} VND")
        else:
            lines.append("💰 Giá real-time: Không có dữ liệu")
        
        # Thêm kịch bản
        if pred.scenarios:
            lines.append("\n🎲 Các kịch bản có thể:")
            for scenario, prob in sorted(pred.scenarios.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  • {scenario}: {prob*100:.1f}%")
        
        # Thêm tín hiệu kỹ thuật
        if pred.technical_signals:
            signals = pred.technical_signals
            lines.append("\n📊 Chỉ báo kỹ thuật:")
            if signals.get('current_price'):
                lines.append(f"  • Giá phân tích: {signals['current_price']:.2f} (từ dữ liệu lịch sử)")
            
            # Hiển thị MA phù hợp với timeframe
            if investment_style == InvestmentStyle.SHORT_TERM:
                if signals.get('sma_short'):
                    lines.append(f"  • MA5: {signals['sma_short']:.2f}")
                if signals.get('sma_medium'):
                    lines.append(f"  • MA10: {signals['sma_medium']:.2f}")
            elif investment_style == InvestmentStyle.MEDIUM_TERM:
                if signals.get('sma_short'):
                    lines.append(f"  • MA20: {signals['sma_short']:.2f}")
                if signals.get('sma_medium'):
                    lines.append(f"  • MA50: {signals['sma_medium']:.2f}")
            else:  # LONG_TERM
                if signals.get('sma_short'):
                    lines.append(f"  • MA50: {signals['sma_short']:.2f}")
                if signals.get('sma_medium'):
                    lines.append(f"  • MA100: {signals['sma_medium']:.2f}")
                if signals.get('sma_long'):
                    lines.append(f"  • MA200: {signals['sma_long']:.2f}")
            
            if signals.get('rsi'):
                rsi_val = signals['rsi']
                rsi_status = "Oversold" if rsi_val < 30 else "Overbought" if rsi_val > 70 else "Neutral"
                lines.append(f"  • RSI: {rsi_val:.1f} ({rsi_status})")
            if signals.get('macd') and signals.get('macd_signal'):
                macd_trend = "Bullish" if signals['macd'] > signals['macd_signal'] else "Bearish"
                lines.append(f"  • MACD: {macd_trend}")
        
        # Thêm phân tích cơ bản cho đầu tư dài hạn
        if investment_style == InvestmentStyle.LONG_TERM and pred.technical_signals:
            signals = pred.technical_signals
            if signals.get('fundamental_analysis'):
                lines.append("\n🏢 Phân tích cơ bản:")
                for analysis in signals['fundamental_analysis']:
                    lines.append(f"  • {analysis}")
            
            if signals.get('pe_ratio') or signals.get('pb_ratio') or signals.get('roe'):
                lines.append("\n📊 Chỉ số tài chính:")
                if signals.get('pe_ratio'):
                    lines.append(f"  • P/E: {signals['pe_ratio']:.1f}")
                if signals.get('pb_ratio'):
                    lines.append(f"  • P/B: {signals['pb_ratio']:.1f}")
                if signals.get('roe'):
                    lines.append(f"  • ROE: {signals['roe']:.1f}%")
        
        # Gửi kết quả
        result_text = "\n".join(lines)
        await processing_msg.edit_text(result_text)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Lỗi khi phân tích {symbol}: {str(e)}")


async def set_style_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Đặt phong cách đầu tư cho một cổ phiếu cụ thể"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "Cú pháp: /set_style <mã_cổ_phiếu> <phong_cách>\n"
            "Phong cách khả dụng:\n"
            "• SHORT_TERM - Ngắn hạn (1-2 tuần, trading T+)\n"
            "• MEDIUM_TERM - Trung hạn (1-6 tháng)\n"
            "• LONG_TERM - Dài hạn (6+ tháng, value investing)\n"
            "Ví dụ: /set_style VIC LONG_TERM"
        )
        return
    
    symbol = context.args[0].upper().strip()
    style_arg = context.args[1].upper().strip()
    
    try:
        investment_style = InvestmentStyle(style_arg)
        await set_stock_investment_style(user_id, symbol, investment_style)
        
        style_names = {
            InvestmentStyle.SHORT_TERM: "Ngắn hạn (1-2 tuần, trading T+)",
            InvestmentStyle.MEDIUM_TERM: "Trung hạn (1-6 tháng)",
            InvestmentStyle.LONG_TERM: "Dài hạn (6+ tháng, value investing)"
        }
        
        await update.message.reply_text(
            f"✅ Đã đặt phong cách đầu tư cho {symbol}: {style_names[investment_style]}\n"
            f"📊 Dữ liệu phân tích: {PredictionEngine.get_data_period_for_style(investment_style)} ngày\n"
            f"🎯 Chỉ báo kỹ thuật được tối ưu cho timeframe này"
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Phong cách đầu tư không hợp lệ.\n"
            "Sử dụng: SHORT_TERM, MEDIUM_TERM, hoặc LONG_TERM"
        )


async def my_style_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hiển thị phong cách đầu tư cho tất cả cổ phiếu trong danh mục"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    # Lấy danh mục và phong cách đầu tư
    positions = await get_positions(user_id)
    stock_styles = await get_all_stock_styles(user_id)
    
    if not positions:
        await update.message.reply_text("Danh mục trống. Thêm cổ phiếu trước khi xem phong cách đầu tư.")
        return
    
    style_names = {
        InvestmentStyle.SHORT_TERM: "Ngắn hạn",
        InvestmentStyle.MEDIUM_TERM: "Trung hạn", 
        InvestmentStyle.LONG_TERM: "Dài hạn"
    }
    
    lines = ["📊 Phong cách đầu tư cho từng cổ phiếu:"]
    for symbol, qty, avg_cost in positions:
        investment_style = stock_styles.get(symbol, InvestmentStyle.MEDIUM_TERM)
        lines.append(f"• {symbol}: {style_names[investment_style]} (SL: {qty:g})")
    
    lines.append("\n💡 Dùng /set_style <mã> <phong_cách> để thay đổi")
    lines.append("\n📋 Phong cách khả dụng:")
    lines.append("• SHORT_TERM - 1-2 tuần, trading T+")
    lines.append("• MEDIUM_TERM - 1-6 tháng, xu hướng")
    lines.append("• LONG_TERM - 6+ tháng, value investing")
    
    await update.message.reply_text("\n".join(lines))


# Watchlist commands
async def watch_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Thêm cổ phiếu vào danh sách theo dõi"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "📝 **Thêm cổ phiếu vào danh sách theo dõi**\n\n"
            "Cú pháp: `/watch_add <mã_cổ_phiếu> [giá_mục_tiêu] [ghi_chú]`\n\n"
            "Ví dụ:\n"
            "• `/watch_add VIC` - Theo dõi VIC\n"
            "• `/watch_add VIC 50000` - Theo dõi VIC với giá mục tiêu 50,000\n"
            "• `/watch_add VIC 50000 Cổ phiếu tiềm năng` - Thêm ghi chú\n\n"
            "💡 Cổ phiếu trong danh sách theo dõi sẽ được phân tích và gợi ý mua khi có tín hiệu tốt."
        )
        return
    
    symbol = context.args[0].upper()
    target_price = None
    notes = None
    
    # Parse target price if provided
    if len(context.args) > 1:
        try:
            target_price = float(context.args[1])
        except ValueError:
            # If second arg is not a number, treat it as notes
            notes = " ".join(context.args[1:])
    
    # Parse notes if target price was provided
    if len(context.args) > 2 and target_price is not None:
        notes = " ".join(context.args[2:])
    
    # Check if already in portfolio
    positions = await get_positions(user_id)
    if any(pos[0] == symbol for pos in positions):
        await update.message.reply_text(f"❌ {symbol} đã có trong danh mục. Dùng /add để thêm số lượng.")
        return
    
    # Add to watchlist
    success = await add_to_watchlist(user_id, symbol, target_price, notes)
    
    if success:
        msg = f"✅ Đã thêm {symbol} vào danh sách theo dõi"
        if target_price:
            msg += f"\n💰 Giá mục tiêu: {target_price:,.0f}"
        if notes:
            msg += f"\n📝 Ghi chú: {notes}"
        msg += "\n\n💡 Bot sẽ phân tích và gợi ý mua khi có tín hiệu tốt."
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(f"❌ Lỗi khi thêm {symbol} vào danh sách theo dõi.")


async def watch_remove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xóa cổ phiếu khỏi danh sách theo dõi"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "🗑️ **Xóa cổ phiếu khỏi danh sách theo dõi**\n\n"
            "Cú pháp: `/watch_remove <mã_cổ_phiếu>`\n\n"
            "Ví dụ: `/watch_remove VIC`"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Check if in watchlist
    if not await is_in_watchlist(user_id, symbol):
        await update.message.reply_text(f"❌ {symbol} không có trong danh sách theo dõi.")
        return
    
    # Remove from watchlist
    success = await remove_from_watchlist(user_id, symbol)
    
    if success:
        await update.message.reply_text(f"✅ Đã xóa {symbol} khỏi danh sách theo dõi.")
    else:
        await update.message.reply_text(f"❌ Lỗi khi xóa {symbol} khỏi danh sách theo dõi.")


async def watch_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hiển thị danh sách theo dõi"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    watchlist = await get_watchlist(user_id)
    
    if not watchlist:
        await update.message.reply_text(
            "📝 **Danh sách theo dõi trống**\n\n"
            "Dùng `/watch_add <mã_cổ_phiếu>` để thêm cổ phiếu vào danh sách theo dõi.\n"
            "Bot sẽ phân tích và gợi ý mua khi có tín hiệu tốt."
        )
        return
    
    lines = ["📝 **Danh sách theo dõi:**\n"]
    
    for i, (symbol, target_price, notes, added_at) in enumerate(watchlist, 1):
        lines.append(f"**{i}. {symbol}**")
        if target_price:
            lines.append(f"   💰 Giá mục tiêu: {target_price:,.0f}")
        if notes:
            lines.append(f"   📝 Ghi chú: {notes}")
        
        # Format added date
        try:
            added_date = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
            added_date_str = added_date.strftime("%d/%m/%Y %H:%M")
            lines.append(f"   📅 Thêm lúc: {added_date_str}")
        except:
            lines.append(f"   📅 Thêm lúc: {added_at}")
        
        lines.append("")  # Empty line between items
    
    lines.append("💡 Dùng `/watch_remove <mã>` để xóa khỏi danh sách.")
    
    await update.message.reply_text("\n".join(lines))


async def watch_clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xóa toàn bộ danh sách theo dõi"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    watchlist = await get_watchlist(user_id)
    
    if not watchlist:
        await update.message.reply_text("📝 Danh sách theo dõi đã trống.")
        return
    
    # Show confirmation
    await update.message.reply_text(
        f"⚠️ **Xác nhận xóa toàn bộ danh sách theo dõi**\n\n"
        f"Bạn có {len(watchlist)} cổ phiếu trong danh sách theo dõi:\n"
        f"{', '.join([item[0] for item in watchlist])}\n\n"
        f"Gõ `/confirm_watch_clear` để xác nhận xóa toàn bộ danh sách."
    )


async def confirm_watch_clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xác nhận xóa toàn bộ danh sách theo dõi"""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    success = await clear_watchlist(user_id)
    
    if success:
        await update.message.reply_text("✅ Đã xóa toàn bộ danh sách theo dõi.")
    else:
        await update.message.reply_text("❌ Lỗi khi xóa danh sách theo dõi.")


# (Deprecated) set_schedule_cmd removed; use /track_on or /track_off instead


# Pending reset state (in-memory with TTL)
PENDING_RESET: dict[int, datetime] = {}
RESET_TTL_SECONDS = 120


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    PENDING_RESET[user_id] = datetime.now(timezone.utc)
    await update.message.reply_text(
        "Bạn có chắc muốn xóa toàn bộ danh mục và lịch?\n"
        "Gõ /confirm_reset trong vòng 2 phút để xác nhận, hoặc /cancel_reset để hủy."
    )


async def confirm_reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    ts = PENDING_RESET.get(user_id)
    if ts is None:
        await update.message.reply_text("Không có yêu cầu xóa nào đang chờ.")
        return
    if (datetime.now(timezone.utc) - ts).total_seconds() > RESET_TTL_SECONDS:
        del PENDING_RESET[user_id]
        await update.message.reply_text("Yêu cầu xóa đã hết hạn. Hãy gõ /reset lại nếu vẫn muốn xóa.")
        return
    # Proceed reset
    await reset_user_data(context.application, user_id)
    del PENDING_RESET[user_id]
    await context.application.bot.send_message(chat_id=chat_id, text="Đã xóa toàn bộ danh mục, giao dịch và lịch.")


async def cancel_reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if user_id in PENDING_RESET:
        del PENDING_RESET[user_id]
        await update.message.reply_text("Đã hủy yêu cầu xóa dữ liệu.")
    else:
        await update.message.reply_text("Không có yêu cầu xóa nào đang chờ.")


# Auto-tracking is now enabled by default on trading days
# Manual tracking commands removed - tracking is automatic


async def set_stoploss_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set individual stoploss for a specific stock."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if len(context.args) != 2:
        await update.message.reply_text("Cú pháp: /set_stoploss <mã> <stoploss%>\nVí dụ: /set_stoploss VIC 0.08 (8%)")
        return
    
    symbol = context.args[0].upper()
    try:
        stoploss_pct = float(context.args[1])
        if stoploss_pct <= 0 or stoploss_pct > 1:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Stoploss phải là số từ 0.01 đến 1.0 (1% đến 100%)")
        return
    
    # Check if user has this stock in portfolio
    positions = await get_positions(user_id)
    if not any(pos[0] == symbol for pos in positions):
        await update.message.reply_text(f"Bạn chưa có {symbol} trong danh mục.")
        return
    
    await set_stock_stoploss(user_id, symbol, stoploss_pct)
    await update.message.reply_text(f"✅ Đã đặt stoploss {symbol}: {stoploss_pct*100:.1f}%")


async def set_cost_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set cost price for a specific stock in portfolio."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    if len(context.args) != 2:
        await update.message.reply_text("Cú pháp: /set_cost <mã> <giá_vốn>\nVí dụ: /set_cost VIC 45000")
        return
    
    symbol = context.args[0].upper()
    try:
        new_cost = float(context.args[1])
        if new_cost <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Giá vốn phải là số dương")
        return
    
    # Check if user has this stock in portfolio
    positions = await get_positions(user_id)
    position = next((pos for pos in positions if pos[0] == symbol), None)
    if not position:
        await update.message.reply_text(f"Bạn chưa có {symbol} trong danh mục.")
        return
    
    _, quantity, old_cost = position
    
    # Update the cost price in database
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE positions SET avg_cost=? WHERE user_id=? AND symbol=?",
            (new_cost, user_id, symbol),
        )
        await db.commit()
    
    if update.message:
        await update.message.reply_text(
            f"✅ Đã cập nhật giá vốn {symbol}:\n"
            f"• Số lượng: {quantity:g}\n"
            f"• Giá vốn cũ: {old_cost:.2f}\n"
            f"• Giá vốn mới: {new_cost:.2f}\n"
            f"• Chênh lệch: {new_cost - old_cost:+.2f}"
        )
    else:
        print(f"Warning: update.message is None for set_cost_cmd")


async def set_trailing_stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set trailing stop for a specific stock."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "Cú pháp: /set_trailing_stop <mã> <phần_trăm> [on/off]\n"
            "Ví dụ: /set_trailing_stop VIC 0.10 on (10% trailing stop)\n"
            "Ví dụ: /set_trailing_stop VIC 0.10 off (tắt trailing stop)\n"
            "Ví dụ: /set_trailing_stop VIC 0.10 (bật trailing stop với 10%)"
        )
        return
    
    symbol = context.args[0].upper()
    try:
        trailing_pct = float(context.args[1])
        if trailing_pct <= 0 or trailing_pct > 1:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Phần trăm trailing stop phải từ 0.01 đến 1.0 (1% đến 100%)")
        return
    
    # Check if user has this stock in portfolio
    positions = await get_positions(user_id)
    if not any(pos[0] == symbol for pos in positions):
        await update.message.reply_text(f"Bạn chưa có {symbol} trong danh mục.")
        return
    
    # Check enable/disable flag
    enabled = True
    if len(context.args) >= 3:
        flag = context.args[2].lower()
        if flag == "off":
            enabled = False
        elif flag == "on":
            enabled = True
        else:
            await update.message.reply_text("Flag phải là 'on' hoặc 'off'")
            return
    
    try:
        if enabled:
            # Get current price to set initial trailing stop
            current_price = await MarketData.get_price(symbol)
            if current_price is None:
                await update.message.reply_text(f"Không thể lấy giá hiện tại cho {symbol}")
                return
            
            await set_trailing_stop_settings(user_id, symbol, True, trailing_pct)
            
            await update.message.reply_text(
                f"✅ Đã bật Trailing Stop cho {symbol}:\n"
                f"• Phần trăm: {trailing_pct*100:.1f}%\n"
                f"• Giá hiện tại: {current_price:.2f}\n"
                f"• Trailing Stop: {current_price * (1 - trailing_pct):.2f}\n"
                f"• Highest Price: {current_price:.2f}\n\n"
                f"🎯 Trailing Stop sẽ tự động điều chỉnh khi giá tăng và bảo vệ lợi nhuận khi giá giảm."
            )
        else:
            await set_trailing_stop_settings(user_id, symbol, False, trailing_pct)
            await update.message.reply_text(f"❌ Đã tắt Trailing Stop cho {symbol}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi cài đặt trailing stop: {str(e)}")


async def trailing_config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trailing stop configuration for all stocks."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    positions = await get_positions(user_id)
    if not positions:
        await update.message.reply_text("Danh mục trống. Thêm cổ phiếu trước khi cài đặt trailing stop.")
        return
    
    trailing_stops = await get_all_trailing_stops(user_id)
    
    lines = ["🎯 **Cấu hình Trailing Stop:**\n"]
    
    for symbol, qty, avg_cost in positions:
        trailing_info = trailing_stops.get(symbol)
        if trailing_info and trailing_info['enabled']:
            current_price = await MarketData.get_price(symbol)
            if current_price:
                # Update trailing stop to get current values
                current_trailing = await update_trailing_stop_price(user_id, symbol, current_price)
                if current_trailing:
                    pnl_pct = ((current_price - avg_cost) / avg_cost) * 100
                    lines.append(
                        f"• **{symbol}**: {current_price:.2f} "
                        f"(Trailing: {current_trailing:.2f}, Highest: {trailing_info['highest_price']:.2f}) "
                        f"- {trailing_info['trailing_pct']*100:.1f}% - PnL: {pnl_pct:+.1f}%"
                    )
                else:
                    lines.append(f"• **{symbol}**: Trailing Stop đã kích hoạt")
            else:
                lines.append(f"• **{symbol}**: {trailing_info['trailing_pct']*100:.1f}% (Không có dữ liệu giá)")
        else:
            lines.append(f"• **{symbol}**: Chưa bật Trailing Stop")
    
    lines.append("\n💡 **Hướng dẫn:**")
    lines.append("• `/set_trailing_stop <mã> <phần_trăm>` - Bật trailing stop")
    lines.append("• `/set_trailing_stop <mã> <phần_trăm> off` - Tắt trailing stop")
    lines.append("• Trailing stop tự động điều chỉnh theo giá cao nhất")
    lines.append("• Khi giá giảm chạm trailing stop → Gợi ý SELL")
    
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the running bot process to load latest code."""
    # Inform user first
    try:
        await update.message.reply_text("Bot sẽ khởi động lại ngay bây giờ...")
    except Exception:
        pass
    # Give Telegram time to deliver the message, then re-exec the process
    async def _do_restart() -> None:
        await asyncio.sleep(1.0)
        os.execv(sys.executable, [sys.executable, *sys.argv])

    asyncio.create_task(_do_restart())


async def track_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable automatic tracking for user's portfolio."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Ensure we store chat_id for this user (needed by scheduler)
        await upsert_user(user_id, chat_id)

        # Check if user has any positions
        positions = await get_positions(user_id)
        if not positions:
            await update.message.reply_text(
                "❌ **Danh mục trống!**\n\n"
                "Bạn cần có cổ phiếu trong danh mục trước khi bật tracking tự động.\n"
                "Sử dụng `/add <mã> <số_lượng> <giá> <stoploss%>` để thêm cổ phiếu.\n\n"
                "**Ví dụ:** `/add VIC 100 45000 0.08`"
            )
            return

        # Enable tracking with default settings (sl_pct will be overridden by individual stock stoploss)
        await set_tracking_settings(user_id, enabled=True, sl_pct=0.05, tp_pct=0.10, vol_ma_days=20)
        print(f"Track ON: Enabled tracking for user {user_id}")
        
        # Start smart tracking during trading hours (9:00-15:00 VN time)
        smart_job_name = f"smart_track_{user_id}"
        for job in context.application.job_queue.get_jobs_by_name(smart_job_name):
            job.schedule_removal()
        
        # Schedule smart tracking job every 15 seconds during trading hours
        job_data = {'user_id': user_id, 'chat_id': str(chat_id)}
        
        # Get current time
        current_time = datetime.now(VN_TZ)
        current_hour = current_time.hour
        
        # Check if we're in trading hours (9:00-15:00)
        if 9 <= current_hour < 15:
            # Currently in trading hours - start immediately
            context.application.job_queue.run_repeating(
                name=smart_job_name,
                interval=timedelta(seconds=15),
                first=datetime.now(VN_TZ) + timedelta(seconds=2),  # Start after 2 seconds
                callback=smart_track_15s_callback,
                data=job_data,
            )
            next_tracking = "Ngay bây giờ (15s)"
            trading_status = "🟢 Đang trong giờ giao dịch"
        else:
            # Outside trading hours - schedule for next trading day
            next_trading_start = datetime.combine(
                current_time.date() + timedelta(days=1) if current_hour >= 15 else current_time.date(),
                time(9, 0, 0, tzinfo=VN_TZ)
            )
            context.application.job_queue.run_repeating(
                name=smart_job_name,
                interval=timedelta(seconds=15),
                first=next_trading_start,
                callback=smart_track_15s_callback,
                data=job_data,
            )
            next_tracking = f"09:00 ngày {next_trading_start.strftime('%d/%m')}"
            trading_status = "🔴 Ngoài giờ giao dịch"
        
        # Also schedule traditional tracking jobs for scheduled times
        await schedule_tracking_jobs(context.application, user_id)
        print(f"Track ON: Scheduled smart tracking + traditional jobs for user {user_id}")
        
        # Verify jobs were scheduled
        job_queue = context.application.job_queue
        user_jobs = []
        if job_queue:
            all_jobs = list(job_queue.jobs())
            user_jobs = [job for job in all_jobs if job.name and f"track_" in job.name and str(user_id) in job.name]
            print(f"Track ON: Found {len(user_jobs)} jobs for user {user_id}")
        
        await update.message.reply_text(
            f"✅ **Smart Tracking đã được bật!**\n\n"
            f"📊 **Danh mục:** {len(positions)} cổ phiếu\n"
            f"• {', '.join([pos[0] for pos in positions])}\n\n"
            f"⏰ **Trạng thái:** {trading_status}\n"
            f"🔄 **Lần theo dõi tiếp theo:** {next_tracking}\n\n"
            f"🧠 **Smart Tracking (15s trong giờ giao dịch 9:00-15:00):**\n"
            f"• 🚨 Stoploss: Giá ≤ SL → Gợi ý SELL\n"
            f"• 🎯 Take Profit: Giá ≥ TP + Volume → Gợi ý chốt lời/mua thêm\n"
            f"• 📊 Volume Spike: Tăng >50% → Gợi ý mua thêm\n"
            f"• 📉 Volume Drop: Giảm >30% → Gợi ý giảm tỷ trọng\n\n"
            f"⏰ **Lịch theo dõi truyền thống:**\n"
            f"• 09:05 - ATO check\n"
            f"• 09:15-10:30 - Mỗi 5 phút\n"
            f"• 10:30-13:30 - Mỗi 5 phút\n"
            f"• 13:30-14:30 - Mỗi 5 phút\n"
            f"• 14:35 - ATC check\n"
            f"• 14:40 - Tóm tắt cuối ngày\n\n"
            f"📈 **Jobs đã lên lịch:** {len(user_jobs)}\n\n"
            f"💡 **Lưu ý:**\n"
            f"• Bot chỉ gửi thông báo khi có tín hiệu quan trọng\n"
            f"• Tracking 15s chỉ hoạt động trong giờ giao dịch\n"
            f"• Sử dụng `/track_15s` để xem tất cả thông tin\n"
            f"• Sử dụng `/smart_track_stop` để tắt smart tracking",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        print(f"Error in track_on_cmd: {e}")
        await update.message.reply_text(f"❌ Lỗi khi bật tracking: {str(e)}")


async def track_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disable automatic tracking for user's portfolio."""
    user_id = update.effective_user.id
    
    # Disable tracking
    await set_tracking_settings(user_id, enabled=False, sl_pct=0.05, tp_pct=0.10, vol_ma_days=20)
    
    # Remove traditional tracking jobs
    for tag in ["ato_once", "morning_5m", "mid_5m", "late_5m", "atc_once", "summary_once"]:
        for job in context.application.job_queue.get_jobs_by_name(_track_job_name(user_id, tag)):
            job.schedule_removal()
    
    # Remove smart tracking job
    smart_job_name = f"smart_track_{user_id}"
    smart_jobs_removed = 0
    for job in context.application.job_queue.get_jobs_by_name(smart_job_name):
        job.schedule_removal()
        smart_jobs_removed += 1
    
    await update.message.reply_text(
        f"❌ **Tracking đã được tắt!**\n\n"
        f"Đã tắt tất cả tracking:\n"
        f"• Traditional tracking jobs\n"
        f"• Smart tracking jobs: {smart_jobs_removed}\n\n"
        f"Bot sẽ không tự động theo dõi portfolio nữa.\n"
        f"Sử dụng `/track_on` để bật lại.",
        parse_mode=ParseMode.MARKDOWN
    )


async def track_config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current tracking configuration and allow modification."""
    user_id = update.effective_user.id
    enabled, sl_pct, tp_pct, vol_ma_days = await get_tracking_settings(user_id)
    
    status = "🟢 BẬT" if enabled else "🔴 TẮT"
    
    # Get individual stoploss settings for each stock
    positions = await get_positions(user_id)
    stoploss_info = []
    if positions:
        for symbol, qty, avg_cost in positions:
            individual_sl = await get_stock_stoploss(user_id, symbol)
            stoploss_info.append(f"• {symbol}: {individual_sl*100:.1f}%")
    
    stoploss_text = "\n".join(stoploss_info) if stoploss_info else "Chưa có cổ phiếu nào"
    
    # Get current jobs status
    job_queue = context.application.job_queue
    user_jobs = []
    if job_queue:
        all_jobs = list(job_queue.jobs())
        user_jobs = [job for job in all_jobs if job.name and f"track_" in job.name and str(user_id) in job.name]
    
    # Get current time and next tracking time
    current_time = datetime.now(VN_TZ)
    next_tracking = "09:05" if current_time.time() < time(9, 5) else "Hôm sau 09:05"
    
    await update.message.reply_text(
        f"📊 **Cấu hình Tracking hiện tại:**\n\n"
        f"**Trạng thái:** {status}\n"
        f"**Danh mục:** {len(positions)} cổ phiếu\n"
        f"**Stop Loss theo cổ phiếu:**\n{stoploss_text}\n"
        f"**Take Profit:** {tp_pct*100:.0f}%\n"
        f"**Volume MA:** {vol_ma_days} ngày\n\n"
        f"**Lịch theo dõi:**\n"
        f"• 09:05 - ATO check\n"
        f"• 09:15-10:30 - Mỗi 5 phút\n"
        f"• 10:30-13:30 - Mỗi 5 phút\n"
        f"• 13:30-14:30 - Mỗi 5 phút\n"
        f"• 14:35 - ATC check\n"
        f"• 14:40 - Tóm tắt cuối ngày\n\n"
        f"**Thông tin hiện tại:**\n"
        f"• Lần theo dõi tiếp theo: {next_tracking}\n"
        f"• Jobs đang chạy: {len(user_jobs)}\n"
        f"• Thời gian hiện tại: {current_time.strftime('%H:%M:%S %d/%m/%Y')}\n\n"
        f"**Commands:**\n"
        f"• `/track_on` - Bật tracking\n"
        f"• `/track_off` - Tắt tracking\n"
        f"• `/track_15s` - Tracking real-time 15s\n"
        f"• `/track_config` - Xem cấu hình",
        parse_mode=ParseMode.MARKDOWN
    )




async def track_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show scheduled tracking jobs and next run times for current user."""
    user_id = update.effective_user.id
    # Ensure current chat is recorded to avoid stale chat_id issues
    try:
        await upsert_user(user_id, update.effective_chat.id)
    except Exception:
        pass
    jq = context.application.job_queue
    if jq is None:
        await update.message.reply_text("JobQueue is None")
        return
    jobs = [job for job in jq.jobs() if job.name and job.name.startswith(f"track_") and str(user_id) in job.name]
    if not jobs:
        await update.message.reply_text("Không có tracking job nào đang chạy.")
        return
    lines = ["Các tracking jobs:"]
    for job in jobs:
        next_run = getattr(job, "next_t", None) or getattr(job, "next_run_time", None)
        lines.append(f"- {job.name} | next: {next_run}")
    await update.message.reply_text("\n".join(lines))


async def track_now_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Schedule an immediate one-off tracking run to verify execution."""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    jq = context.application.job_queue
    if jq is None:
        await update.message.reply_text("JobQueue is None")
        return
    # Ensure chat is recorded for this user
    await upsert_user(user_id, chat_id)
    # Remove any existing immediate job with the same name to allow re-scheduling
    immediate_name = _track_job_name(user_id, "immediate")
    for job in jq.get_jobs_by_name(immediate_name):
        job.schedule_removal()
    # Schedule once after ~2 seconds; use numeric seconds for maximum compatibility
    data = {'user_id': user_id, 'chat_id': chat_id, 'job_type': 'check_positions'}
    jq.run_once(callback=tracking_callback, when=2, name=immediate_name, data=data)
    await update.message.reply_text("Đã schedule chạy thử sau 2 giây. Đang chạy ngay bây giờ...")
    # Also trigger immediately to avoid any scheduler edge cases
    try:
        await check_positions_and_alert(context.application, user_id, chat_id, force_status=True)
    except Exception as e:
        try:
            await update.message.reply_text(f"❌ Lỗi khi chạy ngay: {e}")
        except Exception:
            pass


async def track_ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a test message to verify the bot can send messages to this chat."""
    await update.message.reply_text("Pong ✅ Bot có thể gửi tin nhắn.")


async def track_now_summary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Schedule an immediate one-off SUMMARY run to verify EOD callback."""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    jq = context.application.job_queue
    if jq is None:
        await update.message.reply_text("JobQueue is None")
        return
    data = {'user_id': user_id, 'chat_id': chat_id, 'job_type': 'summary'}
    # Remove any existing immediate summary job with the same name
    immediate_sum_name = _track_job_name(user_id, "immediate_summary")
    for job in jq.get_jobs_by_name(immediate_sum_name):
        job.schedule_removal()
    jq.run_once(callback=tracking_callback, when=2, name=immediate_sum_name, data=data)
    await update.message.reply_text("Đã schedule chạy thử SUMMARY sau 2 giây. Đang chạy ngay bây giờ...")
    # Also trigger immediately
    try:
        await summarize_eod_and_outlook(context.application, user_id, chat_id)
    except Exception as e:
        try:
            await update.message.reply_text(f"❌ Lỗi khi chạy SUMMARY ngay: {e}")
        except Exception:
            pass


async def track_bind_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bind auto-tracking messages to THIS chat and reschedule jobs."""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    try:
        await upsert_user(user_id, chat_id)
        # Reschedule tracking jobs to use the new chat binding
        await schedule_tracking_jobs(context.application, user_id)
        await update.message.reply_text("✅ Đã liên kết chat hiện tại để nhận thông báo tự động.")
    except Exception as e:
        await update.message.reply_text(f"❌ Không thể liên kết chat: {e}")


async def market_report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send immediate market report."""
    if not MARKET_ANALYSIS_AVAILABLE:
        await update.message.reply_text(
            "❌ Chức năng phân tích thị trường chưa khả dụng.\n"
            "Vui lòng kiểm tra cài đặt API keys trong môi trường."
        )
        return
    
    if not SERPER_API_KEY:
        await update.message.reply_text(
            "❌ Thiếu SERPER_API_KEY.\n"
            "Vui lòng cấu hình SERPER_API_KEY trong file .env để sử dụng chức năng này."
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text("🔍 Đang phân tích thị trường...")
    
    try:
        message = await get_daily_market_report_message(
            SERPER_API_KEY,
            GEMINI_API_KEY if GEMINI_API_KEY else None,
            OPENAI_API_KEY if OPENAI_API_KEY else None
        )
        
        await processing_msg.edit_text(message, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Lỗi khi tạo báo cáo thị trường: {str(e)}")


async def market_report_schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Schedule daily market report for user."""
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    try:
        # Ensure user is registered
        await upsert_user(user_id, chat_id)
        
        # Check if market analysis is available
        if not MARKET_ANALYSIS_AVAILABLE:
            await update.message.reply_text(
                "❌ **Chức năng phân tích thị trường chưa khả dụng!**\n\n"
                "Vui lòng kiểm tra cài đặt API keys trong môi trường:\n"
                "• SERPER_API_KEY\n"
                "• GEMINI_API_KEY (tùy chọn)\n"
                "• OPENAI_API_KEY (tùy chọn)\n\n"
                "Sau khi cấu hình, hãy khởi động lại bot."
            )
            return
        
        # Check if we have required API keys
        if not SERPER_API_KEY:
            await update.message.reply_text(
                "❌ **Thiếu SERPER_API_KEY!**\n\n"
                "Vui lòng cấu hình SERPER_API_KEY trong file .env để sử dụng chức năng này.\n"
                "SERPER_API_KEY là bắt buộc để lấy tin tức thị trường."
            )
            return
        
        # Remove any existing market report jobs first
        job_name = f"daily_market_report_{user_id}"
        jobs_removed = 0
        for job in context.application.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
            jobs_removed += 1
        
        # Schedule daily market report
        await schedule_daily_market_report(context.application, user_id)
        
        # Get current time to show next report time
        current_time = datetime.now(VN_TZ)
        next_report = "08:15 hôm nay" if current_time.time() < time(8, 15) else "08:15 ngày mai"
        
        # Check API keys status
        api_status = []
        if SERPER_API_KEY:
            api_status.append("✅ SERPER_API_KEY")
        if GEMINI_API_KEY:
            api_status.append("✅ GEMINI_API_KEY")
        if OPENAI_API_KEY:
            api_status.append("✅ OPENAI_API_KEY")
        
        api_status_text = "\n".join(api_status) if api_status else "❌ Không có API keys"
        
        await update.message.reply_text(
            f"✅ **Đã lên lịch báo cáo thị trường hàng ngày!**\n\n"
            f"📊 **Lịch báo cáo:** {next_report}\n"
            f"🔄 **Jobs đã xóa:** {jobs_removed}\n\n"
            f"🔍 **Báo cáo bao gồm:**\n"
            f"• Dự báo xu hướng VN-Index\n"
            f"• Phân tích tin tức trong nước & quốc tế\n"
            f"• Tín hiệu kỹ thuật\n"
            f"• Khuyến nghị đầu tư\n\n"
            f"🔑 **API Keys Status:**\n{api_status_text}\n\n"
            f"💡 **Lưu ý:**\n"
            f"• Sử dụng `/market_report` để xem báo cáo ngay lập tức\n"
            f"• Sử dụng `/market_report_off` để tắt báo cáo tự động",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi lên lịch báo cáo: {str(e)}")
        print(f"❌ Error in market_report_schedule_cmd: {e}")


async def market_report_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disable daily market report for user."""
    user_id = update.effective_user.id
    
    try:
        # Remove market report jobs
        job_name = f"daily_market_report_{user_id}"
        jobs_removed = 0
        for job in context.application.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
            jobs_removed += 1
        
        if jobs_removed > 0:
            await update.message.reply_text(
                "❌ **Đã tắt báo cáo thị trường hàng ngày!**\n\n"
                "Bot sẽ không gửi báo cáo tự động nữa.\n"
                "Sử dụng `/market_report_schedule` để bật lại."
            )
        else:
            await update.message.reply_text(
                "ℹ️ Không có báo cáo thị trường nào đang được lên lịch."
            )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi tắt báo cáo: {str(e)}")

async def test_price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test real-time price for a symbol."""
    assert update.effective_user is not None
    if len(context.args) != 1:
        await update.message.reply_text("Cú pháp: /test_price <mã>\nVí dụ: /test_price VIC")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"🔍 Đang lấy giá real-time cho {symbol}...")
    
    try:
        price = await MarketData.get_price(symbol)
        if price is not None:
            await update.message.reply_text(f"✅ Giá {symbol}: {price:.2f} VND")
        else:
            await update.message.reply_text(f"❌ Không thể lấy giá cho {symbol}")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")


async def test_notification_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test notification system by sending a test message."""
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    try:
        # Ensure user is registered
        await upsert_user(user_id, chat_id)
        
        # Send test message
        test_message = (
            f"🧪 **TEST NOTIFICATION**\n\n"
            f"⏰ Thời gian: {datetime.now(VN_TZ).strftime('%H:%M:%S %d/%m/%Y')}\n"
            f"👤 User ID: {user_id}\n"
            f"💬 Chat ID: {chat_id}\n"
            f"✅ Bot có thể gửi tin nhắn thành công!"
        )
        
        await update.message.reply_text(test_message, parse_mode=ParseMode.MARKDOWN)
        print(f"✅ Test notification sent to user {user_id} in chat {chat_id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi gửi test notification: {str(e)}")
        print(f"❌ Error in test_notification_cmd: {e}")


async def test_15s_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start 15-second interval test notifications."""
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    try:
        # Ensure user is registered
        await upsert_user(user_id, chat_id)
        
        # Remove any existing test job
        test_job_name = f"test_15s_{user_id}"
        for job in context.application.job_queue.get_jobs_by_name(test_job_name):
            job.schedule_removal()
        
        # Schedule repeating test job every 15 seconds
        job_data = {'user_id': user_id, 'chat_id': chat_id}
        context.application.job_queue.run_repeating(
            name=test_job_name,
            interval=timedelta(seconds=15),
            first=datetime.now(VN_TZ) + timedelta(seconds=2),  # Start after 2 seconds
            callback=test_15s_callback,
            data=job_data,
        )
        
        await update.message.reply_text(
            f"🧪 **Bắt đầu test 15 giây!**\n\n"
            f"Bot sẽ gửi thông báo test mỗi 15 giây.\n"
            f"⏰ Bắt đầu sau 2 giây...\n\n"
            f"Sử dụng `/test_15s_stop` để dừng test."
        )
        print(f"✅ Started 15s test for user {user_id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi bắt đầu test 15s: {str(e)}")
        print(f"❌ Error in test_15s_cmd: {e}")


async def test_15s_stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop 15-second interval test notifications."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    try:
        # Remove test job
        test_job_name = f"test_15s_{user_id}"
        jobs_removed = 0
        for job in context.application.job_queue.get_jobs_by_name(test_job_name):
            job.schedule_removal()
            jobs_removed += 1
        
        if jobs_removed > 0:
            await update.message.reply_text(
                f"⏹️ **Đã dừng test 15 giây!**\n\n"
                f"Đã xóa {jobs_removed} job test."
            )
            print(f"✅ Stopped 15s test for user {user_id}")
        else:
            await update.message.reply_text("ℹ️ Không có test 15s nào đang chạy.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi dừng test 15s: {str(e)}")
        print(f"❌ Error in test_15s_stop_cmd: {e}")


async def test_15s_callback(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for 15-second test notifications."""
    try:
        job = ctx.job
        user_id = job.data.get('user_id')
        chat_id = job.data.get('chat_id')
        
        if not user_id or not chat_id:
            print("Test 15s callback: Missing user_id or chat_id")
            return
        
        # Create test message
        current_time = datetime.now(VN_TZ)
        test_message = (
            f"🧪 **TEST 15s NOTIFICATION**\n\n"
            f"⏰ Thời gian: {current_time.strftime('%H:%M:%S %d/%m/%Y')}\n"
            f"👤 User ID: {user_id}\n"
            f"💬 Chat ID: {chat_id}\n"
            f"🔄 Test notification #{job.data.get('count', 1)}\n"
            f"✅ Bot hoạt động bình thường!"
        )
        
        # Send test message
        await ctx.application.bot.send_message(
            chat_id=chat_id,
            text=test_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Update counter
        job.data['count'] = job.data.get('count', 0) + 1
        
        print(f"✅ Test 15s notification #{job.data.get('count', 1)} sent to user {user_id}")
        
    except Exception as e:
        print(f"❌ Error in test_15s_callback: {e}")
        # Try to send error message to user
        try:
            job = ctx.job
            user_id = job.data.get('user_id')
            chat_id = job.data.get('chat_id')
            if user_id and chat_id:
                await ctx.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Lỗi trong test 15s: {str(e)}"
                )
        except Exception as e2:
            print(f"❌ Error sending error message: {e2}")


async def test_job_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show status of all test jobs."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    try:
        jq = context.application.job_queue
        if jq is None:
            await update.message.reply_text("❌ JobQueue is None")
            return
        
        # Get all jobs for this user
        all_jobs = list(jq.jobs())
        user_jobs = [job for job in all_jobs if job.name and str(user_id) in job.name]
        
        if not user_jobs:
            await update.message.reply_text("ℹ️ Không có job nào đang chạy cho user này.")
            return
        
        lines = [f"📊 **Job Status cho User {user_id}:**\n"]
        
        for job in user_jobs:
            next_run = getattr(job, "next_t", None) or getattr(job, "next_run_time", None)
            job_type = job.data.get('job_type', 'unknown') if hasattr(job, 'data') else 'unknown'
            count = job.data.get('count', 0) if hasattr(job, 'data') else 0
            
            lines.append(f"• **{job.name}**")
            lines.append(f"  - Type: {job_type}")
            lines.append(f"  - Next run: {next_run}")
            if count > 0:
                lines.append(f"  - Count: {count}")
            lines.append("")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi kiểm tra job status: {str(e)}")
        print(f"❌ Error in test_job_status_cmd: {e}")


async def track_15s_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start 15-second interval portfolio tracking."""
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    try:
        # Ensure user is registered
        await upsert_user(user_id, chat_id)
        
        # Check if user has any positions
        positions = await get_positions(user_id)
        if not positions:
            await update.message.reply_text(
                "❌ **Danh mục trống!**\n\n"
                "Bạn cần có cổ phiếu trong danh mục trước khi bật tracking 15s.\n"
                "Sử dụng `/add <mã> <số_lượng> <giá> <stoploss%>` để thêm cổ phiếu."
            )
            return
        
        # Remove any existing tracking 15s job
        track_job_name = f"track_15s_{user_id}"
        for job in context.application.job_queue.get_jobs_by_name(track_job_name):
            job.schedule_removal()
        
        # Schedule repeating tracking job every 15 seconds
        job_data = {'user_id': user_id, 'chat_id': chat_id}
        context.application.job_queue.run_repeating(
            name=track_job_name,
            interval=timedelta(seconds=15),
            first=datetime.now(VN_TZ) + timedelta(seconds=2),  # Start after 2 seconds
            callback=track_15s_callback,
            data=job_data,
        )
        
        await update.message.reply_text(
            f"📊 **Bắt đầu tracking 15 giây!**\n\n"
            f"Bot sẽ theo dõi {len(positions)} cổ phiếu mỗi 15 giây:\n"
            f"• {', '.join([pos[0] for pos in positions])}\n\n"
            f"⏰ Bắt đầu sau 2 giây...\n\n"
            f"Sử dụng `/track_15s_stop` để dừng tracking."
        )
        print(f"✅ Started 15s portfolio tracking for user {user_id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi bắt đầu tracking 15s: {str(e)}")
        print(f"❌ Error in track_15s_cmd: {e}")


async def track_15s_stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop 15-second interval portfolio tracking."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    try:
        # Remove tracking 15s job
        track_job_name = f"track_15s_{user_id}"
        jobs_removed = 0
        for job in context.application.job_queue.get_jobs_by_name(track_job_name):
            job.schedule_removal()
            jobs_removed += 1
        
        if jobs_removed > 0:
            await update.message.reply_text(
                f"⏹️ **Đã dừng tracking 15 giây!**\n\n"
                f"Đã xóa {jobs_removed} job tracking."
            )
            print(f"✅ Stopped 15s portfolio tracking for user {user_id}")
        else:
            await update.message.reply_text("ℹ️ Không có tracking 15s nào đang chạy.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi dừng tracking 15s: {str(e)}")
        print(f"❌ Error in track_15s_stop_cmd: {e}")


async def smart_track_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start smart 15-second interval portfolio tracking - only alerts on important signals."""
    assert update.effective_user is not None
    assert update.effective_chat is not None
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    
    try:
        # Ensure user is registered
        await upsert_user(user_id, chat_id)
        
        # Check if user has any positions
        positions = await get_positions(user_id)
        if not positions:
            await update.message.reply_text(
                "❌ **Danh mục trống!**\n\n"
                "Bạn cần có cổ phiếu trong danh mục trước khi bật smart tracking.\n"
                "Sử dụng `/add <mã> <số_lượng> <giá> <stoploss%>` để thêm cổ phiếu.\n\n"
                "**Ví dụ:** `/add VIC 100 45000 0.08`"
            )
            return
        
        # Remove any existing smart tracking job
        smart_job_name = f"smart_track_{user_id}"
        for job in context.application.job_queue.get_jobs_by_name(smart_job_name):
            job.schedule_removal()
        
        # Schedule repeating smart tracking job every 15 seconds
        job_data = {'user_id': user_id, 'chat_id': chat_id}
        context.application.job_queue.run_repeating(
            name=smart_job_name,
            interval=timedelta(seconds=15),
            first=datetime.now(VN_TZ) + timedelta(seconds=2),  # Start after 2 seconds
            callback=smart_track_15s_callback,
            data=job_data,
        )
        
        await update.message.reply_text(
            f"🧠 **Bắt đầu Smart Tracking!**\n\n"
            f"📊 **Danh mục:** {len(positions)} cổ phiếu\n"
            f"• {', '.join([pos[0] for pos in positions])}\n\n"
            f"🚨 **Chỉ cảnh báo khi:**\n"
            f"• 🚨 Stoploss: Giá ≤ SL → Gợi ý SELL\n"
            f"• 🎯 Take Profit: Giá ≥ TP + Volume xác nhận → Gợi ý chốt lời/mua thêm\n"
            f"• 📊 Volume Spike: Tăng >50% → Gợi ý mua thêm\n"
            f"• 📉 Volume Drop: Giảm >30% → Gợi ý giảm tỷ trọng\n\n"
            f"⏰ Bắt đầu sau 2 giây...\n\n"
            f"Sử dụng `/smart_track_stop` để dừng tracking."
        )
        print(f"✅ Started smart tracking for user {user_id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi bắt đầu smart tracking: {str(e)}")
        print(f"❌ Error in smart_track_cmd: {e}")


async def smart_track_stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop smart 15-second interval portfolio tracking."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    
    try:
        # Remove smart tracking job
        smart_job_name = f"smart_track_{user_id}"
        jobs_removed = 0
        for job in context.application.job_queue.get_jobs_by_name(smart_job_name):
            job.schedule_removal()
            jobs_removed += 1
        
        if jobs_removed > 0:
            await update.message.reply_text(
                f"⏹️ **Đã dừng Smart Tracking!**\n\n"
                f"Đã xóa {jobs_removed} job smart tracking."
            )
            print(f"✅ Stopped smart tracking for user {user_id}")
        else:
            await update.message.reply_text("ℹ️ Không có smart tracking nào đang chạy.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi dừng smart tracking: {str(e)}")
        print(f"❌ Error in smart_track_stop_cmd: {e}")


async def track_15s_callback(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for 15-second portfolio tracking."""
    try:
        job = ctx.job
        user_id = job.data.get('user_id')
        chat_id = job.data.get('chat_id')
        
        if not user_id or not chat_id:
            print("Track 15s callback: Missing user_id or chat_id")
            return
        
        # Get user's positions
        positions = await get_positions(user_id)
        if not positions:
            print(f"Track 15s: No positions found for user {user_id}")
            return
        
        # Get current time
        current_time = datetime.now(VN_TZ)
        
        # Create tracking message
        lines = [f"📊 **Portfolio Tracking - {current_time.strftime('%H:%M:%S')}**\n"]
        
        total_pnl = 0.0
        total_cost = 0.0
        any_price_available = False
        
        for symbol, qty, avg_cost in positions:
            # Get current price
            price = await MarketData.get_price(symbol)
            
            if price is not None:
                any_price_available = True
                pnl = (price - avg_cost) * qty
                pnl_pct = ((price - avg_cost) / avg_cost) * 100
                cost_value = avg_cost * qty
                current_value = price * qty
                
                total_pnl += pnl
                total_cost += cost_value
                
                # Price change indicator
                if pnl > 0:
                    price_indicator = "📈"
                elif pnl < 0:
                    price_indicator = "📉"
                else:
                    price_indicator = "➡️"
                
                lines.append(
                    f"{price_indicator} **{symbol}**: {price:.2f} "
                    f"(SL: {qty:g}, Cost: {avg_cost:.2f}) "
                    f"PnL: {pnl:+.0f} ({pnl_pct:+.1f}%)"
                )
            else:
                lines.append(f"❓ **{symbol}**: N/A (SL: {qty:g}, Cost: {avg_cost:.2f})")
        
        # Add summary if we have price data
        if any_price_available and total_cost > 0:
            total_pnl_pct = (total_pnl / total_cost) * 100
            lines.append(f"\n💰 **Tổng PnL**: {total_pnl:+.0f} ({total_pnl_pct:+.1f}%)")
        
        # Add tracking info
        lines.append(f"\n🔄 Tracking #{job.data.get('count', 1)} | Next: 15s")
        
        # Send tracking message
        message_text = "\n".join(lines)
        await ctx.application.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Update counter
        job.data['count'] = job.data.get('count', 0) + 1
        
        print(f"✅ Track 15s notification #{job.data.get('count', 1)} sent to user {user_id}")
        
    except Exception as e:
        print(f"❌ Error in track_15s_callback: {e}")
        # Try to send error message to user
        try:
            job = ctx.job
            user_id = job.data.get('user_id')
            chat_id = job.data.get('chat_id')
            if user_id and chat_id:
                await ctx.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Lỗi trong tracking 15s: {str(e)}"
                )
        except Exception as e2:
            print(f"❌ Error sending error message: {e2}")


async def smart_track_15s_callback(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for smart 15-second portfolio tracking - only alerts on important signals."""
    try:
        job = ctx.job
        user_id = job.data.get('user_id')
        chat_id = job.data.get('chat_id')
        
        if not user_id or not chat_id:
            print("Smart track 15s callback: Missing user_id or chat_id")
            return
        
        # Get user's positions
        positions = await get_positions(user_id)
        if not positions:
            print(f"Smart track 15s: No positions found for user {user_id}")
            return
        
        # Get tracking settings
        enabled, sl_pct, tp_pct, vol_ma_days = await get_tracking_settings(user_id)
        if not enabled:
            print(f"Smart track 15s: Tracking disabled for user {user_id}")
            return
        
        # Get current time
        current_time = datetime.now(VN_TZ)
        current_hour = current_time.hour
        
        # Only run during trading hours (9:00-15:00 VN time)
        if not (9 <= current_hour < 15):
            print(f"🔕 Smart track: Outside trading hours ({current_time.strftime('%H:%M')}) - skipping")
            return
        
        # Update counter first
        current_count = job.data.get('count', 0) + 1
        job.data['count'] = current_count
        
        print(f"🔍 Smart tracking check #{current_count} for user {user_id} at {current_time.strftime('%H:%M:%S')}")
        
        # Check for alerts
        alerts = []
        any_alert = False
        
        for symbol, qty, avg_cost in positions:
            # Get current price and volume data
            price, vol, vol_ma = await get_price_and_volume(symbol, vol_ma_days)
            
            if price is None:
                print(f"  ❓ {symbol}: No price data available")
                continue
            
            print(f"  📊 {symbol}: Price={price:.2f}, Qty={qty}, Cost={avg_cost:.2f}")
            print(f"    📊 Volume: {vol}, MA: {vol_ma}")
            
            # Calculate PnL
            pnl = (price - avg_cost) * qty
            pnl_pct = ((price - avg_cost) / avg_cost) * 100
            
            # Get individual stoploss for this stock
            individual_sl_pct = await get_stock_stoploss(user_id, symbol)
            sl_price = avg_cost * (1 - individual_sl_pct)
            tp_price = avg_cost * (1 + tp_pct)
            
            print(f"    📈 {symbol}: SL={sl_price:.2f} ({individual_sl_pct*100:.1f}%), TP={tp_price:.2f} ({tp_pct*100:.1f}%)")
            
            # 1. Check Stoploss
            if price <= sl_price:
                any_alert = True
                alerts.append(
                    f"🚨 **STOPLOSS ALERT - {symbol}**\n"
                    f"💰 Giá: {price:.2f} ≤ {sl_price:.2f} ({individual_sl_pct*100:.1f}%)\n"
                    f"📉 PnL: {pnl:+.0f} ({pnl_pct:+.1f}%)\n"
                    f"⚠️ **Gợi ý: SELL ngay để hạn chế rủi ro!**"
                )
                print(f"    ⛔ STOPLOSS ALERT: {symbol} - Price: {price:.2f} <= SL: {sl_price:.2f}")
            
            # 2. Check Take Profit
            elif price >= tp_price:
                # Check volume confirmation
                vol_ok = (vol is not None and vol_ma is not None and vol > vol_ma) or (vol is None or vol_ma is None)
                
                if vol_ok:
                    any_alert = True
                    alerts.append(
                        f"🎯 **TAKE PROFIT ALERT - {symbol}**\n"
                        f"💰 Giá: {price:.2f} ≥ {tp_price:.2f} ({tp_pct*100:.1f}%)\n"
                        f"📈 PnL: {pnl:+.0f} ({pnl_pct:+.1f}%)\n"
                        f"📊 Volume: {'Tăng' if vol and vol_ma and vol > vol_ma else 'N/A'}\n"
                        f"✅ **Gợi ý: Chốt lời hoặc mua thêm nếu xu hướng mạnh!**"
                    )
                    print(f"    ✅ TAKE PROFIT ALERT: {symbol} - Price: {price:.2f} >= TP: {tp_price:.2f}")
                else:
                    # Price hit TP but volume not confirmed
                    alerts.append(
                        f"⚠️ **{symbol}**: Giá {price:.2f} ≥ {tp_price:.2f} nhưng volume chưa xác nhận. Theo dõi thêm."
                    )
                    print(f"    ⚠️ {symbol}: Price hit TP but volume not confirmed")
            
            # 3. Check Volume Anomaly - Compare with historical data
            elif vol is not None and vol_ma is not None:
                vol_change_pct = ((vol - vol_ma) / vol_ma) * 100
                
                # Smart volume anomaly detection based on time of day
                try:
                    import pandas as pd
                    from vnstock import Quote
                    quote = Quote(source='VCI', symbol=symbol)
                    current_time = datetime.now(VN_TZ)
                    current_hour = current_time.hour
                    current_minute = current_time.minute
                    
                    # Get historical data for comparison
                    today = datetime.now().date()
                    start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
                    end_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
                    
                    # Get historical daily data for comparison
                    df_history = quote.history(start=start_date, end=end_date, interval="1D")
                    if df_history is not None and len(df_history) > 0:
                        # Convert index to datetime if it's not already
                        if not isinstance(df_history.index, pd.DatetimeIndex):
                            df_history.index = pd.to_datetime(df_history.index)
                        
                        # Calculate time-based volume adjustment factor
                        # Early morning (9:00-10:00): lower volume expected
                        # Mid morning (10:00-11:00): normal volume
                        # Afternoon (13:00-15:00): higher volume expected
                        time_factor = 1.0
                        if current_hour == 9:  # 9:00-9:59
                            time_factor = 0.3  # 30% of daily average
                        elif current_hour == 10:  # 10:00-10:59
                            time_factor = 0.6  # 60% of daily average
                        elif current_hour == 11:  # 11:00-11:59
                            time_factor = 0.8  # 80% of daily average
                        elif current_hour == 13:  # 13:00-13:59
                            time_factor = 1.2  # 120% of daily average
                        elif current_hour == 14:  # 14:00-14:59
                            time_factor = 1.5  # 150% of daily average
                        
                        # Get historical volumes and calculate expected volume for this time
                        historical_volumes = df_history['volume'].dropna()
                        if len(historical_volumes) > 0:
                            daily_avg_volume = float(historical_volumes.mean())
                            expected_volume = daily_avg_volume * time_factor
                            
                            # Calculate z-score based on expected volume for this time
                            vol_std = float(historical_volumes.std())
                            z_score = (vol - expected_volume) / vol_std if vol_std > 0 else 0
                            
                            print(f"    📊 {symbol}: Vol={vol:,.0f}, Expected={expected_volume:,.0f} (factor={time_factor:.1f}), Z-score={z_score:.2f}")
                            
                            # More reasonable thresholds for time-based comparison
                            if z_score > 2.5:  # Volume significantly higher than expected for this time
                                any_alert = True
                                alerts.append(
                                    f"📊 **VOLUME SPIKE - {symbol}**\n"
                                    f"💰 Giá: {price:.2f}\n"
                                    f"📈 Volume: {vol:,.0f} (Z-score: {z_score:.2f})\n"
                                    f"📊 Expected for {current_hour:02d}:{current_minute:02d}: {expected_volume:,.0f}\n"
                                    f"📈 Change: +{vol_change_pct:.1f}% vs MA\n"
                                    f"💡 **Gợi ý: Volume cao bất thường so với cùng giờ - có thể có tin tức!**"
                                )
                                print(f"    📊 VOLUME SPIKE: {symbol} - Z-score: {z_score:.2f} (Volume: {vol:,.0f})")
                            
                            elif z_score < -2.0 and vol < (expected_volume * 0.5):  # Very low volume
                                any_alert = True
                                alerts.append(
                                    f"📉 **VOLUME DROP - {symbol}**\n"
                                    f"💰 Giá: {price:.2f}\n"
                                    f"📉 Volume: {vol:,.0f} (Z-score: {z_score:.2f})\n"
                                    f"📊 Expected for {current_hour:02d}:{current_minute:02d}: {expected_volume:,.0f}\n"
                                    f"📉 Change: {vol_change_pct:.1f}% vs MA\n"
                                    f"⚠️ **Gợi ý: Volume cực thấp so với cùng giờ - có thể có áp lực bán!**"
                                )
                                print(f"    📉 VOLUME DROP: {symbol} - Z-score: {z_score:.2f} (Volume: {vol:,.0f})")
                            
                            else:
                                print(f"    ➡️ {symbol}: Normal volume for this time (Z-score: {z_score:.2f})")
                        else:
                            print(f"    ❓ {symbol}: No historical volume data")
                    else:
                        print(f"    ❓ {symbol}: No historical data available")
                        
                except Exception as e:
                    print(f"    ❌ Error in smart volume analysis: {e}")
                    # Fallback to simple percentage comparison with more reasonable thresholds
                    if vol_change_pct > 100:  # Volume doubled
                        any_alert = True
                        alerts.append(
                            f"📊 **VOLUME SPIKE - {symbol}**\n"
                            f"💰 Giá: {price:.2f}\n"
                            f"📈 Volume: {vol:,.0f} (+{vol_change_pct:.1f}% vs MA)\n"
                            f"📊 MA Volume: {vol_ma:,.0f}\n"
                            f"💡 **Gợi ý: Volume tăng mạnh - có thể có tin tức quan trọng!**"
                        )
                        print(f"    📊 VOLUME SPIKE: {symbol} - Volume: {vol:,.0f} (+{vol_change_pct:.1f}%)")
                    elif vol_change_pct < -80:  # Volume dropped significantly
                        any_alert = True
                        alerts.append(
                            f"📉 **VOLUME DROP - {symbol}**\n"
                            f"💰 Giá: {price:.2f}\n"
                            f"📉 Volume: {vol:,.0f} ({vol_change_pct:.1f}% vs MA)\n"
                            f"📊 MA Volume: {vol_ma:,.0f}\n"
                            f"⚠️ **Gợi ý: Volume giảm mạnh - có thể có áp lực bán!**"
                        )
                        print(f"    📉 VOLUME DROP: {symbol} - Volume: {vol:,.0f} ({vol_change_pct:.1f}%)")
                    else:
                        print(f"    ➡️ {symbol}: Normal volume (Change: {vol_change_pct:+.1f}%)")
                        
            else:
                print(f"    ❓ {symbol}: No volume data available for anomaly check")
        
        # Send alerts if any
        if any_alert:
            # Create alert message
            alert_lines = [f"🚨 **SMART ALERTS - {current_time.strftime('%H:%M:%S')}**\n"]
            alert_lines.extend(alerts)
            alert_lines.append(f"\n🔄 Smart Tracking #{current_count} | Next: 15s")
            
            message_text = "\n".join(alert_lines)
            await ctx.application.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            print(f"🚨 Smart alerts sent to user {user_id} - {len(alerts)} alerts triggered")
        else:
            # Just log that we checked but no alerts
            print(f"✅ Smart track check #{current_count} - No alerts for user {user_id} (monitoring {len(positions)} positions)")
        
    except Exception as e:
        print(f"❌ Error in smart_track_15s_callback: {e}")
        # Try to send error message to user
        try:
            job = ctx.job
            user_id = job.data.get('user_id')
            chat_id = job.data.get('chat_id')
            if user_id and chat_id:
                await ctx.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Lỗi trong smart tracking: {str(e)}"
                )
        except Exception as e2:
            print(f"❌ Error sending error message: {e2}")


async def debug_pnl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Debug PnL calculation with detailed breakdown."""
    assert update.effective_user is not None
    user_id = update.effective_user.id
    positions = await get_positions(user_id)
    
    if not positions:
        await update.message.reply_text("Danh mục trống.")
        return
    
    lines = ["🔍 Debug PnL Calculation:"]
    total_pnl = 0.0
    total_cost = 0.0
    total_value = 0.0
    
    for symbol, qty, avg_cost in positions:
        price = await MarketData.get_price(symbol)
        if price is not None:
            pnl = (price - avg_cost) * qty
            cost_value = avg_cost * qty
            current_value = price * qty
            pnl_pct = ((price - avg_cost) / avg_cost) * 100
            
            total_pnl += pnl
            total_cost += cost_value
            total_value += current_value
            
            lines.append(f"\n📊 {symbol}:")
            lines.append(f"  • Số lượng: {qty:g}")
            lines.append(f"  • Giá vốn: {avg_cost:.2f}")
            lines.append(f"  • Giá RT: {price:.2f}")
            lines.append(f"  • Giá trị vốn: {cost_value:,.0f}")
            lines.append(f"  • Giá trị hiện tại: {current_value:,.0f}")
            lines.append(f"  • Lãi/lỗ: {pnl:,.0f} ({pnl_pct:+.2f}%)")
        else:
            lines.append(f"\n❌ {symbol}: Không có dữ liệu giá")
    
    lines.append(f"\n💰 Tổng kết:")
    lines.append(f"  • Tổng vốn: {total_cost:,.0f}")
    lines.append(f"  • Tổng giá trị: {total_value:,.0f}")
    lines.append(f"  • Tổng lãi/lỗ: {total_pnl:,.0f}")
    if total_cost > 0:
        total_pnl_pct = (total_pnl / total_cost) * 100
        lines.append(f"  • Lãi/lỗ %: {total_pnl_pct:+.2f}%")
    
    await update.message.reply_text("\n".join(lines))


async def ui_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Launch Streamlit UI in the background and send the URL to the user."""
    try:
        # Prefer project venv python if exists, fallback to current interpreter
        project_root = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(project_root, ".venv", "bin", "python")
        python_exec = venv_python if os.path.exists(venv_python) else sys.executable

        # Build command to run via `python -m streamlit`
        app_path = os.path.join(project_root, "streamlit_app.py")
        if sys.platform == "win32":
            # Windows detached start
            os.spawnl(os.P_NOWAIT, python_exec, python_exec, "-m", "streamlit", "run", app_path)
        else:
            # Unix/Mac detached with logs
            log_dir = os.path.expanduser("~/Library/Logs")
            os.makedirs(log_dir, exist_ok=True)
            out_log = os.path.join(log_dir, "vnstockadvisor.streamlit.out.log")
            err_log = os.path.join(log_dir, "vnstockadvisor.streamlit.err.log")
            cmd = (
                f"nohup '{python_exec}' -m streamlit run '{app_path}' >> "
                f"'{out_log}' 2>> '{err_log}' &"
            )
            os.system(cmd)

        await update.message.reply_text(
            "Đã mở UI Streamlit. Mở trình duyệt tại: http://localhost:8501"
        )
    except Exception as e:
        await update.message.reply_text(f"Không thể mở UI: {e}")


# Callback function for daily analysis jobs
async def daily_analysis_callback(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for daily analysis jobs - extracts user_id and chat_id from job data."""
    job = ctx.job
    user_id = job.data.get('user_id')
    chat_id = job.data.get('chat_id')
    
    if not user_id or not chat_id:
        return
    
    await analyze_and_notify(ctx.application, user_id, chat_id)


async def schedule_user_job(app: Application, user_id: int) -> None:
    hhmm = await get_schedule(user_id)
    chat_id = await get_user_chat_id(user_id)
    if not hhmm or not chat_id:
        return
    t = parse_hhmm(hhmm)
    if t is None:
        return
    job_name = f"daily_analysis_{user_id}"
    # Remove old job if exists
    for job in app.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    # Schedule new daily job (local time of the machine)
    app.job_queue.run_daily(
        callback=daily_analysis_callback,
        time=t,
        name=job_name,
        data={'user_id': user_id, 'chat_id': chat_id},
    )


async def bootstrap_schedules(app: Application) -> None:
    # Load all users with schedules and register their jobs
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM settings WHERE schedule_hhmm IS NOT NULL") as cur:
            rows = await cur.fetchall()
            for (user_id,) in rows:
                await schedule_user_job(app, int(user_id))


async def push_to_default_chat_if_set(app: Application, text: str) -> None:
    if DEFAULT_CHAT_ID:
        try:
            await app.bot.send_message(chat_id=DEFAULT_CHAT_ID, text=text)
        except Exception:
            pass


async def _post_init(application: Application) -> None:
    await init_db()
    
    # Ensure JobQueue is started
    try:
        jq = application.job_queue
        if jq is None:
            print("Warning: Application.job_queue is None; cannot start scheduler.")
        else:
            # In PTB v20+, run_polling starts JobQueue automatically, but starting here is safe
            await jq.start()
            print("JobQueue started successfully")
    except Exception as e:
        print(f"Error starting JobQueue: {e}")
    
    await bootstrap_schedules(application)
    await bootstrap_tracking(application)
    await bootstrap_market_reports(application)
    await push_to_default_chat_if_set(application, "Bot đã khởi động trên máy local.")


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment.")

    # Configure robust HTTP timeouts to avoid startup/network hiccups
    httpx_request = HTTPXRequest(
        connect_timeout=20.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=20.0,
    )

    application: Application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .request(httpx_request)
        .defaults(Defaults(tzinfo=VN_TZ))
        .post_init(_post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_notification", test_notification))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("add", add_cmd))
    application.add_handler(CommandHandler("sell", sell_cmd))
    application.add_handler(CommandHandler("portfolio", portfolio_cmd))
    application.add_handler(CommandHandler("pnl", pnl_cmd))
    application.add_handler(CommandHandler("analyze_now", analyze_now_cmd))
    application.add_handler(CommandHandler("predict", predict_cmd))
    application.add_handler(CommandHandler("set_style", set_style_cmd))
    application.add_handler(CommandHandler("my_style", my_style_cmd))
    application.add_handler(CommandHandler("reset", reset_cmd))
    application.add_handler(CommandHandler("confirm_reset", confirm_reset_cmd))
    application.add_handler(CommandHandler("cancel_reset", cancel_reset_cmd))
    application.add_handler(CommandHandler("set_stoploss", set_stoploss_cmd))
    application.add_handler(CommandHandler("set_cost", set_cost_cmd))
    application.add_handler(CommandHandler("set_trailing_stop", set_trailing_stop_cmd))
    application.add_handler(CommandHandler("trailing_config", trailing_config_cmd))
    application.add_handler(CommandHandler("restart", restart_cmd))
    application.add_handler(CommandHandler("ui", ui_cmd))
    application.add_handler(CommandHandler("track_on", track_on_cmd))
    application.add_handler(CommandHandler("track_off", track_off_cmd))
    application.add_handler(CommandHandler("track_config", track_config_cmd))
    application.add_handler(CommandHandler("track_status", track_status_cmd))
    application.add_handler(CommandHandler("track_now", track_now_cmd))
    application.add_handler(CommandHandler("track_ping", track_ping_cmd))
    application.add_handler(CommandHandler("track_now_summary", track_now_summary_cmd))
    application.add_handler(CommandHandler("track_bind", track_bind_cmd))
    application.add_handler(CommandHandler("market_report", market_report_cmd))
    application.add_handler(CommandHandler("market_report_schedule", market_report_schedule_cmd))
    application.add_handler(CommandHandler("market_report_off", market_report_off_cmd))
    application.add_handler(CommandHandler("test_notification", test_notification_cmd))
    application.add_handler(CommandHandler("test_15s", test_15s_cmd))
    application.add_handler(CommandHandler("test_15s_stop", test_15s_stop_cmd))
    application.add_handler(CommandHandler("test_job_status", test_job_status_cmd))
    application.add_handler(CommandHandler("track_15s", track_15s_cmd))
    application.add_handler(CommandHandler("track_15s_stop", track_15s_stop_cmd))
    application.add_handler(CommandHandler("smart_track", smart_track_cmd))
    application.add_handler(CommandHandler("smart_track_stop", smart_track_stop_cmd))
    
    # Watchlist commands
    application.add_handler(CommandHandler("watch_add", watch_add_cmd))
    application.add_handler(CommandHandler("watch_remove", watch_remove_cmd))
    application.add_handler(CommandHandler("watch_list", watch_list_cmd))
    application.add_handler(CommandHandler("watch_clear", watch_clear_cmd))
    application.add_handler(CommandHandler("confirm_watch_clear", confirm_watch_clear_cmd))

    # Add simple retry on startup timeout
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except TimedOut:
        print("Startup timed out once, retrying run_polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


