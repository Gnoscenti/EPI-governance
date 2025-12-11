"""
MicroAI Governance API

FastAPI server for the EPI-based governance framework.
Provides REST endpoints for:
- EPI calculation and validation
- Policy validation
- AI agent interactions
- Thought logging and audit
- Governance proposal management
"""

import os
import time
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# Import EPI modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.epi.calculator import EPICalculator, EPIScores
from src.epi.trust_accumulator import TrustAccumulator, ViolationRecord
from src.policy_engine.validator import PolicyValidator
from src.policy_engine.logger import ThoughtLogger
from src.ai_c_suite.ceo_ai_stub import CEOAIAgent
from src.ai_c_suite.cfo_ai_stub import CFOAIAgent


# ============ Pydantic Models ============

class EPIScoreInput(BaseModel):
    """Input for EPI calculation."""
    profit: float = Field(..., ge=0.0, le=1.0, description="Profit score (0-1)")
    ethics: float = Field(..., ge=0.0, le=1.0, description="Ethics score (0-1)")
    violations: List[float] = Field(default=[], description="List of violation severities (0-1)")
    stakeholder_sentiment: Optional[float] = Field(None, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "profit": 0.85,
                "ethics": 0.78,
                "violations": [0.1, 0.05],
                "stakeholder_sentiment": 0.82
            }
        }


class EPIResponse(BaseModel):
    """Response from EPI calculation."""
    epi: float
    valid: bool
    threshold: float
    trace: Dict[str, Any]
    timestamp: str


class IntentInput(BaseModel):
    """Input for policy validation."""
    action: str = Field(..., description="Type of action")
    roi_proxy: float = Field(0.5, ge=0.0, le=1.0)
    ethics_factors: Dict[str, float] = Field(default={})
    exposure_ratio: float = Field(0.0, ge=0.0, le=1.0)
    past_violations: List[float] = Field(default=[])
    metadata: Optional[Dict[str, Any]] = None


class ValidationResponse(BaseModel):
    """Response from policy validation."""
    approved: bool
    reason: str
    epi_trace: Dict[str, Any]
    risk_score: float
    timestamp: str


class ProposalInput(BaseModel):
    """Input for strategic proposal generation."""
    sector: str = Field(..., description="Target sector")
    investment_amount: float = Field(..., gt=0)
    timeline_months: int = Field(18, ge=1, le=60)


class ProposalResponse(BaseModel):
    """Response for strategic proposal."""
    proposal_id: str
    title: str
    approved: bool
    epi_score: float
    profit_score: float
    ethics_score: float
    expected_roi: float
    reasoning: str
    timestamp: str


class BudgetInput(BaseModel):
    """Input for budget allocation."""
    total_amount: float = Field(..., gt=0)
    priorities: Dict[str, float] = Field(...)

    @validator('priorities')
    def priorities_must_sum_to_one(cls, v):
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError('Priorities must sum to 1.0')
        return v


class PaymentInput(BaseModel):
    """Input for payment request."""
    recipient: str
    amount: float = Field(..., gt=0)
    category: str
    description: str


class ThoughtLogInput(BaseModel):
    """Input for thought logging."""
    agent_id: str
    action: str
    reasoning: str
    epi_trace: Dict[str, Any]
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    version: str
    timestamp: str
    components: Dict[str, str]


# ============ Application Setup ============

# Global instances (initialized on startup)
epi_calculator: Optional[EPICalculator] = None
trust_accumulator: Optional[TrustAccumulator] = None
policy_validator: Optional[PolicyValidator] = None
thought_logger: Optional[ThoughtLogger] = None
ceo_agent: Optional[CEOAIAgent] = None
cfo_agent: Optional[CFOAIAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global epi_calculator, trust_accumulator, policy_validator
    global thought_logger, ceo_agent, cfo_agent

    # Startup
    log_dir = Path(os.getenv("LOG_DIR", "./logs/api"))
    log_dir.mkdir(parents=True, exist_ok=True)

    epi_threshold = float(os.getenv("EPI_THRESHOLD", "0.7"))
    treasury_balance = float(os.getenv("TREASURY_BALANCE", "5000000"))

    epi_calculator = EPICalculator(threshold=epi_threshold)
    trust_accumulator = TrustAccumulator(initial_trust=1.0)
    policy_validator = PolicyValidator()
    thought_logger = ThoughtLogger(log_dir=str(log_dir), enable_ipfs=False)
    ceo_agent = CEOAIAgent(epi_threshold=epi_threshold)
    cfo_agent = CFOAIAgent(epi_threshold=epi_threshold, treasury_balance=treasury_balance)

    yield

    # Cleanup (if needed)


app = FastAPI(
    title="MicroAI Governance API",
    description="REST API for EPI-based AI governance framework",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Health Endpoints ============

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health status."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        components={
            "epi_calculator": "ok" if epi_calculator else "not_initialized",
            "policy_validator": "ok" if policy_validator else "not_initialized",
            "thought_logger": "ok" if thought_logger else "not_initialized",
            "ceo_agent": "ok" if ceo_agent else "not_initialized",
            "cfo_agent": "ok" if cfo_agent else "not_initialized",
        }
    )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "MicroAI Governance API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ============ EPI Endpoints ============

