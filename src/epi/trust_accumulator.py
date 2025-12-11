"""
Trust Accumulator: Geometric decay model for violation tracking.
Reference: Jøsang et al. (2007), "Trust network analysis with subjective logic"
"""

from typing import List
from dataclasses import dataclass


@dataclass
class ViolationRecord:
    """Record of a single violation event."""
    severity: float  # Penalty factor [0,1], where 1 = complete trust loss
    timestamp: int  # Unix timestamp
    description: str = ""


class TrustAccumulator:
    """
    Tracks trust over time using geometric decay on violations.
    
    Key properties:
    - Multiplicative decay: trust *= (1 - severity) for each violation
    - Non-recoverable: trust can only decrease (unless explicit rehabilitation)
    - Threshold-based: trust below threshold triggers restrictions
    """
    
    def __init__(self, initial_trust: float = 1.0, min_threshold: float = 0.1):
        """
        Initialize trust accumulator.
        
        Args:
            initial_trust: Starting trust level [0,1]
            min_threshold: Minimum trust before complete restriction
        """
        self.initial_trust = initial_trust
        self.min_threshold = min_threshold
        self.current_trust = initial_trust
        self.violations: List[ViolationRecord] = []
    
    def record_violation(self, violation: ViolationRecord) -> float:
        """
        Record a violation and update trust.
        
        Args:
            violation: ViolationRecord with severity and metadata
            
        Returns:
            Updated trust level after applying penalty
        """
        self.violations.append(violation)
        penalty = 1 - violation.severity
        self.current_trust *= penalty
        
        # Numerical stability: clamp to zero if below threshold
        if self.current_trust < self.min_threshold:
            self.current_trust = 0.0
        
        return self.current_trust
    
    def compute_trust(self, violations: List[float]) -> float:
        """
        Compute trust from a list of violation severities (stateless).
        
        Args:
            violations: List of severity values [0,1]
            
        Returns:
            Final trust level after all violations
        """
        trust = self.initial_trust
        for severity in violations:
            trust *= (1 - severity)
            if trust < self.min_threshold:
                return 0.0
        return trust
    
    def get_trust_history(self) -> List[dict]:
        """
        Get historical trust trajectory.
        
        Returns:
            List of {timestamp, trust, violation} records
        """
        history = []
        trust = self.initial_trust
        
        for v in self.violations:
            trust *= (1 - v.severity)
            if trust < self.min_threshold:
                trust = 0.0
            history.append({
                'timestamp': v.timestamp,
                'trust': trust,
                'violation': v.description,
                'severity': v.severity
            })
        
        return history
    
    def reset(self, new_trust: float = None):
        """
        Reset trust (e.g., after rehabilitation period).
        
        Args:
            new_trust: New trust level (defaults to initial_trust)
        """
        self.current_trust = new_trust if new_trust is not None else self.initial_trust
        self.violations = []


# Example usage
if __name__ == "__main__":
    import time
    
    accumulator = TrustAccumulator(initial_trust=1.0, min_threshold=0.1)
    
    # Simulate violations
    violations = [
        ViolationRecord(0.1, int(time.time()), "Minor compliance issue"),
        ViolationRecord(0.3, int(time.time()) + 100, "Moderate risk breach"),
        ViolationRecord(0.2, int(time.time()) + 200, "Ethics violation"),
    ]
    
    for v in violations:
        trust = accumulator.record_violation(v)
        print(f"After {v.description}: trust = {trust:.3f}")
    
    # Get history
    history = accumulator.get_trust_history()
    print("\nTrust History:")
    for record in history:
        print(f"  {record['timestamp']}: {record['trust']:.3f} (severity: {record['severity']})")
