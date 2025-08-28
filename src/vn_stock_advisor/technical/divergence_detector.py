"""
Divergence Detector for VN Stock Advisor.

This module detects bullish and bearish divergences between
price and technical indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

try:
    import talib as ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    print("Warning: TA-Lib not available in divergence detector.")

@dataclass
class DivergenceSignal:
    """Divergence signal information."""
    divergence_type: str    # 'BULLISH', 'BEARISH'
    indicator: str          # 'RSI', 'MACD', 'STOCH', etc.
    strength: str           # 'STRONG', 'MEDIUM', 'WEAK'
    confidence: float
    start_index: int
    end_index: int
    description: str
    price_trend: str        # 'HIGHER_HIGHS', 'LOWER_LOWS', etc.
    indicator_trend: str

class DivergenceDetector:
    """
    Detect price-indicator divergences for trading signals.
    """
    
    def __init__(self, min_periods: int = 10, lookback_periods: int = 50):
        self.min_periods = min_periods
        self.lookback_periods = lookback_periods
    
    def detect_rsi_divergence(self, prices: List[float], period: int = 14) -> List[DivergenceSignal]:
        """Detect RSI divergences."""
        if len(prices) < period + self.lookback_periods:
            return []
        
        prices_array = np.array(prices)
        rsi = ta.RSI(prices_array, timeperiod=period)
        
        return self._detect_oscillator_divergence(prices_array, rsi, 'RSI')
    
    def detect_macd_divergence(self, prices: List[float], fast: int = 12, 
                              slow: int = 26, signal: int = 9) -> List[DivergenceSignal]:
        """Detect MACD divergences."""
        if len(prices) < slow + self.lookback_periods:
            return []
        
        prices_array = np.array(prices)
        macd, macd_signal, macd_histogram = ta.MACD(prices_array, fastperiod=fast, 
                                                   slowperiod=slow, signalperiod=signal)
        
        return self._detect_oscillator_divergence(prices_array, macd, 'MACD')
    
    def detect_stochastic_divergence(self, highs: List[float], lows: List[float], 
                                   closes: List[float], k_period: int = 14, 
                                   d_period: int = 3) -> List[DivergenceSignal]:
        """Detect Stochastic divergences."""
        if len(closes) < k_period + self.lookback_periods:
            return []
        
        highs_array = np.array(highs)
        lows_array = np.array(lows)
        closes_array = np.array(closes)
        
        slowk, slowd = ta.STOCH(highs_array, lows_array, closes_array, 
                               fastk_period=k_period, slowk_period=d_period, 
                               slowd_period=d_period)
        
        return self._detect_oscillator_divergence(closes_array, slowk, 'STOCHASTIC')
    
    def detect_volume_divergence(self, prices: List[float], volumes: List[float]) -> List[DivergenceSignal]:
        """Detect price-volume divergences."""
        if len(prices) != len(volumes) or len(prices) < self.lookback_periods:
            return []
        
        prices_array = np.array(prices)
        volumes_array = np.array(volumes)
        
        # Calculate On-Balance Volume (OBV)
        obv = self._calculate_obv(prices_array, volumes_array)
        
        return self._detect_oscillator_divergence(prices_array, obv, 'VOLUME_OBV')
    
    def _calculate_obv(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Calculate On-Balance Volume."""
        obv = np.zeros_like(prices)
        obv[0] = volumes[0]
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv[i] = obv[i-1] + volumes[i]
            elif prices[i] < prices[i-1]:
                obv[i] = obv[i-1] - volumes[i]
            else:
                obv[i] = obv[i-1]
        
        return obv
    
    def _detect_oscillator_divergence(self, prices: np.ndarray, indicator: np.ndarray, 
                                    indicator_name: str) -> List[DivergenceSignal]:
        """Generic oscillator divergence detection."""
        divergences = []
        
        # Remove NaN values
        valid_mask = ~np.isnan(indicator)
        if not np.any(valid_mask):
            return divergences
        
        start_idx = np.where(valid_mask)[0][0]
        prices_clean = prices[start_idx:]
        indicator_clean = indicator[start_idx:]
        
        if len(prices_clean) < self.lookback_periods:
            return divergences
        
        # Find peaks and troughs in price and indicator
        price_peaks = self._find_peaks(prices_clean, min_distance=self.min_periods)
        price_troughs = self._find_troughs(prices_clean, min_distance=self.min_periods)
        
        indicator_peaks = self._find_peaks(indicator_clean, min_distance=self.min_periods)
        indicator_troughs = self._find_troughs(indicator_clean, min_distance=self.min_periods)
        
        # Detect bullish divergences (price makes lower lows, indicator makes higher lows)
        bullish_divs = self._find_bullish_divergences(
            prices_clean, indicator_clean, price_troughs, indicator_troughs, 
            indicator_name, start_idx
        )
        divergences.extend(bullish_divs)
        
        # Detect bearish divergences (price makes higher highs, indicator makes lower highs)
        bearish_divs = self._find_bearish_divergences(
            prices_clean, indicator_clean, price_peaks, indicator_peaks, 
            indicator_name, start_idx
        )
        divergences.extend(bearish_divs)
        
        return divergences
    
    def _find_peaks(self, data: np.ndarray, min_distance: int = 10) -> List[int]:
        """Find peaks in data."""
        peaks = []
        
        for i in range(min_distance, len(data) - min_distance):
            if all(data[i] >= data[j] for j in range(i - min_distance, i + min_distance + 1)):
                peaks.append(i)
        
        return peaks
    
    def _find_troughs(self, data: np.ndarray, min_distance: int = 10) -> List[int]:
        """Find troughs in data."""
        troughs = []
        
        for i in range(min_distance, len(data) - min_distance):
            if all(data[i] <= data[j] for j in range(i - min_distance, i + min_distance + 1)):
                troughs.append(i)
        
        return troughs
    
    def _find_bullish_divergences(self, prices: np.ndarray, indicator: np.ndarray, 
                                price_troughs: List[int], indicator_troughs: List[int], 
                                indicator_name: str, offset: int) -> List[DivergenceSignal]:
        """Find bullish divergences."""
        divergences = []
        
        if len(price_troughs) < 2 or len(indicator_troughs) < 2:
            return divergences
        
        # Look for recent divergences
        recent_price_troughs = [t for t in price_troughs if t >= len(prices) - self.lookback_periods]
        recent_indicator_troughs = [t for t in indicator_troughs if t >= len(indicator) - self.lookback_periods]
        
        if len(recent_price_troughs) < 2 or len(recent_indicator_troughs) < 2:
            return divergences
        
        # Check each pair of recent troughs
        for i in range(len(recent_price_troughs) - 1):
            for j in range(i + 1, len(recent_price_troughs)):
                price_trough1_idx = recent_price_troughs[i]
                price_trough2_idx = recent_price_troughs[j]
                
                # Find corresponding indicator troughs
                indicator_trough1_idx = self._find_nearest_trough(price_trough1_idx, recent_indicator_troughs)
                indicator_trough2_idx = self._find_nearest_trough(price_trough2_idx, recent_indicator_troughs)
                
                if indicator_trough1_idx is None or indicator_trough2_idx is None:
                    continue
                
                # Check for bullish divergence
                price_lower = prices[price_trough2_idx] < prices[price_trough1_idx]
                indicator_higher = indicator[indicator_trough2_idx] > indicator[indicator_trough1_idx]
                
                if price_lower and indicator_higher:
                    # Calculate strength and confidence
                    price_change = (prices[price_trough1_idx] - prices[price_trough2_idx]) / prices[price_trough1_idx]
                    indicator_change = (indicator[indicator_trough2_idx] - indicator[indicator_trough1_idx]) / abs(indicator[indicator_trough1_idx]) if indicator[indicator_trough1_idx] != 0 else 0
                    
                    strength, confidence = self._calculate_divergence_strength(price_change, indicator_change)
                    
                    divergences.append(DivergenceSignal(
                        divergence_type='BULLISH',
                        indicator=indicator_name,
                        strength=strength,
                        confidence=confidence,
                        start_index=price_trough1_idx + offset,
                        end_index=price_trough2_idx + offset,
                        description=f"Bullish divergence: Giá tạo đáy thấp hơn nhưng {indicator_name} tạo đáy cao hơn",
                        price_trend='LOWER_LOWS',
                        indicator_trend='HIGHER_LOWS'
                    ))
        
        return divergences
    
    def _find_bearish_divergences(self, prices: np.ndarray, indicator: np.ndarray, 
                                price_peaks: List[int], indicator_peaks: List[int], 
                                indicator_name: str, offset: int) -> List[DivergenceSignal]:
        """Find bearish divergences."""
        divergences = []
        
        if len(price_peaks) < 2 or len(indicator_peaks) < 2:
            return divergences
        
        # Look for recent divergences
        recent_price_peaks = [p for p in price_peaks if p >= len(prices) - self.lookback_periods]
        recent_indicator_peaks = [p for p in indicator_peaks if p >= len(indicator) - self.lookback_periods]
        
        if len(recent_price_peaks) < 2 or len(recent_indicator_peaks) < 2:
            return divergences
        
        # Check each pair of recent peaks
        for i in range(len(recent_price_peaks) - 1):
            for j in range(i + 1, len(recent_price_peaks)):
                price_peak1_idx = recent_price_peaks[i]
                price_peak2_idx = recent_price_peaks[j]
                
                # Find corresponding indicator peaks
                indicator_peak1_idx = self._find_nearest_peak(price_peak1_idx, recent_indicator_peaks)
                indicator_peak2_idx = self._find_nearest_peak(price_peak2_idx, recent_indicator_peaks)
                
                if indicator_peak1_idx is None or indicator_peak2_idx is None:
                    continue
                
                # Check for bearish divergence
                price_higher = prices[price_peak2_idx] > prices[price_peak1_idx]
                indicator_lower = indicator[indicator_peak2_idx] < indicator[indicator_peak1_idx]
                
                if price_higher and indicator_lower:
                    # Calculate strength and confidence
                    price_change = (prices[price_peak2_idx] - prices[price_peak1_idx]) / prices[price_peak1_idx]
                    indicator_change = (indicator[indicator_peak1_idx] - indicator[indicator_peak2_idx]) / abs(indicator[indicator_peak1_idx]) if indicator[indicator_peak1_idx] != 0 else 0
                    
                    strength, confidence = self._calculate_divergence_strength(price_change, indicator_change)
                    
                    divergences.append(DivergenceSignal(
                        divergence_type='BEARISH',
                        indicator=indicator_name,
                        strength=strength,
                        confidence=confidence,
                        start_index=price_peak1_idx + offset,
                        end_index=price_peak2_idx + offset,
                        description=f"Bearish divergence: Giá tạo đỉnh cao hơn nhưng {indicator_name} tạo đỉnh thấp hơn",
                        price_trend='HIGHER_HIGHS',
                        indicator_trend='LOWER_HIGHS'
                    ))
        
        return divergences
    
    def _find_nearest_trough(self, target_idx: int, troughs: List[int], tolerance: int = 5) -> Optional[int]:
        """Find nearest trough to target index."""
        nearest = None
        min_distance = float('inf')
        
        for trough in troughs:
            distance = abs(trough - target_idx)
            if distance <= tolerance and distance < min_distance:
                min_distance = distance
                nearest = trough
        
        return nearest
    
    def _find_nearest_peak(self, target_idx: int, peaks: List[int], tolerance: int = 5) -> Optional[int]:
        """Find nearest peak to target index."""
        nearest = None
        min_distance = float('inf')
        
        for peak in peaks:
            distance = abs(peak - target_idx)
            if distance <= tolerance and distance < min_distance:
                min_distance = distance
                nearest = peak
        
        return nearest
    
    def _calculate_divergence_strength(self, price_change: float, indicator_change: float) -> Tuple[str, float]:
        """Calculate divergence strength and confidence."""
        # Normalize changes
        total_change = abs(price_change) + abs(indicator_change)
        
        if total_change == 0:
            return 'WEAK', 0.3
        
        # The larger the opposing changes, the stronger the divergence
        if total_change > 0.1:  # 10% combined change
            strength = 'STRONG'
            confidence = min(0.9, total_change * 5)
        elif total_change > 0.05:  # 5% combined change
            strength = 'MEDIUM'
            confidence = min(0.7, total_change * 8)
        else:
            strength = 'WEAK'
            confidence = min(0.5, total_change * 10)
        
        return strength, confidence
    
    def get_comprehensive_divergence_analysis(self, prices: List[float], volumes: List[float], 
                                            highs: List[float] = None, lows: List[float] = None) -> Dict:
        """Get comprehensive divergence analysis."""
        all_divergences = []
        
        try:
            # RSI divergences
            rsi_divs = self.detect_rsi_divergence(prices)
            all_divergences.extend(rsi_divs)
            
            # MACD divergences
            macd_divs = self.detect_macd_divergence(prices)
            all_divergences.extend(macd_divs)
            
            # Volume divergences
            if volumes:
                volume_divs = self.detect_volume_divergence(prices, volumes)
                all_divergences.extend(volume_divs)
            
            # Stochastic divergences (if highs/lows provided)
            if highs and lows:
                stoch_divs = self.detect_stochastic_divergence(highs, lows, prices)
                all_divergences.extend(stoch_divs)
            
            # Sort by confidence
            all_divergences.sort(key=lambda x: x.confidence, reverse=True)
            
            # Count by type and strength
            bullish_count = len([d for d in all_divergences if d.divergence_type == 'BULLISH'])
            bearish_count = len([d for d in all_divergences if d.divergence_type == 'BEARISH'])
            
            strong_count = len([d for d in all_divergences if d.strength == 'STRONG'])
            medium_count = len([d for d in all_divergences if d.strength == 'MEDIUM'])
            
            # Determine overall signal
            if strong_count > 0:
                if bullish_count > bearish_count:
                    overall_signal = 'STRONG_BULLISH'
                elif bearish_count > bullish_count:
                    overall_signal = 'STRONG_BEARISH'
                else:
                    overall_signal = 'MIXED_STRONG'
            elif medium_count > 0:
                if bullish_count > bearish_count:
                    overall_signal = 'MEDIUM_BULLISH'
                elif bearish_count > bullish_count:
                    overall_signal = 'MEDIUM_BEARISH'
                else:
                    overall_signal = 'MIXED_MEDIUM'
            else:
                overall_signal = 'WEAK' if all_divergences else 'NONE'
            
            # Generate summary
            summary = self._generate_divergence_summary(all_divergences, overall_signal)
            
            return {
                'total_divergences': len(all_divergences),
                'bullish_divergences': bullish_count,
                'bearish_divergences': bearish_count,
                'strong_divergences': strong_count,
                'medium_divergences': medium_count,
                'overall_signal': overall_signal,
                'summary': summary,
                'divergences': [
                    {
                        'type': d.divergence_type,
                        'indicator': d.indicator,
                        'strength': d.strength,
                        'confidence': d.confidence,
                        'description': d.description,
                        'start_index': d.start_index,
                        'end_index': d.end_index
                    }
                    for d in all_divergences[:5]  # Top 5 divergences
                ]
            }
            
        except Exception as e:
            return {
                'error': f'Lỗi trong divergence analysis: {str(e)}',
                'total_divergences': 0,
                'overall_signal': 'ERROR'
            }
    
    def _generate_divergence_summary(self, divergences: List[DivergenceSignal], overall_signal: str) -> str:
        """Generate divergence analysis summary."""
        if not divergences:
            return "Không phát hiện divergence nào đáng kể"
        
        if overall_signal.startswith('STRONG_BULLISH'):
            return f"Phát hiện {len(divergences)} divergence với tín hiệu bullish mạnh - Cơ hội mua tiềm năng"
        elif overall_signal.startswith('STRONG_BEARISH'):
            return f"Phát hiện {len(divergences)} divergence với tín hiệu bearish mạnh - Cảnh báo bán"
        elif overall_signal.startswith('MEDIUM_BULLISH'):
            return f"Phát hiện {len(divergences)} divergence với xu hướng bullish vừa phải"
        elif overall_signal.startswith('MEDIUM_BEARISH'):
            return f"Phát hiện {len(divergences)} divergence với xu hướng bearish vừa phải"
        elif 'MIXED' in overall_signal:
            return f"Phát hiện {len(divergences)} divergence hỗn hợp - Tín hiệu không rõ ràng"
        else:
            return f"Phát hiện {len(divergences)} divergence yếu - Cần xác nhận thêm"
