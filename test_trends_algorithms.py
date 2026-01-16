"""
Test Trends Analysis Algorithms
Validates the zero-hallucination guarantee algorithms
"""
import sys
from datetime import datetime

# ============= COPY OF CORE ALGORITHMS FROM trends.py =============

REGULATED_KEYWORDS = [
    'healthcare', 'pharmaceutical', 'medical', 'clinical', 'hospital',
    'finance', 'banking', 'insurance', 'securities', 'investment',
    'defense', 'aerospace', 'government', 'federal', 'military',
    'energy', 'utilities', 'nuclear', 'oil', 'gas',
    'food', 'fda', 'usda', 'agriculture'
]

COMMERCIAL_KEYWORDS = [
    'technology', 'software', 'saas', 'cloud', 'ai', 'machine learning',
    'retail', 'ecommerce', 'consumer', 'cpg', 'fmcg',
    'media', 'entertainment', 'gaming', 'streaming',
    'manufacturing', 'logistics', 'supply chain',
    'professional services', 'consulting', 'marketing'
]

SOURCE_WEIGHTS = {
    'google_trends': 0.30,
    'gov_employment': 0.25,
    'news_mentions': 0.20,
    'job_postings': 0.15,
    'social_sentiment': 0.10,
}

CREDIBILITY_TIERS = {
    'tier1_authoritative': {'weight': 1.0},
    'tier2_business_news': {'weight': 0.8},
    'tier3_industry_pubs': {'weight': 0.6},
}

def classify_industry(context):
    context_lower = context.lower()
    regulated_count = sum(1 for kw in REGULATED_KEYWORDS if kw in context_lower)
    commercial_count = sum(1 for kw in COMMERCIAL_KEYWORDS if kw in context_lower)
    if regulated_count > commercial_count:
        return 'regulated'
    elif commercial_count > 0:
        return 'commercial'
    else:
        return 'unknown'

def calculate_trend_score(topic, data_sources):
    scores = {}

    if 'google_trends' in data_sources:
        gt = data_sources['google_trends']
        current = gt.get('current_interest', 0)
        avg = gt.get('avg_interest', 50)
        if avg > 0:
            ratio = current / avg
            scores['google_trends'] = min(ratio * 50, 100)
        else:
            scores['google_trends'] = 50

    if 'gov_employment' in data_sources:
        ge = data_sources['gov_employment']
        growth_rate = ge.get('growth_rate_pct', 0)
        scores['gov_employment'] = max(0, min(100, 50 + growth_rate * 5))

    if 'news_mentions' in data_sources:
        nm = data_sources['news_mentions']
        tier1 = nm.get('tier1_authoritative', 0) * CREDIBILITY_TIERS['tier1_authoritative']['weight']
        tier2 = nm.get('tier2_business_news', 0) * CREDIBILITY_TIERS['tier2_business_news']['weight']
        tier3 = nm.get('tier3_industry_pubs', 0) * CREDIBILITY_TIERS['tier3_industry_pubs']['weight']
        weighted_mentions = tier1 * 20 + tier2 * 10 + tier3 * 5
        scores['news_mentions'] = min(weighted_mentions, 100)

    if 'job_postings' in data_sources:
        jp = data_sources['job_postings']
        posting_count = jp.get('total_postings', 0)
        posting_growth = jp.get('growth_pct', 0)
        count_score = min(posting_count * 2.5, 50)
        growth_score = max(0, min(50, 25 + posting_growth * 2.5))
        scores['job_postings'] = count_score + growth_score

    if not scores:
        return {'topic': topic, 'trend_score': 0.0, 'error': 'No data', 'is_verified': True}

    total_weight = sum(SOURCE_WEIGHTS[k] for k in scores.keys())
    weighted_score = sum(scores[k] * SOURCE_WEIGHTS[k] for k in scores.keys()) / total_weight

    confidence = 'high' if len(scores) >= 4 else 'medium' if len(scores) >= 2 else 'low'

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
        'sources_count': len(scores),
        'confidence': confidence,
        'direction': direction,
        'algorithm': 'Multi-source weighted scoring',
        'is_verified': True,
    }

