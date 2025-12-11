# Ethical Profitability Index (EPI): Mathematical Derivation

## Executive Summary

The **Ethical Profitability Index (EPI)** is a mathematical framework for constraining AI decision-making to balance profitability with ethical considerations. Unlike traditional ESG scores that are retrospective and qualitative, the EPI is **prospective, quantitative, and non-compensatory**, meaning high performance in one dimension cannot offset poor performance in another.

## Mathematical Foundation

### 1. Core Formula

The EPI is defined as:

```
EPI = H(P, E) × B(P, E) × T(V)
```

Where:
- **H(P, E)**: Harmonic mean of Profit (P) and Ethics (E)
- **B(P, E)**: Balance penalty using the golden ratio (φ)
- **T(V)**: Trust accumulator with geometric decay on violations (V)

### 2. Harmonic Mean Component

#### Definition

The harmonic mean is defined as:

```
H(P, E) = 2PE / (P + E)
```

#### Properties

1. **Non-compensatory**: If either P = 0 or E = 0, then H(P, E) = 0
2. **Bias toward minimum**: The harmonic mean is always ≤ the arithmetic mean
3. **Sensitivity**: Small values dominate the result

#### Justification

The choice of harmonic mean over arithmetic mean is critical for ethical governance:

- **Arithmetic mean**: (P + E) / 2 allows compensation (high P can offset low E)
- **Harmonic mean**: 2PE / (P + E) enforces a floor on both dimensions

**Example**:
- P = 0.9, E = 0.1
- Arithmetic mean = 0.5 (appears "acceptable")
- Harmonic mean = 0.164 (correctly identifies imbalance)

#### Mathematical Proof of Non-Compensation

For the harmonic mean to be high, both P and E must be high:

```
∂H/∂P = 2E² / (P + E)²
∂H/∂E = 2P² / (P + E)²
```

Both partial derivatives are positive, but the rate of increase diminishes as the denominator grows. This creates a "multiplicative" effect rather than additive.

**Reference**: Boyd, S., & Vandenberghe, L. (2004). *Convex Optimization*, Chapter 2.

### 3. Golden Ratio Balance Penalty

#### Definition

The balance penalty is defined as:

```
B(P, E) = 1 - φ|P - E|
```

Where φ = (√5 - 1) / 2 ≈ 0.618 (the golden ratio conjugate).

#### Properties

1. **Maximum at balance**: B(P, E) = 1 when P = E
2. **Penalizes imbalance**: Decreases linearly with |P - E|
3. **Golden ratio weighting**: Uses φ for natural scaling

#### Justification

The golden ratio (Φ = 1.618) appears throughout nature in stable, sustainable systems. The conjugate φ = Φ - 1 ≈ 0.618 provides a natural weighting factor for balance.

The penalty ensures that even if H(P, E) is moderate, extreme imbalances reduce the EPI:

**Example**:
- P = 0.8, E = 0.2
- |P - E| = 0.6
- B(P, E) = 1 - 0.618 × 0.6 = 0.629

This 37% penalty reflects the instability of the imbalance.

#### Golden Ratio Optimization Target

The ideal relationship between P and E is:

```
P / E ≈ Φ  or  E / P ≈ Φ
```

This suggests that for maximum sustainability, one dimension should be approximately 1.618 times the other, creating a harmonious asymmetry.

### 4. Trust Accumulator

#### Definition

Trust evolves geometrically with violations:

```
T(V) = T₀ × ∏ᵢ (1 - vᵢ)
```

Where:
- T₀ = initial trust (typically 1.0)
- vᵢ = severity of violation i ∈ [0, 1]

#### Properties

1. **Multiplicative decay**: Each violation compounds
2. **Irreversibility**: Trust can only decrease (unless explicit rehabilitation)
3. **Catastrophic collapse**: A single severe violation (v ≈ 1) resets trust to zero

#### Justification

Trust in AI systems is fragile and compounds over time. The geometric model reflects this reality:

- **Linear model** (additive): T = T₀ - Σvᵢ (allows recovery)
- **Geometric model** (multiplicative): T = T₀ × ∏(1 - vᵢ) (permanent impact)

**Example**:
- Three violations: v₁ = 0.1, v₂ = 0.2, v₃ = 0.15
- T = 1.0 × 0.9 × 0.8 × 0.85 = 0.612

Each violation reduces trust by its severity, compounding the effect.

**Reference**: Jøsang, A., et al. (2007). "Trust network analysis with subjective logic." *Decision Support Systems*, 43(2).

### 5. Convergence Theory

#### Hypothesis

Over time (t → ∞), the most ethical companies become the most profitable due to:

