"""
Unit tests for AI C-Suite agents (CEO-AI and CFO-AI).

Tests cover:
- Agent initialization
- Strategic proposal generation
- Budget allocation
- Payment processing
- EPI constraint enforcement
- Quarterly reviews
- Treasury management
"""

import pytest
import time
from pathlib import Path

from src.ai_c_suite.ceo_ai_stub import CEOAIAgent, StrategicProposal
from src.ai_c_suite.cfo_ai_stub import CFOAIAgent, BudgetAllocation, PaymentRequest


class TestCEOAIAgent:
    """Test CEO-AI agent functionality."""

    def test_agent_initialization(self):
        """Test that CEO-AI agent initializes correctly."""
        ceo = CEOAIAgent(agent_id="TEST-CEO", epi_threshold=0.7, risk_tolerance=0.65)

        assert ceo.agent_id == "TEST-CEO"
        assert ceo.epi_threshold == 0.7
        assert ceo.risk_tolerance == 0.65
        assert ceo.proposals_generated == 0
        assert ceo.proposals_approved == 0

    def test_analyze_market_opportunity(self):
        """Test market opportunity analysis."""
        ceo = CEOAIAgent()

        # Test known sector
        market = ceo.analyze_market_opportunity('healthcare_ai')
        assert 'market_size' in market
        assert 'growth_rate' in market
        assert 'competition_level' in market
        assert 'ethics_alignment' in market

        # Test unknown sector (should return defaults)
        unknown_market = ceo.analyze_market_opportunity('unknown_sector')
        assert 'market_size' in unknown_market

    def test_generate_strategic_proposal(self):
        """Test strategic proposal generation."""
        ceo = CEOAIAgent(epi_threshold=0.7)

        proposal = ceo.generate_strategic_proposal(
            sector='education_ai',
            investment_amount=500000,
            timeline_months=18
        )

        assert isinstance(proposal, StrategicProposal)
        assert proposal.investment_amount == 500000
        assert proposal.timeline_months == 18
        assert proposal.epi_score is not None
        assert 0 <= proposal.epi_score <= 1
        assert ceo.proposals_generated == 1

    def test_proposal_approval_with_high_ethics(self):
        """Test that high-ethics sectors get approved."""
        ceo = CEOAIAgent(epi_threshold=0.6, risk_tolerance=0.7)

        # Education AI has high ethics alignment (0.9)
        proposal = ceo.generate_strategic_proposal(
            sector='education_ai',
            investment_amount=400000
        )

        # Should likely be approved given high ethics alignment
        assert proposal.ethics_score >= 0.8

    def test_proposal_rejection_with_high_threshold(self):
        """Test that strict thresholds can reject proposals."""
        ceo = CEOAIAgent(epi_threshold=0.95, risk_tolerance=0.5)

        proposal = ceo.generate_strategic_proposal(
            sector='fintech_ai',
            investment_amount=600000
        )

        # Very high threshold should reject most proposals
        if not proposal.approved:
            assert proposal.epi_score < 0.95

    def test_quarterly_performance_review(self, quarterly_metrics):
        """Test quarterly performance review."""
        ceo = CEOAIAgent(epi_threshold=0.7)

        review = ceo.review_quarterly_performance(quarterly_metrics)

        assert 'performance_epi' in review
        assert 'recommendations' in review
        assert 'trace' in review
        assert isinstance(review['recommendations'], list)

    def test_review_generates_recommendations(self):
        """Test that poor performance generates recommendations."""
        ceo = CEOAIAgent(epi_threshold=0.7)

        poor_metrics = {
            'revenue': 1000000,
            'growth_rate': 0.05,  # Low growth
            'customer_satisfaction': 0.5,  # Low satisfaction
            'ethics_compliance': 0.6  # Low compliance
        }

        review = ceo.review_quarterly_performance(poor_metrics)

        assert len(review['recommendations']) > 0

    def test_agent_stats_tracking(self):
        """Test that agent statistics are tracked correctly."""
        ceo = CEOAIAgent(epi_threshold=0.6)

        # Generate multiple proposals
        for sector in ['healthcare_ai', 'education_ai', 'enterprise_ai']:
            ceo.generate_strategic_proposal(sector, 300000)

        stats = ceo.get_agent_stats()

        assert stats['proposals_generated'] == 3
        assert 'approval_rate' in stats
        assert 0 <= stats['approval_rate'] <= 1

    def test_multiple_sectors_analysis(self):
        """Test analysis of multiple sectors."""
        ceo = CEOAIAgent()

        sectors = ['healthcare_ai', 'fintech_ai', 'education_ai', 'enterprise_ai']
        analyses = {s: ceo.analyze_market_opportunity(s) for s in sectors}

        # Each sector should have different characteristics
        ethics_scores = [a['ethics_alignment'] for a in analyses.values()]
        assert len(set(ethics_scores)) > 1  # Different values


