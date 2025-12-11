"""
Policy Engine: Intent -> Tx validation.
Integrates EPI, compliance (stubbed), risk (e.g., VaR proxy).
"""

from src.epi.calculator import EPICalculator, EPIScores
from typing import Dict, Any
import numpy as np

class PolicyValidator:
    def __init__(self):
        self.epi_calc = EPICalculator()
    
    def validate_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AI-generated intent (e.g., {'action': 'invest', 'amount': 1000, 'ethics_factors': {...}})."""
        # Stub compliance (e.g., sanctions check)
        if 'sanctioned' in intent:
            return {'approved': False, 'reason': 'Compliance fail'}
        
        # Risk check (simple concentration proxy)
        risk_score = 1.0 - min(intent.get('exposure_ratio', 0), 1.0)
        
        # Ethics from factors (e.g., env=0.8, equity=0.7 -> avg=0.75)
        ethics = np.mean(list(intent.get('ethics_factors', {}).values()))
        profit = intent.get('roi_proxy', 0.0)  # Normalize [0,1]
        violations = intent.get('past_violations', [])
        
        scores = EPIScores(profit=profit, ethics=ethics, violations=violations)
        epi, epi_valid, epi_trace = self.epi_calc.compute_epi(scores)
        
        approved = epi_valid and risk_score > 0.5
        return {
            'approved': approved,
            'epi_trace': epi_trace,
            'risk_score': risk_score,
            'reason': 'EPI rejection' if not epi_valid else 'Risk exceed' if risk_score <= 0.5 else 'Approved'
        }

# Example
if __name__ == "__main__":
    validator = PolicyValidator()
    intent = {'action': 'proposal', 'roi_proxy': 0.85, 'ethics_factors': {'env': 0.9, 'equity': 0.7}, 'violations': []}
    result = validator.validate_intent(intent)
    print(result)  # {'approved': True, ...}
