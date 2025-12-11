"""
EPI Calculator: Harmonic-mean-based ethical constraint with Golden Ratio optimization.

References:
- Harmonic mean robustness: Boyd & Vandenberghe (2004), Convex Optimization, Ch. 2.
- Geometric decay: Jøsang et al. (2007), Decision Support Systems, 43(2).
- Golden Ratio optimization: MicroAI Ethical Governance Framework (2025)

Mathematical Foundation:
    EPI = H(P, E) × B(P, E) × T(V)
    
Where:
    H(P, E) = 2PE/(P+E)  # Harmonic mean
    B(P, E) = 1 - φ|P-E|  # Balance penalty using golden ratio
    T(V) = Π(1 - v_i)     # Trust accumulator (geometric decay)
    φ ≈ 0.618            # Golden ratio conjugate
"""

import numpy as np
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass

# Golden Ratio conjugate (φ - 1) ≈ 0.618
PHI = (np.sqrt(5) - 1) / 2

# Full Golden Ratio for optimization target
GOLDEN_RATIO = (1 + np.sqrt(5)) / 2  # ≈ 1.618


@dataclass
class EPIScores:
    """Input scores for EPI computation."""
    profit: float  # Normalized ROI proxy [0,1]
    ethics: float  # Multi-dim ethics score [0,1] (e.g., env/equity/fairness avg)
    violations: List[float]  # Per-incident penalties [0,1]
    stakeholder_sentiment: float = 0.5  # Community sentiment [0,1]