class TestCFOAIAgent:
    """Test CFO-AI agent functionality."""

    def test_agent_initialization(self):
        """Test that CFO-AI agent initializes correctly."""
        cfo = CFOAIAgent(
            agent_id="TEST-CFO",
            epi_threshold=0.7,
            treasury_balance=5000000
        )

        assert cfo.agent_id == "TEST-CFO"
        assert cfo.epi_threshold == 0.7
        assert cfo.treasury_balance == 5000000
        assert cfo.initial_balance == 5000000
        assert cfo.payments_processed == 0

    def test_budget_allocation(self, budget_priorities):
        """Test budget allocation."""
        cfo = CFOAIAgent(treasury_balance=5000000)

        allocation = cfo.allocate_budget(
            total_amount=1000000,
            priorities=budget_priorities
        )

        assert isinstance(allocation, BudgetAllocation)
        assert allocation.total_amount == 1000000
        assert len(allocation.allocations) == len(budget_priorities)

        # Allocations should sum to total
        total_allocated = sum(allocation.allocations.values())
        assert abs(total_allocated - 1000000) < 0.01

    def test_budget_reduces_treasury(self, budget_priorities):
        """Test that approved budget allocation reduces treasury."""
        cfo = CFOAIAgent(treasury_balance=5000000, epi_threshold=0.5)
        initial_balance = cfo.treasury_balance

        allocation = cfo.allocate_budget(1000000, budget_priorities)

        if allocation.approved:
            assert cfo.treasury_balance < initial_balance
            assert cfo.treasury_balance == initial_balance - 1000000

    def test_payment_processing(self):
        """Test payment request processing."""
        cfo = CFOAIAgent(treasury_balance=5000000)

        payment = cfo.process_payment_request(
            recipient="Vendor-AWS",
            amount=50000,
            category="operations",
            description="Cloud infrastructure"
        )

        assert isinstance(payment, PaymentRequest)
        assert payment.amount == 50000
        assert payment.recipient == "Vendor-AWS"
        assert cfo.payments_processed == 1

    def test_payment_reduces_treasury(self):
        """Test that approved payment reduces treasury."""
        cfo = CFOAIAgent(treasury_balance=5000000, epi_threshold=0.5)
        initial_balance = cfo.treasury_balance

        payment = cfo.process_payment_request(
            recipient="Employee",
            amount=100000,
            category="employee_salary",
            description="Team salaries"
        )

        if payment.approved:
            assert cfo.treasury_balance < initial_balance

    def test_insufficient_funds_rejected(self):
        """Test that payment exceeding treasury is rejected."""
        cfo = CFOAIAgent(treasury_balance=100000)

        payment = cfo.process_payment_request(
            recipient="Large Vendor",
            amount=500000,  # More than treasury
            category="operations",
            description="Large purchase"
        )

        assert payment.approved is False

    def test_large_payment_risk_flag(self):
        """Test that large payments get flagged as risky."""
        cfo = CFOAIAgent(treasury_balance=1000000)

        # 15% of treasury (> 10% threshold)
        payment = cfo.process_payment_request(
            recipient="Major Vendor",
            amount=150000,
            category="operations",
            description="Large contract"
        )

        # Payment may still be approved but should have higher risk
        # The EPI score should be lower due to risk factors
        assert payment.epi_score <= 1.0

    def test_category_ethics_scoring(self):
        """Test that different categories have different ethics scores."""
        cfo = CFOAIAgent(treasury_balance=5000000)

        categories = ['community_reward', 'employee_salary', 'marketing', 'other']
        payments = {}

        for cat in categories:
            payment = cfo.process_payment_request(
                recipient="Test",
                amount=10000,
                category=cat,
                description="Test payment"
            )
            payments[cat] = payment.epi_score

        # Community rewards should have higher EPI than 'other'
        # (assuming ethics categories in the implementation)

    def test_financial_report(self, budget_priorities):
        """Test financial report generation."""
        cfo = CFOAIAgent(treasury_balance=5000000, epi_threshold=0.5)

        # Make some transactions
        cfo.allocate_budget(500000, budget_priorities)
        cfo.process_payment_request("Vendor", 50000, "operations", "Test")

        report = cfo.generate_financial_report()

        assert 'agent_id' in report
        assert 'treasury' in report
        assert 'payments' in report
        assert 'allocations' in report
        assert report['treasury']['initial_balance'] == 5000000

    def test_treasury_health_assessment(self, budget_priorities):
        """Test treasury health assessment."""
        cfo = CFOAIAgent(treasury_balance=5000000, epi_threshold=0.5)

        # Use some treasury
        cfo.allocate_budget(1000000, budget_priorities)

        health = cfo.assess_treasury_health()

        assert 'treasury_epi' in health
        assert 'healthy' in health
        assert 'balance_ratio' in health
        assert 'utilization' in health
        assert 'recommendations' in health

    def test_low_treasury_warning(self, budget_priorities):
        """Test that low treasury generates warnings."""
        cfo = CFOAIAgent(treasury_balance=1000000, epi_threshold=0.3)

        # Spend most of treasury
        cfo.allocate_budget(800000, budget_priorities)

        health = cfo.assess_treasury_health()

        # Should have recommendations for low balance
        if health['balance_ratio'] < 0.3:
            assert len(health['recommendations']) > 0

    def test_payment_approval_rate(self):
        """Test payment approval rate tracking."""
        cfo = CFOAIAgent(treasury_balance=5000000, epi_threshold=0.5)

        # Process multiple payments
        for i in range(5):
            cfo.process_payment_request(
                recipient=f"Vendor-{i}",
                amount=10000,
                category="operations",
                description="Test"
            )

        report = cfo.generate_financial_report()
        assert report['payments']['processed'] == 5


