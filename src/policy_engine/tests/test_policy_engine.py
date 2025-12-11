"""
Unit tests for the Policy Engine module.

Tests cover:
- PolicyValidator intent validation
- ThoughtLogger functionality
- EPI integration
- Compliance checks
- Risk assessment
"""

import pytest
import json
import time
from pathlib import Path

from src.policy_engine.validator import PolicyValidator
from src.policy_engine.logger import ThoughtLogger, ThoughtRecord
from src.epi.calculator import EPIScores


class TestPolicyValidator:
    """Test PolicyValidator functionality."""

    def test_validator_initialization(self, policy_validator):
        """Test that PolicyValidator initializes correctly."""
        assert policy_validator is not None
        assert policy_validator.epi_calc is not None

    def test_valid_intent_approved(self, policy_validator, valid_intent):
        """Test that valid intents are approved."""
        result = policy_validator.validate_intent(valid_intent)

        assert result['approved'] is True
        assert result['reason'] == 'Approved'
        assert 'epi_trace' in result
        assert result['epi_trace']['epi'] >= 0.7

    def test_low_ethics_rejected(self, policy_validator, invalid_intent_low_ethics):
        """Test that low ethics intents are rejected."""
        result = policy_validator.validate_intent(invalid_intent_low_ethics)

        assert result['approved'] is False
        assert result['reason'] == 'EPI rejection'
        assert result['epi_trace']['epi'] < 0.7

    def test_sanctioned_intent_rejected(self, policy_validator, sanctioned_intent):
        """Test that sanctioned intents are rejected."""
        result = policy_validator.validate_intent(sanctioned_intent)

        assert result['approved'] is False
        assert result['reason'] == 'Compliance fail'

    def test_high_risk_intent_rejected(self, policy_validator, high_risk_intent):
        """Test that high-risk intents are rejected."""
        result = policy_validator.validate_intent(high_risk_intent)

        # High exposure ratio should result in low risk score
        assert result['risk_score'] < 0.5
        if result['approved'] is False:
            assert 'Risk' in result['reason'] or 'EPI' in result['reason']

    def test_intent_with_violations(self, policy_validator):
        """Test intent validation with past violations."""
        intent = {
            'action': 'proposal',
            'roi_proxy': 0.85,
            'ethics_factors': {'env': 0.85, 'equity': 0.8},
            'past_violations': [0.1, 0.2, 0.15]
        }

        result = policy_validator.validate_intent(intent)

        # Violations should reduce trust and potentially EPI
        assert 'epi_trace' in result
        assert result['epi_trace']['trust'] < 1.0

    def test_empty_ethics_factors(self, policy_validator):
        """Test intent with empty ethics factors."""
        intent = {
            'action': 'proposal',
            'roi_proxy': 0.8,
            'ethics_factors': {},
        }

        # Should handle empty ethics gracefully
        result = policy_validator.validate_intent(intent)
        assert 'approved' in result

    def test_missing_fields_defaults(self, policy_validator):
        """Test that missing fields use reasonable defaults."""
        intent = {
            'action': 'proposal',
            'ethics_factors': {'env': 0.8}
        }

        result = policy_validator.validate_intent(intent)
        assert 'approved' in result


