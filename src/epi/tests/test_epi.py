"""
Unit tests for the EPI Calculator.

Tests cover:
- Harmonic mean calculation
- Golden ratio balance penalty
- Trust accumulator with violations
- Full EPI computation
- Edge cases and boundary conditions
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.epi.calculator import EPICalculator, EPIScores, PHI, GOLDEN_RATIO


class TestHarmonicMean:
    """Test harmonic mean calculation."""

    def test_balanced_scores(self):
        """Test harmonic mean with balanced scores."""
        calc = EPICalculator()
        result = calc.harmonic_mean(0.8, 0.8)
        assert result == pytest.approx(0.8, rel=1e-6)

    def test_unbalanced_scores(self):
        """Test harmonic mean with unbalanced scores."""
        calc = EPICalculator()
        result = calc.harmonic_mean(0.9, 0.5)
        # Harmonic mean should be closer to the lower value
        assert result < 0.7
        assert result == pytest.approx(0.6429, rel=1e-3)

    def test_zero_profit(self):
        """Test that zero profit collapses harmonic mean."""
        calc = EPICalculator()
        result = calc.harmonic_mean(0.0, 0.8)
        assert result == 0.0

    def test_zero_ethics(self):
        """Test that zero ethics collapses harmonic mean."""
        calc = EPICalculator()
        result = calc.harmonic_mean(0.9, 0.0)
        assert result == 0.0

    def test_both_zero(self):
        """Test that both zero returns zero."""
        calc = EPICalculator()
        result = calc.harmonic_mean(0.0, 0.0)
        assert result == 0.0


class TestBalancePenalty:
    """Test golden ratio balance penalty."""

    def test_perfect_balance(self):
        """Test penalty with perfectly balanced scores."""
        calc = EPICalculator()
        result = calc.balance_penalty(0.8, 0.8)
        assert result == 1.0

    def test_small_imbalance(self):
        """Test penalty with small imbalance."""
        calc = EPICalculator()
        result = calc.balance_penalty(0.8, 0.7)
        # Penalty should be close to 1.0 for small imbalance
        assert result > 0.9
        assert result < 1.0

    def test_large_imbalance(self):
        """Test penalty with large imbalance."""
        calc = EPICalculator()
        result = calc.balance_penalty(0.9, 0.1)
        # Large imbalance should result in significant penalty
        assert result < 0.6

    def test_extreme_imbalance(self):
        """Test penalty with extreme imbalance."""
        calc = EPICalculator()
        result = calc.balance_penalty(1.0, 0.0)
        # Should be close to zero but not negative
        assert result >= 0.0
        assert result < 0.4

    def test_phi_weight(self):
        """Test that phi weight affects penalty."""
        calc_normal = EPICalculator(phi_weight=1.0)
        calc_heavy = EPICalculator(phi_weight=2.0)

        penalty_normal = calc_normal.balance_penalty(0.8, 0.5)
        penalty_heavy = calc_heavy.balance_penalty(0.8, 0.5)

        # Higher phi weight should result in lower penalty
        assert penalty_heavy < penalty_normal


class TestTrustAccumulator:
    """Test trust accumulator with violations."""

    def test_no_violations(self):
        """Test trust with no violations."""
        calc = EPICalculator()
        result = calc.trust_accumulator([])
        assert result == 1.0

    def test_single_violation(self):
        """Test trust with single violation."""
        calc = EPICalculator()
        result = calc.trust_accumulator([0.1])
        assert result == pytest.approx(0.9, rel=1e-6)

    def test_multiple_violations(self):
        """Test trust with multiple violations."""
        calc = EPICalculator()
        result = calc.trust_accumulator([0.1, 0.2, 0.15])
        # Trust = 1.0 * 0.9 * 0.8 * 0.85 = 0.612
        assert result == pytest.approx(0.612, rel=1e-3)

    def test_severe_violation(self):
        """Test trust with severe violation."""
        calc = EPICalculator()
        result = calc.trust_accumulator([0.9])
        # Should be close to zero
        assert result < 0.2
        assert result == pytest.approx(0.1, rel=1e-6)

    def test_complete_violation(self):
        """Test trust with complete violation."""
        calc = EPICalculator()
        result = calc.trust_accumulator([1.0])
        assert result == 0.0

    def test_numerical_stability(self):
        """Test that very small trust values collapse to zero."""
        calc = EPICalculator()
        # Many small violations should eventually collapse
        violations = [0.3] * 10
        result = calc.trust_accumulator(violations)
        assert result == 0.0


class TestGoldenRatioDeviation:
    """Test golden ratio deviation calculation."""

    def test_perfect_golden_ratio(self):
        """Test deviation with perfect golden ratio."""
        calc = EPICalculator()
        # P/E = φ
        deviation = calc.golden_ratio_deviation(GOLDEN_RATIO * 0.5, 0.5)
        assert deviation == pytest.approx(0.0, abs=1e-6)

    def test_inverse_golden_ratio(self):
        """Test deviation with inverse golden ratio."""
        calc = EPICalculator()
        # E/P = φ (or P/E = 1/φ)
        deviation = calc.golden_ratio_deviation(0.5, GOLDEN_RATIO * 0.5)
        assert deviation == pytest.approx(0.0, abs=1e-6)

    def test_balanced_ratio(self):
        """Test deviation with 1:1 ratio."""
        calc = EPICalculator()
        deviation = calc.golden_ratio_deviation(0.5, 0.5)
        # Should be distance from φ (1.618)
        expected = abs(1.0 - GOLDEN_RATIO)
        assert deviation == pytest.approx(expected, rel=1e-3)

    def test_zero_ethics(self):
        """Test deviation with zero ethics."""
        calc = EPICalculator()
        deviation = calc.golden_ratio_deviation(0.5, 0.0)
        assert deviation == float("inf")


class TestEPIComputation:
    """Test full EPI computation."""

    def test_high_performance_no_violations(self):
        """Test EPI with high performance and no violations."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.9, ethics=0.8, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        assert epi > 0.7
        assert valid is True
        assert trace["reason"] == "approved"

    def test_balanced_moderate_performance(self):
        """Test EPI with balanced moderate performance."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.75, ethics=0.75, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        assert epi >= 0.7
        assert valid is True

    def test_high_profit_low_ethics(self):
        """Test that high profit cannot compensate for low ethics."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.95, ethics=0.2, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        # Harmonic mean should collapse
        assert epi < 0.5
        assert valid is False
        assert "harmonic mean" in trace["reason"].lower()

    def test_low_profit_high_ethics(self):
        """Test that high ethics cannot compensate for low profit."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.2, ethics=0.95, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        # Harmonic mean should collapse
        assert epi < 0.5
        assert valid is False

    def test_with_minor_violations(self):
        """Test EPI with minor violations."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.85, ethics=0.8, violations=[0.1, 0.05])

        epi, valid, trace = calc.compute_epi(scores)

        # Should still pass but with reduced EPI
        assert trace["trust"] < 1.0
        assert trace["trust"] == pytest.approx(0.855, rel=1e-3)

    def test_with_severe_violations(self):
        """Test EPI with severe violations."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.9, ethics=0.85, violations=[0.5, 0.3])

        epi, valid, trace = calc.compute_epi(scores)

        # Trust should be severely impacted
        assert trace["trust"] < 0.5
        assert valid is False
        assert "trust" in trace["reason"].lower()

    def test_extreme_imbalance(self):
        """Test EPI with extreme imbalance."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.95, ethics=0.1, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        # Both harmonic mean and balance penalty should be low
        assert trace["hmean"] < 0.3
        assert trace["balance_penalty"] < 0.6
        assert valid is False

    def test_threshold_boundary(self):
        """Test EPI at threshold boundary."""
        calc = EPICalculator(threshold=0.7)

        # Try to find scores that result in EPI ≈ 0.7
        scores = EPIScores(profit=0.78, ethics=0.78, violations=[])
        epi, valid, trace = calc.compute_epi(scores)

        # Should be close to threshold
        assert abs(epi - 0.7) < 0.1

    def test_with_stakeholder_sentiment(self):
        """Test EPI with stakeholder sentiment included."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=0.8, ethics=0.8, violations=[], stakeholder_sentiment=0.9)

        epi_without, _, _ = calc.compute_epi(scores, include_sentiment=False)
        epi_with, _, _ = calc.compute_epi(scores, include_sentiment=True)

        # EPI with sentiment should be higher
        assert epi_with > epi_without


class TestGoldenRatioOptimization:
    """Test golden ratio optimization."""

    def test_optimization_basic(self):
        """Test basic optimization for target EPI."""
        calc = EPICalculator(threshold=0.7)

        result = calc.optimize_for_golden_ratio(target_epi=0.75, current_ethics=0.7, violations=[])

        assert "optimal_profit" in result
        assert result["optimal_profit"] > 0
        assert result["optimal_profit"] <= 1.0
        assert abs(result["achieved_epi"] - 0.75) < 0.1

    def test_optimization_with_violations(self):
        """Test optimization with violations present."""
        calc = EPICalculator(threshold=0.7)

        result = calc.optimize_for_golden_ratio(
            target_epi=0.7, current_ethics=0.8, violations=[0.1, 0.05]
        )

        # Should find a profit level that compensates for trust loss
        assert result["optimal_profit"] > 0
        assert result["achieved_epi"] >= 0.65  # Close to target


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_zeros(self):
        """Test EPI with all zero scores."""
        calc = EPICalculator()
        scores = EPIScores(profit=0.0, ethics=0.0, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        assert epi == 0.0
        assert valid is False

    def test_all_ones(self):
        """Test EPI with perfect scores."""
        calc = EPICalculator(threshold=0.7)
        scores = EPIScores(profit=1.0, ethics=1.0, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        assert epi == 1.0
        assert valid is True
        assert trace["hmean"] == 1.0
        assert trace["balance_penalty"] == 1.0
        assert trace["trust"] == 1.0

    def test_very_low_threshold(self):
        """Test with very low threshold."""
        calc = EPICalculator(threshold=0.1)
        scores = EPIScores(profit=0.3, ethics=0.3, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        # Should pass with low threshold
        assert valid is True

    def test_very_high_threshold(self):
        """Test with very high threshold."""
        calc = EPICalculator(threshold=0.95)
        scores = EPIScores(profit=0.9, ethics=0.85, violations=[])

        epi, valid, trace = calc.compute_epi(scores)

        # Should fail with high threshold
        assert valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
