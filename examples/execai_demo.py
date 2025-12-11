"""
ExecAI Demo: Simulated multi-agent AI governance workflow.

This demonstrates the MicroAI governance framework in action with
CEO-AI and CFO-AI agents making coordinated decisions under EPI constraints.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_c_suite.ceo_ai_stub import CEOAIAgent
from src.ai_c_suite.cfo_ai_stub import CFOAIAgent
from src.epi.calculator import EPICalculator


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}\n")


def main():
    """Run the ExecAI demonstration."""
    
    print_header("MicroAI ExecAI Governance Demo")
    print("Demonstrating autonomous AI C-Suite decision-making")
    print("with Ethical Profitability Index (EPI) constraints\n")
    
    time.sleep(1)
    
    # Initialize AI agents
    print_section("Phase 1: Initializing AI C-Suite")
    
    print("🤖 Initializing CEO-AI...")
    ceo = CEOAIAgent(epi_threshold=0.7, risk_tolerance=0.65)
    print(f"   ✓ CEO-AI initialized (EPI threshold: {ceo.epi_threshold})")
    
    print("\n💰 Initializing CFO-AI...")
    cfo = CFOAIAgent(epi_threshold=0.7, treasury_balance=5000000)
    print(f"   ✓ CFO-AI initialized (Treasury: ${cfo.treasury_balance:,.0f})")
    
    time.sleep(1)
    
    # CEO generates strategic proposals
    print_section("Phase 2: Strategic Planning (CEO-AI)")
    
    print("🎯 CEO-AI analyzing market opportunities...\n")
    time.sleep(1)
    
    sectors = [
        ('healthcare_ai', 500000),
        ('education_ai', 350000),
        ('fintech_ai', 600000),
    ]
    
    approved_proposals = []
    
    for sector, investment in sectors:
        print(f"📊 Evaluating {sector.replace('_', ' ').title()}...")
        proposal = ceo.generate_strategic_proposal(sector, investment, timeline_months=18)
        
        if proposal.approved:
            print(f"   ✅ APPROVED - EPI: {proposal.epi_score:.3f}")
            print(f"      Investment: ${proposal.investment_amount:,.0f}")
            print(f"      Expected ROI: {proposal.expected_roi*100:.1f}%")
            print(f"      Ethics Score: {proposal.ethics_score:.2f}")
            approved_proposals.append(proposal)
        else:
            print(f"   ❌ REJECTED - EPI: {proposal.epi_score:.3f}")
            print(f"      Reason: Below EPI threshold")
        
        time.sleep(0.5)
    
    # CFO processes approved proposals
    print_section("Phase 3: Financial Execution (CFO-AI)")
    
    if approved_proposals:
        print("💼 CFO-AI processing approved proposals...\n")
        time.sleep(1)
        
        for proposal in approved_proposals:
            print(f"💳 Processing payment for: {proposal.title}")
            payment = cfo.process_payment_request(
                recipient=f"Project-{proposal.proposal_id}",
                amount=proposal.investment_amount,
                category="r_and_d",
                description=proposal.description
            )
            
            if payment.approved:
                print(f"   ✅ Payment APPROVED - ${payment.amount:,.0f}")
                print(f"      EPI: {payment.epi_score:.3f}")
            else:
                print(f"   ❌ Payment REJECTED")
            
            time.sleep(0.5)
    else:
        print("⚠️  No proposals approved - skipping financial execution")
    
    print(f"\n💰 Treasury Balance: ${cfo.treasury_balance:,.0f}")
    
    # Budget allocation
    print_section("Phase 4: Quarterly Budget Allocation (CFO-AI)")
    
    print("📈 CFO-AI allocating Q4 budget...\n")
    time.sleep(1)
    
    allocation = cfo.allocate_budget(
        total_amount=1000000,
        priorities={
            'r_and_d': 0.35,
            'marketing': 0.25,
            'operations': 0.15,
            'treasury_reserve': 0.15,
            'team_compensation': 0.10
        }
    )
    
    if allocation.approved:
        print("✅ Budget Allocation APPROVED\n")
        print("   Breakdown:")
        for category, amount in allocation.allocations.items():
            percentage = (amount / allocation.total_amount) * 100
            print(f"      {category:20s}: ${amount:>10,.0f} ({percentage:>5.1f}%)")
        print(f"\n   EPI Score: {allocation.epi_score:.3f}")
    else:
        print(f"❌ Budget Allocation REJECTED")
        print(f"   Reason: {allocation.reasoning}")
    
    print(f"\n💰 Treasury Balance: ${cfo.treasury_balance:,.0f}")
    
    # Performance review
    print_section("Phase 5: Quarterly Performance Review (CEO-AI)")
    
    print("📊 CEO-AI conducting quarterly review...\n")
    time.sleep(1)
    
    performance = ceo.review_quarterly_performance({
        'revenue': 3200000,
        'growth_rate': 0.28,
        'customer_satisfaction': 0.87,
        'ethics_compliance': 0.85
    })
    
    print(f"Performance EPI: {performance['performance_epi']:.3f}")
    print(f"Status: {'✅ HEALTHY' if performance['performance_epi'] >= 0.7 else '⚠️  NEEDS ATTENTION'}")
    
    if performance['recommendations']:
        print(f"\nRecommendations:")
        for rec in performance['recommendations']:
            print(f"   • {rec}")
    else:
        print(f"\n✓ No critical issues - maintain current strategy")
    
    # Treasury health assessment
    print_section("Phase 6: Treasury Health Assessment (CFO-AI)")
    
    print("🏦 CFO-AI assessing treasury health...\n")
    time.sleep(1)
    
    health = cfo.assess_treasury_health()
    
    print(f"Treasury EPI: {health['treasury_epi']:.3f}")
    print(f"Status: {'✅ HEALTHY' if health['healthy'] else '⚠️  NEEDS ATTENTION'}")
    print(f"\nMetrics:")
    print(f"   Balance Ratio: {health['balance_ratio']*100:.1f}% of initial")
    print(f"   Utilization: {health['utilization']*100:.1f}%")
    
    if health['recommendations']:
        print(f"\nRecommendations:")
        for rec in health['recommendations']:
            print(f"   • {rec}")
    
    # Final summary
    print_section("Phase 7: Executive Summary")
    
    ceo_stats = ceo.get_agent_stats()
    cfo_report = cfo.generate_financial_report()
    
    print("🤖 CEO-AI Performance:")
    print(f"   Proposals Generated: {ceo_stats['proposals_generated']}")
    print(f"   Proposals Approved: {ceo_stats['proposals_approved']}")
    print(f"   Approval Rate: {ceo_stats['approval_rate']*100:.1f}%")
    print(f"   Total Investment Proposed: ${ceo_stats['total_investment_proposed']:,.0f}")
    
    print("\n💰 CFO-AI Performance:")
    print(f"   Payments Processed: {cfo_report['payments']['processed']}")
    print(f"   Payments Approved: {cfo_report['payments']['approved']}")
    print(f"   Approval Rate: {cfo_report['payments']['approval_rate']*100:.1f}%")
    print(f"   Treasury Utilization: {cfo_report['treasury']['utilization_rate']*100:.1f}%")
    
    print("\n📈 Overall System Health:")
    epi_calc = EPICalculator()
    
    # Calculate system-wide EPI
    from src.epi.calculator import EPIScores
    system_epi_scores = EPIScores(
        profit=min(ceo_stats['approval_rate'], 1.0),
        ethics=(performance['performance_epi'] + health['treasury_epi']) / 2,
        violations=[]
    )
    system_epi, system_healthy, _ = epi_calc.compute_epi(system_epi_scores)
    
    print(f"   System EPI: {system_epi:.3f}")
    print(f"   Status: {'✅ OPERATIONAL' if system_healthy else '⚠️  REQUIRES ATTENTION'}")
    
    print_header("Demo Complete")
    print("All AI agent decisions were constrained by EPI thresholds")
    print("Thought logs saved to ./logs/ directory")
    print("\nFor detailed audit trails, review the JSON logs in:")
    print("   • ./logs/ceo_ai/")
    print("   • ./logs/cfo_ai/")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
