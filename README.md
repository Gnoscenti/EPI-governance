# MicroAI Governance Framework

## Overview

The **MicroAI Governance Framework** is an ethical AI governance system that integrates the **Ethical Performance Index (EPI)** with blockchain-based decision validation. This framework ensures that AI-driven decisions balance profitability with ethical considerations through mathematical constraints and on-chain enforcement.

## Architecture

### Core Components

1. **EPI Calculator** (`src/epi/calculator.py`)
   - Harmonic mean-based ethical constraint
   - Golden ratio balance penalty
   - Geometric trust accumulator
   - References: Boyd & Vandenberghe (2004), Jøsang et al. (2007)

2. **Policy Engine** (`src/policy_engine/validator.py`)
   - Intent validation pipeline
   - Compliance checks (sanctions, regulations)
   - Risk assessment (VaR proxy, concentration limits)
   - EPI threshold enforcement

3. **Smart Contracts** (`contracts/`)
   - **Ethereum**: EPI-enforced governance with Chainlink oracle integration
   - **Solana**: High-throughput proposal system with thought logging

4. **AI C-Suite Stubs** (`src/ai_c_suite/`)
   - Simulated executive AI agents (CEO, CFO)
   - Intent generation for testing and demonstration

## Key Features

- **Ethical Constraint**: EPI ensures balanced profit-ethics optimization
- **On-Chain Validation**: Proposals validated against EPI thresholds
- **Multi-Chain Support**: Ethereum (anchor) and Solana (high-throughput)
- **Thought Logging**: Transparent AI decision trails
- **Trust Accumulation**: Violation-based reputation system

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Rust (for Solana development)
- Hardhat (for Ethereum development)

### Setup

```bash
# Clone the repository
git clone https://github.com/Gnoscenti/EPI-governance.git
cd EPI-governance

# Install Python dependencies
pip install -r requirements.txt

# Or use Poetry
poetry install

# Install JavaScript dependencies
npm install

# Run deployment script
./deploy.sh
```

## Usage

### Python: EPI Calculation

```python
from src.epi.calculator import EPICalculator, EPIScores

calc = EPICalculator()
scores = EPIScores(profit=0.9, ethics=0.8, violations=[])
epi, valid, trace = calc.compute_epi(scores)
print(f"EPI: {epi:.3f}, Valid: {valid}")
```

### Python: Policy Validation

```python
from src.policy_engine.validator import PolicyValidator

validator = PolicyValidator()
intent = {
    'action': 'proposal',
    'roi_proxy': 0.85,
    'ethics_factors': {'env': 0.9, 'equity': 0.7},
    'violations': []
}
result = validator.validate_intent(intent)
print(result)
```

### Smart Contract Deployment

```bash
# Ethereum (Hardhat)
cd contracts/ethereum
npx hardhat compile
npx hardhat run scripts/deploy.js --network sepolia

# Solana (Anchor)
cd contracts/solana
anchor build
anchor deploy
```

## Project Structure

```
microai-governance-framework/
├── README.md                  # This file
├── .gitignore                 # Git ignore patterns
├── deploy.sh                  # Deployment automation script
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Poetry configuration
├── package.json               # NPM dependencies
├── contracts/                 # Smart contracts
│   ├── ethereum/              # Ethereum contracts (Solidity)
│   └── solana/                # Solana programs (Rust/Anchor)
├── src/                       # Python core modules
│   ├── epi/                   # EPI calculation engine
│   ├── policy_engine/         # Policy validation
│   └── ai_c_suite/            # AI agent stubs
├── examples/                  # Usage demonstrations
├── docs/                      # Documentation and research
└── .github/workflows/         # CI/CD pipelines
```

## Mathematical Foundation

### EPI Formula

```
EPI = H(P, E) × B(P, E) × T(V)
```

Where:
- **H(P, E)**: Harmonic mean of Profit (P) and Ethics (E)
- **B(P, E)**: Balance penalty using golden ratio (φ)
- **T(V)**: Trust accumulator with geometric decay on violations (V)

### Properties

1. **Non-compensatory**: Low ethics cannot be offset by high profit
2. **Balance-enforcing**: Penalizes extreme imbalances
3. **Trust-sensitive**: Violations compound multiplicatively

## Testing

```bash
# Run Python tests
pytest src/epi/tests/

# Run Ethereum tests
cd contracts/ethereum
npx hardhat test

# Run Solana tests
cd contracts/solana
anchor test
```

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Python: PEP 8, type hints, docstrings
- Solidity: Solhint, NatSpec comments
- Rust: Clippy, rustfmt

## Documentation

- **EPI Derivation**: See `docs/EPI_derivation.pdf` for mathematical proofs
- **Synthetic Trust**: See `docs/synthetic_trust.md` for certification pathways
- **API Reference**: Generated via Sphinx (coming soon)

## Roadmap

- [ ] Mainnet deployment (Ethereum, Solana)
- [ ] IPFS integration for thought logging
- [ ] Advanced compliance modules (GDPR, SEC)
- [ ] Multi-agent coordination framework
- [ ] Real-time EPI oracle feeds
- [ ] Governance token (DAO structure)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

1. Boyd, S., & Vandenberghe, L. (2004). *Convex Optimization*. Cambridge University Press.
2. Jøsang, A., et al. (2007). "Trust network analysis with subjective logic." *Decision Support Systems*, 43(2).
3. Buterin, V. (2014). "A Next-Generation Smart Contract and Decentralized Application Platform." *Ethereum Whitepaper*.

## Contact

- **GitHub**: [Gnoscenti/EPI-governance](https://github.com/Gnoscenti/EPI-governance)
- **Issues**: [Report bugs or request features](https://github.com/Gnoscenti/EPI-governance/issues)

---

**Built with ethical AI governance in mind** 🤖⚖️