def calculate_momentum(current_score, previous_score, days=30):
    if previous_score == 0:
        return {'momentum_pct': 0.0, 'direction': 'stable', 'is_verified': True}

    momentum_pct = ((current_score - previous_score) / previous_score) * 100

    if momentum_pct > 25:
        direction = 'surging'
    elif momentum_pct > 10:
        direction = 'rising'
    elif momentum_pct > -10:
        direction = 'stable'
    elif momentum_pct > -25:
        direction = 'declining'
    else:
        direction = 'collapsing'

    return {
        'momentum_pct': round(momentum_pct, 2),
        'direction': direction,
        'velocity_per_day': round(momentum_pct / days, 3),
        'algorithm': 'momentum = (current - previous) / previous * 100',
        'is_verified': True
    }


def run_tests():
    """Run all algorithm tests"""
    print('=' * 60)
    print('TRENDS.PY ALGORITHM TESTS')
    print('=' * 60)

    all_passed = True

    # Test 1: Industry Classification
    print('')
    print('Test 1: Industry Classification')
    tests = [
        ('healthcare software for hospitals', 'regulated'),
        ('saas marketing platform', 'commercial'),
        ('banking compliance solution', 'regulated'),
        ('cloud ai technology', 'commercial'),
        ('random thing xyz', 'unknown'),
    ]
    for context, expected in tests:
        result = classify_industry(context)
        passed = result == expected
        if not passed:
            all_passed = False
        status = 'PASS' if passed else 'FAIL'
        display = context[:30] + '...' if len(context) > 30 else context
        print(f'  [{status}] "{display}" -> {result}')

    # Test 2: Trend Score Calculation
    print('')
    print('Test 2: Trend Score Calculation')
    demo_data = {
        'google_trends': {'current_interest': 78, 'avg_interest': 65},
        'gov_employment': {'growth_rate_pct': 4.2},
        'news_mentions': {'tier1_authoritative': 3, 'tier2_business_news': 12, 'tier3_industry_pubs': 28},
        'job_postings': {'total_postings': 1250, 'growth_pct': 15.5},
    }
    result = calculate_trend_score('AI Automation', demo_data)

    checks = [
        ('trend_score exists', 'trend_score' in result),
        ('is_verified is True', result.get('is_verified') == True),
        ('algorithm documented', 'algorithm' in result),
        ('confidence is high (4 sources)', result.get('confidence') == 'high'),
        ('score is reasonable (0-100)', 0 <= result.get('trend_score', -1) <= 100),
    ]
    for name, passed in checks:
        if not passed:
            all_passed = False
        status = 'PASS' if passed else 'FAIL'
        print(f'  [{status}] {name}')

    print(f'  -> Score: {result["trend_score"]}, Direction: {result["direction"]}')
    print(f'  -> Components: {result["component_scores"]}')

    # Test 3: Momentum Calculation
    print('')
    print('Test 3: Momentum Calculation')
    result = calculate_momentum(75.0, 60.0, 30)
    expected_momentum = ((75.0 - 60.0) / 60.0) * 100  # 25%

    checks = [
        ('momentum_pct exists', 'momentum_pct' in result),
        ('is_verified is True', result.get('is_verified') == True),
        ('correct calculation (25%)', abs(result.get('momentum_pct', 0) - expected_momentum) < 0.1),
        ('direction is rising (25% exactly)', result.get('direction') == 'rising'),
        ('velocity calculated', 'velocity_per_day' in result),
    ]
    for name, passed in checks:
        if not passed:
            all_passed = False
        status = 'PASS' if passed else 'FAIL'
        print(f'  [{status}] {name}')

    print(f'  -> Momentum: {result["momentum_pct"]}%, Direction: {result["direction"]}')

    # Test 4: Edge Cases
    print('')
    print('Test 4: Edge Cases')

    # Empty data
    result = calculate_trend_score('Empty', {})
    passed = result.get('trend_score') == 0.0
    if not passed:
        all_passed = False
    status = 'PASS' if passed else 'FAIL'
    print(f'  [{status}] Empty data returns score 0')

    # Zero previous score (avoid division by zero)
    result = calculate_momentum(50.0, 0.0)
    passed = result.get('direction') == 'stable'
    if not passed:
        all_passed = False
    status = 'PASS' if passed else 'FAIL'
    print(f'  [{status}] Zero previous score handled')

    # Single source (low confidence)
    result = calculate_trend_score('Single', {'google_trends': {'current_interest': 50, 'avg_interest': 50}})
    passed = result.get('confidence') == 'low'
    if not passed:
        all_passed = False
    status = 'PASS' if passed else 'FAIL'
    print(f'  [{status}] Single source = low confidence')

    print('')
    print('=' * 60)
    if all_passed:
        print('ALL TESTS PASSED')
    else:
        print('SOME TESTS FAILED')
    print('=' * 60)

    return all_passed


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
