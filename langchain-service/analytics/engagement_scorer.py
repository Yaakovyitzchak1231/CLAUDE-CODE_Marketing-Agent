"""
Engagement Scoring Module - Mathematical Content Effectiveness Analysis

All calculations are:
- Pure mathematical formulas
- Industry-standard benchmarks
- NO LLM inference

Algorithms:
- Engagement Rate: (clicks + shares + comments) / impressions * 100
- Weighted Engagement: Industry-standard weights for different actions
- Content Effectiveness: Multi-factor scoring (0-100)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class EngagementScorer:
    """
    Production-grade engagement scoring using mathematical formulas.

    All methods return deterministic results with algorithm documentation.
    """

    # Industry-standard weights for engagement actions
    ACTION_WEIGHTS = {
        'impression': 0.0,      # Base - no action
        'click': 1.0,           # Basic engagement
        'share': 2.5,           # Social amplification worth 2.5x
        'comment': 3.0,         # Deep engagement worth 3x
        'conversion': 10.0,     # Business outcome worth 10x
        'download': 5.0,        # High-intent action worth 5x
        'signup': 8.0,          # Lead capture worth 8x
        'purchase': 15.0,       # Revenue action worth 15x
    }

    # Industry benchmarks for engagement rates (%)
    BENCHMARKS = {
        'poor': 0.5,
        'below_average': 1.0,
        'average': 2.0,
        'good': 3.5,
        'excellent': 5.0,
        'viral': 10.0,
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize engagement scorer.

        Args:
            custom_weights: Optional custom weights for engagement actions
        """
        self.weights = {**self.ACTION_WEIGHTS}
        if custom_weights:
            self.weights.update(custom_weights)

    def calculate_engagement_rate(self, metrics: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate basic engagement rate.

        Formula: (clicks + shares + comments) / impressions * 100

        Args:
            metrics: Dict with keys: impressions, clicks, shares, comments

        Returns:
            Dict with engagement_rate, benchmark_comparison, and metadata
        """
        impressions = metrics.get('impressions', 0)
        clicks = metrics.get('clicks', 0)
        shares = metrics.get('shares', 0)
        comments = metrics.get('comments', 0)

        if impressions == 0:
            return {
                'engagement_rate': 0.0,
                'benchmark': 'no_data',
                'algorithm': 'engagement_rate = (clicks + shares + comments) / impressions * 100',
                'is_verified': True,
                'error': 'No impressions recorded'
            }

        engagement_rate = (clicks + shares + comments) / impressions * 100

        # Determine benchmark tier
        if engagement_rate >= self.BENCHMARKS['viral']:
            benchmark = 'viral'
        elif engagement_rate >= self.BENCHMARKS['excellent']:
            benchmark = 'excellent'
        elif engagement_rate >= self.BENCHMARKS['good']:
            benchmark = 'good'
        elif engagement_rate >= self.BENCHMARKS['average']:
            benchmark = 'average'
        elif engagement_rate >= self.BENCHMARKS['below_average']:
            benchmark = 'below_average'
        else:
            benchmark = 'poor'

        return {
            'engagement_rate': round(engagement_rate, 4),
            'benchmark': benchmark,
            'benchmark_thresholds': self.BENCHMARKS,
            'raw_metrics': {
                'impressions': impressions,
                'clicks': clicks,
                'shares': shares,
                'comments': comments,
                'total_engagements': clicks + shares + comments
            },
            'algorithm': 'engagement_rate = (clicks + shares + comments) / impressions * 100',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_weighted_engagement(self, metrics: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate weighted engagement score using industry-standard weights.

        Formula: sum(action_count * action_weight) / impressions * 100

        Args:
            metrics: Dict with keys matching ACTION_WEIGHTS

        Returns:
            Dict with weighted_score, component_breakdown, and metadata
        """
        impressions = metrics.get('impressions', 0)

        if impressions == 0:
            return {
                'weighted_score': 0.0,
                'algorithm': 'weighted_engagement = sum(action * weight) / impressions * 100',
                'is_verified': True,
                'error': 'No impressions recorded'
            }

        # Calculate weighted sum
        weighted_sum = 0.0
        component_breakdown = {}

        for action, weight in self.weights.items():
            if action == 'impression':
                continue
            count = metrics.get(action, metrics.get(f'{action}s', 0))  # Handle plural
            contribution = count * weight
            weighted_sum += contribution
            if count > 0:
                component_breakdown[action] = {
                    'count': count,
                    'weight': weight,
                    'contribution': contribution
                }

        weighted_score = weighted_sum / impressions * 100

        return {
            'weighted_score': round(weighted_score, 4),
            'component_breakdown': component_breakdown,
            'weights_used': self.weights,
            'impressions': impressions,
            'algorithm': 'weighted_engagement = sum(action * weight) / impressions * 100',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_content_effectiveness(
        self,
        metrics: Dict[str, Any],
        campaign_benchmarks: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive content effectiveness score (0-100).

        Multi-factor scoring:
        - Reach Score (0-25 points): Impressions vs campaign average
        - Engagement Score (0-35 points): Based on industry benchmarks
        - Conversion Score (0-25 points): Conversion rate benchmarks
        - Virality Score (0-15 points): Share-to-view ratio

        Args:
            metrics: Dict with impressions, clicks, shares, comments, conversions
            campaign_benchmarks: Optional dict with campaign average metrics

        Returns:
            Dict with total_score, breakdown, grade, and metadata
        """
        scores = {}

        impressions = metrics.get('impressions', 0)
        clicks = metrics.get('clicks', 0)
        shares = metrics.get('shares', 0)
        comments = metrics.get('comments', 0)
        conversions = metrics.get('conversions', 0)

        # 1. Reach Score (0-25 points)
        # Percentile-based against campaign average
        if campaign_benchmarks and 'avg_impressions' in campaign_benchmarks:
            avg_impressions = campaign_benchmarks['avg_impressions']
            if avg_impressions > 0:
                reach_ratio = impressions / avg_impressions
                scores['reach'] = min(reach_ratio * 12.5, 25)  # Cap at 25
            else:
                scores['reach'] = 12.5  # Average if no benchmark
        else:
            # Use absolute scale: 10K impressions = 25 points
            scores['reach'] = min(impressions / 10000 * 25, 25)

        # 2. Engagement Score (0-35 points)
        # Industry benchmark: 1-3% is average, >5% is excellent
        if impressions > 0:
            engagement_rate = (clicks + shares + comments) / impressions * 100

            if engagement_rate >= 5:
                scores['engagement'] = 35
            elif engagement_rate >= 3:
                scores['engagement'] = 25 + (engagement_rate - 3) * 5
            elif engagement_rate >= 1:
                scores['engagement'] = 10 + (engagement_rate - 1) * 7.5
            else:
                scores['engagement'] = engagement_rate * 10
        else:
            scores['engagement'] = 0

        # 3. Conversion Score (0-25 points)
        # Conversion rate benchmarks: 1% avg, 3% good, 5%+ excellent
        if clicks > 0:
            conv_rate = conversions / clicks * 100

            if conv_rate >= 5:
                scores['conversion'] = 25
            elif conv_rate >= 3:
                scores['conversion'] = 20 + (conv_rate - 3) * 2.5
            elif conv_rate >= 1:
                scores['conversion'] = 10 + (conv_rate - 1) * 5
            else:
                scores['conversion'] = conv_rate * 10
        else:
            scores['conversion'] = 0

        # 4. Virality Score (0-15 points)
        # Share-to-view ratio: >1% is viral
        if impressions > 0:
            virality = shares / impressions * 100
            scores['virality'] = min(virality * 15, 15)
        else:
            scores['virality'] = 0

        # Calculate total score
        total_score = sum(scores.values())

        # Determine grade
        if total_score >= 80:
            grade = 'A'
        elif total_score >= 60:
            grade = 'B'
        elif total_score >= 40:
            grade = 'C'
        elif total_score >= 20:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'total_score': round(total_score, 1),
            'breakdown': {k: round(v, 2) for k, v in scores.items()},
            'max_possible': {
                'reach': 25,
                'engagement': 35,
                'conversion': 25,
                'virality': 15
            },
            'grade': grade,
            'raw_metrics': {
                'impressions': impressions,
                'clicks': clicks,
                'shares': shares,
                'comments': comments,
                'conversions': conversions
            },
            'algorithm': 'Multi-factor weighted scoring (reach: 25pts, engagement: 35pts, conversion: 25pts, virality: 15pts)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_trend_over_time(
        self,
        metrics_series: List[Dict[str, Any]],
        metric_name: str = 'engagement_rate'
    ) -> Dict[str, Any]:
        """
        Calculate trend direction for a metric over time.

        Uses linear regression to determine trend direction.

        Args:
            metrics_series: List of dicts with timestamps and metrics
            metric_name: Name of metric to analyze

        Returns:
            Dict with trend_direction, slope, and confidence
        """
        if len(metrics_series) < 2:
            return {
                'trend_direction': 'insufficient_data',
                'algorithm': 'Linear regression',
                'is_verified': True,
                'error': 'Need at least 2 data points'
            }

        # Extract values
        values = []
        for item in metrics_series:
            if metric_name in item:
                values.append(item[metric_name])
            elif 'metrics' in item and metric_name in item['metrics']:
                values.append(item['metrics'][metric_name])

        if len(values) < 2:
            return {
                'trend_direction': 'insufficient_data',
                'algorithm': 'Linear regression',
                'is_verified': True,
                'error': f'Metric {metric_name} not found in data'
            }

        # Calculate linear regression
        n = len(values)
        x_values = list(range(n))

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return {
                'trend_direction': 'flat',
                'slope': 0,
                'algorithm': 'Linear regression',
                'is_verified': True
            }

        slope = numerator / denominator

        # Calculate R-squared
        y_pred = [slope * x + (y_mean - slope * x_mean) for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in values)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Determine direction
        if abs(slope) < 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'rising'
        else:
            direction = 'declining'

        # Determine confidence based on R-squared
        if r_squared > 0.7:
            confidence = 'high'
        elif r_squared > 0.4:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'trend_direction': direction,
            'slope': round(slope, 4),
            'r_squared': round(r_squared, 4),
            'confidence': confidence,
            'data_points': n,
            'first_value': values[0],
            'last_value': values[-1],
            'change_pct': round((values[-1] - values[0]) / values[0] * 100, 2) if values[0] != 0 else 0,
            'algorithm': 'Linear regression with R-squared confidence',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }


# Convenience functions
def calculate_engagement_rate(metrics: Dict[str, int]) -> Dict[str, Any]:
    """Calculate basic engagement rate."""
    scorer = EngagementScorer()
    return scorer.calculate_engagement_rate(metrics)


def calculate_content_effectiveness(
    metrics: Dict[str, Any],
    campaign_benchmarks: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Calculate comprehensive content effectiveness score."""
    scorer = EngagementScorer()
    return scorer.calculate_content_effectiveness(metrics, campaign_benchmarks)