@app.post("/epi/calculate", response_model=EPIResponse, tags=["EPI"])
async def calculate_epi(scores: EPIScoreInput):
    """Calculate Ethical Profitability Index."""
    if not epi_calculator:
        raise HTTPException(status_code=503, detail="EPI calculator not initialized")

    epi_scores = EPIScores(
        profit=scores.profit,
        ethics=scores.ethics,
        violations=scores.violations,
        stakeholder_sentiment=scores.stakeholder_sentiment
    )

    include_sentiment = scores.stakeholder_sentiment is not None
    epi, valid, trace = epi_calculator.compute_epi(epi_scores, include_sentiment=include_sentiment)

    return EPIResponse(
        epi=round(epi, 6),
        valid=valid,
        threshold=epi_calculator.threshold,
        trace=trace,
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/epi/optimize", tags=["EPI"])
async def optimize_epi(
    target_epi: float = Query(..., ge=0.0, le=1.0),
    current_ethics: float = Query(..., ge=0.0, le=1.0),
    violations: List[float] = Query(default=[])
):
    """Find optimal profit level to achieve target EPI."""
    if not epi_calculator:
        raise HTTPException(status_code=503, detail="EPI calculator not initialized")

    result = epi_calculator.optimize_for_golden_ratio(
        target_epi=target_epi,
        current_ethics=current_ethics,
        violations=violations
    )

    return {
        **result,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/epi/threshold", tags=["EPI"])
async def get_threshold():
    """Get current EPI threshold."""
    if not epi_calculator:
        raise HTTPException(status_code=503, detail="EPI calculator not initialized")

    return {
        "threshold": epi_calculator.threshold,
        "phi_weight": epi_calculator.phi_weight
    }


# ============ Trust Endpoints ============

@app.get("/trust/current", tags=["Trust"])
async def get_current_trust():
    """Get current trust level."""
    if not trust_accumulator:
        raise HTTPException(status_code=503, detail="Trust accumulator not initialized")

    return {
        "trust": trust_accumulator.current_trust,
        "violation_count": len(trust_accumulator.violation_history),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/trust/violation", tags=["Trust"])
async def record_violation(severity: float = Query(..., ge=0.0, le=1.0), description: str = ""):
    """Record a new violation."""
    if not trust_accumulator:
        raise HTTPException(status_code=503, detail="Trust accumulator not initialized")

    old_trust = trust_accumulator.current_trust
    trust_accumulator.record_violation(severity, description)

    return {
        "old_trust": old_trust,
        "new_trust": trust_accumulator.current_trust,
        "severity": severity,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/trust/history", tags=["Trust"])
async def get_trust_history(limit: int = Query(10, ge=1, le=100)):
    """Get violation history."""
    if not trust_accumulator:
        raise HTTPException(status_code=503, detail="Trust accumulator not initialized")

    history = trust_accumulator.get_violation_history(limit=limit)

    return {
        "violations": [
            {
                "severity": v.severity,
                "timestamp": v.timestamp,
                "description": v.description
            }
            for v in history
        ],
        "count": len(history)
    }


# ============ Policy Endpoints ============

@app.post("/policy/validate", response_model=ValidationResponse, tags=["Policy"])
async def validate_intent(intent: IntentInput, background_tasks: BackgroundTasks):
    """Validate an intent against policy rules."""
    if not policy_validator or not thought_logger:
        raise HTTPException(status_code=503, detail="Policy engine not initialized")

    intent_dict = intent.model_dump()
    result = policy_validator.validate_intent(intent_dict)

    # Log the validation in background
    background_tasks.add_task(
        thought_logger.log_thought,
        agent_id="POLICY-API",
        action="intent_validation",
        reasoning=f"Validated intent: {result['reason']}",
        epi_trace=result['epi_trace'],
        inputs=intent_dict,
        outputs={'approved': result['approved']}
    )

    return ValidationResponse(
        approved=result['approved'],
        reason=result['reason'],
        epi_trace=result['epi_trace'],
        risk_score=result.get('risk_score', 0.0),
        timestamp=datetime.utcnow().isoformat()
    )


# ============ AI Agent Endpoints ============

@app.post("/agent/ceo/proposal", response_model=ProposalResponse, tags=["AI Agents"])
async def generate_proposal(proposal_input: ProposalInput):
    """Generate a strategic proposal via CEO-AI."""
    if not ceo_agent:
        raise HTTPException(status_code=503, detail="CEO agent not initialized")

    proposal = ceo_agent.generate_strategic_proposal(
        sector=proposal_input.sector,
        investment_amount=proposal_input.investment_amount,
        timeline_months=proposal_input.timeline_months
    )

    return ProposalResponse(
        proposal_id=proposal.proposal_id,
        title=proposal.title,
        approved=proposal.approved,
        epi_score=proposal.epi_score,
        profit_score=proposal.profit_score,
        ethics_score=proposal.ethics_score,
        expected_roi=proposal.expected_roi,
        reasoning=proposal.reasoning,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/agent/ceo/stats", tags=["AI Agents"])
async def get_ceo_stats():
    """Get CEO-AI agent statistics."""
    if not ceo_agent:
        raise HTTPException(status_code=503, detail="CEO agent not initialized")

    return ceo_agent.get_agent_stats()


@app.post("/agent/cfo/allocate", tags=["AI Agents"])
async def allocate_budget(budget: BudgetInput):
    """Allocate budget via CFO-AI."""
    if not cfo_agent:
        raise HTTPException(status_code=503, detail="CFO agent not initialized")

    allocation = cfo_agent.allocate_budget(
        total_amount=budget.total_amount,
        priorities=budget.priorities
    )

    return {
        "approved": allocation.approved,
        "total_amount": allocation.total_amount,
        "allocations": allocation.allocations,
        "epi_score": allocation.epi_score,
        "reasoning": allocation.reasoning,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/agent/cfo/payment", tags=["AI Agents"])
async def process_payment(payment: PaymentInput):
    """Process payment request via CFO-AI."""
    if not cfo_agent:
        raise HTTPException(status_code=503, detail="CFO agent not initialized")

    result = cfo_agent.process_payment_request(
        recipient=payment.recipient,
        amount=payment.amount,
        category=payment.category,
        description=payment.description
    )

    return {
        "approved": result.approved,
        "recipient": result.recipient,
        "amount": result.amount,
        "epi_score": result.epi_score,
        "treasury_balance": cfo_agent.treasury_balance,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/agent/cfo/treasury", tags=["AI Agents"])
async def get_treasury_health():
    """Get treasury health assessment."""
    if not cfo_agent:
        raise HTTPException(status_code=503, detail="CFO agent not initialized")

    return cfo_agent.assess_treasury_health()


@app.get("/agent/cfo/report", tags=["AI Agents"])
async def get_financial_report():
    """Get financial report from CFO-AI."""
    if not cfo_agent:
        raise HTTPException(status_code=503, detail="CFO agent not initialized")

    return cfo_agent.generate_financial_report()


# ============ Audit Endpoints ============

@app.post("/audit/log", tags=["Audit"])
async def log_thought(thought: ThoughtLogInput):
    """Log an AI thought for audit trail."""
    if not thought_logger:
        raise HTTPException(status_code=503, detail="Thought logger not initialized")

    thought_hash = thought_logger.log_thought(
        agent_id=thought.agent_id,
        action=thought.action,
        reasoning=thought.reasoning,
        epi_trace=thought.epi_trace,
        inputs=thought.inputs,
        outputs=thought.outputs
    )

    return {
        "thought_hash": thought_hash,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/audit/history", tags=["Audit"])
async def get_audit_history(
    agent_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """Get thought log history."""
    if not thought_logger:
        raise HTTPException(status_code=503, detail="Thought logger not initialized")

    history = thought_logger.get_thought_history(agent_id=agent_id, limit=limit)

    return {
        "records": [
            {
                "agent_id": r.agent_id,
                "action": r.action,
                "epi_score": r.epi_trace.get('epi', 0),
                "timestamp": r.timestamp,
                "thought_hash": r.thought_hash
            }
            for r in history
        ],
        "count": len(history)
    }


@app.get("/audit/report", tags=["Audit"])
async def get_audit_report():
    """Generate audit report."""
    if not thought_logger:
        raise HTTPException(status_code=503, detail="Thought logger not initialized")

    return thought_logger.generate_audit_report()


@app.get("/audit/verify", tags=["Audit"])
async def verify_thought(thought_hash: str, content: str):
    """Verify thought log integrity."""
    if not thought_logger:
        raise HTTPException(status_code=503, detail="Thought logger not initialized")

    is_valid = thought_logger.verify_thought(content, thought_hash)

    return {
        "valid": is_valid,
        "thought_hash": thought_hash,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============ Error Handlers ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============ CLI Entry Point ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true"
    )
