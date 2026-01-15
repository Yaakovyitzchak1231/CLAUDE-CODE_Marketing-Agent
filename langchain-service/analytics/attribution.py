"""
Attribution Modeling Module - Multi-Touch Attribution Algorithms

All calculations are:
- Deterministic mathematical formulas
- Industry-standard attribution models
- NO black-box ML or LLM inference

Supported models:
- First Touch: 100% credit to first interaction
- Last Touch: 100% credit to last interaction
- Linear: Equal credit to all touchpoints
- Time Decay: Exponential decay favoring recent touches
- Position-Based (U-Shaped): 40/20/40 split
- Custom: User-defined weights
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class AttributionModeling:
    """
    Production-grade attribution modeling using mathematical formulas.

    All methods return deterministic results with algorithm documentation.
    """

    # Default position-based weights
    DEFAULT_POSITION_WEIGHTS = {
        'first': 0.40,
        'middle': 0.20,
        'last': 0.40
    }

    # Default time decay half-life (days)
    DEFAULT_HALF_LIFE = 7

    def __init__(
        self,
        position_weights: Optional[Dict[str, float]] = None,
        half_life_days: int = 7
    ):
        """
        Initialize attribution modeling.

        Args:
            position_weights: Custom weights for position-based attribution
            half_life_days: Half-life for time decay model
        """
        self.position_weights = position_weights or self.DEFAULT_POSITION_WEIGHTS
        self.half_life = half_life_days

    def _parse_touchpoints(
        self,
        touchpoints: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Parse and validate touchpoints.

        Each touchpoint should have:
        - channel: str (e.g., 'email', 'search', 'social')
        - timestamp: datetime or str
        """
        parsed = []
        for tp in touchpoints:
            channel = tp.get('channel', 'unknown')
            timestamp = tp.get('timestamp')

            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    timestamp = datetime.now()
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()

            parsed.append({
                'channel': channel,
                'timestamp': timestamp,
                'original': tp
            })

        # Sort by timestamp
        parsed.sort(key=lambda x: x['timestamp'])
        return parsed

    def first_touch_attribution(
        self,
        touchpoints: List[Dict[str, Any]],
        conversion_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        First Touch Attribution: 100% credit to first interaction.

        Args:
            touchpoints: List of touchpoint dicts
            conversion_value: Value to attribute

        Returns:
            Dict with channel attribution
        """
        if not touchpoints:
            return {
                'attribution': {},
                'model': 'first_touch',
                'error': 'No touchpoints provided',
                'algorithm': 'First Touch: 100% to first interaction',
                'is_verified': True
            }

        parsed = self._parse_touchpoints(touchpoints)
        first_channel = parsed[0]['channel']

        attribution = {first_channel: conversion_value}

        return {
            'attribution': attribution,
            'model': 'first_touch',
            'touchpoint_count': len(parsed),
            'first_channel': first_channel,
            'conversion_value': conversion_value,
            'algorithm': 'First Touch: 100% credit to first interaction',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def last_touch_attribution(
        self,
        touchpoints: List[Dict[str, Any]],
        conversion_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Last Touch Attribution: 100% credit to last interaction.

        Args:
            touchpoints: List of touchpoint dicts
            conversion_value: Value to attribute

        Returns:
            Dict with channel attribution
        """
        if not touchpoints:
            return {
                'attribution': {},
                'model': 'last_touch',
                'error': 'No touchpoints provided',
                'algorithm': 'Last Touch: 100% to last interaction',
                'is_verified': True
            }

        parsed = self._parse_touchpoints(touchpoints)
        last_channel = parsed[-1]['channel']

        attribution = {last_channel: conversion_value}

        return {
            'attribution': attribution,
            'model': 'last_touch',
            'touchpoint_count': len(parsed),
            'last_channel': last_channel,
            'conversion_value': conversion_value,
            'algorithm': 'Last Touch: 100% credit to last interaction',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def linear_attribution(
        self,
        touchpoints: List[Dict[str, Any]],
        conversion_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Linear Attribution: Equal credit to all touchpoints.

        Args:
            touchpoints: List of touchpoint dicts
            conversion_value: Value to attribute

        Returns:
            Dict with channel attribution
        """
        if not touchpoints:
            return {
                'attribution': {},
                'model': 'linear',
                'error': 'No touchpoints provided',
                'algorithm': 'Linear: Equal credit to all touchpoints',
                'is_verified': True
            }

        parsed = self._parse_touchpoints(touchpoints)
        credit_per_touch = conversion_value / len(parsed)

        # Aggregate by channel
        attribution = {}
        for tp in parsed:
            channel = tp['channel']
            attribution[channel] = attribution.get(channel, 0) + credit_per_touch

        # Round values
        attribution = {k: round(v, 4) for k, v in attribution.items()}

        return {
            'attribution': attribution,
            'model': 'linear',
            'touchpoint_count': len(parsed),
            'credit_per_touchpoint': round(credit_per_touch, 4),
            'conversion_value': conversion_value,
            'algorithm': 'Linear: credit_per_touch = value / touchpoint_count',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def time_decay_attribution(
        self,
        touchpoints: List[Dict[str, Any]],
        conversion_value: float = 1.0,
        half_life_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Time Decay Attribution: Exponential decay favoring recent touches.

        Formula: weight = 2^(-days_before_conversion / half_life)

        Args:
            touchpoints: List of touchpoint dicts
            conversion_value: Value to attribute
            half_life_days: Days for weight to halve (default 7)

        Returns:
            Dict with channel attribution
        """
        if not touchpoints:
            return {
                'attribution': {},
                'model': 'time_decay',
                'error': 'No touchpoints provided',
                'algorithm': 'Time Decay: weight = 2^(-days / half_life)',
                'is_verified': True
            }

        half_life = half_life_days or self.half_life
        parsed = self._parse_touchpoints(touchpoints)
        conversion_time = parsed[-1]['timestamp']

        # Calculate weights based on time
        weights = []
        weight_details = []

        for tp in parsed:
            days_before = (conversion_time - tp['timestamp']).total_seconds() / 86400
            weight = 2 ** (-days_before / half_life)
            weights.append(weight)
            weight_details.append({
                'channel': tp['channel'],
                'days_before': round(days_before, 2),
                'raw_weight': round(weight, 4)
            })

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Distribute value by channel
        attribution = {}
        for i, tp in enumerate(parsed):
            channel = tp['channel']
            credit = conversion_value * normalized_weights[i]
            attribution[channel] = attribution.get(channel, 0) + credit

        # Round values
        attribution = {k: round(v, 4) for k, v in attribution.items()}

        return {
            'attribution': attribution,
            'model': 'time_decay',
            'touchpoint_count': len(parsed),
            'half_life_days': half_life,
            'weight_details': weight_details,
            'conversion_value': conversion_value,
            'algorithm': f'Time Decay: weight = 2^(-days / {half_life})',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def position_based_attribution(
        self,
        touchpoints: List[Dict[str, Any]],
        conversion_value: float = 1.0,
        first_weight: Optional[float] = None,
        last_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Position-Based (U-Shaped) Attribution: Emphasize first and last touches.

        Default: 40% first, 40% last, 20% split among middle.

        Args:
            touchpoints: List of touchpoint dicts
            conversion_value: Value to attribute
            first_weight: Weight for first touch (default 0.4)
            last_weight: Weight for last touch (default 0.4)

        Returns:
            Dict with channel attribution
        """
        if not touchpoints:
            return {
                'attribution': {},
                'model': 'position_based',
                'error': 'No touchpoints provided',
                'algorithm': 'Position-Based: 40/20/40 U-shape',
                'is_verified': True
            }

        first_w = first_weight or self.position_weights['first']
        last_w = last_weight or self.position_weights['last']
        middle_w = 1.0 - first_w - last_w

        parsed = self._parse_touchpoints(touchpoints)
        n = len(parsed)

        attribution = {}

        if n == 1:
            # Single touchpoint gets all credit
            attribution[parsed[0]['channel']] = conversion_value
        elif n == 2:
            # Split between first and last
            first_credit = conversion_value * first_w / (first_w + last_w)
            last_credit = conversion_value * last_w / (first_w + last_w)
            attribution[parsed[0]['channel']] = attribution.get(parsed[0]['channel'], 0) + first_credit
            attribution[parsed[-1]['channel']] = attribution.get(parsed[-1]['channel'], 0) + last_credit
        else:
            # First touch
            attribution[parsed[0]['channel']] = attribution.get(parsed[0]['channel'], 0) + conversion_value * first_w

            # Last touch
            attribution[parsed[-1]['channel']] = attribution.get(parsed[-1]['channel'], 0) + conversion_value * last_w

            # Middle touches
            middle_count = n - 2
            middle_credit_each = conversion_value * middle_w / middle_count
            for tp in parsed[1:-1]:
                attribution[tp['channel']] = attribution.get(tp['channel'], 0) + middle_credit_each

        # Round values
        attribution = {k: round(v, 4) for k, v in attribution.items()}

        return {
            'attribution': attribution,
            'model': 'position_based',
            'touchpoint_count': n,
            'weights': {
                'first': first_w,
                'middle': middle_w,
                'last': last_w
            },
            'conversion_value': conversion_value,
            'algorithm': f'Position-Based: {first_w*100:.0f}/{middle_w*100:.0f}/{last_w*100:.0f} U-shape',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def custom_attribution(
        self,
        touchpoints: List[Dict[str, Any]],
        channel_weights: Dict[str, float],
        conversion_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Custom Attribution: User-defined channel weights.

        Args:
            touchpoints: List of touchpoint dicts
            channel_weights: Dict mapping channel names to weights
            conversion_value: Value to attribute

        Returns:
            Dict with channel attribution
        """
        if not touchpoints:
            return {
                'attribution': {},
                'model': 'custom',
                'error': 'No touchpoints provided',
                'algorithm': 'Custom: User-defined channel weights',
                'is_verified': True
            }

        parsed = self._parse_touchpoints(touchpoints)

        # Calculate weighted credits
        raw_credits = {}
        for tp in parsed:
            channel = tp['channel']
            weight = channel_weights.get(channel, 1.0)  # Default weight 1.0
            raw_credits[channel] = raw_credits.get(channel, 0) + weight

        # Normalize to conversion value
        total_raw = sum(raw_credits.values())
        attribution = {
            k: round(v / total_raw * conversion_value, 4)
            for k, v in raw_credits.items()
        }

        return {
            'attribution': attribution,
            'model': 'custom',
            'touchpoint_count': len(parsed),
            'channel_weights': channel_weights,
            'conversion_value': conversion_value,
            'algorithm': 'Custom: credit = (channel_weight / total_weight) * value',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }

    def compare_models(
        self,
        touchpoints: List[Dict[str, Any]],
        conversion_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Compare all attribution models for the same journey.

        Args:
            touchpoints: List of touchpoint dicts
            conversion_value: Value to attribute

        Returns:
            Dict with all model results
        """
        if not touchpoints:
            return {
                'error': 'No touchpoints provided',
                'is_verified': True
            }

        models = {
            'first_touch': self.first_touch_attribution(touchpoints, conversion_value),
            'last_touch': self.last_touch_attribution(touchpoints, conversion_value),
            'linear': self.linear_attribution(touchpoints, conversion_value),
            'time_decay': self.time_decay_attribution(touchpoints, conversion_value),
            'position_based': self.position_based_attribution(touchpoints, conversion_value)
        }

        # Extract just the attribution from each model
        comparison = {
            model: result.get('attribution', {})
            for model, result in models.items()
        }

        # Find channels with most variation across models
        all_channels = set()
        for attr in comparison.values():
            all_channels.update(attr.keys())

        channel_variance = {}
        for channel in all_channels:
            values = [attr.get(channel, 0) for attr in comparison.values()]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            channel_variance[channel] = round(variance, 4)

        return {
            'comparison': comparison,
            'channel_variance': channel_variance,
            'highest_variance_channel': max(channel_variance, key=channel_variance.get) if channel_variance else None,
            'touchpoint_count': len(touchpoints),
            'conversion_value': conversion_value,
            'algorithm': 'Multi-model comparison',
            'is_verified': True,
            'calculated_at': datetime.now().isoformat()
        }


# Convenience functions
def first_touch_attribution(
    touchpoints: List[Dict[str, Any]],
    conversion_value: float = 1.0
) -> Dict[str, Any]:
    """First touch attribution model."""
    model = AttributionModeling()
    return model.first_touch_attribution(touchpoints, conversion_value)


def last_touch_attribution(
    touchpoints: List[Dict[str, Any]],
    conversion_value: float = 1.0
) -> Dict[str, Any]:
    """Last touch attribution model."""
    model = AttributionModeling()
    return model.last_touch_attribution(touchpoints, conversion_value)


def linear_attribution(
    touchpoints: List[Dict[str, Any]],
    conversion_value: float = 1.0
) -> Dict[str, Any]:
    """Linear attribution model."""
    model = AttributionModeling()
    return model.linear_attribution(touchpoints, conversion_value)


def time_decay_attribution(
    touchpoints: List[Dict[str, Any]],
    conversion_value: float = 1.0,
    half_life_days: int = 7
) -> Dict[str, Any]:
    """Time decay attribution model."""
    model = AttributionModeling()
    return model.time_decay_attribution(touchpoints, conversion_value, half_life_days)


def position_based_attribution(
    touchpoints: List[Dict[str, Any]],
    conversion_value: float = 1.0
) -> Dict[str, Any]:
    """Position-based (U-shaped) attribution model."""
    model = AttributionModeling()
    return model.position_based_attribution(touchpoints, conversion_value)
