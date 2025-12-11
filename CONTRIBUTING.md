# Contributing to MicroAI Governance Framework

Thank you for your interest in contributing to the MicroAI Governance Framework! This document provides guidelines for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- Clear description of the feature
- Use case and benefits
- Potential implementation approach

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Ensure tests pass**: `pytest src/epi/tests/`
6. **Format code**: `black src examples`
7. **Commit changes**: `git commit -m 'Add amazing feature'`
8. **Push to branch**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Rust (for Solana development)

### Installation

```bash
# Clone the repository
git clone https://github.com/Gnoscenti/EPI-governance.git
cd EPI-governance

# Install Python dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Install Node.js dependencies
npm install

# Run tests
pytest src/epi/tests/ -v
```

## Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints for function signatures
- Write docstrings for all public functions
- Maximum line length: 100 characters
- Use Black for formatting: `black src`

Example:
```python
def calculate_epi(profit: float, ethics: float, violations: List[float]) -> float:
    """
    Calculate the Ethical Profitability Index.
    
    Args:
        profit: Profit score [0,1]
        ethics: Ethics score [0,1]
        violations: List of violation severities
        
    Returns:
        EPI score [0,1]
    """
    # Implementation
    pass
```

### Solidity

- Follow Solhint recommendations
- Use NatSpec comments
- Implement access controls
- Test all edge cases

Example:
```solidity
/// @notice Submit a proposal with EPI validation
/// @param title Proposal title
/// @param epiScore EPI score (scaled by 1e6)
/// @return proposalId The ID of the created proposal
function submitProposal(
    string memory title,
    uint256 epiScore
) external returns (uint256 proposalId) {
    // Implementation
}
```

### Rust/Anchor

- Follow Rust style guidelines
- Use `cargo fmt` for formatting
- Use `cargo clippy` for linting
- Document public functions

## Testing

### Python Tests

```bash
# Run all tests
pytest src/epi/tests/ -v

# Run with coverage
pytest src/epi/tests/ --cov=src --cov-report=html

# Run specific test
pytest src/epi/tests/test_epi.py::TestHarmonicMean -v
```

### Smart Contract Tests

```bash
# Ethereum (Hardhat)
cd contracts/ethereum
npx hardhat test

# Solana (Anchor)
cd contracts/solana
anchor test
```

## Documentation

- Update README.md for user-facing changes
- Update relevant documentation in `docs/`
- Add docstrings to new functions
- Update CHANGELOG.md

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add golden ratio optimization to EPI calculator
fix: Correct trust accumulator numerical stability
docs: Update EPI derivation with formal proofs
test: Add edge case tests for harmonic mean
refactor: Simplify balance penalty calculation
```

Prefixes:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or modifications
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

## Review Process

1. All PRs require at least one approval
2. CI/CD pipeline must pass
3. Code coverage should not decrease
4. Documentation must be updated

## Areas for Contribution

### High Priority

- [ ] Smart contract audits
- [ ] Additional test coverage
- [ ] Performance optimizations
- [ ] Documentation improvements

### Medium Priority

- [ ] Integration with real oracles
- [ ] Frontend dashboard
- [ ] Additional AI agent types
- [ ] Multi-language support

### Research

- [ ] Alternative EPI formulations
- [ ] Machine learning integration
- [ ] Cross-chain bridges
- [ ] Governance mechanisms

## Questions?

- Create an issue for questions
- Join our Discord (link TBD)
- Email: founder@aiintegrationcourse.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to ethical AI governance! 🤖⚖️
