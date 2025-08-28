"""
Weighted Scoring System for VN Stock Advisor.
"""

import yaml
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ScoringResult:
    total_score: float
    weighted_score: float
    confidence_level: str
    component_scores: Dict[str, float]
    component_weights: Dict[str, float]
    industry_adjustment: str
    market_condition: str
    recommendation: str
    reasoning: str

class WeightedScoringSystem:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "scoring_weights.yaml"
        
        self.config = self._load_config(config_path)
        self.base_weights = self.config['base_weights']
        self.industry_adjustments = self.config['industry_adjustments']
        self.market_conditions = self.config['market_conditions']
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        return {
            'base_weights': {
                'macro_analysis': 0.25,
                'fundamental_analysis': 0.35,
                'technical_analysis': 0.25,
                'risk_analysis': 0.15
            },
            'industry_adjustments': {},
            'market_conditions': {},
        }
    
    def calculate_weights(self, industry: str, market_condition: str = "normal") -> Dict[str, float]:
        weights = self.base_weights.copy()
        
        if industry in self.industry_adjustments:
            industry_weights = self.industry_adjustments[industry]
            for component, weight in industry_weights.items():
                if component in weights:
                    weights[component] = weight
        
        if market_condition in self.market_conditions:
            market_weights = self.market_conditions[market_condition]
            for component, weight in market_weights.items():
                if component in weights:
                    weights[component] = weight
        
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def calculate_score(self, component_scores: Dict[str, float], industry: str, market_condition: str = "normal") -> ScoringResult:
        weights = self.calculate_weights(industry, market_condition)
        
        weighted_score = 0.0
        for component, score in component_scores.items():
            if component in weights:
                weighted_score += score * weights[component]
        
        total_score = np.mean(list(component_scores.values()))
        confidence_level = self._determine_confidence_level(weighted_score, component_scores)
        recommendation, reasoning = self._generate_recommendation(weighted_score, confidence_level)
        
        return ScoringResult(
            total_score=total_score,
            weighted_score=weighted_score,
            confidence_level=confidence_level,
            component_scores=component_scores,
            component_weights=weights,
            industry_adjustment=industry,
            market_condition=market_condition,
            recommendation=recommendation,
            reasoning=reasoning
        )
    
    def _determine_confidence_level(self, weighted_score: float, component_scores: Dict[str, float]) -> str:
        if weighted_score >= 8.5:
            base_confidence = "very_high"
        elif weighted_score >= 7.5:
            base_confidence = "high"
        elif weighted_score >= 6.5:
            base_confidence = "medium_high"
        elif weighted_score >= 5.5:
            base_confidence = "medium"
        elif weighted_score >= 4.5:
            base_confidence = "medium_low"
        elif weighted_score >= 3.5:
            base_confidence = "low"
        else:
            base_confidence = "very_low"
        
        scores_list = list(component_scores.values())
        score_std = np.std(scores_list)
        
        if score_std <= 1.0:
            return base_confidence
        elif score_std <= 2.0:
            if base_confidence in ["very_high", "high"]:
                return "medium_high"
            elif base_confidence in ["very_low", "low"]:
                return "medium_low"
            else:
                return base_confidence
        else:
            if base_confidence in ["very_high", "high"]:
                return "medium"
            elif base_confidence in ["very_low", "low"]:
                return "medium"
            else:
                return base_confidence
    
    def _generate_recommendation(self, weighted_score: float, confidence_level: str) -> Tuple[str, str]:
        if weighted_score >= 8.0 and confidence_level in ["very_high", "high"]:
            return "STRONG_BUY", f"Điểm số cao ({weighted_score:.1f}/10) với độ tin cậy {confidence_level}"
        elif weighted_score >= 7.0:
            return "BUY", f"Điểm số tốt ({weighted_score:.1f}/10) với độ tin cậy {confidence_level}"
        elif weighted_score >= 5.5:
            return "HOLD", f"Điểm số trung bình ({weighted_score:.1f}/10), cần theo dõi thêm"
        elif weighted_score >= 4.0:
            return "HOLD", f"Điểm số thấp ({weighted_score:.1f}/10), cân nhắc giảm vị thế"
        else:
            return "SELL", f"Điểm số rất thấp ({weighted_score:.1f}/10), khuyến nghị bán"
