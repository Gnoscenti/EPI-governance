"""
Pytest configuration and shared fixtures for MicroAI Governance tests.
"""

import pytest
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.epi.calculator import EPICalculator, EPIScores
from src.epi.trust_accumulator import TrustAccumulator, ViolationRecord
from src.policy_engine.validator import PolicyValidator
from src.policy_engine.logger import ThoughtLogger
from src.ai_c_suite.ceo_ai_stub import CEOAIAgent
from src.ai_c_suite.cfo_ai_stub import CFOAIAgent


# ============ EPI Calculator Fixtures ============

@pytest.fixture
def epi_calculator():
    """Create a default EPI calculator."""
    return EPICalculator(threshold=0.7)


@pytest.fixture
def strict_epi_calculator():
    """Create a strict EPI calculator with high threshold."""
    return EPICalculator(threshold=0.9)


@pytest.fixture
def lenient_epi_calculator():
    """Create a lenient EPI calculator with low threshold."""
    return EPICalculator(threshold=0.5)


@pytest.fixture
def high_performance_scores():
    """Create high performance EPI scores."""
    return EPIScores(profit=0.9, ethics=0.85, violations=[])


@pytest.fixture
def balanced_scores():
    """Create balanced moderate EPI scores."""
    return EPIScores(profit=0.75, ethics=0.75, violations=[])


@pytest.fixture
def unbalanced_scores():
    """Create unbalanced EPI scores (high profit, low ethics)."""
    return EPIScores(profit=0.95, ethics=0.3, violations=[])


@pytest.fixture
def scores_with_violations():
    """Create EPI scores with violations."""
    return EPIScores(profit=0.85, ethics=0.8, violations=[0.1, 0.15, 0.05])


@pytest.fixture
def severe_violation_scores():
    """Create EPI scores with severe violations."""
    return EPIScores(profit=0.9, ethics=0.85, violations=[0.5, 0.3])


# ============ Trust Accumulator Fixtures ============

@pytest.fixture
def trust_accumulator():
    """Create a default trust accumulator."""
    return TrustAccumulator(initial_trust=1.0, min_threshold=0.1)


@pytest.fixture
def sample_violations():
    """Create sample violation records."""
    import time
    base_time = int(time.time())
    return [
        ViolationRecord(0.1, base_time, "Minor compliance issue"),
        ViolationRecord(0.2, base_time + 100, "Moderate risk breach"),
        ViolationRecord(0.15, base_time + 200, "Ethics violation"),
    ]


# ============ Policy Validator Fixtures ============

@pytest.fixture
def policy_validator():
    """Create a policy validator."""
    return PolicyValidator()


@pytest.fixture
def valid_intent():
    """Create a valid intent that should pass validation."""
    return {
        'action': 'proposal',
        'roi_proxy': 0.85,
        'ethics_factors': {'env': 0.9, 'equity': 0.8, 'fairness': 0.85},
        'exposure_ratio': 0.2,
        'past_violations': []
    }


@pytest.fixture
def invalid_intent_low_ethics():
    """Create an intent with low ethics that should fail."""
    return {
        'action': 'proposal',
        'roi_proxy': 0.95,
        'ethics_factors': {'env': 0.3, 'equity': 0.2, 'fairness': 0.25},
        'exposure_ratio': 0.2,
        'past_violations': []
    }


@pytest.fixture
def sanctioned_intent():
    """Create a sanctioned intent that should fail compliance."""
    return {
        'action': 'transfer',
        'sanctioned': True,
        'roi_proxy': 0.85,
        'ethics_factors': {'env': 0.9, 'equity': 0.8},
    }


@pytest.fixture
def high_risk_intent():
    """Create a high-risk intent with high exposure."""
    return {
        'action': 'investment',
        'roi_proxy': 0.9,
        'ethics_factors': {'env': 0.8, 'equity': 0.75},
        'exposure_ratio': 0.9,  # High exposure
        'past_violations': []
    }


# ============ Thought Logger Fixtures ============

@pytest.fixture
def thought_logger(tmp_path):
    """Create a thought logger with temporary directory."""
    log_dir = tmp_path / "thought_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return ThoughtLogger(log_dir=str(log_dir), enable_ipfs=False)


@pytest.fixture
def sample_thought_data():
    """Create sample thought log data."""
    return {
        'agent_id': 'CEO-AI',
        'action': 'strategic_proposal',
        'reasoning': 'Market analysis indicates growth opportunity in healthcare AI.',
        'epi_trace': {
            'epi': 0.82,
            'hmean': 0.88,
            'balance_penalty': 0.95,
            'trust': 1.0,
            'reason': 'approved'
        },
        'inputs': {
            'sector': 'healthcare_ai',
            'investment_amount': 500000
        },
        'outputs': {
            'proposal_id': 'PROP-001',
            'approved': True
        }
    }


# ============ AI C-Suite Fixtures ============

@pytest.fixture
def ceo_agent(tmp_path):
    """Create a CEO-AI agent with temp logging directory."""
    return CEOAIAgent(
        agent_id="CEO-AI-TEST",
        epi_threshold=0.7,
        risk_tolerance=0.65
    )


@pytest.fixture
def cfo_agent(tmp_path):
    """Create a CFO-AI agent."""
    return CFOAIAgent(
        agent_id="CFO-AI-TEST",
        epi_threshold=0.7,
        treasury_balance=5000000
    )


@pytest.fixture
def budget_priorities():
    """Create sample budget priorities."""
    return {
        'r_and_d': 0.35,
        'marketing': 0.25,
        'operations': 0.15,
        'treasury_reserve': 0.15,
        'team_compensation': 0.10
    }


@pytest.fixture
def quarterly_metrics():
    """Create sample quarterly metrics."""
    return {
        'revenue': 3200000,
        'growth_rate': 0.28,
        'customer_satisfaction': 0.87,
        'ethics_compliance': 0.85
    }


# ============ Test Utilities ============

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
