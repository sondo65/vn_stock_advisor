"""
Data Validator - Phase 3

Validates and ensures data quality for financial data from multiple sources.
Implements data consistency checks, outlier detection, and data completeness validation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json

class ValidationLevel(Enum):
    """Data validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Data validation result."""
    field: str
    level: ValidationLevel
    message: str
    value: Any
    expected_range: Optional[Tuple[float, float]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class DataQualityReport:
    """Comprehensive data quality report."""
    symbol: str
    timestamp: datetime
    total_checks: int
    passed_checks: int
    warnings: int
    errors: int
    critical_issues: int
    quality_score: float
    validation_results: List[ValidationResult]
    recommendations: List[str]

class DataValidator:
    """Validates financial data quality and consistency."""
    
    def __init__(self):
        """Initialize data validator."""
        self.logger = logging.getLogger(__name__)
        
        # Define validation rules
        self.price_rules = {
            'min_price': 0.1,
            'max_price': 1000000,  # 1M VND
            'max_change_percent': 7.0,  # Daily limit in Vietnam
            'min_volume': 0,
            'max_volume': 1000000000  # 1B shares
        }
        
        self.ratio_rules = {
            'PE': {'min': -100, 'max': 500, 'typical_range': (5, 50)},
            'PB': {'min': 0, 'max': 50, 'typical_range': (0.5, 5)},
            'ROE': {'min': -100, 'max': 200, 'typical_range': (5, 30)},
            'ROA': {'min': -50, 'max': 100, 'typical_range': (1, 20)},
            'debt_to_equity': {'min': 0, 'max': 20, 'typical_range': (0, 3)},
            'current_ratio': {'min': 0, 'max': 20, 'typical_range': (1, 3)},
            'quick_ratio': {'min': 0, 'max': 10, 'typical_range': (0.5, 2)}
        }
        
        # Industry-specific validation rules
        self.industry_rules = {
            'banking': {
                'PE': (3, 15),
                'PB': (0.5, 3),
                'ROE': (8, 25),
                'NPL_ratio': (0, 5)
            },
            'real_estate': {
                'PE': (5, 30),
                'PB': (0.8, 4),
                'inventory_turnover': (0.1, 2)
            },
            'technology': {
                'PE': (10, 100),
                'PB': (1, 20),
                'revenue_growth': (0, 200)
            }
        }
    
    def validate_price_data(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate price and trading data.
        
        Args:
            data: Dictionary containing price data
            
        Returns:
            List of validation results
        """
        results = []
        
        try:
            # Validate price
            price = data.get('price', 0)
            if price < self.price_rules['min_price']:
                results.append(ValidationResult(
                    field='price',
                    level=ValidationLevel.ERROR,
                    message=f"Price {price} below minimum threshold",
                    value=price,
                    expected_range=(self.price_rules['min_price'], self.price_rules['max_price'])
                ))
            elif price > self.price_rules['max_price']:
                results.append(ValidationResult(
                    field='price',
                    level=ValidationLevel.WARNING,
                    message=f"Price {price} unusually high",
                    value=price,
                    expected_range=(self.price_rules['min_price'], self.price_rules['max_price'])
                ))
            
            # Validate price change
            change_percent = data.get('change_percent', 0)
            if abs(change_percent) > self.price_rules['max_change_percent']:
                results.append(ValidationResult(
                    field='change_percent',
                    level=ValidationLevel.CRITICAL,
                    message=f"Price change {change_percent}% exceeds daily limit",
                    value=change_percent,
                    expected_range=(-self.price_rules['max_change_percent'], self.price_rules['max_change_percent'])
                ))
            
            # Validate volume
            volume = data.get('volume', 0)
            if volume < 0:
                results.append(ValidationResult(
                    field='volume',
                    level=ValidationLevel.ERROR,
                    message="Volume cannot be negative",
                    value=volume
                ))
            elif volume > self.price_rules['max_volume']:
                results.append(ValidationResult(
                    field='volume',
                    level=ValidationLevel.WARNING,
                    message=f"Volume {volume} unusually high",
                    value=volume
                ))
            
            # Validate OHLC consistency
            open_price = data.get('open', 0)
            high = data.get('high', 0)
            low = data.get('low', 0)
            close = data.get('close', price)
            
            if high < low:
                results.append(ValidationResult(
                    field='ohlc',
                    level=ValidationLevel.ERROR,
                    message="High price cannot be less than low price",
                    value={'high': high, 'low': low}
                ))
            
            if close > high or close < low:
                results.append(ValidationResult(
                    field='ohlc',
                    level=ValidationLevel.ERROR,
                    message="Close price outside high-low range",
                    value={'close': close, 'high': high, 'low': low}
                ))
            
            if open_price > high or open_price < low:
                results.append(ValidationResult(
                    field='ohlc',
                    level=ValidationLevel.ERROR,
                    message="Open price outside high-low range",
                    value={'open': open_price, 'high': high, 'low': low}
                ))
            
        except Exception as e:
            results.append(ValidationResult(
                field='price_data',
                level=ValidationLevel.ERROR,
                message=f"Error validating price data: {str(e)}",
                value=str(e)
            ))
        
        return results
    
    def validate_financial_ratios(self, ratios: Dict[str, float], industry: str = None) -> List[ValidationResult]:
        """
        Validate financial ratios.
        
        Args:
            ratios: Dictionary of financial ratios
            industry: Industry classification for context-specific validation
            
        Returns:
            List of validation results
        """
        results = []
        
        try:
            for ratio_name, value in ratios.items():
                if ratio_name in self.ratio_rules:
                    rule = self.ratio_rules[ratio_name]
                    
                    # Check absolute bounds
                    if value < rule['min'] or value > rule['max']:
                        results.append(ValidationResult(
                            field=ratio_name,
                            level=ValidationLevel.ERROR,
                            message=f"{ratio_name} {value} outside valid range",
                            value=value,
                            expected_range=(rule['min'], rule['max'])
                        ))
                        continue
                    
                    # Check typical range
                    typical_min, typical_max = rule['typical_range']
                    if value < typical_min or value > typical_max:
                        results.append(ValidationResult(
                            field=ratio_name,
                            level=ValidationLevel.WARNING,
                            message=f"{ratio_name} {value} outside typical range",
                            value=value,
                            expected_range=(typical_min, typical_max)
                        ))
                    
                    # Industry-specific validation
                    if industry and industry in self.industry_rules:
                        industry_rule = self.industry_rules[industry]
                        if ratio_name in industry_rule:
                            ind_min, ind_max = industry_rule[ratio_name]
                            if value < ind_min or value > ind_max:
                                results.append(ValidationResult(
                                    field=f"{ratio_name}_industry",
                                    level=ValidationLevel.INFO,
                                    message=f"{ratio_name} {value} outside industry range for {industry}",
                                    value=value,
                                    expected_range=(ind_min, ind_max)
                                ))
            
            # Cross-ratio validation
            results.extend(self._validate_ratio_relationships(ratios))
            
        except Exception as e:
            results.append(ValidationResult(
                field='financial_ratios',
                level=ValidationLevel.ERROR,
                message=f"Error validating financial ratios: {str(e)}",
                value=str(e)
            ))
        
        return results
    
    def validate_time_series_data(self, data: pd.DataFrame) -> List[ValidationResult]:
        """
        Validate time series data for consistency and completeness.
        
        Args:
            data: Time series DataFrame
            
        Returns:
            List of validation results
        """
        results = []
        
        try:
            if data.empty:
                results.append(ValidationResult(
                    field='time_series',
                    level=ValidationLevel.ERROR,
                    message="Time series data is empty",
                    value=len(data)
                ))
                return results
            
            # Check for missing values
            missing_pct = (data.isnull().sum() / len(data) * 100)
            for column, pct in missing_pct.items():
                if pct > 50:
                    results.append(ValidationResult(
                        field=f'missing_data_{column}',
                        level=ValidationLevel.ERROR,
                        message=f"Column {column} has {pct:.1f}% missing values",
                        value=pct
                    ))
                elif pct > 10:
                    results.append(ValidationResult(
                        field=f'missing_data_{column}',
                        level=ValidationLevel.WARNING,
                        message=f"Column {column} has {pct:.1f}% missing values",
                        value=pct
                    ))
            
            # Check for data gaps
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                date_diff = data['date'].diff().dt.days
                large_gaps = date_diff[date_diff > 7]  # More than 1 week gap
                
                if len(large_gaps) > 0:
                    results.append(ValidationResult(
                        field='time_gaps',
                        level=ValidationLevel.WARNING,
                        message=f"Found {len(large_gaps)} time gaps larger than 7 days",
                        value=len(large_gaps)
                    ))
            
            # Check for outliers in numeric columns
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            for column in numeric_columns:
                if column in data.columns:
                    outliers = self._detect_outliers(data[column])
                    if len(outliers) > len(data) * 0.1:  # More than 10% outliers
                        results.append(ValidationResult(
                            field=f'outliers_{column}',
                            level=ValidationLevel.WARNING,
                            message=f"Column {column} has {len(outliers)} potential outliers",
                            value=len(outliers)
                        ))
            
        except Exception as e:
            results.append(ValidationResult(
                field='time_series',
                level=ValidationLevel.ERROR,
                message=f"Error validating time series data: {str(e)}",
                value=str(e)
            ))
        
        return results
    
    def validate_data_consistency(self, data_sources: Dict[str, Dict[str, Any]]) -> List[ValidationResult]:
        """
        Validate consistency across multiple data sources.
        
        Args:
            data_sources: Dictionary of data from different sources
            
        Returns:
            List of validation results
        """
        results = []
        
        try:
            if len(data_sources) < 2:
                return results
            
            # Compare prices across sources
            prices = {}
            for source, data in data_sources.items():
                if 'price' in data:
                    prices[source] = data['price']
            
            if len(prices) > 1:
                price_values = list(prices.values())
                price_std = np.std(price_values)
                price_mean = np.mean(price_values)
                
                # Check for significant price discrepancies
                if price_std / price_mean > 0.05:  # More than 5% coefficient of variation
                    results.append(ValidationResult(
                        field='price_consistency',
                        level=ValidationLevel.WARNING,
                        message=f"Price discrepancy across sources: {prices}",
                        value=prices
                    ))
            
            # Compare volumes
            volumes = {}
            for source, data in data_sources.items():
                if 'volume' in data:
                    volumes[source] = data['volume']
            
            if len(volumes) > 1:
                volume_values = list(volumes.values())
                if max(volume_values) > 0:
                    volume_ratio = max(volume_values) / min([v for v in volume_values if v > 0])
                    
                    if volume_ratio > 2:  # More than 2x difference
                        results.append(ValidationResult(
                            field='volume_consistency',
                            level=ValidationLevel.WARNING,
                            message=f"Volume discrepancy across sources: {volumes}",
                            value=volumes
                        ))
            
        except Exception as e:
            results.append(ValidationResult(
                field='data_consistency',
                level=ValidationLevel.ERROR,
                message=f"Error validating data consistency: {str(e)}",
                value=str(e)
            ))
        
        return results
    
    def generate_quality_report(self, symbol: str, all_results: List[ValidationResult]) -> DataQualityReport:
        """
        Generate comprehensive data quality report.
        
        Args:
            symbol: Stock symbol
            all_results: All validation results
            
        Returns:
            DataQualityReport object
        """
        total_checks = len(all_results)
        errors = len([r for r in all_results if r.level == ValidationLevel.ERROR])
        warnings = len([r for r in all_results if r.level == ValidationLevel.WARNING])
        critical_issues = len([r for r in all_results if r.level == ValidationLevel.CRITICAL])
        passed_checks = total_checks - errors - warnings - critical_issues
        
        # Calculate quality score (0-100)
        if total_checks == 0:
            quality_score = 100.0
        else:
            score = (passed_checks * 1.0 + warnings * 0.7 + errors * 0.3 + critical_issues * 0.0) / total_checks * 100
            quality_score = max(0, min(100, score))
        
        # Generate recommendations
        recommendations = []
        if critical_issues > 0:
            recommendations.append("Address critical data issues immediately")
        if errors > 0:
            recommendations.append("Fix data errors before using for analysis")
        if warnings > total_checks * 0.2:
            recommendations.append("Review data sources for consistency")
        if quality_score < 80:
            recommendations.append("Consider using alternative data sources")
        
        return DataQualityReport(
            symbol=symbol,
            timestamp=datetime.now(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            warnings=warnings,
            errors=errors,
            critical_issues=critical_issues,
            quality_score=quality_score,
            validation_results=all_results,
            recommendations=recommendations
        )
    
    def _validate_ratio_relationships(self, ratios: Dict[str, float]) -> List[ValidationResult]:
        """Validate relationships between financial ratios."""
        results = []
        
        try:
            # ROE = ROA * Equity Multiplier
            if all(k in ratios for k in ['ROE', 'ROA', 'debt_to_equity']):
                roe = ratios['ROE']
                roa = ratios['ROA']
                de_ratio = ratios['debt_to_equity']
                
                equity_multiplier = 1 + de_ratio
                expected_roe = roa * equity_multiplier
                
                if abs(roe - expected_roe) > 2:  # Allow 2% tolerance
                    results.append(ValidationResult(
                        field='roe_roa_relationship',
                        level=ValidationLevel.WARNING,
                        message=f"ROE-ROA relationship inconsistent: ROE={roe}, expected={expected_roe:.2f}",
                        value={'ROE': roe, 'expected_ROE': expected_roe}
                    ))
            
            # PB = PE * ROE (approximately)
            if all(k in ratios for k in ['PE', 'PB', 'ROE']):
                pe = ratios['PE']
                pb = ratios['PB']
                roe = ratios['ROE'] / 100  # Convert percentage to decimal
                
                expected_pb = pe * roe
                
                if abs(pb - expected_pb) > pb * 0.3:  # Allow 30% tolerance
                    results.append(ValidationResult(
                        field='pe_pb_roe_relationship',
                        level=ValidationLevel.INFO,
                        message=f"PE-PB-ROE relationship check: PB={pb}, expected={expected_pb:.2f}",
                        value={'PB': pb, 'expected_PB': expected_pb}
                    ))
            
        except Exception as e:
            results.append(ValidationResult(
                field='ratio_relationships',
                level=ValidationLevel.ERROR,
                message=f"Error validating ratio relationships: {str(e)}",
                value=str(e)
            ))
        
        return results
    
    def _detect_outliers(self, series: pd.Series) -> List[int]:
        """Detect outliers using IQR method."""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = series[(series < lower_bound) | (series > upper_bound)].index.tolist()
            return outliers
            
        except Exception:
            return []

# Example usage
def test_data_validator():
    """Test the data validator."""
    validator = DataValidator()
    
    # Test price data validation
    price_data = {
        'price': 25000,
        'change_percent': 3.5,
        'volume': 1000000,
        'open': 24500,
        'high': 25200,
        'low': 24300,
        'close': 25000
    }
    
    price_results = validator.validate_price_data(price_data)
    print(f"Price validation: {len(price_results)} issues found")
    
    # Test financial ratios validation
    ratios = {
        'PE': 15.3,
        'PB': 1.7,
        'ROE': 11.7,
        'ROA': 5.2,
        'debt_to_equity': 0.7
    }
    
    ratio_results = validator.validate_financial_ratios(ratios, industry='steel')
    print(f"Ratio validation: {len(ratio_results)} issues found")
    
    # Generate quality report
    all_results = price_results + ratio_results
    report = validator.generate_quality_report('HPG', all_results)
    print(f"Quality Score: {report.quality_score:.1f}/100")
    print(f"Recommendations: {report.recommendations}")

if __name__ == "__main__":
    test_data_validator()
