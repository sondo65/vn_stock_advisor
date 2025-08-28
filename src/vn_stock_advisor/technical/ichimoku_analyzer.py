"""
Ichimoku Analyzer for VN Stock Advisor.

This module implements Ichimoku Kinko Hyo (Ichimoku Cloud) analysis
for comprehensive trend and momentum analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class IchimokuSignal:
    """Ichimoku trading signal."""
    signal_type: str      # 'BUY', 'SELL', 'NEUTRAL'
    strength: str         # 'STRONG', 'MEDIUM', 'WEAK'
    confidence: float
    description: str
    conditions_met: List[str]

class IchimokuAnalyzer:
    """
    Comprehensive Ichimoku Kinko Hyo analysis.
    """
    
    def __init__(self, conversion_period: int = 9, base_period: int = 26, 
                 span_b_period: int = 52, displacement: int = 26):
        self.conversion_period = conversion_period
        self.base_period = base_period
        self.span_b_period = span_b_period
        self.displacement = displacement
    
    def calculate_ichimoku_components(self, highs: List[float], lows: List[float], 
                                    closes: List[float]) -> Dict:
        """
        Calculate all Ichimoku components.
        
        Args:
            highs: High prices
            lows: Low prices  
            closes: Close prices
            
        Returns:
            Dictionary with all Ichimoku components
        """
        if len(highs) < self.span_b_period + self.displacement:
            return {'error': 'Không đủ dữ liệu để tính Ichimoku'}
        
        highs_array = np.array(highs)
        lows_array = np.array(lows)
        closes_array = np.array(closes)
        
        # Calculate Tenkan-sen (Conversion Line)
        tenkan_sen = self._calculate_midpoint(highs_array, lows_array, self.conversion_period)
        
        # Calculate Kijun-sen (Base Line)
        kijun_sen = self._calculate_midpoint(highs_array, lows_array, self.base_period)
        
        # Calculate Senkou Span A (Leading Span A)
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        
        # Calculate Senkou Span B (Leading Span B)
        senkou_span_b = self._calculate_midpoint(highs_array, lows_array, self.span_b_period)
        
        # Calculate Chikou Span (Lagging Span) - displaced backwards
        chikou_span = np.full_like(closes_array, np.nan)
        if len(closes_array) > self.displacement:
            chikou_span[:-self.displacement] = closes_array[self.displacement:]
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span,
            'closes': closes_array
        }
    
    def _calculate_midpoint(self, highs: np.ndarray, lows: np.ndarray, period: int) -> np.ndarray:
        """Calculate midpoint of highest high and lowest low over period."""
        result = np.full_like(highs, np.nan, dtype=float)
        
        for i in range(period - 1, len(highs)):
            period_highs = highs[i - period + 1:i + 1]
            period_lows = lows[i - period + 1:i + 1]
            result[i] = (np.max(period_highs) + np.min(period_lows)) / 2
        
        return result
    
    def analyze_cloud_position(self, components: Dict, current_index: int = -1) -> Dict:
        """Analyze price position relative to Ichimoku cloud."""
        if 'error' in components:
            return components
        
        closes = components['closes']
        senkou_a = components['senkou_span_a']
        senkou_b = components['senkou_span_b']
        
        # Get current values
        current_price = closes[current_index]
        
        # Cloud values at current time (displaced forward)
        cloud_index = current_index - self.displacement
        if cloud_index < 0:
            return {'cloud_analysis': 'Không đủ dữ liệu cloud'}
        
        current_senkou_a = senkou_a[cloud_index]
        current_senkou_b = senkou_b[cloud_index]
        
        if np.isnan(current_senkou_a) or np.isnan(current_senkou_b):
            return {'cloud_analysis': 'Dữ liệu cloud không hợp lệ'}
        
        # Determine cloud color
        cloud_top = max(current_senkou_a, current_senkou_b)
        cloud_bottom = min(current_senkou_a, current_senkou_b)
        
        if current_senkou_a > current_senkou_b:
            cloud_color = 'GREEN'  # Bullish cloud
            cloud_sentiment = 'BULLISH'
        else:
            cloud_color = 'RED'    # Bearish cloud
            cloud_sentiment = 'BEARISH'
        
        # Price position relative to cloud
        if current_price > cloud_top:
            price_position = 'ABOVE_CLOUD'
            position_sentiment = 'BULLISH'
        elif current_price < cloud_bottom:
            price_position = 'BELOW_CLOUD'
            position_sentiment = 'BEARISH'
        else:
            price_position = 'IN_CLOUD'
            position_sentiment = 'NEUTRAL'
        
        # Calculate cloud thickness (volatility indicator)
        cloud_thickness = abs(current_senkou_a - current_senkou_b)
        cloud_thickness_pct = cloud_thickness / current_price * 100
        
        return {
            'cloud_color': cloud_color,
            'cloud_sentiment': cloud_sentiment,
            'price_position': price_position,
            'position_sentiment': position_sentiment,
            'cloud_top': cloud_top,
            'cloud_bottom': cloud_bottom,
            'cloud_thickness': cloud_thickness,
            'cloud_thickness_pct': cloud_thickness_pct,
            'current_price': current_price
        }
    
    def analyze_line_relationships(self, components: Dict, current_index: int = -1) -> Dict:
        """Analyze relationships between Ichimoku lines."""
        if 'error' in components:
            return components
        
        tenkan = components['tenkan_sen'][current_index]
        kijun = components['kijun_sen'][current_index]
        closes = components['closes'][current_index]
        
        if np.isnan(tenkan) or np.isnan(kijun):
            return {'line_analysis': 'Dữ liệu lines không đầy đủ'}
        
        analysis = {}
        
        # Tenkan-Kijun relationship
        if tenkan > kijun:
            analysis['tk_cross'] = 'GOLDEN_CROSS'
            analysis['tk_sentiment'] = 'BULLISH'
        elif tenkan < kijun:
            analysis['tk_cross'] = 'DEATH_CROSS'
            analysis['tk_sentiment'] = 'BEARISH'
        else:
            analysis['tk_cross'] = 'NEUTRAL'
            analysis['tk_sentiment'] = 'NEUTRAL'
        
        # Price relationship with lines
        price_vs_tenkan = 'ABOVE' if closes > tenkan else 'BELOW'
        price_vs_kijun = 'ABOVE' if closes > kijun else 'BELOW'
        
        analysis.update({
            'tenkan_sen': tenkan,
            'kijun_sen': kijun,
            'price_vs_tenkan': price_vs_tenkan,
            'price_vs_kijun': price_vs_kijun,
            'tenkan_kijun_distance': abs(tenkan - kijun),
            'tenkan_kijun_distance_pct': abs(tenkan - kijun) / closes * 100
        })
        
        return analysis
    
    def analyze_chikou_span(self, components: Dict, current_index: int = -1) -> Dict:
        """Analyze Chikou Span (Lagging Span) signals."""
        if 'error' in components:
            return components
        
        chikou = components['chikou_span']
        closes = components['closes']
        
        # Chikou span analysis
        chikou_index = current_index - self.displacement
        if chikou_index < 0 or chikou_index >= len(closes):
            return {'chikou_analysis': 'Không đủ dữ liệu Chikou'}
        
        current_chikou = chikou[current_index]
        historical_price = closes[chikou_index]
        
        if np.isnan(current_chikou):
            return {'chikou_analysis': 'Dữ liệu Chikou không hợp lệ'}
        
        if current_chikou > historical_price:
            chikou_signal = 'BULLISH'
            chikou_description = 'Chikou Span trên giá quá khứ - Tín hiệu tích cực'
        elif current_chikou < historical_price:
            chikou_signal = 'BEARISH'
            chikou_description = 'Chikou Span dưới giá quá khứ - Tín hiệu tiêu cực'
        else:
            chikou_signal = 'NEUTRAL'
            chikou_description = 'Chikou Span bằng giá quá khứ - Trung tính'
        
        return {
            'chikou_signal': chikou_signal,
            'chikou_description': chikou_description,
            'current_chikou': current_chikou,
            'historical_price': historical_price,
            'chikou_difference': current_chikou - historical_price,
            'chikou_difference_pct': (current_chikou - historical_price) / historical_price * 100
        }
    
    def generate_trading_signals(self, components: Dict, current_index: int = -1) -> IchimokuSignal:
        """Generate comprehensive Ichimoku trading signals."""
        if 'error' in components:
            return IchimokuSignal(
                signal_type='NEUTRAL',
                strength='WEAK',
                confidence=0.0,
                description=components['error'],
                conditions_met=[]
            )
        
        # Get all analyses
        cloud_analysis = self.analyze_cloud_position(components, current_index)
        line_analysis = self.analyze_line_relationships(components, current_index)
        chikou_analysis = self.analyze_chikou_span(components, current_index)
        
        # Collect bullish and bearish conditions
        bullish_conditions = []
        bearish_conditions = []
        
        # Cloud analysis
        if cloud_analysis.get('position_sentiment') == 'BULLISH':
            bullish_conditions.append('Giá trên Kumo (cloud)')
        elif cloud_analysis.get('position_sentiment') == 'BEARISH':
            bearish_conditions.append('Giá dưới Kumo (cloud)')
        
        if cloud_analysis.get('cloud_sentiment') == 'BULLISH':
            bullish_conditions.append('Kumo màu xanh (bullish)')
        elif cloud_analysis.get('cloud_sentiment') == 'BEARISH':
            bearish_conditions.append('Kumo màu đỏ (bearish)')
        
        # Line analysis
        if line_analysis.get('tk_sentiment') == 'BULLISH':
            bullish_conditions.append('Tenkan trên Kijun (Golden Cross)')
        elif line_analysis.get('tk_sentiment') == 'BEARISH':
            bearish_conditions.append('Tenkan dưới Kijun (Death Cross)')
        
        if line_analysis.get('price_vs_tenkan') == 'ABOVE':
            bullish_conditions.append('Giá trên Tenkan-sen')
        else:
            bearish_conditions.append('Giá dưới Tenkan-sen')
        
        if line_analysis.get('price_vs_kijun') == 'ABOVE':
            bullish_conditions.append('Giá trên Kijun-sen')
        else:
            bearish_conditions.append('Giá dưới Kijun-sen')
        
        # Chikou analysis
        if chikou_analysis.get('chikou_signal') == 'BULLISH':
            bullish_conditions.append('Chikou trên giá quá khứ')
        elif chikou_analysis.get('chikou_signal') == 'BEARISH':
            bearish_conditions.append('Chikou dưới giá quá khứ')
        
        # Determine overall signal
        bullish_score = len(bullish_conditions)
        bearish_score = len(bearish_conditions)
        total_conditions = bullish_score + bearish_score
        
        if bullish_score >= 4:
            signal_type = 'BUY'
            strength = 'STRONG' if bullish_score >= 5 else 'MEDIUM'
            confidence = bullish_score / 6  # Max 6 conditions
            conditions_met = bullish_conditions
            description = f"Tín hiệu mua mạnh với {bullish_score}/6 điều kiện bullish"
            
        elif bearish_score >= 4:
            signal_type = 'SELL'
            strength = 'STRONG' if bearish_score >= 5 else 'MEDIUM'
            confidence = bearish_score / 6
            conditions_met = bearish_conditions
            description = f"Tín hiệu bán mạnh với {bearish_score}/6 điều kiện bearish"
            
        elif bullish_score > bearish_score:
            signal_type = 'BUY'
            strength = 'WEAK'
            confidence = (bullish_score - bearish_score) / total_conditions if total_conditions > 0 else 0
            conditions_met = bullish_conditions
            description = f"Tín hiệu mua yếu với {bullish_score} điều kiện bullish vs {bearish_score} bearish"
            
        elif bearish_score > bullish_score:
            signal_type = 'SELL'
            strength = 'WEAK'
            confidence = (bearish_score - bullish_score) / total_conditions if total_conditions > 0 else 0
            conditions_met = bearish_conditions
            description = f"Tín hiệu bán yếu với {bearish_score} điều kiện bearish vs {bullish_score} bullish"
            
        else:
            signal_type = 'NEUTRAL'
            strength = 'WEAK'
            confidence = 0.5
            conditions_met = bullish_conditions + bearish_conditions
            description = "Tín hiệu trung tính - Cân bằng giữa bullish và bearish"
        
        return IchimokuSignal(
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            description=description,
            conditions_met=conditions_met
        )
    
    def get_ichimoku_summary(self, highs: List[float], lows: List[float], 
                           closes: List[float]) -> Dict:
        """Get comprehensive Ichimoku analysis summary."""
        # Calculate components
        components = self.calculate_ichimoku_components(highs, lows, closes)
        
        if 'error' in components:
            return components
        
        # Get all analyses
        cloud_analysis = self.analyze_cloud_position(components)
        line_analysis = self.analyze_line_relationships(components)
        chikou_analysis = self.analyze_chikou_span(components)
        trading_signal = self.generate_trading_signals(components)
        
        # Current values
        current_values = {
            'tenkan_sen': components['tenkan_sen'][-1],
            'kijun_sen': components['kijun_sen'][-1],
            'senkou_span_a': components['senkou_span_a'][-1],
            'senkou_span_b': components['senkou_span_b'][-1],
            'chikou_span': components['chikou_span'][-1],
            'current_price': components['closes'][-1]
        }
        
        return {
            'current_values': current_values,
            'cloud_analysis': cloud_analysis,
            'line_analysis': line_analysis,
            'chikou_analysis': chikou_analysis,
            'trading_signal': {
                'signal': trading_signal.signal_type,
                'strength': trading_signal.strength,
                'confidence': trading_signal.confidence,
                'description': trading_signal.description,
                'conditions_met': trading_signal.conditions_met
            },
            'interpretation': self._generate_interpretation(
                cloud_analysis, line_analysis, chikou_analysis, trading_signal
            )
        }
    
    def _generate_interpretation(self, cloud_analysis: Dict, line_analysis: Dict, 
                               chikou_analysis: Dict, signal: IchimokuSignal) -> str:
        """Generate human-readable interpretation of Ichimoku analysis."""
        interpretation = []
        
        # Cloud interpretation
        if cloud_analysis.get('price_position') == 'ABOVE_CLOUD':
            interpretation.append("Giá đang trên Kumo - Xu hướng tăng mạnh")
        elif cloud_analysis.get('price_position') == 'BELOW_CLOUD':
            interpretation.append("Giá đang dưới Kumo - Xu hướng giảm mạnh")
        else:
            interpretation.append("Giá đang trong Kumo - Giai đoạn cân bằng/đảo chiều")
        
        # Line interpretation
        if line_analysis.get('tk_sentiment') == 'BULLISH':
            interpretation.append("Tenkan-Kijun Golden Cross - Momentum tích cực")
        elif line_analysis.get('tk_sentiment') == 'BEARISH':
            interpretation.append("Tenkan-Kijun Death Cross - Momentum tiêu cực")
        
        # Overall signal
        interpretation.append(f"Tín hiệu tổng thể: {signal.signal_type} ({signal.strength})")
        
        return " | ".join(interpretation)