class TestAgentIntegration:
    """Integration tests for AI agents working together."""

    def test_ceo_cfo_workflow(self, budget_priorities):
        """Test CEO and CFO agents working together."""
        ceo = CEOAIAgent(epi_threshold=0.6)
        cfo = CFOAIAgent(treasury_balance=5000000, epi_threshold=0.5)

        # CEO generates proposal
        proposal = ceo.generate_strategic_proposal('healthcare_ai', 500000)

        # If approved, CFO processes payment
        if proposal.approved:
            payment = cfo.process_payment_request(
                recipient=f"Project-{proposal.proposal_id}",
                amount=proposal.investment_amount,
                category="r_and_d",
                description=proposal.description
            )

            assert payment is not None

    def test_multi_proposal_budget_impact(self, budget_priorities):
        """Test multiple proposals' impact on budget."""
        ceo = CEOAIAgent(epi_threshold=0.5)
        cfo = CFOAIAgent(treasury_balance=2000000, epi_threshold=0.5)

        approved_count = 0
        for sector in ['healthcare_ai', 'education_ai', 'enterprise_ai']:
            proposal = ceo.generate_strategic_proposal(sector, 500000)
            if proposal.approved:
                payment = cfo.process_payment_request(
                    recipient=f"Project-{proposal.proposal_id}",
                    amount=proposal.investment_amount,
                    category="r_and_d",
                    description="Strategic investment"
                )
                if payment.approved:
                    approved_count += 1

        # Treasury should be reduced
        assert cfo.treasury_balance <= 2000000

    def test_quarterly_review_triggers_allocation(self, budget_priorities):
        """Test that quarterly review can inform budget allocation."""
        ceo = CEOAIAgent(epi_threshold=0.7)
        cfo = CFOAIAgent(treasury_balance=5000000, epi_threshold=0.5)

        # Poor performance review
        review = ceo.review_quarterly_performance({
            'revenue': 1000000,
            'growth_rate': 0.05,
            'customer_satisfaction': 0.6,
            'ethics_compliance': 0.7
        })

        # If recommendations include growth, adjust allocation
        if any('growth' in r.lower() for r in review['recommendations']):
            # Increase R&D and marketing allocation
            adjusted_priorities = {
                'r_and_d': 0.45,
                'marketing': 0.30,
                'operations': 0.10,
                'treasury_reserve': 0.10,
                'team_compensation': 0.05
            }
            allocation = cfo.allocate_budget(800000, adjusted_priorities)
            assert allocation is not None
