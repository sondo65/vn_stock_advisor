"""
Anomaly Detection for VN Stock Advisor.

This module identifies unusual patterns, outliers, and anomalies
in stock price and volume data that may indicate significant events.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

@dataclass
class AnomalySignal:
    """Signal for detected anomaly."""
    anomaly_type: str
    timestamp_index: int
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    confidence: float
    description: str
    value: float
    expected_range: Tuple[float, float]
    recommendation: str

class AnomalyDetection:
    """
    Advanced anomaly detection using statistical and ML methods.
    """
    
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination=contamination, 
            random_state=42,
            n_estimators=100
        )
        self.pca = PCA(n_components=2)
        
    def detect_price_anomalies(self, prices: List[float], window: int = 20) -> List[AnomalySignal]:
        """Detect price anomalies using statistical methods."""
        if len(prices) < window * 2:
            return []
        
        prices_array = np.array(prices)
        anomalies = []
        
        # Calculate rolling statistics
        prices_series = pd.Series(prices_array)
        rolling_mean = prices_series.rolling(window=window).mean()
        rolling_std = prices_series.rolling(window=window).std()
        
        # Z-score based anomaly detection
        z_scores = np.abs((prices_array - rolling_mean) / rolling_std)
        
        for i, z_score in enumerate(z_scores):
            if np.isnan(z_score):
                continue
                
            if z_score > 3:  # 3-sigma rule
                severity = self._determine_severity(z_score)
                confidence = min(0.95, (z_score - 3) / 2)
                
                expected_range = (
                    rolling_mean.iloc[i] - 2 * rolling_std.iloc[i],
                    rolling_mean.iloc[i] + 2 * rolling_std.iloc[i]
                )
                
                anomalies.append(AnomalySignal(
                    anomaly_type='price_outlier',
                    timestamp_index=i,
                    severity=severity,
                    confidence=confidence,
                    description=f"Giá {prices_array[i]:.0f} bất thường so với kỳ vọng",
                    value=prices_array[i],
                    expected_range=expected_range,
                    recommendation=self._get_price_anomaly_recommendation(
                        prices_array[i], rolling_mean.iloc[i], severity
                    )
                ))
        
        return anomalies
    
    def detect_volume_anomalies(self, volumes: List[float], window: int = 20) -> List[AnomalySignal]:
        """Detect volume anomalies."""
        if len(volumes) < window * 2:
            return []
        
        volumes_array = np.array(volumes)
        anomalies = []
        
        # Log transform volumes to handle skewness
        log_volumes = np.log1p(volumes_array)
        volumes_series = pd.Series(log_volumes)
        
        rolling_mean = volumes_series.rolling(window=window).mean()
        rolling_std = volumes_series.rolling(window=window).std()
        
        # Detect volume spikes
        z_scores = (log_volumes - rolling_mean) / rolling_std
        
        for i, z_score in enumerate(z_scores):
            if np.isnan(z_score):
                continue
                
            if z_score > 2.5:  # Volume spike
                severity = self._determine_volume_severity(z_score)
                confidence = min(0.9, (z_score - 2.5) / 2)
                
                expected_volume = np.expm1(rolling_mean.iloc[i])
                actual_volume = volumes_array[i]
                
                anomalies.append(AnomalySignal(
                    anomaly_type='volume_spike',
                    timestamp_index=i,
                    severity=severity,
                    confidence=confidence,
                    description=f"Khối lượng {actual_volume:,.0f} bất thường cao",
                    value=actual_volume,
                    expected_range=(0, expected_volume * 2),
                    recommendation=self._get_volume_anomaly_recommendation(severity)
                ))
        
        return anomalies
    
    def detect_price_volume_divergence(self, prices: List[float], volumes: List[float]) -> List[AnomalySignal]:
        """Detect price-volume divergence anomalies."""
        if len(prices) != len(volumes) or len(prices) < 20:
            return []
        
        prices_array = np.array(prices)
        volumes_array = np.array(volumes)
        anomalies = []
        
        # Calculate price and volume changes
        price_changes = np.diff(prices_array) / prices_array[:-1]
        volume_changes = np.diff(volumes_array) / volumes_array[:-1]
        
        # Calculate correlation in rolling windows
        window = 10
        for i in range(window, len(price_changes)):
            price_window = price_changes[i-window:i]
            volume_window = volume_changes[i-window:i]
            
            # Calculate correlation
            correlation = np.corrcoef(price_window, volume_window)[0, 1]
            
            if np.isnan(correlation):
                continue
            
            # Detect negative correlation (divergence)
            if correlation < -0.5:
                confidence = abs(correlation)
                severity = self._determine_divergence_severity(correlation)
                
                anomalies.append(AnomalySignal(
                    anomaly_type='price_volume_divergence',
                    timestamp_index=i,
                    severity=severity,
                    confidence=confidence,
                    description=f"Phân kỳ giá-khối lượng (correlation: {correlation:.2f})",
                    value=correlation,
                    expected_range=(0.2, 0.8),
                    recommendation=self._get_divergence_recommendation(correlation)
                ))
        
        return anomalies
    
    def detect_ml_anomalies(self, prices: List[float], volumes: List[float]) -> List[AnomalySignal]:
        """Detect anomalies using machine learning (Isolation Forest)."""
        if len(prices) < 50 or len(volumes) < 50:
            return []
        
        # Prepare features
        features = self._prepare_features(prices, volumes)
        
        if features.shape[0] < 10:
            return []
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Detect anomalies
        anomaly_scores = self.isolation_forest.fit_predict(features_scaled)
        anomaly_probabilities = self.isolation_forest.score_samples(features_scaled)
        
        anomalies = []
        for i, (score, prob) in enumerate(zip(anomaly_scores, anomaly_probabilities)):
            if score == -1:  # Anomaly detected
                confidence = abs(prob)
                severity = self._determine_ml_severity(prob)
                
                anomalies.append(AnomalySignal(
                    anomaly_type='ml_anomaly',
                    timestamp_index=i,
                    severity=severity,
                    confidence=confidence,
                    description="Bất thường được phát hiện bởi mô hình ML",
                    value=prob,
                    expected_range=(-0.1, 0.1),
                    recommendation=self._get_ml_anomaly_recommendation(severity)
                ))
        
        return anomalies
    
    def _prepare_features(self, prices: List[float], volumes: List[float]) -> np.ndarray:
        """Prepare features for ML anomaly detection."""
        prices_array = np.array(prices)
        volumes_array = np.array(volumes)
        
        # Calculate technical indicators
        returns = np.diff(prices_array) / prices_array[:-1]
        volume_changes = np.diff(volumes_array) / volumes_array[:-1]
        
        # Rolling statistics
        window = 5
        price_series = pd.Series(prices_array)
        volume_series = pd.Series(volumes_array)
        
        price_ma = price_series.rolling(window=window).mean().iloc[window:]
        price_std = price_series.rolling(window=window).std().iloc[window:]
        volume_ma = volume_series.rolling(window=window).mean().iloc[window:]
        
        # Ensure all arrays have the same length
        min_length = min(len(returns), len(volume_changes), len(price_ma), len(price_std), len(volume_ma))
        
        features = np.column_stack([
            returns[:min_length],
            volume_changes[:min_length],
            (prices_array[1:min_length+1] - price_ma[:min_length]) / price_std[:min_length],
            volumes_array[1:min_length+1] / volume_ma[:min_length]
        ])
        
        # Remove any rows with NaN values
        features = features[~np.isnan(features).any(axis=1)]
        
        return features
    
    def _determine_severity(self, z_score: float) -> str:
        """Determine severity based on z-score."""
        if z_score > 5:
            return 'CRITICAL'
        elif z_score > 4:
            return 'HIGH'
        elif z_score > 3.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _determine_volume_severity(self, z_score: float) -> str:
        """Determine volume anomaly severity."""
        if z_score > 4:
            return 'CRITICAL'
        elif z_score > 3.5:
            return 'HIGH'
        elif z_score > 3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _determine_divergence_severity(self, correlation: float) -> str:
        """Determine divergence severity."""
        if correlation < -0.8:
            return 'CRITICAL'
        elif correlation < -0.7:
            return 'HIGH'
        elif correlation < -0.6:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _determine_ml_severity(self, anomaly_score: float) -> str:
        """Determine ML anomaly severity."""
        if anomaly_score < -0.3:
            return 'CRITICAL'
        elif anomaly_score < -0.2:
            return 'HIGH'
        elif anomaly_score < -0.1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_price_anomaly_recommendation(self, actual_price: float, expected_price: float, severity: str) -> str:
        """Get recommendation for price anomaly."""
        if actual_price > expected_price:
            if severity in ['CRITICAL', 'HIGH']:
                return "Giá tăng bất thường mạnh - Cân nhắc chốt lời hoặc chờ điều chỉnh"
            else:
                return "Giá tăng vượt kỳ vọng - Theo dõi để xác nhận xu hướng"
        else:
            if severity in ['CRITICAL', 'HIGH']:
                return "Giá giảm bất thường mạnh - Cơ hội mua hoặc cắt lỗ nếu đang nắm giữ"
            else:
                return "Giá giảm dưới kỳ vọng - Theo dõi hỗ trợ"
    
    def _get_volume_anomaly_recommendation(self, severity: str) -> str:
        """Get recommendation for volume anomaly."""
        if severity in ['CRITICAL', 'HIGH']:
            return "Khối lượng giao dịch bất thường cao - Có thể có tin tức quan trọng hoặc thao túng"
        else:
            return "Khối lượng giao dịch tăng - Quan sát thêm để xác nhận tín hiệu"
    
    def _get_divergence_recommendation(self, correlation: float) -> str:
        """Get recommendation for price-volume divergence."""
        return "Phân kỳ giá-khối lượng - Có thể báo hiệu đảo chiều xu hướng"
    
    def _get_ml_anomaly_recommendation(self, severity: str) -> str:
        """Get recommendation for ML-detected anomaly."""
        if severity in ['CRITICAL', 'HIGH']:
            return "Mô hình ML phát hiện bất thường nghiêm trọng - Cần điều tra nguyên nhân"
        else:
            return "Mô hình ML phát hiện bất thường nhẹ - Theo dõi thêm"
    
    def comprehensive_anomaly_analysis(self, prices: List[float], volumes: List[float]) -> Dict:
        """Comprehensive anomaly analysis."""
        all_anomalies = []
        
        # Detect different types of anomalies
        price_anomalies = self.detect_price_anomalies(prices)
        volume_anomalies = self.detect_volume_anomalies(volumes)
        divergence_anomalies = self.detect_price_volume_divergence(prices, volumes)
        ml_anomalies = self.detect_ml_anomalies(prices, volumes)
        
        all_anomalies.extend(price_anomalies)
        all_anomalies.extend(volume_anomalies)
        all_anomalies.extend(divergence_anomalies)
        all_anomalies.extend(ml_anomalies)
        
        # Sort by severity and confidence
        severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        all_anomalies.sort(
            key=lambda x: (severity_order[x.severity], x.confidence), 
            reverse=True
        )
        
        # Generate summary
        critical_count = len([a for a in all_anomalies if a.severity == 'CRITICAL'])
        high_count = len([a for a in all_anomalies if a.severity == 'HIGH'])
        
        if critical_count > 0:
            risk_level = 'CRITICAL'
            summary = f"Phát hiện {critical_count} bất thường nghiêm trọng - Cần hành động ngay"
        elif high_count > 0:
            risk_level = 'HIGH'
            summary = f"Phát hiện {high_count} bất thường mức cao - Cần theo dõi chặt chẽ"
        elif len(all_anomalies) > 0:
            risk_level = 'MEDIUM'
            summary = f"Phát hiện {len(all_anomalies)} bất thường - Theo dõi thường xuyên"
        else:
            risk_level = 'LOW'
            summary = "Không phát hiện bất thường đáng kể"
        
        return {
            'total_anomalies': len(all_anomalies),
            'critical_anomalies': critical_count,
            'high_anomalies': high_count,
            'risk_level': risk_level,
            'summary': summary,
            'anomalies': [
                {
                    'type': a.anomaly_type,
                    'severity': a.severity,
                    'confidence': a.confidence,
                    'description': a.description,
                    'recommendation': a.recommendation,
                    'timestamp_index': a.timestamp_index
                }
                for a in all_anomalies[:10]  # Top 10 anomalies
            ]
        }
