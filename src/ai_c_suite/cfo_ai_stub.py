"""
CFO-AI Stub: Financial management agent for the MicroAI governance framework.

This is a simplified simulation of the CFO-AI agent described in the MicroAI
architecture. In production, this would integrate with financial systems,
treasury management, and on-chain payment execution.

Responsibilities:
- Treasury management and budget allocation
- Financial risk assessment
- Payment execution and vendor management
- Financial reporting and compliance
- EPI-constrained financial decisions
"""

import random
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from src.epi.calculator import EPICalculator, EPIScores
from src.policy_engine.logger import ThoughtLogger


class AllocationCategory(Enum):
    """Budget allocation categories."""
    R_AND_D = "r_and_d"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    TREASURY_RESERVE = "treasury_reserve"
    TEAM_COMPENSATION = "team_compensation"
    COMMUNITY_REWARDS = "community_rewards"


@dataclass
class BudgetAllocation:
    """A budget allocation decision."""
    allocation_id: str
    total_amount: float
    allocations: Dict[str, float]
    reasoning: str
    epi_score: float
    approved: bool
    timestamp: int


@dataclass
class PaymentRequest:
    """A payment request to be processed."""
    request_id: str
    recipient: str
    amount: float
    category: str
    description: str
    approved: bool
    epi_score: float


