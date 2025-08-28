"""
Confidence Calculator for VN Stock Advisor.

This module calculates confidence levels based on various factors including:
- Data quality and freshness
- Market volatility
- Analysis consistency
- Historical accuracy
"""

import yaml
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConfidenceFactors:
    data_quality: float = 1.0
    data_freshness: float = 1.0
    market_volatility: float = 1.0
    analysis_consistency: float = 1.0
    historical_accuracy: float = 1.0

class ConfidenceCalculator:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "confidence_thresholds.yaml"
        
        self.config = self._load_config(config_path)
        self.confidence_levels = self.config['confidence_levels']
        self.confidence_factors = self.config['confidence_factors']
        self.confidence_weights = self.config['confidence_weights']
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        return {
            'confidence_levels': {
                'very_high': {'min_threshold': 0.90, 'description': 'Rất cao'},
                'high': {'min_threshold': 0.80, 'description': 'Cao'},
                'medium': {'min_threshold': 0.60, 'description': 'Trung bình'},
                'low': {'min_threshold': 0.40, 'description': 'Thấp'},
                'very_low': {'min_threshold': 0.20, 'description': 'Rất thấp'}
            },
            'confidence_factors': {},
            'confidence_weights': {}
        }
    
    def calculate_confidence(self, 
                           base_score: float,
                           factors: ConfidenceFactors,
                           component_scores: Dict[str, float]) -> Dict:
        """
        Calculate confidence level based on base score and various factors.
        
        Args:
            base_score: Base confidence score (0-1)
            factors: ConfidenceFactors object
            component_scores: Dictionary of component scores
            
        Returns:
            Dictionary with confidence details
        """
        # Calculate factor adjustments
        factor_adjustment = self._calculate_factor_adjustment(factors)
        
        # Calculate consistency adjustment
        consistency_adjustment = self._calculate_consistency_adjustment(component_scores)
        
        # Calculate final confidence
        final_confidence = base_score + factor_adjustment + consistency_adjustment
        final_confidence = np.clip(final_confidence, 0.0, 1.0)
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(final_confidence)
        
        return {
            'confidence_score': final_confidence,
            'confidence_level': confidence_level,
            'base_score': base_score,
            'factor_adjustment': factor_adjustment,
            'consistency_adjustment': consistency_adjustment,
            'description': self.confidence_levels[confidence_level]['description'],
            'action': self.confidence_levels[confidence_level].get('action', 'Không xác định')
        }
    
    def _calculate_factor_adjustment(self, factors: ConfidenceFactors) -> float:
        """Calculate adjustment based on confidence factors."""
        adjustment = 0.0
        
        # Data quality adjustment
        if factors.data_quality >= 0.9:
            adjustment += 0.1
        elif factors.data_quality >= 0.8:
            adjustment += 0.05
        elif factors.data_quality <= 0.6:
            adjustment -= 0.1
        
        # Data freshness adjustment
        if factors.data_freshness >= 0.95:
            adjustment += 0.05
        elif factors.data_freshness <= 0.8:
            adjustment -= 0.05
        
        # Market volatility adjustment
        if factors.market_volatility <= 0.8:
            adjustment += 0.05
        elif factors.market_volatility >= 0.9:
            adjustment -= 0.05
        
        # Historical accuracy adjustment
        if factors.historical_accuracy >= 0.8:
            adjustment += 0.1
        elif factors.historical_accuracy <= 0.6:
            adjustment -= 0.1
        
        return adjustment
    
    def _calculate_consistency_adjustment(self, component_scores: Dict[str, float]) -> float:
        """Calculate adjustment based on consistency of component scores."""
        if not component_scores:
            return 0.0
        
        scores = list(component_scores.values())
        score_std = np.std(scores)
        score_mean = np.mean(scores)
        
        # High consistency (low std) increases confidence
        if score_std <= 1.0:
            return 0.1
        elif score_std <= 2.0:
            return 0.05
        elif score_std >= 3.0:
            return -0.1
        else:
            return 0.0
    
    def _determine_confidence_level(self, confidence_score: float) -> str:
        """Determine confidence level based on score."""
        for level, config in self.confidence_levels.items():
            if confidence_score >= config['min_threshold']:
                return level
        return 'very_low'
    
    def get_confidence_description(self, confidence_level: str) -> str:
        """Get human-readable description of confidence level."""
        return self.confidence_levels.get(confidence_level, {}).get('description', 'Không xác định')
