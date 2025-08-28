"""
Pattern Recognition for VN Stock Advisor.

This module uses machine learning to identify and classify
common chart patterns in stock price data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.signal import find_peaks, find_peaks_cwt

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestClassifier
    import talib as ta
except ImportError:
    StandardScaler = None
    KMeans = None
    RandomForestClassifier = None
    ta = None

@dataclass
class PatternSignal:
    """Signal detected from pattern recognition."""
    pattern_name: str
    confidence: float
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    start_index: int
    end_index: int
    description: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None

class PatternRecognition:
    """
    Advanced pattern recognition using ML and traditional techniques.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.known_patterns = {
            'double_top': 'Double Top - Bearish reversal pattern',
            'double_bottom': 'Double Bottom - Bullish reversal pattern',
            'head_shoulders': 'Head and Shoulders - Bearish reversal pattern',
            'inverse_head_shoulders': 'Inverse Head and Shoulders - Bullish reversal pattern',
            'ascending_triangle': 'Ascending Triangle - Bullish continuation pattern',
            'descending_triangle': 'Descending Triangle - Bearish continuation pattern',
            'symmetrical_triangle': 'Symmetrical Triangle - Neutral pattern',
            'flag': 'Flag - Continuation pattern',
            'pennant': 'Pennant - Continuation pattern',
            'cup_handle': 'Cup and Handle - Bullish continuation pattern'
        }
    
    def detect_support_resistance(self, prices: List[float], window: int = 20) -> Dict:
        """Detect support and resistance levels."""
        prices_array = np.array(prices)
        
        # Find peaks (resistance) and troughs (support)
        peaks, _ = find_peaks(prices_array, distance=window, prominence=np.std(prices_array)*0.5)
        troughs, _ = find_peaks(-prices_array, distance=window, prominence=np.std(prices_array)*0.5)
        
        # Calculate support and resistance levels
        resistance_levels = prices_array[peaks] if len(peaks) > 0 else []
        support_levels = prices_array[troughs] if len(troughs) > 0 else []
        
        return {
            'support_levels': support_levels.tolist(),
            'resistance_levels': resistance_levels.tolist(),
            'support_indices': troughs.tolist(),
            'resistance_indices': peaks.tolist()
        }
    
    def detect_double_top(self, prices: List[float], threshold: float = 0.02) -> Optional[PatternSignal]:
        """Detect double top pattern."""
        if len(prices) < 50:
            return None
        
        prices_array = np.array(prices)
        peaks, _ = find_peaks(prices_array, distance=20, prominence=np.std(prices_array)*0.5)
        
        if len(peaks) < 2:
            return None
        
        # Check for double top pattern
        for i in range(len(peaks) - 1):
            peak1_idx, peak2_idx = peaks[i], peaks[i + 1]
            peak1_price, peak2_price = prices_array[peak1_idx], prices_array[peak2_idx]
            
            # Check if peaks are approximately equal
            if abs(peak1_price - peak2_price) / max(peak1_price, peak2_price) <= threshold:
                # Find the valley between peaks
                valley_idx = np.argmin(prices_array[peak1_idx:peak2_idx]) + peak1_idx
                valley_price = prices_array[valley_idx]
                
                # Calculate confidence based on pattern quality
                height_ratio = (min(peak1_price, peak2_price) - valley_price) / min(peak1_price, peak2_price)
                confidence = min(0.95, height_ratio * 2)
                
                return PatternSignal(
                    pattern_name='double_top',
                    confidence=confidence,
                    signal_type='SELL',
                    start_index=peak1_idx,
                    end_index=peak2_idx,
                    description=self.known_patterns['double_top'],
                    price_target=valley_price * 0.98,  # Target below valley
                    stop_loss=max(peak1_price, peak2_price) * 1.02
                )
        
        return None
    
    def detect_double_bottom(self, prices: List[float], threshold: float = 0.02) -> Optional[PatternSignal]:
        """Detect double bottom pattern."""
        if len(prices) < 50:
            return None
        
        prices_array = np.array(prices)
        troughs, _ = find_peaks(-prices_array, distance=20, prominence=np.std(prices_array)*0.5)
        
        if len(troughs) < 2:
            return None
        
        # Check for double bottom pattern
        for i in range(len(troughs) - 1):
            trough1_idx, trough2_idx = troughs[i], troughs[i + 1]
            trough1_price, trough2_price = prices_array[trough1_idx], prices_array[trough2_idx]
            
            # Check if troughs are approximately equal
            if abs(trough1_price - trough2_price) / max(trough1_price, trough2_price) <= threshold:
                # Find the peak between troughs
                peak_idx = np.argmax(prices_array[trough1_idx:trough2_idx]) + trough1_idx
                peak_price = prices_array[peak_idx]
                
                # Calculate confidence
                height_ratio = (peak_price - max(trough1_price, trough2_price)) / peak_price
                confidence = min(0.95, height_ratio * 2)
                
                return PatternSignal(
                    pattern_name='double_bottom',
                    confidence=confidence,
                    signal_type='BUY',
                    start_index=trough1_idx,
                    end_index=trough2_idx,
                    description=self.known_patterns['double_bottom'],
                    price_target=peak_price * 1.02,  # Target above peak
                    stop_loss=min(trough1_price, trough2_price) * 0.98
                )
        
        return None
    
    def detect_head_shoulders(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect head and shoulders pattern."""
        if len(prices) < 60:
            return None
        
        prices_array = np.array(prices)
        peaks, _ = find_peaks(prices_array, distance=15, prominence=np.std(prices_array)*0.3)
        
        if len(peaks) < 3:
            return None
        
        # Look for head and shoulders pattern
        for i in range(len(peaks) - 2):
            left_shoulder = peaks[i]
            head = peaks[i + 1]
            right_shoulder = peaks[i + 2]
            
            left_price = prices_array[left_shoulder]
            head_price = prices_array[head]
            right_price = prices_array[right_shoulder]
            
            # Check head and shoulders criteria
            if (head_price > left_price and head_price > right_price and
                abs(left_price - right_price) / max(left_price, right_price) <= 0.05):
                
                # Find neckline (valleys between shoulders and head)
                left_valley_idx = np.argmin(prices_array[left_shoulder:head]) + left_shoulder
                right_valley_idx = np.argmin(prices_array[head:right_shoulder]) + head
                
                neckline_price = (prices_array[left_valley_idx] + prices_array[right_valley_idx]) / 2
                
                confidence = min(0.9, (head_price - neckline_price) / head_price * 2)
                
                return PatternSignal(
                    pattern_name='head_shoulders',
                    confidence=confidence,
                    signal_type='SELL',
                    start_index=left_shoulder,
                    end_index=right_shoulder,
                    description=self.known_patterns['head_shoulders'],
                    price_target=neckline_price * 0.95,
                    stop_loss=head_price * 1.02
                )
        
        return None
    
    def detect_triangle_patterns(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        if len(prices) < 40:
            return None
        
        prices_array = np.array(prices)
        
        # Find recent highs and lows
        recent_data = prices_array[-40:]
        peaks, _ = find_peaks(recent_data, distance=5)
        troughs, _ = find_peaks(-recent_data, distance=5)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Get trend lines
        peak_prices = recent_data[peaks]
        trough_prices = recent_data[troughs]
        
        # Calculate trend slopes
        if len(peaks) >= 2:
            peak_slope = (peak_prices[-1] - peak_prices[0]) / (peaks[-1] - peaks[0])
        else:
            peak_slope = 0
            
        if len(troughs) >= 2:
            trough_slope = (trough_prices[-1] - trough_prices[0]) / (troughs[-1] - troughs[0])
        else:
            trough_slope = 0
        
        # Determine triangle type
        if abs(peak_slope) < 0.001 and trough_slope > 0.001:
            pattern_type = 'ascending_triangle'
            signal_type = 'BUY'
            confidence = 0.7
        elif peak_slope < -0.001 and abs(trough_slope) < 0.001:
            pattern_type = 'descending_triangle'
            signal_type = 'SELL'
            confidence = 0.7
        elif abs(peak_slope) < 0.002 and abs(trough_slope) < 0.002:
            pattern_type = 'symmetrical_triangle'
            signal_type = 'NEUTRAL'
            confidence = 0.6
        else:
            return None
        
        return PatternSignal(
            pattern_name=pattern_type,
            confidence=confidence,
            signal_type=signal_type,
            start_index=len(prices) - 40,
            end_index=len(prices) - 1,
            description=self.known_patterns[pattern_type],
            price_target=prices_array[-1] * (1.05 if signal_type == 'BUY' else 0.95),
            stop_loss=prices_array[-1] * (0.98 if signal_type == 'BUY' else 1.02)
        )
    
    def detect_flag_pattern(self, prices: List[float], volumes: List[float] = None) -> Optional[PatternSignal]:
        """Detect flag and pennant patterns."""
        if len(prices) < 30:
            return None
        
        prices_array = np.array(prices)
        
        # Look for strong trend followed by consolidation
        recent_prices = prices_array[-30:]
        trend_prices = prices_array[-50:-30] if len(prices) >= 50 else prices_array[:-30]
        
        if len(trend_prices) < 10:
            return None
        
        # Calculate trend strength
        trend_change = (trend_prices[-1] - trend_prices[0]) / trend_prices[0]
        
        # Check for consolidation
        consolidation_volatility = np.std(recent_prices) / np.mean(recent_prices)
        
        # Flag pattern criteria
        if abs(trend_change) > 0.05 and consolidation_volatility < 0.03:
            signal_type = 'BUY' if trend_change > 0 else 'SELL'
            confidence = min(0.8, abs(trend_change) * 10)
            
            return PatternSignal(
                pattern_name='flag',
                confidence=confidence,
                signal_type=signal_type,
                start_index=len(prices) - 30,
                end_index=len(prices) - 1,
                description=self.known_patterns['flag'],
                price_target=prices_array[-1] * (1.1 if signal_type == 'BUY' else 0.9),
                stop_loss=prices_array[-1] * (0.95 if signal_type == 'BUY' else 1.05)
            )
        
        return None
    
    def analyze_patterns(self, prices: List[float], volumes: List[float] = None) -> List[PatternSignal]:
        """Comprehensive pattern analysis."""
        patterns = []
        
        # Detect various patterns
        double_top = self.detect_double_top(prices)
        if double_top:
            patterns.append(double_top)
        
        double_bottom = self.detect_double_bottom(prices)
        if double_bottom:
            patterns.append(double_bottom)
        
        head_shoulders = self.detect_head_shoulders(prices)
        if head_shoulders:
            patterns.append(head_shoulders)
        
        triangle = self.detect_triangle_patterns(prices)
        if triangle:
            patterns.append(triangle)
        
        flag = self.detect_flag_pattern(prices, volumes)
        if flag:
            patterns.append(flag)
        
        # Sort by confidence
        patterns.sort(key=lambda x: x.confidence, reverse=True)
        
        return patterns
    
    def get_pattern_summary(self, patterns: List[PatternSignal]) -> Dict:
        """Get summary of detected patterns."""
        if not patterns:
            return {
                'total_patterns': 0,
                'bullish_signals': 0,
                'bearish_signals': 0,
                'neutral_signals': 0,
                'max_confidence': 0.0,
                'primary_signal': 'NEUTRAL',
                'recommendation': 'No clear pattern signals detected'
            }
        
        bullish = len([p for p in patterns if p.signal_type == 'BUY'])
        bearish = len([p for p in patterns if p.signal_type == 'SELL'])
        neutral = len([p for p in patterns if p.signal_type == 'NEUTRAL'])
        
        # Determine primary signal based on highest confidence patterns
        high_confidence_patterns = [p for p in patterns if p.confidence > 0.7]
        
        if high_confidence_patterns:
            primary_pattern = high_confidence_patterns[0]
            primary_signal = primary_pattern.signal_type
            recommendation = f"Phát hiện pattern {primary_pattern.pattern_name} với độ tin cậy {primary_pattern.confidence:.1%}"
        else:
            primary_signal = 'NEUTRAL'
            recommendation = 'Các pattern có độ tin cậy thấp, cần quan sát thêm'
        
        return {
            'total_patterns': len(patterns),
            'bullish_signals': bullish,
            'bearish_signals': bearish,
            'neutral_signals': neutral,
            'max_confidence': max(p.confidence for p in patterns),
            'primary_signal': primary_signal,
            'recommendation': recommendation,
            'patterns': [
                {
                    'name': p.pattern_name,
                    'confidence': p.confidence,
                    'signal': p.signal_type,
                    'description': p.description
                }
                for p in patterns[:3]  # Top 3 patterns
            ]
        }
