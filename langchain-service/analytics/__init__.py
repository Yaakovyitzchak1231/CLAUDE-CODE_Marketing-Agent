"""
Analytics Module - Production-Grade Marketing Analytics

This module provides mathematically-grounded algorithms for:
- Engagement scoring
- Brand voice analysis
- Anti-AI detection
- Trend scoring
- SEO optimization
- A/B testing
- Attribution modeling
- Cost tracking

ALL algorithms are:
- Deterministic (same input = same output)
- Auditable (algorithm documented in output)
- Verifiable (data sources tracked)
- NOT hallucinated (no LLM inference for scoring)

Every output includes:
- `algorithm`: Description of calculation method
- `is_verified`: True (indicates real data, not LLM)
- `confidence`: Based on data source count
"""

from .engagement_scorer import (
    EngagementScorer,
    calculate_engagement_rate,
    calculate_content_effectiveness,
)

from .brand_voice_analyzer import (
    BrandVoiceAnalyzer,
    analyze_brand_voice,
    calculate_readability_score,
)

from .ai_detection import (
    AIDetector,
    calculate_ai_likelihood,
    detect_ngram_repetition,
    calculate_burstiness,
)

from .brand_fingerprint import (
    BrandFingerprint,
    calculate_brand_alignment,
)

from .trend_scorer import (
    TrendScorer,
    calculate_trend_score,
    calculate_momentum,
)

from .seo_scorer import (
    SEOScorer,
    calculate_seo_score,
)

from .ab_testing import (
    ABTestFramework,
    analyze_ab_test,
    calculate_sample_size,
)

from .attribution import (
    AttributionModeling,
    first_touch_attribution,
    last_touch_attribution,
    linear_attribution,
    time_decay_attribution,
    position_based_attribution,
)

from .cost_scorer import (
    CostScorer,
    calculate_api_cost,
)

__all__ = [
    # Engagement
    'EngagementScorer',
    'calculate_engagement_rate',
    'calculate_content_effectiveness',

    # Brand Voice
    'BrandVoiceAnalyzer',
    'analyze_brand_voice',
    'calculate_readability_score',

    # AI Detection
    'AIDetector',
    'calculate_ai_likelihood',
    'detect_ngram_repetition',
    'calculate_burstiness',

    # Brand Fingerprint
    'BrandFingerprint',
    'calculate_brand_alignment',

    # Trend Scoring
    'TrendScorer',
    'calculate_trend_score',
    'calculate_momentum',

    # SEO
    'SEOScorer',
    'calculate_seo_score',

    # A/B Testing
    'ABTestFramework',
    'analyze_ab_test',
    'calculate_sample_size',

    # Attribution
    'AttributionModeling',
    'first_touch_attribution',
    'last_touch_attribution',
    'linear_attribution',
    'time_decay_attribution',
    'position_based_attribution',

    # Cost Tracking
    'CostScorer',
    'calculate_api_cost',
]
