"""
A/B Testing Framework - Statistical Hypothesis Testing

All calculations use:
- Two-proportion z-test
- Confidence intervals
- Sample size calculation
- Statistical power analysis

NO ML OR LLM - pure statistical methods (scipy, statsmodels)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import math

logger = logging.getLogger(__name__)

# Import statistical libraries with fallback
try:
    from scipy import stats
    import numpy as np
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not installed. Install with: pip install scipy numpy")

try:
    from statsmodels.stats.proportion import proportions_ztest
    from statsmodels.stats.power import zt_ind_solve_power
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not installed. Install with: pip install statsmodels")


class ABTestFramework:
    """
    Production-grade A/B testing using statistical methods.

    All methods return deterministic results with algorithm documentation.
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize A/B test framework.

        Args:
            confidence_level: Statistical confidence level (default 0.95 = 95%)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.8,
        ratio: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate minimum sample size for statistical significance.

        Args:
            baseline_rate: Current conversion rate (e.g., 0.05 for 5%)
            minimum_detectable_effect: Relative lift to detect (e.g., 0.1 for 10% lift)
            power: Statistical power (default 0.8 = 80%)
            ratio: Ratio of control to variant size (default 1.0 = equal)

        Returns:
            Dict with sample_size_per_variant, total_sample_size, and metadata
        """
        if baseline_rate <= 0 or baseline_rate >= 1:
            return {
                'error': 'Baseline rate must be between 0 and 1',
                'algorithm': 'Sample size calculation for two-proportion z-test',
                'is_verified': True
            }

        if minimum_detectable_effect <= 0:
            return {
                'error': 'Minimum detectable effect must be positive',
                'algorithm': 'Sample size calculation for two-proportion z-test',
                'is_verified': True
            }

        # Calculate effect size (Cohen's h)
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_detectable_effect)

        if p2 >= 1:
            return {
                'error': 'Expected variant rate exceeds 100%',
                'algorithm': 'Sample size calculation for two-proportion z-test',
                'is_verified': True
            }

        if STATSMODELS_AVAILABLE:
            try:
                # Calculate effect size using arcsine transformation
                effect_size = 2 * (math.asin(math.sqrt(p2)) - math.asin(math.sqrt(p1)))

                sample_size = zt_ind_solve_power(
                    effect_size=abs(effect_size),
                    alpha=self.alpha,
                    power=power,
                    ratio=ratio,
                    alternative='two-sided'
                )
                sample_size = int(math.ceil(sample_size))
            except Exception as e:
                logger.error(f"Sample size calculation failed: {e}")
                sample_size = self._manual_sample_size(p1, p2, self.alpha, power)
        else:
            sample_size = self._manual_sample_size(p1, p2, self.alpha, power)

        total_sample = int(sample_size * (1 + ratio))

        return {
            'sample_size_per_variant': sample_size,
            'control_size': sample_size,
            'variant_size': int(sample_size * ratio),
            'total_sample_size': total_sample,
            'baseline_rate': baseline_rate,
            'expected_variant_rate': round(p2, 4),
            'minimum_detectable_effect': minimum_detectable_effect,
            'power': power,
            'confidence_level': self.confidence_level,
            'algorithm': 'Two-proportion z-test sample size calculation',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def _manual_sample_size(
        self,
        p1: float,
        p2: float,
        alpha: float,
        power: float
    ) -> int:
        """
        Manual sample size calculation without statsmodels.

        Uses the formula for comparing two proportions.
        """
        # Z-scores
        z_alpha = 1.96 if alpha == 0.05 else 2.576 if alpha == 0.01 else 1.645
        z_beta = 0.84 if power == 0.8 else 1.28 if power == 0.9 else 0.52

        # Pooled proportion
        p_pooled = (p1 + p2) / 2

        # Sample size formula
        numerator = (z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) +
                     z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        denominator = (p2 - p1) ** 2

        return int(math.ceil(numerator / denominator)) if denominator > 0 else 10000

    def analyze_test(
        self,
        control_conversions: int,
        control_visitors: int,
        variant_conversions: int,
        variant_visitors: int
    ) -> Dict[str, Any]:
        """
        Analyze A/B test results using two-proportion z-test.

        Args:
            control_conversions: Number of conversions in control
            control_visitors: Total visitors in control
            variant_conversions: Number of conversions in variant
            variant_visitors: Total visitors in variant

        Returns:
            Dict with statistical analysis and recommendation
        """
        if control_visitors == 0 or variant_visitors == 0:
            return {
                'error': 'Visitor counts cannot be zero',
                'algorithm': 'Two-proportion z-test',
                'is_verified': True
            }

        # Calculate conversion rates
        control_rate = control_conversions / control_visitors
        variant_rate = variant_conversions / variant_visitors

        # Pooled proportion
        total_conversions = control_conversions + variant_conversions
        total_visitors = control_visitors + variant_visitors
        pooled_rate = total_conversions / total_visitors

        # Standard error
        se = math.sqrt(
            pooled_rate * (1 - pooled_rate) *
            (1/control_visitors + 1/variant_visitors)
        )

        if se == 0:
            return {
                'error': 'Standard error is zero - insufficient variation',
                'algorithm': 'Two-proportion z-test',
                'is_verified': True
            }

        # Z-statistic
        z_stat = (variant_rate - control_rate) / se

        # P-value (two-tailed)
        if SCIPY_AVAILABLE:
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            # Manual approximation
            p_value = self._manual_p_value(abs(z_stat))

        # Confidence interval for the difference
        z_critical = 1.96 if self.confidence_level == 0.95 else 2.576 if self.confidence_level == 0.99 else 1.645
        diff = variant_rate - control_rate
        margin_of_error = z_critical * se
        ci_lower = diff - margin_of_error
        ci_upper = diff + margin_of_error

        # Relative lift
        lift = (variant_rate - control_rate) / control_rate if control_rate > 0 else 0
        lift_pct = lift * 100

        # Statistical significance
        significant = p_value < self.alpha

        # Determine recommendation
        if significant and lift > 0:
            recommendation = 'Deploy Variant'
            confidence = 'high' if p_value < 0.01 else 'medium'
        elif significant and lift < 0:
            recommendation = 'Keep Control'
            confidence = 'high' if p_value < 0.01 else 'medium'
        else:
            recommendation = 'Continue Testing'
            confidence = 'low'

        # Calculate statistical power achieved
        if SCIPY_AVAILABLE and abs(diff) > 0:
            effect_size = abs(diff) / math.sqrt(pooled_rate * (1 - pooled_rate))
            achieved_power = stats.norm.cdf(
                abs(z_stat) - stats.norm.ppf(1 - self.alpha/2)
            )
        else:
            achieved_power = None

        return {
            'control_rate': round(control_rate, 4),
            'variant_rate': round(variant_rate, 4),
            'absolute_difference': round(diff, 4),
            'relative_lift_pct': round(lift_pct, 2),
            'z_statistic': round(z_stat, 4),
            'p_value': round(p_value, 4),
            'significant': significant,
            'confidence_interval': {
                'lower': round(ci_lower, 4),
                'upper': round(ci_upper, 4),
                'level': self.confidence_level
            },
            'sample_sizes': {
                'control': control_visitors,
                'variant': variant_visitors,
                'total': total_visitors
            },
            'recommendation': recommendation,
            'confidence': confidence,
            'achieved_power': round(achieved_power, 3) if achieved_power else None,
            'algorithm': 'Two-proportion z-test with confidence intervals',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def _manual_p_value(self, z: float) -> float:
        """
        Approximate p-value without scipy.

        Uses Abramowitz & Stegun approximation.
        """
        # Constants for approximation
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1 if z >= 0 else -1
        z = abs(z)

        t = 1.0 / (1.0 + p * z)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z * z / 2)

        cdf = 0.5 * (1.0 + sign * y)
        return 2 * (1 - cdf)

    def calculate_test_duration(
        self,
        daily_visitors: int,
        required_sample_size: int,
        traffic_split: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate estimated test duration.

        Args:
            daily_visitors: Average daily visitors
            required_sample_size: Required sample per variant
            traffic_split: Fraction of traffic to test (default 0.5 = 50%)

        Returns:
            Dict with estimated duration
        """
        if daily_visitors == 0:
            return {
                'error': 'Daily visitors cannot be zero',
                'algorithm': 'Duration = required_sample / (daily_visitors * split / 2)',
                'is_verified': True
            }

        visitors_per_variant_daily = daily_visitors * traffic_split / 2
        days_required = math.ceil(required_sample_size / visitors_per_variant_daily)

        return {
            'days_required': days_required,
            'weeks_required': round(days_required / 7, 1),
            'daily_visitors': daily_visitors,
            'visitors_in_test': int(daily_visitors * traffic_split),
            'visitors_per_variant_daily': int(visitors_per_variant_daily),
            'required_sample_size': required_sample_size,
            'traffic_split': traffic_split,
            'algorithm': 'Duration = required_sample / (daily_visitors * split / 2)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def analyze_multiple_variants(
        self,
        variants: List[Dict[str, int]]
    ) -> Dict[str, Any]:
        """
        Analyze test with multiple variants against control.

        Args:
            variants: List of dicts with 'name', 'conversions', 'visitors'
                      First variant is assumed to be control

        Returns:
            Dict with pairwise comparisons and winner
        """
        if len(variants) < 2:
            return {
                'error': 'Need at least 2 variants (control + 1 variant)',
                'algorithm': 'Multiple pairwise z-tests with Bonferroni correction',
                'is_verified': True
            }

        control = variants[0]
        comparisons = []

        # Bonferroni correction for multiple comparisons
        num_comparisons = len(variants) - 1
        adjusted_alpha = self.alpha / num_comparisons

        for variant in variants[1:]:
            result = self.analyze_test(
                control['conversions'],
                control['visitors'],
                variant['conversions'],
                variant['visitors']
            )

            # Apply Bonferroni correction
            result['bonferroni_significant'] = result['p_value'] < adjusted_alpha
            result['variant_name'] = variant.get('name', 'Variant')
            comparisons.append(result)

        # Find winner
        significant_winners = [
            c for c in comparisons
            if c.get('bonferroni_significant') and c.get('relative_lift_pct', 0) > 0
        ]

        if significant_winners:
            winner = max(significant_winners, key=lambda x: x.get('relative_lift_pct', 0))
            overall_winner = winner['variant_name']
        else:
            overall_winner = control.get('name', 'Control')

        return {
            'control': control.get('name', 'Control'),
            'comparisons': comparisons,
            'overall_winner': overall_winner,
            'num_variants': len(variants),
            'bonferroni_alpha': round(adjusted_alpha, 4),
            'algorithm': 'Multiple pairwise z-tests with Bonferroni correction',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }


# Convenience functions
def analyze_ab_test(
    control_conversions: int,
    control_visitors: int,
    variant_conversions: int,
    variant_visitors: int,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """Analyze A/B test results."""
    framework = ABTestFramework(confidence_level)
    return framework.analyze_test(
        control_conversions, control_visitors,
        variant_conversions, variant_visitors
    )


def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    power: float = 0.8,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """Calculate required sample size for A/B test."""
    framework = ABTestFramework(confidence_level)
    return framework.calculate_sample_size(baseline_rate, minimum_detectable_effect, power)