class EPICalculator:
    """
    Ethical Profitability Index Calculator.
    
    Implements the MicroAI governance framework's core mathematical logic
    for balancing profit and ethics through non-compensatory constraints.
    """
    
    def __init__(self, threshold: float = 0.7, phi_weight: float = 1.0):
        """
        Initialize EPI calculator.
        
        Args:
            threshold: Minimum EPI score for approval [0,1]
            phi_weight: Weight for golden ratio balance penalty
        """
        self.threshold = threshold
        self.phi_weight = phi_weight
    
    @staticmethod
    def harmonic_mean(p: float, e: float) -> float:
        """
        Harmonic mean: collapses to 0 if p or e -> 0.
        
        This enforces non-compensatory behavior: high profit cannot
        offset zero ethics, and vice versa.
        
        Args:
            p: Profit score [0,1]
            e: Ethics score [0,1]
            
        Returns:
            Harmonic mean H(p,e) = 2pe/(p+e)
        """
        if p == 0 or e == 0:
            return 0.0
        return 2 * p * e / (p + e)

    def balance_penalty(self, p: float, e: float) -> float:
        """
        Golden-ratio penalty for imbalance.
        
        Penalizes extreme deviations between profit and ethics.
        The golden ratio (φ) represents the ideal balance point.
        
        Args:
            p: Profit score [0,1]
            e: Ethics score [0,1]
            
        Returns:
            Balance penalty B(p,e) = 1 - φ|p-e|
        """
        imbalance = abs(p - e)
        penalty = 1 - (self.phi_weight * PHI * imbalance)
        return max(0.0, penalty)  # Ensure non-negative

    @staticmethod
    def trust_accumulator(violations: List[float], initial_trust: float = 1.0) -> float:
        """
        Geometric product: multiplicative decay on violations.
        
        Trust compounds geometrically: T_n = T_0 * Π(1 - v_i)
        A single severe violation can collapse trust to zero.
        
        Args:
            violations: List of violation severities [0,1]
            initial_trust: Starting trust level
            
        Returns:
            Final trust level after all violations
        """
        trust = initial_trust
        for delta in violations:
            trust *= (1 - delta)
            if trust < 1e-6:  # Numerical stability
                return 0.0
        return trust
    
    def golden_ratio_deviation(self, p: float, e: float) -> float:
        """
        Calculate deviation from golden ratio ideal.
        
        The optimal relationship is P/E ≈ φ (1.618) or E/P ≈ φ.
        This measures how far the current ratio deviates from ideal.
        
        Args:
            p: Profit score [0,1]
            e: Ethics score [0,1]
            
        Returns:
            Deviation from golden ratio [0,∞)
        """
        if e == 0:
            return float('inf')
        
        ratio = p / e
        # Check deviation from both φ and 1/φ
        dev_phi = abs(ratio - GOLDEN_RATIO)
        dev_inv_phi = abs(ratio - (1 / GOLDEN_RATIO))
        
        return min(dev_phi, dev_inv_phi)
    
    def compute_epi(
        self, 
        scores: EPIScores, 
        include_sentiment: bool = False
    ) -> Tuple[float, bool, Dict[str, Any]]:
        """
        Compute EPI and validate against threshold.
        
        Formula: EPI = H(P, E) × B(P, E) × T(V) [× S]
        
        Args:
            scores: EPIScores object with profit, ethics, violations
            include_sentiment: Whether to include stakeholder sentiment
            
        Returns:
            Tuple of (epi_value, is_valid, trace_dict)
            
        Trace includes:
            - hmean: Harmonic mean component
            - balance_penalty: Golden ratio balance penalty
            - trust: Trust accumulator value
            - epi: Final EPI score
            - golden_ratio_dev: Deviation from ideal φ ratio
            - reason: Approval/rejection reason
        """
        # Core components
        hmean = self.harmonic_mean(scores.profit, scores.ethics)
        penalty = self.balance_penalty(scores.profit, scores.ethics)
        trust = self.trust_accumulator(scores.violations)
        
        # Base EPI calculation
        epi = hmean * penalty * trust
        
        # Optional: Include stakeholder sentiment
        if include_sentiment:
            epi *= scores.stakeholder_sentiment
        
        # Calculate golden ratio deviation for analysis
        gr_deviation = self.golden_ratio_deviation(scores.profit, scores.ethics)
        
        # Determine approval status
        is_valid = epi >= self.threshold
        
        # Determine rejection reason
        if not is_valid:
            if hmean < 0.5:
                reason = 'rejected: harmonic mean too low (profit or ethics insufficient)'
            elif penalty < 0.7:
                reason = 'rejected: imbalance between profit and ethics'
            elif trust < 0.5:
                reason = 'rejected: trust compromised by violations'
            else:
                reason = f'rejected: EPI {epi:.3f} below threshold {self.threshold}'
        else:
            reason = 'approved'
        
        trace = {
            'hmean': hmean,
            'balance_penalty': penalty,
            'trust': trust,
            'epi': epi,
            'golden_ratio_deviation': gr_deviation,
            'stakeholder_sentiment': scores.stakeholder_sentiment if include_sentiment else None,
            'threshold': self.threshold,
            'reason': reason
        }
        
        return epi, is_valid, trace
    
    def optimize_for_golden_ratio(
        self, 
        target_epi: float,
        current_ethics: float,
        violations: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate optimal profit level to achieve target EPI with golden ratio balance.
        
        Args:
            target_epi: Desired EPI score
            current_ethics: Fixed ethics score
            violations: List of violations
            
        Returns:
            Dictionary with optimal profit and analysis
        """
        trust = self.trust_accumulator(violations)
        
        # Search for optimal profit that achieves target EPI
        best_profit = 0.0
        best_epi = 0.0
        best_deviation = float('inf')
        
        for p in np.linspace(0.1, 1.0, 100):
            scores = EPIScores(profit=p, ethics=current_ethics, violations=violations)
            epi, _, _ = self.compute_epi(scores)
            deviation = self.golden_ratio_deviation(p, current_ethics)
            
            # Find profit that gets closest to target EPI with minimal φ deviation
            if abs(epi - target_epi) < 0.05 and deviation < best_deviation:
                best_profit = p
                best_epi = epi
                best_deviation = deviation
        
        return {
            'optimal_profit': best_profit,
            'achieved_epi': best_epi,
            'golden_ratio_deviation': best_deviation,
            'profit_ethics_ratio': best_profit / current_ethics if current_ethics > 0 else 0,
            'ideal_ratio': GOLDEN_RATIO
        }


# Example usage and testing
if __name__ == "__main__":
    calc = EPICalculator(threshold=0.7)
    
    print("=" * 60)
    print("MicroAI EPI Calculator - Test Cases")
    print("=" * 60)
    
    # Test 1: Balanced high performance
    print("\n[Test 1] Balanced High Performance")
    scores1 = EPIScores(profit=0.9, ethics=0.8, violations=[])
    epi1, valid1, trace1 = calc.compute_epi(scores1)
    print(f"Profit: {scores1.profit}, Ethics: {scores1.ethics}")
    print(f"EPI: {epi1:.3f}, Valid: {valid1}")
    print(f"Golden Ratio Deviation: {trace1['golden_ratio_deviation']:.3f}")
    print(f"Status: {trace1['reason']}")
    
    # Test 2: High profit, low ethics (should fail)
    print("\n[Test 2] High Profit, Low Ethics")
    scores2 = EPIScores(profit=0.95, ethics=0.3, violations=[])
    epi2, valid2, trace2 = calc.compute_epi(scores2)
    print(f"Profit: {scores2.profit}, Ethics: {scores2.ethics}")
    print(f"EPI: {epi2:.3f}, Valid: {valid2}")
    print(f"Status: {trace2['reason']}")
    
    # Test 3: With violations
    print("\n[Test 3] With Violations")
    scores3 = EPIScores(profit=0.85, ethics=0.75, violations=[0.1, 0.15])
    epi3, valid3, trace3 = calc.compute_epi(scores3)
    print(f"Profit: {scores3.profit}, Ethics: {scores3.ethics}")
    print(f"Violations: {scores3.violations}")
    print(f"Trust: {trace3['trust']:.3f}")
    print(f"EPI: {epi3:.3f}, Valid: {valid3}")
    print(f"Status: {trace3['reason']}")
    
    # Test 4: Golden ratio optimization
    print("\n[Test 4] Golden Ratio Optimization")
    optimization = calc.optimize_for_golden_ratio(
        target_epi=0.75,
        current_ethics=0.7,
        violations=[]
    )
    print(f"Target EPI: 0.75, Fixed Ethics: 0.7")
    print(f"Optimal Profit: {optimization['optimal_profit']:.3f}")
    print(f"Achieved EPI: {optimization['achieved_epi']:.3f}")
    print(f"P/E Ratio: {optimization['profit_ethics_ratio']:.3f}")
    print(f"Ideal φ Ratio: {optimization['ideal_ratio']:.3f}")
    print(f"Deviation: {optimization['golden_ratio_deviation']:.3f}")
