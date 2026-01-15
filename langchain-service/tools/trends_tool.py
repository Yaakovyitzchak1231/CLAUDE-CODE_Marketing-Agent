"""
Trends Tool - Real-time market interest data using Google Trends

Provides:
- Search interest over time for keywords
- Regional interest breakdown
- Related queries and rising topics
- Trend direction calculation (not hallucinated - mathematically computed)
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

# Try to import pytrends, provide fallback if not installed
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logger.warning("pytrends not installed. Google Trends features will be limited.")


class TrendsTool:
    """
    Real-time trend analysis using Google Trends data.

    All trend calculations use mathematical algorithms:
    - Linear regression for trend direction
    - Standard deviation for volatility
    - Percentage change for momentum
    - Moving averages for smoothing

    NO LLM hallucination - all insights are computed from actual data.
    """

    def __init__(self, hl: str = 'en-US', tz: int = 360):
        """
        Initialize trends tool.

        Args:
            hl: Host language for Google Trends
            tz: Timezone offset (360 = US Central)
        """
        self.hl = hl
        self.tz = tz
        self.pytrends = None

        if PYTRENDS_AVAILABLE:
            self.pytrends = TrendReq(hl=hl, tz=tz)

    def _calculate_trend_direction(self, values: List[float]) -> Dict[str, Any]:
        """
        Calculate trend direction using linear regression.

        This is a MATHEMATICAL calculation, not LLM inference.

        Args:
            values: List of numeric values (oldest to newest)

        Returns:
            Dict with slope, direction, and confidence
        """
        if len(values) < 2:
            return {'direction': 'insufficient_data', 'confidence': 0}

        n = len(values)
        x_values = list(range(n))

        # Calculate means
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        # Calculate slope using least squares
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return {'direction': 'flat', 'slope': 0, 'confidence': 0}

        slope = numerator / denominator

        # Calculate R-squared for confidence
        y_pred = [slope * x + (y_mean - slope * x_mean) for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in values)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Determine direction based on slope magnitude
        if abs(slope) < 0.5:
            direction = 'stable'
        elif slope > 0:
            direction = 'rising'
        else:
            direction = 'declining'

        return {
            'direction': direction,
            'slope': round(slope, 4),
            'r_squared': round(r_squared, 4),
            'confidence': 'high' if r_squared > 0.7 else 'medium' if r_squared > 0.4 else 'low'
        }

    def _calculate_momentum(self, values: List[float], window: int = 4) -> Dict[str, Any]:
        """
        Calculate momentum as rate of change.

        Uses percentage change between periods - pure math.

        Args:
            values: List of values (oldest to newest)
            window: Comparison window size

        Returns:
            Dict with momentum metrics
        """
        if len(values) < window + 1:
            return {'momentum': 0, 'interpretation': 'insufficient_data'}

        recent = statistics.mean(values[-window:])
        earlier = statistics.mean(values[:window])

        if earlier == 0:
            return {'momentum': 0, 'interpretation': 'baseline_zero'}

        momentum = ((recent - earlier) / earlier) * 100

        # Interpret momentum mathematically
        if momentum > 50:
            interpretation = 'strong_growth'
        elif momentum > 20:
            interpretation = 'moderate_growth'
        elif momentum > 5:
            interpretation = 'slight_growth'
        elif momentum > -5:
            interpretation = 'stable'
        elif momentum > -20:
            interpretation = 'slight_decline'
        elif momentum > -50:
            interpretation = 'moderate_decline'
        else:
            interpretation = 'strong_decline'

        return {
            'momentum_pct': round(momentum, 2),
            'interpretation': interpretation,
            'recent_avg': round(recent, 2),
            'earlier_avg': round(earlier, 2)
        }

    def _calculate_volatility(self, values: List[float]) -> Dict[str, Any]:
        """
        Calculate volatility using standard deviation.

        Args:
            values: List of values

        Returns:
            Dict with volatility metrics
        """
        if len(values) < 3:
            return {'volatility': 0, 'level': 'insufficient_data'}

        mean = statistics.mean(values)
        stdev = statistics.stdev(values)

        # Coefficient of variation (normalized volatility)
        cv = (stdev / mean * 100) if mean > 0 else 0

        if cv > 50:
            level = 'high'
        elif cv > 25:
            level = 'moderate'
        else:
            level = 'low'

        return {
            'stdev': round(stdev, 2),
            'coefficient_of_variation': round(cv, 2),
            'level': level,
            'mean': round(mean, 2)
        }

    def get_interest_over_time(self, keywords: List[str],
                               timeframe: str = 'today 12-m') -> Dict[str, Any]:
        """
        Get Google Trends interest over time for keywords.

        Args:
            keywords: List of keywords to track (max 5)
            timeframe: Timeframe string (e.g., 'today 12-m', 'today 3-m', 'now 7-d')

        Returns:
            Dict with trend data and calculated metrics
        """
        if not PYTRENDS_AVAILABLE:
            return {
                'error': 'pytrends library not installed',
                'install_command': 'pip install pytrends',
                'confidence': 'none'
            }

        if len(keywords) > 5:
            keywords = keywords[:5]
            logger.warning("Truncated to 5 keywords (Google Trends limit)")

        try:
            self.pytrends.build_payload(keywords, timeframe=timeframe)
            interest_df = self.pytrends.interest_over_time()

            if interest_df.empty:
                return {
                    'keywords': keywords,
                    'error': 'No data returned from Google Trends',
                    'confidence': 'none'
                }

            # Process each keyword
            keyword_data = {}
            for keyword in keywords:
                if keyword in interest_df.columns:
                    values = interest_df[keyword].tolist()

                    keyword_data[keyword] = {
                        'current_interest': values[-1] if values else 0,
                        'max_interest': max(values) if values else 0,
                        'min_interest': min(values) if values else 0,
                        'avg_interest': round(statistics.mean(values), 2) if values else 0,
                        'trend': self._calculate_trend_direction(values),
                        'momentum': self._calculate_momentum(values),
                        'volatility': self._calculate_volatility(values),
                        'data_points': len(values)
                    }

            # Determine overall confidence
            data_points = sum(kd['data_points'] for kd in keyword_data.values())

            return {
                'keywords': keywords,
                'timeframe': timeframe,
                'keyword_data': keyword_data,
                'data_source': 'Google Trends',
                'confidence': 'high' if data_points > 20 else 'medium',
                'is_verified': True,
                'algorithm': 'Linear regression for trend, % change for momentum, stdev for volatility',
                'retrieved_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Google Trends error: {e}")
            return {
                'keywords': keywords,
                'error': str(e),
                'confidence': 'none'
            }

    def get_related_queries(self, keyword: str) -> Dict[str, Any]:
        """
        Get related queries and rising topics for a keyword.

        Args:
            keyword: Keyword to find related queries for

        Returns:
            Dict with related and rising queries
        """
        if not PYTRENDS_AVAILABLE:
            return {
                'error': 'pytrends library not installed',
                'confidence': 'none'
            }

        try:
            self.pytrends.build_payload([keyword], timeframe='today 3-m')
            related = self.pytrends.related_queries()

            result = {
                'keyword': keyword,
                'top_queries': [],
                'rising_queries': []
            }

            if keyword in related:
                # Top queries (most searched related terms)
                top_df = related[keyword].get('top')
                if top_df is not None and not top_df.empty:
                    result['top_queries'] = top_df.to_dict('records')

                # Rising queries (fastest growing related terms)
                rising_df = related[keyword].get('rising')
                if rising_df is not None and not rising_df.empty:
                    result['rising_queries'] = rising_df.to_dict('records')

            result['data_source'] = 'Google Trends Related Queries'
            result['confidence'] = 'high' if result['top_queries'] else 'low'
            result['is_verified'] = True
            result['retrieved_at'] = datetime.now().isoformat()

            return result

        except Exception as e:
            logger.error(f"Related queries error: {e}")
            return {
                'keyword': keyword,
                'error': str(e),
                'confidence': 'none'
            }

    def get_regional_interest(self, keyword: str, resolution: str = 'COUNTRY') -> Dict[str, Any]:
        """
        Get regional breakdown of interest for a keyword.

        Args:
            keyword: Keyword to analyze
            resolution: Geographic resolution ('COUNTRY', 'REGION', 'CITY', 'DMA')

        Returns:
            Dict with regional interest data
        """
        if not PYTRENDS_AVAILABLE:
            return {
                'error': 'pytrends library not installed',
                'confidence': 'none'
            }

        try:
            self.pytrends.build_payload([keyword], timeframe='today 12-m')
            regional = self.pytrends.interest_by_region(resolution=resolution)

            if regional.empty:
                return {
                    'keyword': keyword,
                    'error': 'No regional data available',
                    'confidence': 'none'
                }

            # Get top regions
            regional_sorted = regional.sort_values(by=keyword, ascending=False)
            top_regions = regional_sorted.head(20).to_dict()[keyword]

            return {
                'keyword': keyword,
                'resolution': resolution,
                'top_regions': top_regions,
                'total_regions_with_data': len(regional[regional[keyword] > 0]),
                'data_source': 'Google Trends Regional Data',
                'confidence': 'high',
                'is_verified': True,
                'retrieved_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Regional interest error: {e}")
            return {
                'keyword': keyword,
                'error': str(e),
                'confidence': 'none'
            }

    def compare_keywords(self, keywords: List[str], timeframe: str = 'today 12-m') -> Dict[str, Any]:
        """
        Compare multiple keywords and rank by various metrics.

        Args:
            keywords: Keywords to compare (max 5)
            timeframe: Time period for comparison

        Returns:
            Dict with comparative analysis
        """
        interest_data = self.get_interest_over_time(keywords, timeframe)

        if 'error' in interest_data:
            return interest_data

        # Rank by different metrics
        rankings = {
            'by_current_interest': [],
            'by_growth_momentum': [],
            'by_stability': []
        }

        keyword_data = interest_data.get('keyword_data', {})

        for keyword, data in keyword_data.items():
            rankings['by_current_interest'].append({
                'keyword': keyword,
                'value': data['current_interest']
            })
            rankings['by_growth_momentum'].append({
                'keyword': keyword,
                'value': data['momentum']['momentum_pct']
            })
            rankings['by_stability'].append({
                'keyword': keyword,
                'value': 100 - data['volatility']['coefficient_of_variation']  # Invert so higher = more stable
            })

        # Sort rankings
        for key in rankings:
            rankings[key] = sorted(rankings[key], key=lambda x: x['value'], reverse=True)

        return {
            'keywords': keywords,
            'timeframe': timeframe,
            'rankings': rankings,
            'detailed_data': keyword_data,
            'data_source': 'Google Trends',
            'confidence': 'high',
            'is_verified': True,
            'algorithm': 'Rankings based on computed metrics (no LLM inference)',
            'retrieved_at': datetime.now().isoformat()
        }

    def detect_emerging_trends(self, industry_keywords: List[str],
                               threshold_pct: float = 50.0) -> Dict[str, Any]:
        """
        Detect emerging trends based on momentum thresholds.

        Args:
            industry_keywords: Keywords to check
            threshold_pct: Momentum threshold to classify as "emerging" (default 50%)

        Returns:
            Dict with emerging trends identified
        """
        interest_data = self.get_interest_over_time(industry_keywords, 'today 3-m')

        if 'error' in interest_data:
            return interest_data

        emerging = []
        declining = []
        stable = []

        for keyword, data in interest_data.get('keyword_data', {}).items():
            momentum = data['momentum']['momentum_pct']

            entry = {
                'keyword': keyword,
                'momentum_pct': momentum,
                'current_interest': data['current_interest'],
                'trend_direction': data['trend']['direction']
            }

            if momentum >= threshold_pct:
                emerging.append(entry)
            elif momentum <= -threshold_pct:
                declining.append(entry)
            else:
                stable.append(entry)

        # Sort by momentum
        emerging = sorted(emerging, key=lambda x: x['momentum_pct'], reverse=True)
        declining = sorted(declining, key=lambda x: x['momentum_pct'])

        return {
            'emerging_trends': emerging,
            'declining_trends': declining,
            'stable_topics': stable,
            'threshold_used': threshold_pct,
            'total_analyzed': len(industry_keywords),
            'data_source': 'Google Trends',
            'confidence': 'high' if interest_data.get('confidence') == 'high' else 'medium',
            'is_verified': True,
            'algorithm': f'Momentum > {threshold_pct}% = emerging, < -{threshold_pct}% = declining',
            'retrieved_at': datetime.now().isoformat()
        }


# Singleton instance
trends_tool = TrendsTool()


def get_keyword_trends(keywords: List[str], timeframe: str = 'today 12-m') -> Dict[str, Any]:
    """Convenience function for getting keyword trends."""
    return trends_tool.get_interest_over_time(keywords, timeframe)


def find_emerging_trends(keywords: List[str], threshold: float = 50.0) -> Dict[str, Any]:
    """Convenience function for detecting emerging trends."""
    return trends_tool.detect_emerging_trends(keywords, threshold)


def compare_market_interest(keywords: List[str]) -> Dict[str, Any]:
    """Convenience function for comparing keywords."""
    return trends_tool.compare_keywords(keywords)