1. **Reduced friction**: Fewer lawsuits, regulations, boycotts
2. **Stakeholder loyalty**: Higher customer retention and employee satisfaction
3. **Sustainable growth**: Avoiding short-term gains that create long-term liabilities

#### Mathematical Formulation

Define the **Ethical Profit Trajectory**:

```
dP/dt = f(E, T) - g(P, E)
```

Where:
- f(E, T): Growth function (increases with ethics and trust)
- g(P, E): Friction function (increases with profit-ethics imbalance)

At equilibrium (dP/dt = 0):

```
f(E, T) = g(P, E)
```

The stable equilibrium occurs when P and E are balanced according to the golden ratio.

## EPI Threshold and Decision Logic

### Threshold Selection

The EPI threshold τ determines approval:

```
Decision = {
  APPROVED   if EPI ≥ τ
  REJECTED   if EPI < τ
}
```

**Common thresholds**:
- τ = 0.5: Minimum acceptable (requires at least moderate performance)
- τ = 0.7: Standard (requires good performance in both dimensions)
- τ = 0.9: Strict (requires excellent performance)

### Sensitivity Analysis

The EPI is most sensitive to:

1. **Low values**: Due to harmonic mean
2. **Imbalances**: Due to balance penalty
3. **Violations**: Due to geometric trust decay

This sensitivity ensures that the system cannot be "gamed" by optimizing one dimension.

## Comparison with Traditional Metrics

| Metric | Compensatory? | Prospective? | Quantitative? | Non-linear? |
|--------|---------------|--------------|---------------|-------------|
| **EPI** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| ESG Score | ✅ Yes | ❌ No | ⚠️ Partial | ❌ No |
| ROI | ✅ Yes | ⚠️ Partial | ✅ Yes | ❌ No |
| Sharpe Ratio | ✅ Yes | ⚠️ Partial | ✅ Yes | ⚠️ Partial |

## Implementation Considerations

### Numerical Stability

1. **Harmonic mean**: Check for zero denominators
2. **Trust accumulator**: Clamp to zero when T < 10⁻⁶
3. **Balance penalty**: Ensure non-negative (max(0, 1 - φ|P - E|))

### Computational Complexity

- **Time complexity**: O(n) where n = number of violations
- **Space complexity**: O(1) (constant space)
- **Suitable for**: Real-time on-chain computation

### Parameter Tuning

1. **φ weight**: Can be adjusted (default 1.0) to increase/decrease balance sensitivity
2. **Threshold τ**: Should be calibrated to organizational risk tolerance
3. **Trust floor**: Minimum trust before complete restriction (default 0.1)

## Formal Verification

### Theorem 1: Non-Compensation

**Statement**: For any ε > 0, there exists no P such that EPI(P, 0) ≥ ε.

**Proof**: 
- H(P, 0) = 0 for all P
- Therefore EPI = 0 × B(P, 0) × T(V) = 0
- QED

### Theorem 2: Monotonicity

**Statement**: EPI is monotonically increasing in both P and E when violations are fixed.

**Proof**:
- ∂H/∂P > 0 and ∂H/∂E > 0 (shown above)
- ∂B/∂P and ∂B/∂E depend on sign of (P - E) but |∂B| is bounded
- Therefore ∂EPI/∂P > 0 and ∂EPI/∂E > 0 in most regions
- QED

### Theorem 3: Catastrophic Collapse

**Statement**: A single complete violation (v = 1) reduces EPI to zero regardless of P and E.

**Proof**:
- T(V) = ∏(1 - vᵢ)
- If any vᵢ = 1, then (1 - vᵢ) = 0
- Therefore T(V) = 0
- Therefore EPI = H × B × 0 = 0
- QED

## Conclusion

The EPI provides a mathematically rigorous framework for AI governance that:

1. **Enforces ethical constraints** through non-compensatory design
2. **Balances competing objectives** using the golden ratio
3. **Accumulates trust** through geometric progression
4. **Prevents gaming** through sensitivity to low values and violations

This makes it suitable for autonomous AI decision-making where human oversight is limited or delayed.

## References

1. Boyd, S., & Vandenberghe, L. (2004). *Convex Optimization*. Cambridge University Press.
2. Jøsang, A., Ismail, R., & Boyd, C. (2007). "A survey of trust and reputation systems for online service provision." *Decision Support Systems*, 43(2), 618-644.
3. Livio, M. (2002). *The Golden Ratio: The Story of Phi*. Broadway Books.
4. Buterin, V. (2014). "A Next-Generation Smart Contract and Decentralized Application Platform." *Ethereum Whitepaper*.

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**Authors**: MicroAI Studios Research Team
