"""
Fibonacci Calculator for VN Stock Advisor.

This module calculates Fibonacci retracement and extension levels
for technical analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class FibonacciLevel:
    """Fibonacci level information."""
    level: float        # Fibonacci ratio (e.g., 0.382, 0.618)
    price: float        # Price at this level
    level_type: str     # 'retracement' or 'extension'
    significance: str   # 'STRONG', 'MEDIUM', 'WEAK'
    description: str

class FibonacciCalculator:
    """
    Calculate Fibonacci retracement and extension levels.
    """
    
    def __init__(self):
        # Standard Fibonacci ratios
        self.retracement_ratios = [0.236, 0.382, 0.500, 0.618, 0.786]
        self.extension_ratios = [1.272, 1.414, 1.618, 2.000, 2.618]
        
        # Significance levels
        self.strong_levels = [0.382, 0.618, 1.618]  # Golden ratios
        self.medium_levels = [0.500, 1.272, 2.000]
        
    def calculate_retracement_levels(self, high_price: float, low_price: float, 
                                   trend_direction: str = 'UP') -> List[FibonacciLevel]:
        """
        Calculate Fibonacci retracement levels.
        
        Args:
            high_price: Highest price in the move
            low_price: Lowest price in the move
            trend_direction: 'UP' or 'DOWN'
            
        Returns:
            List of FibonacciLevel objects
        """
        levels = []
        
        if trend_direction.upper() == 'UP':
            # For uptrend, retracements are calculated from high to low
            price_range = high_price - low_price
            
            for ratio in self.retracement_ratios:
                retracement_price = high_price - (price_range * ratio)
                significance = self._determine_significance(ratio)
                
                levels.append(FibonacciLevel(
                    level=ratio,
                    price=retracement_price,
                    level_type='retracement',
                    significance=significance,
                    description=f"Fibonacci {ratio:.1%} retracement tại {retracement_price:.0f}"
                ))
        
        else:  # DOWN trend
            # For downtrend, retracements are calculated from low to high
            price_range = high_price - low_price
            
            for ratio in self.retracement_ratios:
                retracement_price = low_price + (price_range * ratio)
                significance = self._determine_significance(ratio)
                
                levels.append(FibonacciLevel(
                    level=ratio,
                    price=retracement_price,
                    level_type='retracement',
                    significance=significance,
                    description=f"Fibonacci {ratio:.1%} retracement tại {retracement_price:.0f}"
                ))
        
        return levels
    
    def calculate_extension_levels(self, high_price: float, low_price: float, 
                                 retracement_price: float, 
                                 trend_direction: str = 'UP') -> List[FibonacciLevel]:
        """
        Calculate Fibonacci extension levels.
        
        Args:
            high_price: Highest price in the initial move
            low_price: Lowest price in the initial move
            retracement_price: Price at the end of retracement
            trend_direction: 'UP' or 'DOWN'
            
        Returns:
            List of FibonacciLevel objects
        """
        levels = []
        price_range = abs(high_price - low_price)
        
        if trend_direction.upper() == 'UP':
            # For uptrend, extensions are above the retracement price
            for ratio in self.extension_ratios:
                extension_price = retracement_price + (price_range * ratio)
                significance = self._determine_significance(ratio)
                
                levels.append(FibonacciLevel(
                    level=ratio,
                    price=extension_price,
                    level_type='extension',
                    significance=significance,
                    description=f"Fibonacci {ratio:.3f} extension tại {extension_price:.0f}"
                ))
        
        else:  # DOWN trend
            # For downtrend, extensions are below the retracement price
            for ratio in self.extension_ratios:
                extension_price = retracement_price - (price_range * ratio)
                significance = self._determine_significance(ratio)
                
                levels.append(FibonacciLevel(
                    level=ratio,
                    price=extension_price,
                    level_type='extension',
                    significance=significance,
                    description=f"Fibonacci {ratio:.3f} extension tại {extension_price:.0f}"
                ))
        
        return levels
    
    def auto_detect_swing_points(self, prices: List[float], window: int = 20) -> Dict:
        """
        Automatically detect swing highs and lows for Fibonacci calculation.
        
        Args:
            prices: List of price values
            window: Window size for swing detection
            
        Returns:
            Dictionary with swing high and low information
        """
        if len(prices) < window * 2:
            return {'swing_high': None, 'swing_low': None, 'trend': None}
        
        prices_array = np.array(prices)
        
        # Find local maxima and minima using a more relaxed approach
        swing_highs = []
        swing_lows = []
        
        # Use smaller window for detection if original fails
        detection_window = min(window, 5)
        
        for i in range(detection_window, len(prices_array) - detection_window):
            # Check for swing high (local maximum)
            is_high = True
            for j in range(i - detection_window, i + detection_window + 1):
                if j != i and prices_array[j] > prices_array[i]:
                    is_high = False
                    break
            if is_high:
                swing_highs.append((i, prices_array[i]))
            
            # Check for swing low (local minimum)
            is_low = True
            for j in range(i - detection_window, i + detection_window + 1):
                if j != i and prices_array[j] < prices_array[i]:
                    is_low = False
                    break
            if is_low:
                swing_lows.append((i, prices_array[i]))
        
        # If still no swing points found, use simple high/low approach
        if not swing_highs or not swing_lows:
            # Find highest and lowest points in the data
            max_idx = np.argmax(prices_array)
            min_idx = np.argmin(prices_array)
            
            swing_highs = [(max_idx, prices_array[max_idx])]
            swing_lows = [(min_idx, prices_array[min_idx])]
        
        # Get most recent significant swing points
        recent_high = max(swing_highs, key=lambda x: x[1])  # Highest high
        recent_low = min(swing_lows, key=lambda x: x[1])    # Lowest low
        
        # Determine trend based on which came last
        last_high_index = recent_high[0]
        last_low_index = recent_low[0]
        
        if last_high_index > last_low_index:
            trend = 'DOWN'  # High came after low, possibly downtrend
        else:
            trend = 'UP'    # Low came after high, possibly uptrend
        
        return {
            'swing_high': {'index': recent_high[0], 'price': recent_high[1]},
            'swing_low': {'index': recent_low[0], 'price': recent_low[1]},
            'trend': trend
        }
    
    def analyze_price_at_fibonacci_levels(self, current_price: float, 
                                        fibonacci_levels: List[FibonacciLevel]) -> Dict:
        """
        Analyze current price position relative to Fibonacci levels.
        
        Args:
            current_price: Current market price
            fibonacci_levels: List of Fibonacci levels
            
        Returns:
            Analysis results
        """
        if not fibonacci_levels:
            return {'status': 'no_levels', 'message': 'Không có Fibonacci levels để phân tích'}
        
        # Find closest levels above and below current price
        levels_below = [level for level in fibonacci_levels if level.price < current_price]
        levels_above = [level for level in fibonacci_levels if level.price > current_price]
        
        # Sort to find nearest levels
        levels_below.sort(key=lambda x: x.price, reverse=True)  # Highest below
        levels_above.sort(key=lambda x: x.price)  # Lowest above
        
        nearest_support = levels_below[0] if levels_below else None
        nearest_resistance = levels_above[0] if levels_above else None
        
        # Check if price is very close to a Fibonacci level (within 1%)
        tolerance = 0.01
        at_fibonacci_level = None
        
        for level in fibonacci_levels:
            if abs(current_price - level.price) / current_price <= tolerance:
                at_fibonacci_level = level
                break
        
        # Generate analysis
        analysis = {
            'current_price': current_price,
            'at_fibonacci_level': at_fibonacci_level,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'support_distance': abs(current_price - nearest_support.price) if nearest_support else None,
            'resistance_distance': abs(nearest_resistance.price - current_price) if nearest_resistance else None
        }
        
        # Generate trading recommendation
        recommendation = self._generate_fibonacci_recommendation(analysis)
        analysis['recommendation'] = recommendation
        
        return analysis
    
    def _determine_significance(self, ratio: float) -> str:
        """Determine the significance of a Fibonacci ratio."""
        if ratio in self.strong_levels:
            return 'STRONG'
        elif ratio in self.medium_levels:
            return 'MEDIUM'
        else:
            return 'WEAK'
    
    def _generate_fibonacci_recommendation(self, analysis: Dict) -> str:
        """Generate trading recommendation based on Fibonacci analysis."""
        current_price = analysis['current_price']
        at_level = analysis['at_fibonacci_level']
        support = analysis['nearest_support']
        resistance = analysis['nearest_resistance']
        
        if at_level:
            if at_level.significance == 'STRONG':
                if at_level.level_type == 'retracement':
                    return f"Giá đang tại vùng Fibonacci {at_level.level:.1%} quan trọng - Có thể là điểm đảo chiều"
                else:
                    return f"Giá đang tại extension {at_level.level:.3f} - Khu vực chốt lời tiềm năng"
            else:
                return f"Giá gần Fibonacci level {at_level.level:.1%} - Theo dõi để xác nhận"
        
        recommendation_parts = []
        
        if support and support.significance in ['STRONG', 'MEDIUM']:
            support_distance = analysis['support_distance']
            support_pct = support_distance / current_price * 100
            
            if support_pct < 2:
                recommendation_parts.append(f"Gần vùng hỗ trợ Fibonacci {support.level:.1%} ({support.price:.0f})")
            else:
                recommendation_parts.append(f"Hỗ trợ Fibonacci tại {support.price:.0f}")
        
        if resistance and resistance.significance in ['STRONG', 'MEDIUM']:
            resistance_distance = analysis['resistance_distance']
            resistance_pct = resistance_distance / current_price * 100
            
            if resistance_pct < 2:
                recommendation_parts.append(f"Gần vùng kháng cự Fibonacci {resistance.level:.1%} ({resistance.price:.0f})")
            else:
                recommendation_parts.append(f"Kháng cự Fibonacci tại {resistance.price:.0f}")
        
        if recommendation_parts:
            return " | ".join(recommendation_parts)
        else:
            return "Giá không ở gần các level Fibonacci quan trọng"
    
    def get_fibonacci_summary(self, prices: List[float], current_price: float = None) -> Dict:
        """
        Get comprehensive Fibonacci analysis summary.
        
        Args:
            prices: Historical price data
            current_price: Current market price (uses last price if not provided)
            
        Returns:
            Complete Fibonacci analysis
        """
        if len(prices) < 40:
            return {'error': 'Không đủ dữ liệu để tính Fibonacci levels'}
        
        if current_price is None:
            current_price = prices[-1]
        
        # Auto-detect swing points
        swing_data = self.auto_detect_swing_points(prices)
        
        if not swing_data['swing_high'] or not swing_data['swing_low']:
            return {'error': 'Không thể xác định swing points'}
        
        high_price = swing_data['swing_high']['price']
        low_price = swing_data['swing_low']['price']
        trend = swing_data['trend']
        
        # Calculate retracement levels
        retracement_levels = self.calculate_retracement_levels(high_price, low_price, trend)
        
        # Calculate extension levels (using current price as retracement point)
        extension_levels = self.calculate_extension_levels(high_price, low_price, current_price, trend)
        
        # Combine all levels
        all_levels = retracement_levels + extension_levels
        
        # Analyze current price position
        price_analysis = self.analyze_price_at_fibonacci_levels(current_price, all_levels)
        
        return {
            'swing_high': high_price,
            'swing_low': low_price,
            'trend_direction': trend,
            'current_price': current_price,
            'retracement_levels': [
                {
                    'ratio': level.level,
                    'price': level.price,
                    'significance': level.significance,
                    'description': level.description
                }
                for level in retracement_levels
            ],
            'extension_levels': [
                {
                    'ratio': level.level,
                    'price': level.price,
                    'significance': level.significance,
                    'description': level.description
                }
                for level in extension_levels
            ],
            'price_analysis': price_analysis,
            'key_levels': [
                level for level in all_levels 
                if level.significance in ['STRONG', 'MEDIUM']
            ]
        }