class TestThoughtLogger:
    """Test ThoughtLogger functionality."""

    def test_logger_initialization(self, thought_logger):
        """Test that ThoughtLogger initializes correctly."""
        assert thought_logger is not None
        assert thought_logger.log_dir.exists()
        assert len(thought_logger.session_id) == 16

    def test_log_thought_returns_hash(self, thought_logger, sample_thought_data):
        """Test that logging a thought returns a valid hash."""
        thought_hash = thought_logger.log_thought(
            agent_id=sample_thought_data['agent_id'],
            action=sample_thought_data['action'],
            reasoning=sample_thought_data['reasoning'],
            epi_trace=sample_thought_data['epi_trace'],
            inputs=sample_thought_data['inputs'],
            outputs=sample_thought_data['outputs']
        )

        assert thought_hash is not None
        assert len(thought_hash) == 64  # SHA256 hex length

    def test_log_creates_file(self, thought_logger, sample_thought_data):
        """Test that logging creates a JSON file."""
        initial_files = list(thought_logger.log_dir.glob("*.json"))

        thought_logger.log_thought(
            agent_id=sample_thought_data['agent_id'],
            action=sample_thought_data['action'],
            reasoning=sample_thought_data['reasoning'],
            epi_trace=sample_thought_data['epi_trace'],
            inputs=sample_thought_data['inputs'],
            outputs=sample_thought_data['outputs']
        )

        new_files = list(thought_logger.log_dir.glob("*.json"))
        assert len(new_files) == len(initial_files) + 1

    def test_log_file_content_valid(self, thought_logger, sample_thought_data):
        """Test that log file contains valid JSON with expected fields."""
        thought_logger.log_thought(
            agent_id=sample_thought_data['agent_id'],
            action=sample_thought_data['action'],
            reasoning=sample_thought_data['reasoning'],
            epi_trace=sample_thought_data['epi_trace'],
            inputs=sample_thought_data['inputs'],
            outputs=sample_thought_data['outputs']
        )

        log_files = list(thought_logger.log_dir.glob("*.json"))
        assert len(log_files) > 0

        with open(log_files[0], 'r') as f:
            data = json.load(f)

        assert data['agent_id'] == sample_thought_data['agent_id']
        assert data['action'] == sample_thought_data['action']
        assert data['reasoning'] == sample_thought_data['reasoning']
        assert 'timestamp' in data
        assert 'epi_trace' in data

    def test_get_thought_history(self, thought_logger, sample_thought_data):
        """Test retrieving thought history."""
        # Log multiple thoughts
        for i in range(3):
            thought_logger.log_thought(
                agent_id=f"Agent-{i}",
                action="test_action",
                reasoning=f"Test reasoning {i}",
                epi_trace=sample_thought_data['epi_trace'],
                inputs=sample_thought_data['inputs'],
                outputs=sample_thought_data['outputs']
            )
            time.sleep(0.1)  # Ensure different timestamps

        history = thought_logger.get_thought_history(limit=10)
        assert len(history) >= 3

    def test_filter_by_agent_id(self, thought_logger, sample_thought_data):
        """Test filtering history by agent ID."""
        # Log thoughts from different agents
        thought_logger.log_thought(
            agent_id="CEO-AI",
            action="strategic",
            reasoning="CEO reasoning",
            epi_trace=sample_thought_data['epi_trace'],
            inputs={},
            outputs={}
        )

        thought_logger.log_thought(
            agent_id="CFO-AI",
            action="financial",
            reasoning="CFO reasoning",
            epi_trace=sample_thought_data['epi_trace'],
            inputs={},
            outputs={}
        )

        ceo_history = thought_logger.get_thought_history(agent_id="CEO-AI")
        assert all(r.agent_id == "CEO-AI" for r in ceo_history)

    def test_verify_thought_integrity(self, thought_logger, sample_thought_data):
        """Test thought integrity verification."""
        import hashlib

        thought_logger.log_thought(
            agent_id=sample_thought_data['agent_id'],
            action=sample_thought_data['action'],
            reasoning=sample_thought_data['reasoning'],
            epi_trace=sample_thought_data['epi_trace'],
            inputs=sample_thought_data['inputs'],
            outputs=sample_thought_data['outputs']
        )

        log_files = list(thought_logger.log_dir.glob("*.json"))
        with open(log_files[0], 'r') as f:
            content = f.read()

        computed_hash = hashlib.sha256(content.encode()).hexdigest()
        assert thought_logger.verify_thought(content, computed_hash)

    def test_generate_audit_report(self, thought_logger, sample_thought_data):
        """Test audit report generation."""
        # Log some thoughts
        for i in range(5):
            thought_logger.log_thought(
                agent_id="TEST-AI",
                action="test_action",
                reasoning=f"Test {i}",
                epi_trace=sample_thought_data['epi_trace'],
                inputs={},
                outputs={}
            )

        report = thought_logger.generate_audit_report()

        assert 'session_id' in report
        assert 'total_records' in report
        assert report['total_records'] >= 5
        assert 'agent_counts' in report
        assert 'action_counts' in report
        assert 'epi_statistics' in report

    def test_mock_ipfs_hash(self, thought_logger, sample_thought_data):
        """Test mock IPFS hash generation."""
        content = json.dumps(sample_thought_data)
        ipfs_hash = thought_logger._push_to_ipfs(content)

        # Mock IPFS hash should start with 'Qm'
        assert ipfs_hash.startswith('Qm')
        assert len(ipfs_hash) == 46  # Standard IPFS CID v0 length


class TestIntegration:
    """Integration tests for policy engine."""

    def test_validator_with_logger(self, policy_validator, thought_logger, valid_intent):
        """Test that validator can integrate with thought logger."""
        result = policy_validator.validate_intent(valid_intent)

        # Log the validation result
        thought_hash = thought_logger.log_thought(
            agent_id="POLICY-ENGINE",
            action="intent_validation",
            reasoning=f"Validated intent: {result['reason']}",
            epi_trace=result['epi_trace'],
            inputs=valid_intent,
            outputs={'approved': result['approved']}
        )

        assert thought_hash is not None

        # Verify we can retrieve it
        history = thought_logger.get_thought_history(agent_id="POLICY-ENGINE")
        assert len(history) > 0

    def test_end_to_end_validation_flow(self, policy_validator, thought_logger):
        """Test complete validation flow from intent to logged decision."""
        # Create intent
        intent = {
            'action': 'strategic_investment',
            'roi_proxy': 0.82,
            'ethics_factors': {
                'environmental': 0.85,
                'equity': 0.78,
                'transparency': 0.9
            },
            'exposure_ratio': 0.3,
            'past_violations': []
        }

        # Validate
        result = policy_validator.validate_intent(intent)

        # Log
        thought_logger.log_thought(
            agent_id="GOVERNANCE",
            action="investment_decision",
            reasoning=f"Investment decision: {result['reason']}",
            epi_trace=result['epi_trace'],
            inputs=intent,
            outputs={
                'approved': result['approved'],
                'risk_score': result['risk_score']
            }
        )

        # Generate report
        report = thought_logger.generate_audit_report()

        assert report['total_records'] >= 1
        assert 'GOVERNANCE' in report['agent_counts']