class CFOAIAgent:
    """
    Simulated CFO-AI agent for financial management.
    
    In production, this would integrate with:
    - Treasury management systems (Gnosis Safe, etc.)
    - Payment processors and banking APIs
    - Financial data providers
    - On-chain governance contracts
    """
    
    def __init__(
        self,
        agent_id: str = "CFO-AI",
        epi_threshold: float = 0.7,
        treasury_balance: float = 5000000.0
    ):
        """
        Initialize CFO-AI agent.
        
        Args:
            agent_id: Unique identifier for this agent
            epi_threshold: Minimum EPI score for financial decisions
            treasury_balance: Initial treasury balance
        """
        self.agent_id = agent_id
        self.epi_threshold = epi_threshold
        self.treasury_balance = treasury_balance
        self.initial_balance = treasury_balance
        
        # Initialize subsystems
        self.epi_calc = EPICalculator(threshold=epi_threshold)
        self.thought_logger = ThoughtLogger(log_dir="./logs/cfo_ai")
        
        # Financial tracking
        self.payments_processed = 0
        self.payments_approved = 0
        self.total_disbursed = 0.0
        self.allocations_made = 0
        
    def allocate_budget(
        self,
        total_amount: float,
        priorities: Dict[str, float]
    ) -> BudgetAllocation:
        """
        Allocate budget across different categories based on priorities.
        
        Args:
            total_amount: Total amount to allocate
            priorities: Dictionary of category priorities (weights)
            
        Returns:
            BudgetAllocation object
        """
        # Normalize priorities to sum to 1.0
        total_priority = sum(priorities.values())
        normalized_priorities = {
            k: v / total_priority for k, v in priorities.items()
        }
        
        # Calculate allocations
        allocations = {
            category: total_amount * weight
            for category, weight in normalized_priorities.items()
        }
        
        # Calculate EPI for this allocation
        # Ethics score based on balance of allocations
        r_and_d_ratio = allocations.get('r_and_d', 0) / total_amount
        community_ratio = allocations.get('community_rewards', 0) / total_amount
        reserve_ratio = allocations.get('treasury_reserve', 0) / total_amount
        
        ethics_score = (r_and_d_ratio * 0.4 + community_ratio * 0.3 + reserve_ratio * 0.3)
        
        # Profit score based on growth-oriented allocations
        growth_categories = ['r_and_d', 'marketing', 'operations']
        growth_ratio = sum(allocations.get(cat, 0) for cat in growth_categories) / total_amount
        profit_score = min(growth_ratio, 1.0)
        
        epi_scores = EPIScores(
            profit=profit_score,
            ethics=ethics_score,
            violations=[]
        )
        epi, approved, trace = self.epi_calc.compute_epi(epi_scores)
        
        # Generate allocation ID
        self.allocations_made += 1
        allocation_id = f"ALLOC-{int(time.time())}-{self.allocations_made:03d}"
        
        # Build reasoning
        reasoning = (
            f"Budget allocation of ${total_amount:,.0f} across {len(allocations)} categories. "
            f"Growth-oriented: {growth_ratio*100:.1f}%, Community/Reserve: {(community_ratio+reserve_ratio)*100:.1f}%. "
            f"EPI Score: {epi:.3f}. "
        )
        
        if approved:
            reasoning += "Allocation approved and executed."
            self.treasury_balance -= total_amount
            self.total_disbursed += total_amount
        else:
            reasoning += f"Allocation rejected: {trace['reason']}"
        
        allocation = BudgetAllocation(
            allocation_id=allocation_id,
            total_amount=total_amount,
            allocations=allocations,
            reasoning=reasoning,
            epi_score=epi,
            approved=approved,
            timestamp=int(time.time())
        )
        
        # Log the decision
        self.thought_logger.log_thought(
            agent_id=self.agent_id,
            action="budget_allocation",
            reasoning=reasoning,
            epi_trace=trace,
            inputs={
                'total_amount': total_amount,
                'priorities': priorities
            },
            outputs={
                'allocation_id': allocation_id,
                'allocations': allocations,
                'approved': approved,
                'treasury_balance': self.treasury_balance
            }
        )
        
        return allocation
    
    def process_payment_request(
        self,
        recipient: str,
        amount: float,
        category: str,
        description: str
    ) -> PaymentRequest:
        """
        Process a payment request with EPI validation.
        
        Args:
            recipient: Payment recipient identifier
            amount: Payment amount
            category: Payment category
            description: Payment description
            
        Returns:
            PaymentRequest object
        """
        # Risk assessment
        risk_factors = []
        
        # Check treasury balance
        if amount > self.treasury_balance * 0.1:
            risk_factors.append("Large payment (>10% of treasury)")
        
        if amount > self.treasury_balance:
            risk_factors.append("Insufficient funds")
        
        # Category-based ethics scoring
        ethics_categories = {
            'vendor_payment': 0.8,
            'employee_salary': 0.9,
            'community_reward': 0.95,
            'r_and_d': 0.85,
            'marketing': 0.7,
            'other': 0.6
        }
        ethics_score = ethics_categories.get(category, 0.6)
        
        # Profit score (inverse of cost impact)
        cost_impact = amount / max(self.treasury_balance, 1)
        profit_score = max(0.1, 1.0 - cost_impact)
        
        # Violations based on risk factors
        violations = [0.2] * len(risk_factors)
        
        epi_scores = EPIScores(
            profit=profit_score,
            ethics=ethics_score,
            violations=violations
        )
        epi, approved, trace = self.epi_calc.compute_epi(epi_scores)
        
        # Override approval if insufficient funds
        if amount > self.treasury_balance:
            approved = False
            trace['reason'] = 'rejected: insufficient treasury funds'
        
        # Generate request ID
        self.payments_processed += 1
        request_id = f"PAY-{int(time.time())}-{self.payments_processed:03d}"
        
        reasoning = (
            f"Payment request: ${amount:,.0f} to {recipient} for {category}. "
            f"Treasury balance: ${self.treasury_balance:,.0f}. "
            f"Risk factors: {', '.join(risk_factors) if risk_factors else 'None'}. "
            f"EPI Score: {epi:.3f}. "
        )
        
        if approved:
            reasoning += "Payment approved and executed."
            self.treasury_balance -= amount
            self.total_disbursed += amount
            self.payments_approved += 1
        else:
            reasoning += f"Payment rejected: {trace['reason']}"
        
        payment = PaymentRequest(
            request_id=request_id,
            recipient=recipient,
            amount=amount,
            category=category,
            description=description,
            approved=approved,
            epi_score=epi
        )
        
        # Log the decision
        self.thought_logger.log_thought(
            agent_id=self.agent_id,
            action="payment_processing",
            reasoning=reasoning,
            epi_trace=trace,
            inputs={
                'recipient': recipient,
                'amount': amount,
                'category': category,
                'description': description
            },
            outputs={
                'request_id': request_id,
                'approved': approved,
                'treasury_balance': self.treasury_balance
            },
            metadata={
                'risk_factors': risk_factors
            }
        )
        
        return payment
    
    def generate_financial_report(self) -> Dict[str, Any]:
        """
        Generate a financial report of the agent's activity.
        
        Returns:
            Financial report dictionary
        """
        return {
            'agent_id': self.agent_id,
            'treasury': {
                'initial_balance': self.initial_balance,
                'current_balance': self.treasury_balance,
                'total_disbursed': self.total_disbursed,
                'utilization_rate': self.total_disbursed / self.initial_balance
            },
            'payments': {
                'processed': self.payments_processed,
                'approved': self.payments_approved,
                'approval_rate': self.payments_approved / max(self.payments_processed, 1)
            },
            'allocations': {
                'made': self.allocations_made
            },
            'epi_threshold': self.epi_threshold
        }
    
    def assess_treasury_health(self) -> Dict[str, Any]:
        """
        Assess the health of the treasury and provide recommendations.
        
        Returns:
            Treasury health assessment
        """
        utilization = self.total_disbursed / self.initial_balance
        balance_ratio = self.treasury_balance / self.initial_balance
        
        # Calculate treasury EPI
        # Profit: based on efficient utilization
        profit_score = min(utilization * 1.5, 1.0)  # Reward utilization up to 67%
        
        # Ethics: based on maintaining reserves
        ethics_score = balance_ratio  # Higher balance = more ethical (sustainability)
        
        epi_scores = EPIScores(
            profit=profit_score,
            ethics=ethics_score,
            violations=[]
        )
        epi, healthy, trace = self.epi_calc.compute_epi(epi_scores)
        
        # Generate recommendations
        recommendations = []
        
        if balance_ratio < 0.3:
            recommendations.append("Critical: Treasury below 30% - seek funding or reduce spending")
        elif balance_ratio < 0.5:
            recommendations.append("Warning: Treasury below 50% - monitor cash flow closely")
        
        if utilization > 0.8:
            recommendations.append("High utilization - ensure ROI on investments")
        elif utilization < 0.3:
            recommendations.append("Low utilization - consider growth investments")
        
        reasoning = (
            f"Treasury Health Assessment: Balance ${self.treasury_balance:,.0f} "
            f"({balance_ratio*100:.1f}% of initial). "
            f"Utilization: {utilization*100:.1f}%. "
            f"Treasury EPI: {epi:.3f}. "
            f"Status: {'Healthy' if healthy else 'Needs Attention'}."
        )
        
        self.thought_logger.log_thought(
            agent_id=self.agent_id,
            action="treasury_assessment",
            reasoning=reasoning,
            epi_trace=trace,
            inputs={
                'current_balance': self.treasury_balance,
                'utilization': utilization
            },
            outputs={
                'treasury_epi': epi,
                'healthy': healthy,
                'recommendations': recommendations
            }
        )
        
        return {
            'treasury_epi': epi,
            'healthy': healthy,
            'balance_ratio': balance_ratio,
            'utilization': utilization,
            'recommendations': recommendations,
            'trace': trace
        }


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("MicroAI CFO-AI Agent - Demo")
    print("=" * 60)
    
    # Initialize CFO-AI
    cfo = CFOAIAgent(epi_threshold=0.7, treasury_balance=5000000)
    
    print(f"\n💰 Initial Treasury: ${cfo.treasury_balance:,.0f}\n")
    
    # Budget allocation
    print("[CFO-AI] Allocating Q4 budget...\n")
    
    allocation = cfo.allocate_budget(
        total_amount=1200000,
        priorities={
            'r_and_d': 0.40,
            'marketing': 0.20,
            'operations': 0.15,
            'treasury_reserve': 0.15,
            'team_compensation': 0.10
        }
    )
    
    if allocation.approved:
        print("✅ Budget Allocation APPROVED")
        for category, amount in allocation.allocations.items():
            print(f"  {category}: ${amount:,.0f}")
        print(f"  EPI Score: {allocation.epi_score:.3f}")
    else:
        print(f"❌ Budget Allocation REJECTED: {allocation.reasoning}")
    
    print(f"\n💰 Treasury Balance: ${cfo.treasury_balance:,.0f}\n")
    
    # Process payments
    print("[CFO-AI] Processing payment requests...\n")
    
    payments = [
        ("Vendor-AWS", 50000, "operations", "Cloud infrastructure Q4"),
        ("Team-Engineering", 300000, "employee_salary", "Engineering team salaries"),
        ("Community-DAO", 25000, "community_reward", "Community contributor rewards"),
        ("Marketing-Agency", 75000, "marketing", "Q4 marketing campaign"),
    ]
    
    for recipient, amount, category, description in payments:
        payment = cfo.process_payment_request(recipient, amount, category, description)
        status = "✅ APPROVED" if payment.approved else "❌ REJECTED"
        print(f"{status} {recipient}: ${amount:,.0f} (EPI: {payment.epi_score:.3f})")
    
    print(f"\n💰 Treasury Balance: ${cfo.treasury_balance:,.0f}\n")
    
    # Treasury health assessment
    print("[CFO-AI] Assessing treasury health...\n")
    
    health = cfo.assess_treasury_health()
    status = "✅ HEALTHY" if health['healthy'] else "⚠️  NEEDS ATTENTION"
    print(f"{status} Treasury EPI: {health['treasury_epi']:.3f}")
    print(f"  Balance: {health['balance_ratio']*100:.1f}% of initial")
    print(f"  Utilization: {health['utilization']*100:.1f}%")
    
    if health['recommendations']:
        print(f"  Recommendations:")
        for rec in health['recommendations']:
            print(f"    • {rec}")
    
    # Financial report
    print("\n" + "=" * 60)
    report = cfo.generate_financial_report()
    print("Financial Report:")
    print(f"  Treasury:")
    print(f"    Initial: ${report['treasury']['initial_balance']:,.0f}")
    print(f"    Current: ${report['treasury']['current_balance']:,.0f}")
    print(f"    Disbursed: ${report['treasury']['total_disbursed']:,.0f}")
    print(f"  Payments:")
    print(f"    Processed: {report['payments']['processed']}")
    print(f"    Approved: {report['payments']['approved']}")
    print(f"    Approval Rate: {report['payments']['approval_rate']*100:.1f}%")
