"""
Volume Analyzer for VN Stock Advisor.

This module provides advanced volume analysis including
Volume Profile, VWAP, and volume-based indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class VolumeLevel:
    """Volume level information."""
    price_level: float
    volume: float
    volume_percentage: float
    level_type: str  # 'POC', 'VAH', 'VAL', 'HVOL', 'LVOL'
    significance: str  # 'HIGH', 'MEDIUM', 'LOW'

class VolumeAnalyzer:
    """
    Advanced volume analysis and Volume Profile calculations.
    """
    
    def __init__(self, price_bins: int = 50):
        self.price_bins = price_bins
    
    def calculate_volume_profile(self, prices: List[float], volumes: List[float], 
                               highs: List[float] = None, lows: List[float] = None) -> Dict:
        """
        Calculate Volume Profile (Volume at Price).
        
        Args:
            prices: Close prices
            volumes: Volume data
            highs: High prices (optional)
            lows: Low prices (optional)
            
        Returns:
            Volume Profile analysis
        """
        if len(prices) != len(volumes):
            return {'error': 'Prices and volumes must have same length'}
        
        if len(prices) < 20:
            return {'error': 'Không đủ dữ liệu để tính Volume Profile'}
        
        prices_array = np.array(prices)
        volumes_array = np.array(volumes)
        
        # Use highs/lows if provided, otherwise use close prices
        if highs and lows:
            price_range_min = min(min(lows), min(prices))
            price_range_max = max(max(highs), max(prices))
        else:
            price_range_min = min(prices)
            price_range_max = max(prices)
        
        # Create price bins
        price_bins = np.linspace(price_range_min, price_range_max, self.price_bins)
        volume_at_price = np.zeros(len(price_bins) - 1)
        
        # Distribute volume across price bins
        for i, (price, volume) in enumerate(zip(prices_array, volumes_array)):
            # Find which bin this price belongs to
            bin_index = np.digitize(price, price_bins) - 1
            
            # Ensure valid bin index
            if 0 <= bin_index < len(volume_at_price):
                if highs and lows and i < len(highs) and i < len(lows):
                    # Distribute volume across the high-low range
                    high_bin = np.digitize(highs[i], price_bins) - 1
                    low_bin = np.digitize(lows[i], price_bins) - 1
                    
                    # Distribute volume evenly across the range
                    start_bin = max(0, min(high_bin, low_bin))
                    end_bin = min(len(volume_at_price) - 1, max(high_bin, low_bin))
                    
                    bins_in_range = end_bin - start_bin + 1
                    if bins_in_range > 0:
                        volume_per_bin = volume / bins_in_range
                        for j in range(start_bin, end_bin + 1):
                            volume_at_price[j] += volume_per_bin
                else:
                    volume_at_price[bin_index] += volume
        
        # Calculate bin centers
        bin_centers = (price_bins[:-1] + price_bins[1:]) / 2
        
        # Calculate key levels
        total_volume = np.sum(volume_at_price)
        volume_percentages = volume_at_price / total_volume * 100
        
        # Find Point of Control (POC) - highest volume price level
        poc_index = np.argmax(volume_at_price)
        poc_price = bin_centers[poc_index]
        poc_volume = volume_at_price[poc_index]
        
        # Calculate Value Area (70% of volume)
        value_area_volume = total_volume * 0.70
        
        # Find Value Area High (VAH) and Value Area Low (VAL)
        sorted_indices = np.argsort(volume_at_price)[::-1]  # Sort by volume descending
        cumulative_volume = 0
        value_area_indices = []
        
        for idx in sorted_indices:
            cumulative_volume += volume_at_price[idx]
            value_area_indices.append(idx)
            if cumulative_volume >= value_area_volume:
                break
        
        vah_price = bin_centers[max(value_area_indices)]
        val_price = bin_centers[min(value_area_indices)]
        
        # Create volume levels
        volume_levels = []
        
        # Add POC
        volume_levels.append(VolumeLevel(
            price_level=poc_price,
            volume=poc_volume,
            volume_percentage=poc_volume / total_volume * 100,
            level_type='POC',
            significance='HIGH'
        ))
        
        # Add VAH and VAL
        if vah_price != poc_price:
            vah_index = np.argmin(np.abs(bin_centers - vah_price))
            volume_levels.append(VolumeLevel(
                price_level=vah_price,
                volume=volume_at_price[vah_index],
                volume_percentage=volume_at_price[vah_index] / total_volume * 100,
                level_type='VAH',
                significance='MEDIUM'
            ))
        
        if val_price != poc_price:
            val_index = np.argmin(np.abs(bin_centers - val_price))
            volume_levels.append(VolumeLevel(
                price_level=val_price,
                volume=volume_at_price[val_index],
                volume_percentage=volume_at_price[val_index] / total_volume * 100,
                level_type='VAL',
                significance='MEDIUM'
            ))
        
        # Add high volume levels
        high_volume_threshold = np.percentile(volume_at_price, 80)
        for i, volume in enumerate(volume_at_price):
            if volume >= high_volume_threshold and bin_centers[i] not in [poc_price, vah_price, val_price]:
                volume_levels.append(VolumeLevel(
                    price_level=bin_centers[i],
                    volume=volume,
                    volume_percentage=volume / total_volume * 100,
                    level_type='HVOL',
                    significance='LOW'
                ))
        
        return {
            'poc_price': poc_price,
            'vah_price': vah_price,
            'val_price': val_price,
            'value_area_range': vah_price - val_price,
            'value_area_range_pct': (vah_price - val_price) / poc_price * 100,
            'total_volume': total_volume,
            'volume_levels': volume_levels,
            'price_bins': bin_centers,
            'volume_at_price': volume_at_price,
            'volume_percentages': volume_percentages
        }
    
    def calculate_vwap(self, prices: List[float], volumes: List[float], 
                      highs: List[float] = None, lows: List[float] = None) -> np.ndarray:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        Args:
            prices: Close prices
            volumes: Volume data
            highs: High prices (optional)
            lows: Low prices (optional)
            
        Returns:
            VWAP values
        """
        if len(prices) != len(volumes):
            raise ValueError("Prices and volumes must have same length")
        
        prices_array = np.array(prices)
        volumes_array = np.array(volumes)
        
        # Calculate typical price if highs/lows provided
        if highs and lows and len(highs) == len(prices) and len(lows) == len(prices):
            typical_prices = (np.array(highs) + np.array(lows) + prices_array) / 3
        else:
            typical_prices = prices_array
        
        # Calculate VWAP
        vwap = np.zeros_like(prices_array)
        cumulative_pv = 0  # Cumulative Price * Volume
        cumulative_volume = 0
        
        for i in range(len(prices_array)):
            cumulative_pv += typical_prices[i] * volumes_array[i]
            cumulative_volume += volumes_array[i]
            
            if cumulative_volume > 0:
                vwap[i] = cumulative_pv / cumulative_volume
            else:
                vwap[i] = typical_prices[i]
        
        return vwap
    
    def analyze_volume_trend(self, volumes: List[float], window: int = 20) -> Dict:
        """Analyze volume trend and patterns."""
        if len(volumes) < window:
            return {'error': 'Không đủ dữ liệu để phân tích volume trend'}
        
        volumes_array = np.array(volumes)
        
        # Calculate volume moving average
        volume_ma = np.convolve(volumes_array, np.ones(window), 'valid') / window
        
        # Current volume vs average
        current_volume = volumes_array[-1]
        recent_avg_volume = volume_ma[-1] if len(volume_ma) > 0 else np.mean(volumes_array[-window:])
        
        volume_ratio = current_volume / recent_avg_volume
        
        # Volume trend analysis
        if len(volume_ma) >= 5:
            recent_volume_ma = volume_ma[-5:]
            if np.all(np.diff(recent_volume_ma) > 0):
                volume_trend = 'INCREASING'
            elif np.all(np.diff(recent_volume_ma) < 0):
                volume_trend = 'DECREASING'
            else:
                volume_trend = 'SIDEWAYS'
        else:
            volume_trend = 'UNCLEAR'
        
        # Volume spikes detection
        volume_spikes = []
        spike_threshold = 2.0  # 2x average volume
        
        for i in range(window, len(volumes_array)):
            avg_volume = np.mean(volumes_array[i-window:i])
            if volumes_array[i] > avg_volume * spike_threshold:
                volume_spikes.append({
                    'index': i,
                    'volume': volumes_array[i],
                    'ratio': volumes_array[i] / avg_volume
                })
        
        # Volume analysis summary
        if volume_ratio > 2.0:
            volume_assessment = 'VERY_HIGH'
            volume_description = f"Khối lượng rất cao ({volume_ratio:.1f}x bình thường)"
        elif volume_ratio > 1.5:
            volume_assessment = 'HIGH'
            volume_description = f"Khối lượng cao ({volume_ratio:.1f}x bình thường)"
        elif volume_ratio > 0.7:
            volume_assessment = 'NORMAL'
            volume_description = f"Khối lượng bình thường ({volume_ratio:.1f}x)"
        else:
            volume_assessment = 'LOW'
            volume_description = f"Khối lượng thấp ({volume_ratio:.1f}x bình thường)"
        
        return {
            'current_volume': current_volume,
            'average_volume': recent_avg_volume,
            'volume_ratio': volume_ratio,
            'volume_trend': volume_trend,
            'volume_assessment': volume_assessment,
            'volume_description': volume_description,
            'volume_spikes': volume_spikes[-5:],  # Recent 5 spikes
            'spike_count': len(volume_spikes)
        }
    
    def analyze_price_volume_relationship(self, prices: List[float], volumes: List[float]) -> Dict:
        """Analyze the relationship between price and volume movements."""
        if len(prices) != len(volumes) or len(prices) < 10:
            return {'error': 'Dữ liệu không đủ để phân tích price-volume relationship'}
        
        prices_array = np.array(prices)
        volumes_array = np.array(volumes)
        
        # Calculate price changes
        price_changes = np.diff(prices_array)
        volume_changes = volumes_array[1:]  # Volume for each price change
        
        # Categorize price movements
        up_days = price_changes > 0
        down_days = price_changes < 0
        
        # Volume on up vs down days
        volume_on_up = volume_changes[up_days]
        volume_on_down = volume_changes[down_days]
        
        avg_volume_up = np.mean(volume_on_up) if len(volume_on_up) > 0 else 0
        avg_volume_down = np.mean(volume_on_down) if len(volume_on_down) > 0 else 0
        
        # Volume ratio analysis
        if avg_volume_down > 0:
            volume_ratio_up_down = avg_volume_up / avg_volume_down
        else:
            volume_ratio_up_down = float('inf') if avg_volume_up > 0 else 1.0
        
        # Price-Volume correlation
        correlation = np.corrcoef(np.abs(price_changes), volume_changes)[0, 1] if len(price_changes) > 1 else 0
        
        # Recent trend analysis (last 10 periods)
        recent_periods = min(10, len(price_changes))
        recent_price_changes = price_changes[-recent_periods:]
        recent_volumes = volume_changes[-recent_periods:]
        
        recent_correlation = np.corrcoef(np.abs(recent_price_changes), recent_volumes)[0, 1] if recent_periods > 1 else 0
        
        # Analysis interpretation
        if volume_ratio_up_down > 1.2:
            volume_bias = 'BULLISH'
            volume_bias_description = f"Khối lượng trung bình ngày tăng cao hơn ngày giảm ({volume_ratio_up_down:.1f}x)"
        elif volume_ratio_up_down < 0.8:
            volume_bias = 'BEARISH'
            volume_bias_description = f"Khối lượng trung bình ngày giảm cao hơn ngày tăng ({1/volume_ratio_up_down:.1f}x)"
        else:
            volume_bias = 'NEUTRAL'
            volume_bias_description = "Khối lượng cân bằng giữa ngày tăng và giảm"
        
        return {
            'avg_volume_up_days': avg_volume_up,
            'avg_volume_down_days': avg_volume_down,
            'volume_ratio_up_down': volume_ratio_up_down,
            'volume_bias': volume_bias,
            'volume_bias_description': volume_bias_description,
            'price_volume_correlation': correlation,
            'recent_correlation': recent_correlation,
            'up_days_count': np.sum(up_days),
            'down_days_count': np.sum(down_days),
            'interpretation': self._interpret_pv_relationship(volume_bias, correlation, recent_correlation)
        }
    
    def _interpret_pv_relationship(self, volume_bias: str, correlation: float, recent_correlation: float) -> str:
        """Interpret price-volume relationship."""
        interpretations = []
        
        if volume_bias == 'BULLISH':
            interpretations.append("Khối lượng hỗ trợ xu hướng tăng")
        elif volume_bias == 'BEARISH':
            interpretations.append("Khối lượng hỗ trợ xu hướng giảm")
        else:
            interpretations.append("Khối lượng trung tính")
        
        if correlation > 0.5:
            interpretations.append("Correlation tích cực mạnh giữa giá và khối lượng")
        elif correlation > 0.2:
            interpretations.append("Correlation tích cực vừa phải")
        elif correlation < -0.2:
            interpretations.append("Correlation tiêu cực - Cần cảnh giác")
        else:
            interpretations.append("Correlation yếu giữa giá và khối lượng")
        
        if abs(recent_correlation - correlation) > 0.3:
            interpretations.append("Thay đổi gần đây trong mối quan hệ price-volume")
        
        return " | ".join(interpretations)
    
    def get_volume_summary(self, prices: List[float], volumes: List[float], 
                          highs: List[float] = None, lows: List[float] = None) -> Dict:
        """Get comprehensive volume analysis summary."""
        try:
            # Volume Profile analysis
            volume_profile = self.calculate_volume_profile(prices, volumes, highs, lows)
            
            # VWAP calculation
            vwap = self.calculate_vwap(prices, volumes, highs, lows)
            
            # Volume trend analysis
            volume_trend = self.analyze_volume_trend(volumes)
            
            # Price-Volume relationship
            pv_relationship = self.analyze_price_volume_relationship(prices, volumes)
            
            # Current price vs key levels
            current_price = prices[-1]
            current_vwap = vwap[-1]
            
            price_vs_vwap = 'ABOVE' if current_price > current_vwap else 'BELOW'
            vwap_distance_pct = abs(current_price - current_vwap) / current_price * 100
            
            # Position relative to Volume Profile levels
            poc_price = volume_profile.get('poc_price', current_price)
            vah_price = volume_profile.get('vah_price', current_price)
            val_price = volume_profile.get('val_price', current_price)
            
            if current_price > vah_price:
                volume_profile_position = 'ABOVE_VALUE_AREA'
            elif current_price < val_price:
                volume_profile_position = 'BELOW_VALUE_AREA'
            else:
                volume_profile_position = 'IN_VALUE_AREA'
            
            return {
                'current_price': current_price,
                'current_vwap': current_vwap,
                'price_vs_vwap': price_vs_vwap,
                'vwap_distance_pct': vwap_distance_pct,
                'volume_profile': volume_profile,
                'volume_profile_position': volume_profile_position,
                'volume_trend': volume_trend,
                'price_volume_relationship': pv_relationship,
                'key_observations': self._generate_key_observations(
                    volume_profile, volume_trend, pv_relationship, 
                    price_vs_vwap, volume_profile_position
                )
            }
            
        except Exception as e:
            return {'error': f'Lỗi trong volume analysis: {str(e)}'}
    
    def _generate_key_observations(self, volume_profile: Dict, volume_trend: Dict, 
                                 pv_relationship: Dict, price_vs_vwap: str, 
                                 vp_position: str) -> List[str]:
        """Generate key observations from volume analysis."""
        observations = []
        
        # VWAP observations
        if price_vs_vwap == 'ABOVE':
            observations.append("Giá trên VWAP - Xu hướng tích cực")
        else:
            observations.append("Giá dưới VWAP - Áp lực giảm")
        
        # Volume Profile observations
        if vp_position == 'ABOVE_VALUE_AREA':
            observations.append("Giá trên Value Area - Vùng giá cao")
        elif vp_position == 'BELOW_VALUE_AREA':
            observations.append("Giá dưới Value Area - Vùng giá thấp")
        else:
            observations.append("Giá trong Value Area - Vùng cân bằng")
        
        # Volume trend observations
        if volume_trend.get('volume_assessment') in ['HIGH', 'VERY_HIGH']:
            observations.append(volume_trend['volume_description'])
        
        # Price-Volume relationship
        if pv_relationship.get('volume_bias') != 'NEUTRAL':
            observations.append(pv_relationship['volume_bias_description'])
        
        return observations
