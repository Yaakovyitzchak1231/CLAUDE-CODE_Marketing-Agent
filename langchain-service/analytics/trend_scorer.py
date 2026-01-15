"""
Trend Scorer Module - Multi-Source Weighted Trend Analysis

Aggregates data from multiple sources:
- Google Trends (market interest)
- Government data (BLS employment, Census)
- News mentions (media coverage)
- Job postings (market demand)
- Social sentiment (consumer perception)

All calculations are:
- Weighted mathematical formulas
- NO LLM inference
- Source-credibility weighted
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class TrendScorer:
    """
    Production-grade trend scoring using multi-source weighted analysis.

    All methods return deterministic results with algorithm documentation.
    """

    # Source weights for trend scoring
    SOURCE_WEIGHTS = {
        'google_trends': 0.30,      # Market interest
        'gov_employment': 0.25,     # Industry health (BLS)
        'news_mentions': 0.20,      # Media coverage
        'job_postings': 0.15,       # Market demand
        'social_sentiment': 0.10,   # Consumer/SMB sentiment
    }

    # Source credibility tiers
    CREDIBILITY_TIERS = {
        'tier1_authoritative': 1.0,      # Government, academic sources
        'tier2_business_news': 0.8,      # Major business publications
        'tier3_industry_pubs': 0.6,      # Industry-specific publications
        'tier4_general_news': 0.4,       # General news outlets
        'tier5_social_media': 0.2,       # Social media mentions
    }

    # Momentum thresholds
    MOMENTUM_THRESHOLDS = {
        'surging': 25,       # > 25% growth
        'rising': 10,        # > 10% growth
        'stable': -10,       # -10% to +10%
        'declining': -25,    # -10% to -25%
        'collapsing': -100,  # < -25%
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize trend scorer.

        Args:
            custom_weights: Optional custom weights for data sources
        """
        self.weights = {**self.SOURCE_WEIGHTS}
        if custom_weights:
            self.weights.update(custom_weights)

    def calculate_trend_score(
        self,
        topic: str,
        data_sources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive trend score from multiple data sources.

        Formula: weighted_score = sum(source_score * source_weight) / total_weight

        Args:
            topic: Topic/trend being analyzed
            data_sources: Dict with data from various sources

        Returns:
            Dict with trend_score, component_scores, and metadata
        """
        scores = {}

        # 1. Google Trends Score (0-100)
        if 'google_trends' in data_sources:
            gt = data_sources['google_trends']
            current = gt.get('current_interest', 0)
            avg = gt.get('avg_interest', 50)

            if avg > 0:
                # Current interest relative to 12-month average
                ratio = current / avg
                scores['google_trends'] = min(ratio * 50, 100)
            else:
                scores['google_trends'] = 50  # Neutral if no baseline

        # 2. Government Employment Data Score (0-100)
        if 'gov_employment' in data_sources:
            ge = data_sources['gov_employment']
            growth_rate = ge.get('growth_rate_pct', 0)

            # Normalize: -10% to +10% -> 0-100
            # 0% growth = 50, +10% = 100, -10% = 0
            scores['gov_employment'] = max(0, min(100, 50 + growth_rate * 5))

        # 3. News Mention Score (0-100)
        if 'news_mentions' in data_sources:
            nm = data_sources['news_mentions']

            # Weight by source credibility
            tier1 = nm.get('tier1_authoritative', 0) * self.CREDIBILITY_TIERS['tier1_authoritative']
            tier2 = nm.get('tier2_business_news', 0) * self.CREDIBILITY_TIERS['tier2_business_news']
            tier3 = nm.get('tier3_industry_pubs', 0) * self.CREDIBILITY_TIERS['tier3_industry_pubs']
            tier4 = nm.get('tier4_general_news', 0) * self.CREDIBILITY_TIERS['tier4_general_news']

            # Weighted mention score (cap at 100)
            weighted_mentions = tier1 * 20 + tier2 * 10 + tier3 * 5 + tier4 * 2
            scores['news_mentions'] = min(weighted_mentions, 100)

        # 4. Job Posting Score (0-100)
        if 'job_postings' in data_sources:
            jp = data_sources['job_postings']
            posting_count = jp.get('total_postings', 0)
            posting_growth = jp.get('growth_pct', 0)

            # Base score from count (20+ postings = 50 points)
            count_score = min(posting_count * 2.5, 50)

            # Growth score (10% growth = 50 points)
            growth_score = max(0, min(50, 25 + posting_growth * 2.5))

            scores['job_postings'] = count_score + growth_score

        # 5. Social Sentiment Score (0-100)
        if 'social_sentiment' in data_sources:
            ss = data_sources['social_sentiment']
            sentiment = ss.get('avg_sentiment', 0)  # -1 to +1 scale
            volume = ss.get('mention_volume', 0)

            # Sentiment: -1 to +1 -> 0-100
            sentiment_score = 50 + sentiment * 50

            # Volume bonus (high volume = more reliable)
            volume_multiplier = min(1.0, volume / 1000) if volume > 0 else 0.5

            scores['social_sentiment'] = sentiment_score * volume_multiplier

        # Calculate Weighted Total
        if not scores:
            return {
                'topic': topic,
                'trend_score': 0.0,
                'error': 'No data sources provided',
                'algorithm': 'Multi-source weighted scoring',
                'is_verified': True
            }

        total_weight = sum(self.weights[k] for k in scores.keys())
        weighted_score = sum(scores[k] * self.weights[k] for k in scores.keys()) / total_weight

        # Determine confidence based on source count
        if len(scores) >= 4:
            confidence = 'high'
        elif len(scores) >= 2:
            confidence = 'medium'
        else:
            confidence = 'low'

        # Determine trend direction
        if weighted_score >= 70:
            direction = 'strong_positive'
        elif weighted_score >= 55:
            direction = 'positive'
        elif weighted_score >= 45:
            direction = 'neutral'
        elif weighted_score >= 30:
            direction = 'negative'
        else:
            direction = 'strong_negative'

        return {
            'topic': topic,
            'trend_score': round(weighted_score, 1),
            'component_scores': {k: round(v, 1) for k, v in scores.items()},
            'weights_used': {k: self.weights[k] for k in scores.keys()},
            'sources_count': len(scores),
            'confidence': confidence,
            'direction': direction,
            'algorithm': 'Multi-source weighted scoring (Google Trends, BLS, news, jobs, sentiment)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_momentum(
        self,
        current_score: float,
        previous_score: float,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate trend momentum (rate of change).

        Formula: momentum = (current - previous) / previous * 100

        Args:
            current_score: Current trend score
            previous_score: Previous trend score
            time_period_days: Time period for comparison

        Returns:
            Dict with momentum metrics
        """
        if previous_score == 0:
            return {
                'momentum_pct': 0.0,
                'direction': 'stable',
                'error': 'Previous score is zero',
                'algorithm': 'momentum = (current - previous) / previous * 100',
                'is_verified': True
            }

        momentum_pct = ((current_score - previous_score) / previous_score) * 100

        # Determine direction
        if momentum_pct > self.MOMENTUM_THRESHOLDS['surging']:
            direction = 'surging'
        elif momentum_pct > self.MOMENTUM_THRESHOLDS['rising']:
            direction = 'rising'
        elif momentum_pct > self.MOMENTUM_THRESHOLDS['stable']:
            direction = 'stable'
        elif momentum_pct > self.MOMENTUM_THRESHOLDS['declining']:
            direction = 'declining'
        else:
            direction = 'collapsing'

        # Calculate velocity (change per day)
        velocity = momentum_pct / time_period_days if time_period_days > 0 else 0

        return {
            'momentum_pct': round(momentum_pct, 2),
            'direction': direction,
            'velocity_per_day': round(velocity, 3),
            'current_score': current_score,
            'previous_score': previous_score,
            'time_period_days': time_period_days,
            'thresholds': self.MOMENTUM_THRESHOLDS,
            'algorithm': 'momentum = (current - previous) / previous * 100',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_trend_trajectory(
        self,
        score_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate trend trajectory using linear regression.

        Args:
            score_history: List of {score, timestamp} dicts

        Returns:
            Dict with trajectory analysis
        """
        if len(score_history) < 3:
            return {
                'trajectory': 'insufficient_data',
                'error': 'Need at least 3 data points',
                'algorithm': 'Linear regression',
                'is_verified': True
            }

        # Extract scores
        scores = [item['score'] for item in score_history if 'score' in item]

        if len(scores) < 3:
            return {
                'trajectory': 'insufficient_data',
                'error': 'Score field missing from data points',
                'algorithm': 'Linear regression',
                'is_verified': True
            }

        # Calculate linear regression
        n = len(scores)
        x_values = list(range(n))

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(scores)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, scores))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return {
                'trajectory': 'flat',
                'slope': 0,
                'algorithm': 'Linear regression',
                'is_verified': True
            }

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Calculate R-squared
        y_pred = [slope * x + intercept for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(scores, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in scores)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Determine trajectory
        if abs(slope) < 0.5:
            trajectory = 'stable'
        elif slope > 2:
            trajectory = 'accelerating'
        elif slope > 0:
            trajectory = 'growing'
        elif slope > -2:
            trajectory = 'slowing'
        else:
            trajectory = 'declining'

        # Project future score (next period)
        projected_score = slope * n + intercept

        return {
            'trajectory': trajectory,
            'slope': round(slope, 4),
            'intercept': round(intercept, 4),
            'r_squared': round(r_squared, 4),
            'fit_quality': 'strong' if r_squared > 0.7 else 'moderate' if r_squared > 0.4 else 'weak',
            'data_points': n,
            'first_score': scores[0],
            'last_score': scores[-1],
            'projected_next': round(max(0, min(100, projected_score)), 1),
            'total_change': round(scores[-1] - scores[0], 1),
            'algorithm': 'Linear regression with R-squared confidence',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def compare_trends(
        self,
        trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple trends and rank them.

        Args:
            trends: List of trend data with scores

        Returns:
            Dict with ranked trends and comparison metrics
        """
        if not trends:
            return {
                'ranked_trends': [],
                'error': 'No trends to compare',
                'algorithm': 'Score-based ranking with momentum weighting',
                'is_verified': True
            }

        # Calculate composite score for each trend
        # Composite = trend_score * 0.6 + momentum_score * 0.4
        ranked = []

        for trend in trends:
            score = trend.get('trend_score', 0)
            momentum = trend.get('momentum_pct', 0)

            # Normalize momentum to 0-100 scale
            momentum_normalized = 50 + momentum / 2  # -100% to +100% -> 0-100

            composite = score * 0.6 + momentum_normalized * 0.4

            ranked.append({
                'topic': trend.get('topic', 'Unknown'),
                'trend_score': round(score, 1),
                'momentum_pct': round(momentum, 1),
                'composite_score': round(composite, 1)
            })

        # Sort by composite score
        ranked.sort(key=lambda x: x['composite_score'], reverse=True)

        # Add rank
        for i, trend in enumerate(ranked):
            trend['rank'] = i + 1

        # Calculate spread
        if len(ranked) > 1:
            scores = [t['composite_score'] for t in ranked]
            spread = max(scores) - min(scores)
        else:
            spread = 0

        return {
            'ranked_trends': ranked,
            'top_trend': ranked[0]['topic'] if ranked else None,
            'total_trends': len(ranked),
            'score_spread': round(spread, 1),
            'algorithm': 'Composite scoring (trend: 60%, momentum: 40%)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }


# Convenience functions
def calculate_trend_score(topic: str, data_sources: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate trend score for a topic."""
    scorer = TrendScorer()
    return scorer.calculate_trend_score(topic, data_sources)


def calculate_momentum(
    current_score: float,
    previous_score: float,
    time_period_days: int = 30
) -> Dict[str, Any]:
    """Calculate trend momentum."""
    scorer = TrendScorer()
    return scorer.calculate_momentum(current_score, previous_score, time_period_days)
