"""
Cost Scorer Unit Tests

Tests all CostScorer methods with comprehensive coverage:
1. All pricing calculations are deterministic
2. Edge cases and error handling
3. Budget tracking and thresholds
4. Cost efficiency scoring
5. All outputs include 'is_verified: True'
"""

import pytest
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analytics.cost_scorer import CostScorer, calculate_api_cost


class TestCostScorer:
    """Test suite for CostScorer class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scorer = CostScorer(
            monthly_image_budget=1000.0,
            monthly_video_budget=2000.0,
            monthly_total_budget=5000.0
        )

    # ===== DALL-E Cost Tests =====

    def test_dalle_standard_1024x1024(self):
        """Test DALL-E standard quality 1024x1024 pricing"""
        result = self.scorer.calculate_dalle_cost('1024x1024', 'standard')

        assert result['cost'] == 0.040
        assert result['provider'] == 'dalle3'
        assert result['size'] == '1024x1024'
        assert result['quality'] == 'standard'
        assert result['pricing_tier'] == 'standard'
        assert result['is_verified'] is True
        assert 'algorithm' in result
        assert 'calculated_at' in result

    def test_dalle_standard_1024x1792(self):
        """Test DALL-E standard quality 1024x1792 pricing"""
        result = self.scorer.calculate_dalle_cost('1024x1792', 'standard')

        assert result['cost'] == 0.080
        assert result['size'] == '1024x1792'
        assert result['quality'] == 'standard'
        assert result['is_verified'] is True

    def test_dalle_standard_1792x1024(self):
        """Test DALL-E standard quality 1792x1024 pricing"""
        result = self.scorer.calculate_dalle_cost('1792x1024', 'standard')

        assert result['cost'] == 0.080
        assert result['size'] == '1792x1024'
        assert result['is_verified'] is True

    def test_dalle_hd_1024x1024(self):
        """Test DALL-E HD quality 1024x1024 pricing"""
        result = self.scorer.calculate_dalle_cost('1024x1024', 'hd')

        assert result['cost'] == 0.080
        assert result['quality'] == 'hd'
        assert result['is_verified'] is True

    def test_dalle_hd_1024x1792(self):
        """Test DALL-E HD quality 1024x1792 pricing"""
        result = self.scorer.calculate_dalle_cost('1024x1792', 'hd')

        assert result['cost'] == 0.120
        assert result['quality'] == 'hd'
        assert result['is_verified'] is True

    def test_dalle_hd_1792x1024(self):
        """Test DALL-E HD quality 1792x1024 pricing"""
        result = self.scorer.calculate_dalle_cost('1792x1024', 'hd')

        assert result['cost'] == 0.120
        assert result['is_verified'] is True

    def test_dalle_invalid_quality(self):
        """Test DALL-E with invalid quality defaults to standard"""
        result = self.scorer.calculate_dalle_cost('1024x1024', 'invalid')

        assert result['cost'] == 0.040
        assert result['quality'] == 'standard'
        assert result['is_verified'] is True

    def test_dalle_invalid_size(self):
        """Test DALL-E with invalid size defaults to 1024x1024"""
        result = self.scorer.calculate_dalle_cost('512x512', 'standard')

        assert result['cost'] == 0.040
        assert result['size'] == '1024x1024'
        assert result['is_verified'] is True

    # ===== Midjourney Cost Tests =====

    def test_midjourney_relax(self):
        """Test Midjourney relax mode pricing"""
        result = self.scorer.calculate_midjourney_cost('relax')

        assert result['cost'] == 0.01
        assert result['provider'] == 'midjourney'
        assert result['process_mode'] == 'relax'
        assert result['is_verified'] is True
        assert 'algorithm' in result

    def test_midjourney_fast(self):
        """Test Midjourney fast mode pricing"""
        result = self.scorer.calculate_midjourney_cost('fast')

        assert result['cost'] == 0.04
        assert result['process_mode'] == 'fast'
        assert result['is_verified'] is True

    def test_midjourney_turbo(self):
        """Test Midjourney turbo mode pricing"""
        result = self.scorer.calculate_midjourney_cost('turbo')

        assert result['cost'] == 0.08
        assert result['process_mode'] == 'turbo'
        assert result['is_verified'] is True

    def test_midjourney_invalid_mode(self):
        """Test Midjourney with invalid mode defaults to relax"""
        result = self.scorer.calculate_midjourney_cost('invalid')

        assert result['cost'] == 0.01
        assert result['process_mode'] == 'relax'
        assert result['is_verified'] is True

    # ===== Runway Cost Tests =====

    def test_runway_gen2(self):
        """Test Runway Gen2 pricing"""
        result = self.scorer.calculate_runway_cost(4, 'gen2')

        assert result['cost'] == 0.20
        assert result['provider'] == 'runway'
        assert result['duration'] == 4
        assert result['model'] == 'gen2'
        assert result['price_per_second'] == 0.05
        assert result['is_verified'] is True
        assert 'algorithm' in result

    def test_runway_gen3(self):
        """Test Runway Gen3 pricing"""
        result = self.scorer.calculate_runway_cost(10, 'gen3')

        assert result['cost'] == 1.0
        assert result['model'] == 'gen3'
        assert result['price_per_second'] == 0.10
        assert result['is_verified'] is True

    def test_runway_zero_duration(self):
        """Test Runway with zero duration"""
        result = self.scorer.calculate_runway_cost(0, 'gen3')

        assert result['cost'] == 0.0
        assert result['is_verified'] is True

    def test_runway_large_duration(self):
        """Test Runway with large duration"""
        result = self.scorer.calculate_runway_cost(300, 'gen3')

        assert result['cost'] == 30.0
        assert result['duration'] == 300
        assert result['is_verified'] is True

    def test_runway_invalid_model(self):
        """Test Runway with invalid model defaults to gen3"""
        result = self.scorer.calculate_runway_cost(5, 'invalid')

        assert result['cost'] == 0.5
        assert result['model'] == 'gen3'
        assert result['is_verified'] is True

    # ===== Pika Cost Tests =====

    def test_pika_standard(self):
        """Test Pika standard tier pricing"""
        result = self.scorer.calculate_pika_cost(3, 'standard')

        assert result['cost'] == 0.21
        assert result['provider'] == 'pika'
        assert result['duration'] == 3
        assert result['tier'] == 'standard'
        assert result['price_per_second'] == 0.07
        assert result['is_verified'] is True
        assert 'algorithm' in result

    def test_pika_pro(self):
        """Test Pika pro tier pricing"""
        result = self.scorer.calculate_pika_cost(5, 'pro')

        assert result['cost'] == 0.25
        assert result['tier'] == 'pro'
        assert result['price_per_second'] == 0.05
        assert result['is_verified'] is True

    def test_pika_zero_duration(self):
        """Test Pika with zero duration"""
        result = self.scorer.calculate_pika_cost(0, 'standard')

        assert result['cost'] == 0.0
        assert result['is_verified'] is True

    def test_pika_invalid_tier(self):
        """Test Pika with invalid tier defaults to standard"""
        result = self.scorer.calculate_pika_cost(4, 'invalid')

        assert result['cost'] == 0.28
        assert result['tier'] == 'standard'
        assert result['is_verified'] is True

    # ===== LLM Cost Tests =====

    def test_llm_claude_opus(self):
        """Test Claude Opus pricing"""
        result = self.scorer.calculate_llm_cost('claude-3-opus', 1000, 500)

        # (1000/1000 * 0.015) + (500/1000 * 0.075) = 0.015 + 0.0375 = 0.0525
        assert result['cost'] == 0.0525
        assert result['provider'] == 'llm'
        assert result['model'] == 'claude-3-opus'
        assert result['input_tokens'] == 1000
        assert result['output_tokens'] == 500
        assert result['total_tokens'] == 1500
        assert result['input_cost'] == 0.015
        assert result['output_cost'] == 0.0375
        assert result['is_verified'] is True
        assert 'algorithm' in result

    def test_llm_claude_sonnet(self):
        """Test Claude Sonnet pricing"""
        result = self.scorer.calculate_llm_cost('claude-3-sonnet', 2000, 1000)

        # (2000/1000 * 0.003) + (1000/1000 * 0.015) = 0.006 + 0.015 = 0.021
        assert result['cost'] == 0.021
        assert result['model'] == 'claude-3-sonnet'
        assert result['is_verified'] is True

    def test_llm_claude_haiku(self):
        """Test Claude Haiku pricing"""
        result = self.scorer.calculate_llm_cost('claude-3-haiku', 5000, 2000)

        # (5000/1000 * 0.00025) + (2000/1000 * 0.00125) = 0.00125 + 0.0025 = 0.00375
        assert result['cost'] == 0.00375
        assert result['model'] == 'claude-3-haiku'
        assert result['is_verified'] is True

    def test_llm_gpt4(self):
        """Test GPT-4 pricing"""
        result = self.scorer.calculate_llm_cost('gpt-4', 1000, 500)

        # (1000/1000 * 0.03) + (500/1000 * 0.06) = 0.03 + 0.03 = 0.06
        assert result['cost'] == 0.06
        assert result['model'] == 'gpt-4'
        assert result['is_verified'] is True

    def test_llm_gpt4_turbo(self):
        """Test GPT-4 Turbo pricing"""
        result = self.scorer.calculate_llm_cost('gpt-4-turbo', 2000, 1000)

        # (2000/1000 * 0.01) + (1000/1000 * 0.03) = 0.02 + 0.03 = 0.05
        assert result['cost'] == 0.05
        assert result['model'] == 'gpt-4-turbo'
        assert result['is_verified'] is True

    def test_llm_gpt35_turbo(self):
        """Test GPT-3.5 Turbo pricing"""
        result = self.scorer.calculate_llm_cost('gpt-3.5-turbo', 10000, 5000)

        # (10000/1000 * 0.0015) + (5000/1000 * 0.002) = 0.015 + 0.01 = 0.025
        assert result['cost'] == 0.025
        assert result['model'] == 'gpt-3.5-turbo'
        assert result['is_verified'] is True

    def test_llm_zero_tokens(self):
        """Test LLM with zero tokens"""
        result = self.scorer.calculate_llm_cost('gpt-3.5-turbo', 0, 0)

        assert result['cost'] == 0.0
        assert result['is_verified'] is True

    def test_llm_unknown_model(self):
        """Test LLM with unknown model"""
        result = self.scorer.calculate_llm_cost('unknown-model', 1000, 500)

        assert result['cost'] == 0.0
        assert 'error' in result
        assert result['is_verified'] is False

    # ===== Budget Status Tests =====

    def test_budget_status_safe(self):
        """Test budget status in safe zone"""
        spending = {
            'image': 400.0,   # 40% of 1000
            'video': 800.0,   # 40% of 2000
            'total': 2000.0   # 40% of 5000
        }

        result = self.scorer.calculate_budget_status(spending)

        assert result['image']['status'] == 'safe'
        assert result['video']['status'] == 'safe'
        assert result['total']['status'] == 'safe'
        assert result['image']['utilization_percent'] == 40.0
        assert result['image']['remaining'] == 600.0
        assert result['is_verified'] is True
        assert 'algorithm' in result
        assert len(result['recommendations']) == 0

    def test_budget_status_warning(self):
        """Test budget status in warning zone"""
        spending = {
            'image': 600.0,   # 60% of 1000
            'video': 1300.0,  # 65% of 2000
            'total': 3000.0   # 60% of 5000
        }

        result = self.scorer.calculate_budget_status(spending)

        assert result['image']['status'] == 'warning'
        assert result['video']['status'] == 'warning'
        assert result['total']['status'] == 'warning'
        assert result['image']['utilization_percent'] == 60.0
        assert result['is_verified'] is True

    def test_budget_status_critical(self):
        """Test budget status in critical zone"""
        spending = {
            'image': 800.0,   # 80% of 1000
            'video': 1600.0,  # 80% of 2000
            'total': 4000.0   # 80% of 5000
        }

        result = self.scorer.calculate_budget_status(spending)

        assert result['image']['status'] == 'critical'
        assert result['video']['status'] == 'critical'
        assert result['total']['status'] == 'critical'
        assert len(result['recommendations']) > 0
        assert result['is_verified'] is True

    def test_budget_status_exceeded(self):
        """Test budget status when exceeded"""
        spending = {
            'image': 1200.0,  # 120% of 1000
            'video': 2500.0,  # 125% of 2000
            'total': 5500.0   # 110% of 5000
        }

        result = self.scorer.calculate_budget_status(spending)

        assert result['image']['status'] == 'exceeded'
        assert result['video']['status'] == 'exceeded'
        assert result['total']['status'] == 'exceeded'
        assert result['image']['utilization_percent'] == 120.0
        assert result['image']['remaining'] == -200.0
        assert len(result['recommendations']) == 3  # All three categories exceeded
        assert result['is_verified'] is True

    def test_budget_status_zero_spending(self):
        """Test budget status with zero spending"""
        spending = {
            'image': 0.0,
            'video': 0.0,
            'total': 0.0
        }

        result = self.scorer.calculate_budget_status(spending)

        assert result['image']['status'] == 'safe'
        assert result['image']['utilization_percent'] == 0.0
        assert result['image']['remaining'] == 1000.0
        assert result['is_verified'] is True

    def test_budget_status_mixed(self):
        """Test budget status with mixed categories"""
        spending = {
            'image': 400.0,   # 40% - safe
            'video': 1600.0,  # 80% - critical
            'total': 3000.0   # 60% - warning
        }

        result = self.scorer.calculate_budget_status(spending)

        assert result['image']['status'] == 'safe'
        assert result['video']['status'] == 'critical'
        assert result['total']['status'] == 'warning'
        assert 'critical' in str(result['recommendations'])
        assert result['is_verified'] is True

    # ===== Cost Efficiency Tests =====

    def test_cost_efficiency_high_score(self):
        """Test cost efficiency with optimal conditions"""
        costs = [
            {'provider': 'dalle3', 'cost': 0.04},
            {'provider': 'midjourney', 'cost': 0.02},
            {'provider': 'runway', 'cost': 0.50},
            {'provider': 'llm', 'cost': 0.01},
        ]

        performance_metrics = {
            'engagement_rate': 5.0,
            'conversion_rate': 3.0
        }

        result = self.scorer.calculate_cost_efficiency(costs, performance_metrics)

        assert result['efficiency_score'] > 70
        assert result['grade'] in ['A', 'B', 'C']
        assert result['total_cost'] == 0.57
        assert result['total_items'] == 4
        assert result['provider_distribution']['dalle3'] == 1
        assert 'component_scores' in result
        assert result['is_verified'] is True
        assert 'algorithm' in result

    def test_cost_efficiency_no_performance_metrics(self):
        """Test cost efficiency without performance metrics"""
        costs = [
            {'provider': 'dalle3', 'cost': 0.04},
            {'provider': 'llm', 'cost': 0.01},
        ]

        result = self.scorer.calculate_cost_efficiency(costs)

        assert 'efficiency_score' in result
        assert result['component_scores']['performance_cost_ratio'] == 15  # Neutral score
        assert result['is_verified'] is True

    def test_cost_efficiency_single_provider(self):
        """Test cost efficiency with single provider"""
        costs = [
            {'provider': 'dalle3', 'cost': 0.04},
            {'provider': 'dalle3', 'cost': 0.08},
        ]

        result = self.scorer.calculate_cost_efficiency(costs)

        assert result['component_scores']['provider_mix'] == 10  # Low score for single provider
        assert result['total_cost'] == 0.12
        assert len(result['optimization_suggestions']) > 0
        assert result['is_verified'] is True

    def test_cost_efficiency_diverse_providers(self):
        """Test cost efficiency with diverse providers"""
        costs = [
            {'provider': 'dalle3', 'cost': 0.04},
            {'provider': 'midjourney', 'cost': 0.02},
            {'provider': 'runway', 'cost': 0.50},
            {'provider': 'pika', 'cost': 0.21},
        ]

        result = self.scorer.calculate_cost_efficiency(costs)

        assert result['component_scores']['provider_mix'] == 30  # Max score for 4+ providers
        assert result['is_verified'] is True

    def test_cost_efficiency_budget_exceeded(self):
        """Test cost efficiency when budget exceeded"""
        costs = [
            {'provider': 'dalle3', 'cost': 1000.0},
            {'provider': 'runway', 'cost': 2000.0},
            {'provider': 'llm', 'cost': 3000.0},
        ]

        result = self.scorer.calculate_cost_efficiency(costs)

        assert result['component_scores']['budget_adherence'] == 0  # Budget exceeded
        assert result['total_cost'] == 6000.0
        assert 'Budget utilization is high' in ' '.join(result['optimization_suggestions'])
        assert result['is_verified'] is True

    def test_cost_efficiency_empty_costs(self):
        """Test cost efficiency with empty costs"""
        result = self.scorer.calculate_cost_efficiency([])

        assert result['efficiency_score'] == 0
        assert 'error' in result
        assert result['is_verified'] is True

    def test_cost_efficiency_grade_mapping(self):
        """Test efficiency grade mapping"""
        # Test private method through cost_efficiency
        assert self.scorer._get_efficiency_grade(95) == 'A'
        assert self.scorer._get_efficiency_grade(85) == 'B'
        assert self.scorer._get_efficiency_grade(75) == 'C'
        assert self.scorer._get_efficiency_grade(65) == 'D'
        assert self.scorer._get_efficiency_grade(50) == 'F'

    # ===== Convenience Function Tests =====

    def test_calculate_api_cost_dalle(self):
        """Test convenience function for DALL-E"""
        result = calculate_api_cost('dalle', size='1024x1024', quality='standard')

        assert result['cost'] == 0.040
        assert result['provider'] == 'dalle3'
        assert result['is_verified'] is True

    def test_calculate_api_cost_midjourney(self):
        """Test convenience function for Midjourney"""
        result = calculate_api_cost('midjourney', process_mode='fast')

        assert result['cost'] == 0.04
        assert result['provider'] == 'midjourney'
        assert result['is_verified'] is True

    def test_calculate_api_cost_runway(self):
        """Test convenience function for Runway"""
        result = calculate_api_cost('runway', duration=5, model='gen3')

        assert result['cost'] == 0.5
        assert result['provider'] == 'runway'
        assert result['is_verified'] is True

    def test_calculate_api_cost_pika(self):
        """Test convenience function for Pika"""
        result = calculate_api_cost('pika', duration=4, tier='pro')

        assert result['cost'] == 0.2
        assert result['provider'] == 'pika'
        assert result['is_verified'] is True

    def test_calculate_api_cost_llm(self):
        """Test convenience function for LLM"""
        result = calculate_api_cost('llm', model='gpt-3.5-turbo', input_tokens=1000, output_tokens=500)

        assert result['cost'] == 0.0025
        assert result['provider'] == 'llm'
        assert result['is_verified'] is True

    def test_calculate_api_cost_unknown_provider(self):
        """Test convenience function with unknown provider"""
        result = calculate_api_cost('unknown-provider')

        assert result['cost'] == 0.0
        assert 'error' in result
        assert result['is_verified'] is False

    def test_calculate_api_cost_with_defaults(self):
        """Test convenience function with default parameters"""
        result = calculate_api_cost('dalle')

        assert result['size'] == '1024x1024'
        assert result['quality'] == 'standard'
        assert result['is_verified'] is True

    # ===== Custom Budget Tests =====

    def test_custom_budgets(self):
        """Test CostScorer with custom budgets"""
        custom_scorer = CostScorer(
            monthly_image_budget=500.0,
            monthly_video_budget=1000.0,
            monthly_total_budget=2500.0
        )

        spending = {
            'image': 250.0,
            'video': 500.0,
            'total': 1250.0
        }

        result = custom_scorer.calculate_budget_status(spending)

        assert result['image']['budget'] == 500.0
        assert result['video']['budget'] == 1000.0
        assert result['total']['budget'] == 2500.0
        assert result['image']['status'] == 'safe'
        assert result['is_verified'] is True

    def test_default_budgets(self):
        """Test CostScorer with default budgets"""
        default_scorer = CostScorer()

        spending = {
            'image': 500.0,
            'video': 1000.0,
            'total': 2500.0
        }

        result = default_scorer.calculate_budget_status(spending)

        assert result['image']['budget'] == 1000.0
        assert result['video']['budget'] == 2000.0
        assert result['total']['budget'] == 5000.0
        assert result['is_verified'] is True


class TestCostScorerEdgeCases:
    """Test suite for edge cases and error handling"""

    def test_negative_duration(self):
        """Test video generation with negative duration"""
        scorer = CostScorer()
        # Negative duration should still calculate (no validation)
        result = scorer.calculate_runway_cost(-5, 'gen3')
        assert result['cost'] == -0.5
        assert result['is_verified'] is True

    def test_very_large_token_count(self):
        """Test LLM with very large token count"""
        scorer = CostScorer()
        result = scorer.calculate_llm_cost('gpt-3.5-turbo', 1000000, 500000)

        # (1000000/1000 * 0.0015) + (500000/1000 * 0.002) = 1.5 + 1.0 = 2.5
        assert result['cost'] == 2.5
        assert result['is_verified'] is True

    def test_cost_precision(self):
        """Test cost calculation precision"""
        scorer = CostScorer()
        result = scorer.calculate_llm_cost('claude-3-haiku', 333, 777)

        # Verify rounding to 6 decimal places
        assert isinstance(result['cost'], float)
        assert len(str(result['cost']).split('.')[-1]) <= 6

    def test_budget_boundary_conditions(self):
        """Test budget thresholds at exact boundaries"""
        scorer = CostScorer()

        # Exactly 50% - should be safe
        spending = {'image': 500.0, 'video': 1000.0, 'total': 2500.0}
        result = scorer.calculate_budget_status(spending)
        assert result['total']['status'] == 'safe'

        # Exactly 75% - should be warning
        spending = {'image': 750.0, 'video': 1500.0, 'total': 3750.0}
        result = scorer.calculate_budget_status(spending)
        assert result['total']['status'] == 'warning'

        # Exactly 90% - should be critical
        spending = {'image': 900.0, 'video': 1800.0, 'total': 4500.0}
        result = scorer.calculate_budget_status(spending)
        assert result['total']['status'] == 'critical'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v'])
