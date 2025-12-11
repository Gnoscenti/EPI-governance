"""
Thought Logger: Records AI decision-making processes for transparency and auditability.

Implements the "Chain of Thought" logging mechanism described in the MicroAI
architecture, where AI reasoning steps are recorded on-chain or to IPFS for
verification and trust-building.
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ThoughtRecord:
    """A single thought/decision record from an AI agent."""

    timestamp: int  # Unix timestamp
    agent_id: str  # e.g., "CEO-AI", "CFO-AI"
    action: str  # e.g., "proposal_submission", "budget_allocation"
    reasoning: str  # Natural language explanation
    epi_trace: Dict[str, Any]  # EPI calculation details
    inputs: Dict[str, Any]  # Input parameters
    outputs: Dict[str, Any]  # Decision outputs
    metadata: Dict[str, Any]  # Additional context


class ThoughtLogger:
    """
    Logs AI decision-making processes for transparency and auditability.

    Features:
    - JSON-based local storage
    - IPFS integration (stubbed)
    - On-chain hash anchoring (stubbed)
    - Cryptographic verification
    """

    def __init__(self, log_dir: str = "./logs", enable_ipfs: bool = False):
        """
        Initialize thought logger.

        Args:
            log_dir: Directory for local log storage
            enable_ipfs: Whether to push logs to IPFS (requires ipfs daemon)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.enable_ipfs = enable_ipfs
        self.session_id = self._generate_session_id()

    def _generate_session_id(self) -> str:
        """Generate unique session ID for this logging session."""
        return hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:16]

    def log_thought(
        self,
        agent_id: str,
        action: str,
        reasoning: str,
        epi_trace: Dict[str, Any],
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log a single AI thought/decision.

        Args:
            agent_id: Identifier of the AI agent
            action: Type of action being taken
            reasoning: Natural language explanation
            epi_trace: EPI calculation trace
            inputs: Input parameters to the decision
            outputs: Decision outputs
            metadata: Additional context

        Returns:
            Hash of the logged thought record
        """
        record = ThoughtRecord(
            timestamp=int(time.time()),
            agent_id=agent_id,
            action=action,
            reasoning=reasoning,
            epi_trace=epi_trace,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata or {},
        )

        # Convert to JSON
        record_json = json.dumps(asdict(record), indent=2, sort_keys=True)

        # Calculate hash for verification
        record_hash = hashlib.sha256(record_json.encode()).hexdigest()

        # Save to local file
        log_file = self.log_dir / f"{self.session_id}_{record.timestamp}.json"
        with open(log_file, "w") as f:
            f.write(record_json)

        # Optional: Push to IPFS
        if self.enable_ipfs:
            ipfs_hash = self._push_to_ipfs(record_json)
            print(f"📌 IPFS Hash: {ipfs_hash}")

        return record_hash

    def _push_to_ipfs(self, content: str) -> str:
        """
        Push content to IPFS (stubbed implementation).

        In production, this would use ipfshttpclient or similar.

        Args:
            content: JSON content to push

        Returns:
            IPFS CID (content identifier)
        """
        # Stub: In production, use ipfshttpclient
        # import ipfshttpclient
        # client = ipfshttpclient.connect()
        # res = client.add_json(json.loads(content))
        # return res

        # For now, return a mock CID
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"Qm{content_hash[:44]}"  # Mock IPFS CID format

    def get_thought_history(
        self, agent_id: Optional[str] = None, action: Optional[str] = None, limit: int = 100
    ) -> List[ThoughtRecord]:
        """
        Retrieve thought history with optional filtering.

        Args:
            agent_id: Filter by agent ID
            action: Filter by action type
            limit: Maximum number of records to return

        Returns:
            List of ThoughtRecord objects
        """
        records = []

        # Get all log files in directory
        log_files = sorted(self.log_dir.glob("*.json"), reverse=True)

        for log_file in log_files[:limit]:
            try:
                with open(log_file, "r") as f:
                    data = json.load(f)
                    record = ThoughtRecord(**data)

                    # Apply filters
                    if agent_id and record.agent_id != agent_id:
                        continue
                    if action and record.action != action:
                        continue

                    records.append(record)
            except Exception as e:
                print(f"⚠️  Error reading {log_file}: {e}")

        return records

    def verify_thought(self, record_json: str, claimed_hash: str) -> bool:
        """
        Verify the integrity of a thought record.

        Args:
            record_json: JSON string of the record
            claimed_hash: Hash claimed for this record

        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = hashlib.sha256(record_json.encode()).hexdigest()
        return actual_hash == claimed_hash

    def generate_audit_report(self, output_file: str = "audit_report.json") -> Dict[str, Any]:
        """
        Generate an audit report of all logged thoughts.

        Args:
            output_file: Path to save the report

        Returns:
            Audit report dictionary
        """
        all_records = self.get_thought_history(limit=10000)

        # Aggregate statistics
        agent_counts = {}
        action_counts = {}
        epi_stats = {"approved": 0, "rejected": 0, "avg_epi": 0.0}

        total_epi = 0.0

        for record in all_records:
            # Count by agent
            agent_counts[record.agent_id] = agent_counts.get(record.agent_id, 0) + 1

            # Count by action
            action_counts[record.action] = action_counts.get(record.action, 0) + 1

            # EPI statistics
            if "epi" in record.epi_trace:
                epi_value = record.epi_trace["epi"]
                total_epi += epi_value

                if record.epi_trace.get("reason", "").startswith("approved"):
                    epi_stats["approved"] += 1
                else:
                    epi_stats["rejected"] += 1

        if all_records:
            epi_stats["avg_epi"] = total_epi / len(all_records)

        report = {
            "session_id": self.session_id,
            "total_records": len(all_records),
            "agent_counts": agent_counts,
            "action_counts": action_counts,
            "epi_statistics": epi_stats,
            "generated_at": int(time.time()),
        }

        # Save report
        report_path = self.log_dir / output_file
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report


# Example usage
if __name__ == "__main__":
    logger = ThoughtLogger(log_dir="./thought_logs")

    print("=" * 60)
    print("MicroAI Thought Logger - Demo")
    print("=" * 60)

    # Simulate CEO-AI logging a strategic decision
    print("\n[CEO-AI] Logging strategic proposal...")
    hash1 = logger.log_thought(
        agent_id="CEO-AI",
        action="strategic_proposal",
        reasoning="Market analysis indicates 35% growth opportunity in healthcare AI. "
        "Proposing $500K investment in medical imaging product line. "
        "EPI analysis shows strong ethics alignment (patient privacy, FDA compliance) "
        "with projected 18-month ROI.",
        epi_trace={
            "epi": 0.82,
            "hmean": 0.88,
            "balance_penalty": 0.95,
            "trust": 1.0,
            "reason": "approved",
        },
        inputs={
            "market_data": {"growth_rate": 0.35, "market_size": "2.5B"},
            "investment_amount": 500000,
            "timeline": "18 months",
        },
        outputs={"proposal_id": "PROP-2025-001", "approved": True, "allocated_budget": 500000},
        metadata={"confidence": 0.87, "risk_level": "medium"},
    )
    print(f"✅ Logged with hash: {hash1[:16]}...")

    # Simulate CFO-AI logging a budget decision
    print("\n[CFO-AI] Logging budget allocation...")
    hash2 = logger.log_thought(
        agent_id="CFO-AI",
        action="budget_allocation",
        reasoning="Q4 revenue exceeded projections by 12%. Allocating surplus: "
        "40% to R&D, 30% to treasury reserve, 20% to team bonuses, "
        "10% to community rewards. Maintains EPI balance and stakeholder alignment.",
        epi_trace={
            "epi": 0.78,
            "hmean": 0.82,
            "balance_penalty": 0.92,
            "trust": 1.0,
            "reason": "approved",
        },
        inputs={"surplus_amount": 1200000, "quarter": "Q4-2025"},
        outputs={
            "allocations": {
                "r_and_d": 480000,
                "treasury": 360000,
                "bonuses": 240000,
                "community": 120000,
            }
        },
    )
    print(f"✅ Logged with hash: {hash2[:16]}...")

    # Generate audit report
    print("\n[Audit] Generating report...")
    report = logger.generate_audit_report()
    print(f"📊 Total records: {report['total_records']}")
    print(f"📊 Agent activity: {report['agent_counts']}")
    print(f"📊 EPI stats: {report['epi_statistics']}")
    print(f"\n💾 Logs saved to: {logger.log_dir}")
