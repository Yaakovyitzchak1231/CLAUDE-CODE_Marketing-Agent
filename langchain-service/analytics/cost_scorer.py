"""
Cost Scorer Module - API Cost Tracking and Budget Analysis

All calculations are:
- Formula-based pricing
- Industry-standard API rates
- NO LLM inference

Tracking:
- Image generation (DALL-E, Midjourney)
- Video generation (Runway, Pika)
- LLM API calls (Claude, GPT-4, GPT-3.5)
- Budget monitoring and optimization
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CostScorer:
    """
    Production-grade API cost tracking using deterministic pricing.

    All methods return deterministic results with algorithm documentation.
    """

    # DALL-E 3 Pricing (as of 2024)
    DALLE_PRICING = {
        'standard': {
            '1024x1024': 0.040,
            '1024x1792': 0.080,
            '1792x1024': 0.080,
        },
        'hd': {
            '1024x1024': 0.080,
            '1024x1792': 0.120,
            '1792x1024': 0.120,
        }
    }

    # Midjourney Pricing (approximate, varies by subscription)
    MIDJOURNEY_PRICING = {
        'relax': 0.01,
        'fast': 0.04,
        'turbo': 0.08,
    }

    # Runway ML Pricing (per second)
    RUNWAY_PRICING = {
        'gen2': 0.05,
        'gen3': 0.10,
    }

    # Pika Pricing (per second)
    PIKA_PRICING = {
        'standard': 0.07,
        'pro': 0.05,
    }

    # LLM Pricing (per 1K tokens)
    LLM_PRICING = {
        'claude-3-opus': {
            'input': 0.015,
            'output': 0.075,
        },
        'claude-3-sonnet': {
            'input': 0.003,
            'output': 0.015,
        },
        'claude-3-haiku': {
            'input': 0.00025,
            'output': 0.00125,
        },
        'gpt-4': {
            'input': 0.03,
            'output': 0.06,
        },
        'gpt-4-turbo': {
            'input': 0.01,
            'output': 0.03,
        },
        'gpt-3.5-turbo': {
            'input': 0.0015,
            'output': 0.002,
        },
    }

    # Budget thresholds (percentage of monthly budget)
    # Thresholds define the UPPER bound of each zone
    BUDGET_THRESHOLDS = {
        'safe': 0.50,          # Under 50% - safe zone
        'warning': 0.50,       # 50% threshold - warning starts here
        'critical': 0.75,      # 75% threshold - critical starts here
        'exceeded': 0.90,      # 90% threshold - exceeded starts here
    }

    def __init__(
        self,
        monthly_image_budget: Optional[float] = None,
        monthly_video_budget: Optional[float] = None,
        monthly_total_budget: Optional[float] = None
    ):
        """
        Initialize cost scorer.

        Args:
            monthly_image_budget: Monthly budget for image generation
            monthly_video_budget: Monthly budget for video generation
            monthly_total_budget: Total monthly API budget
        """
        self.monthly_image_budget = monthly_image_budget or 1000.0
        self.monthly_video_budget = monthly_video_budget or 2000.0
        self.monthly_total_budget = monthly_total_budget or 5000.0

    def calculate_dalle_cost(self, size: str, quality: str) -> Dict[str, Any]:
        """
        Calculate DALL-E 3 generation cost.

        Formula: Fixed pricing based on size and quality tier

        Args:
            size: Image size (1024x1024, 1024x1792, 1792x1024)
            quality: Quality tier (standard, hd)

        Returns:
            Dict with cost, pricing_tier, and metadata
        """
        if quality not in self.DALLE_PRICING:
            logger.warning(f"Invalid quality '{quality}', defaulting to 'standard'")
            quality = 'standard'

        if size not in self.DALLE_PRICING[quality]:
            logger.warning(f"Invalid size '{size}', defaulting to '1024x1024'")
            size = '1024x1024'

        cost = self.DALLE_PRICING[quality][size]

        return {
            'cost': cost,
            'provider': 'dalle3',
            'size': size,
            'quality': quality,
            'pricing_tier': quality,
            'algorithm': 'Fixed pricing by size and quality tier',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_midjourney_cost(self, process_mode: str = 'relax') -> Dict[str, Any]:
        """
        Calculate Midjourney generation cost.

        Formula: Fixed pricing based on process mode

        Args:
            process_mode: Processing mode (relax, fast, turbo)

        Returns:
            Dict with cost, mode, and metadata
        """
        if process_mode not in self.MIDJOURNEY_PRICING:
            logger.warning(f"Invalid mode '{process_mode}', defaulting to 'relax'")
            process_mode = 'relax'

        cost = self.MIDJOURNEY_PRICING[process_mode]

        return {
            'cost': cost,
            'provider': 'midjourney',
            'process_mode': process_mode,
            'algorithm': 'Fixed pricing by process mode',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_runway_cost(self, duration: int, model: str = 'gen3') -> Dict[str, Any]:
        """
        Calculate Runway ML video generation cost.

        Formula: duration_seconds * price_per_second

        Args:
            duration: Video duration in seconds
            model: Model version (gen2, gen3)

        Returns:
            Dict with cost, duration, and metadata
        """
        if model not in self.RUNWAY_PRICING:
            logger.warning(f"Invalid model '{model}', defaulting to 'gen3'")
            model = 'gen3'

        price_per_second = self.RUNWAY_PRICING[model]
        cost = duration * price_per_second

        return {
            'cost': round(cost, 4),
            'provider': 'runway',
            'duration': duration,
            'model': model,
            'price_per_second': price_per_second,
            'algorithm': 'cost = duration * price_per_second',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_pika_cost(self, duration: int, tier: str = 'standard') -> Dict[str, Any]:
        """
        Calculate Pika video generation cost.

        Formula: duration_seconds * price_per_second

        Args:
            duration: Video duration in seconds
            tier: Subscription tier (standard, pro)

        Returns:
            Dict with cost, duration, and metadata
        """
        if tier not in self.PIKA_PRICING:
            logger.warning(f"Invalid tier '{tier}', defaulting to 'standard'")
            tier = 'standard'

        price_per_second = self.PIKA_PRICING[tier]
        cost = duration * price_per_second

        return {
            'cost': round(cost, 4),
            'provider': 'pika',
            'duration': duration,
            'tier': tier,
            'price_per_second': price_per_second,
            'algorithm': 'cost = duration * price_per_second',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_llm_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        Calculate LLM API call cost.

        Formula: (input_tokens/1000 * input_rate) + (output_tokens/1000 * output_rate)

        Args:
            model: LLM model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dict with cost, token breakdown, and metadata
        """
        if model not in self.LLM_PRICING:
            logger.warning(f"Unknown model '{model}', cost calculation unavailable")
            return {
                'cost': 0.0,
                'error': f"Unknown model '{model}'",
                'is_verified': False,
                'calculated_at': datetime.now().isoformat()
            }

        pricing = self.LLM_PRICING[model]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        total_cost = input_cost + output_cost

        return {
            'cost': round(total_cost, 6),
            'provider': 'llm',
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'pricing_rates': pricing,
            'algorithm': 'cost = (input_tokens/1000 * input_rate) + (output_tokens/1000 * output_rate)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_budget_status(
        self,
        current_spending: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate budget utilization and status.

        Formula: utilization = current_spending / budget * 100

        Args:
            current_spending: Dict with 'image', 'video', 'total' spending

        Returns:
            Dict with status, utilization, and recommendations
        """
        image_spending = current_spending.get('image', 0.0)
        video_spending = current_spending.get('video', 0.0)
        total_spending = current_spending.get('total', 0.0)

        # Calculate utilization percentages
        image_utilization = (image_spending / self.monthly_image_budget) * 100
        video_utilization = (video_spending / self.monthly_video_budget) * 100
        total_utilization = (total_spending / self.monthly_total_budget) * 100

        # Determine status for each category
        def get_status(utilization: float) -> str:
            if utilization >= self.BUDGET_THRESHOLDS['exceeded'] * 100:
                return 'exceeded'
            elif utilization >= self.BUDGET_THRESHOLDS['critical'] * 100:
                return 'critical'
            elif utilization >= self.BUDGET_THRESHOLDS['warning'] * 100:
                return 'warning'
            else:
                return 'safe'

        image_status = get_status(image_utilization)
        video_status = get_status(video_utilization)
        total_status = get_status(total_utilization)

        # Generate recommendations
        recommendations = []
        if image_status in ['critical', 'exceeded']:
            recommendations.append(
                f'Image generation budget {image_status} '
                f'({image_utilization:.1f}% used). Consider using lower quality settings.'
            )
        if video_status in ['critical', 'exceeded']:
            recommendations.append(
                f'Video generation budget {video_status} '
                f'({video_utilization:.1f}% used). Consider reducing video duration or quality.'
            )
        if total_status in ['critical', 'exceeded']:
            recommendations.append(
                f'Total API budget {total_status} '
                f'({total_utilization:.1f}% used). Review all API usage immediately.'
            )

        return {
            'image': {
                'spending': image_spending,
                'budget': self.monthly_image_budget,
                'utilization_percent': round(image_utilization, 2),
                'remaining': self.monthly_image_budget - image_spending,
                'status': image_status
            },
            'video': {
                'spending': video_spending,
                'budget': self.monthly_video_budget,
                'utilization_percent': round(video_utilization, 2),
                'remaining': self.monthly_video_budget - video_spending,
                'status': video_status
            },
            'total': {
                'spending': total_spending,
                'budget': self.monthly_total_budget,
                'utilization_percent': round(total_utilization, 2),
                'remaining': self.monthly_total_budget - total_spending,
                'status': total_status
            },
            'recommendations': recommendations,
            'thresholds': self.BUDGET_THRESHOLDS,
            'algorithm': 'utilization = (spending / budget) * 100',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def calculate_cost_efficiency(
        self,
        costs: List[Dict[str, Any]],
        performance_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate cost efficiency score (0-100).

        Multi-factor scoring:
        - Provider Mix (0-30 points): Optimal use of cost-effective providers
        - Budget Adherence (0-40 points): Staying within budget limits
        - Performance/Cost Ratio (0-30 points): Results quality vs spend

        Args:
            costs: List of cost records with provider and amount
            performance_metrics: Optional dict with engagement, conversion rates

        Returns:
            Dict with efficiency_score, breakdown, and optimization suggestions
        """
        if not costs:
            return {
                'efficiency_score': 0,
                'error': 'No cost data provided',
                'is_verified': True,
                'calculated_at': datetime.now().isoformat()
            }

        scores = {}

        # 1. Provider Mix Score (0-30 points)
        provider_counts = {}
        total_cost = 0.0

        for cost_record in costs:
            provider = cost_record.get('provider', 'unknown')
            amount = cost_record.get('cost', 0.0)
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
            total_cost += amount

        # Reward diverse provider usage (not over-relying on expensive options)
        provider_diversity = len(provider_counts)
        if provider_diversity >= 4:
            scores['provider_mix'] = 30
        elif provider_diversity >= 3:
            scores['provider_mix'] = 25
        elif provider_diversity >= 2:
            scores['provider_mix'] = 20
        else:
            scores['provider_mix'] = 10

        # 2. Budget Adherence Score (0-40 points)
        total_utilization = (total_cost / self.monthly_total_budget) * 100

        if total_utilization <= 50:
            scores['budget_adherence'] = 40
        elif total_utilization <= 75:
            scores['budget_adherence'] = 30
        elif total_utilization <= 90:
            scores['budget_adherence'] = 20
        elif total_utilization <= 100:
            scores['budget_adherence'] = 10
        else:
            scores['budget_adherence'] = 0

        # 3. Performance/Cost Ratio (0-30 points)
        if performance_metrics:
            engagement_rate = performance_metrics.get('engagement_rate', 0)
            conversion_rate = performance_metrics.get('conversion_rate', 0)

            # High performance with cost = good efficiency
            avg_cost_per_item = total_cost / len(costs) if costs else 0

            # Calculate performance score (simplified)
            performance_score = (engagement_rate + conversion_rate) / 2

            if avg_cost_per_item > 0:
                efficiency_ratio = performance_score / avg_cost_per_item
                # Scale to 0-30 points (arbitrary scaling for demo)
                scores['performance_cost_ratio'] = min(30, efficiency_ratio * 10)
            else:
                scores['performance_cost_ratio'] = 15
        else:
            scores['performance_cost_ratio'] = 15  # Neutral score if no metrics

        # Calculate total efficiency score
        efficiency_score = sum(scores.values())

        # Generate optimization suggestions
        suggestions = []
        if scores['provider_mix'] < 20:
            suggestions.append('Consider using a more diverse mix of API providers to optimize costs.')
        if scores['budget_adherence'] < 30:
            suggestions.append('Budget utilization is high. Review API usage patterns and consider cost reduction.')
        if scores['performance_cost_ratio'] < 20 and performance_metrics:
            suggestions.append('Cost-to-performance ratio could be improved. Test more cost-effective providers.')

        return {
            'efficiency_score': round(efficiency_score, 2),
            'grade': self._get_efficiency_grade(efficiency_score),
            'component_scores': scores,
            'total_cost': round(total_cost, 2),
            'total_items': len(costs),
            'avg_cost_per_item': round(total_cost / len(costs), 4) if costs else 0,
            'provider_distribution': provider_counts,
            'optimization_suggestions': suggestions,
            'algorithm': 'Multi-factor: provider_mix(30) + budget_adherence(40) + performance_ratio(30)',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def _get_efficiency_grade(self, score: float) -> str:
        """Convert efficiency score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


def calculate_api_cost(
    provider: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to calculate API costs.

    Args:
        provider: API provider (dalle, midjourney, runway, pika, llm)
        **kwargs: Provider-specific parameters

    Returns:
        Cost calculation result
    """
    scorer = CostScorer()

    if provider == 'dalle':
        return scorer.calculate_dalle_cost(
            size=kwargs.get('size', '1024x1024'),
            quality=kwargs.get('quality', 'standard')
        )
    elif provider == 'midjourney':
        return scorer.calculate_midjourney_cost(
            process_mode=kwargs.get('process_mode', 'relax')
        )
    elif provider == 'runway':
        return scorer.calculate_runway_cost(
            duration=kwargs.get('duration', 4),
            model=kwargs.get('model', 'gen3')
        )
    elif provider == 'pika':
        return scorer.calculate_pika_cost(
            duration=kwargs.get('duration', 3),
            tier=kwargs.get('tier', 'standard')
        )
    elif provider == 'llm':
        return scorer.calculate_llm_cost(
            model=kwargs.get('model', 'gpt-3.5-turbo'),
            input_tokens=kwargs.get('input_tokens', 0),
            output_tokens=kwargs.get('output_tokens', 0)
        )
    else:
        logger.error(f"Unknown provider '{provider}'")
        return {
            'cost': 0.0,
            'error': f"Unknown provider '{provider}'",
            'is_verified': False
        }
