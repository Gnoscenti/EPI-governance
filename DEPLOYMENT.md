# Deployment Guide

This guide walks you through setting up and deploying the MicroAI Governance Framework.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for containerized deployment)
- Rust & Cargo (for Solana development)
- Solana CLI & Anchor (for Solana deployment)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/Gnoscenti/EPI-governance.git
cd EPI-governance

# Copy environment template
cp .env.example .env
```

### 2. Python Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from src.epi.calculator import EPICalculator; print('OK')"
```

### 3. Run the API Server

```bash
# Development mode (with auto-reload)
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API available at: http://localhost:8000
Docs available at: http://localhost:8000/docs

### 4. Run Tests

```bash
# Python tests
pytest src/ -v

# With coverage
pytest src/ -v --cov=src --cov-report=html
```

---

## Ethereum Deployment

### Local Development

```bash
# Install Node dependencies
npm install

# Start local Hardhat node
cd contracts/ethereum
npx hardhat node

# In another terminal, deploy contracts
npx hardhat run scripts/deploy.js --network localhost

# Run contract tests
npx hardhat test
```

### Testnet Deployment (Sepolia)

1. **Configure environment:**
   ```bash
   # In .env file
   SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
   PRIVATE_KEY=your_deployer_private_key
   ETHERSCAN_API_KEY=your_etherscan_key
   ```

2. **Get testnet ETH:**
   - Sepolia Faucet: https://sepoliafaucet.com

3. **Deploy:**
   ```bash
   cd contracts/ethereum
   npx hardhat run scripts/deploy.js --network sepolia
   ```

4. **Verify contract:**
   ```bash
   npx hardhat verify --network sepolia DEPLOYED_ADDRESS
   ```

### Mainnet Deployment

```bash
# In .env file
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
PRIVATE_KEY=your_deployer_private_key

# Deploy (use caution - real funds!)
cd contracts/ethereum
npx hardhat run scripts/deploy.js --network mainnet
```

---

## Solana Deployment

### Prerequisites

```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install 0.29.0
avm use 0.29.0

# Configure Solana CLI
solana config set --url devnet  # or mainnet-beta
solana-keygen new  # Generate wallet if needed
```

### Local Development

```bash
cd contracts/solana

# Build program
anchor build

# Run local validator
solana-test-validator

# Deploy locally
anchor deploy
```

### Devnet Deployment

```bash
# Airdrop SOL for deployment
solana airdrop 2

# Update Anchor.toml cluster
# [provider]
# cluster = "Devnet"

# Deploy
anchor deploy --provider.cluster devnet
```

### Mainnet Deployment

```bash
# Update Anchor.toml
# [provider]
# cluster = "Mainnet"

# Deploy (use caution - real funds!)
anchor deploy --provider.cluster mainnet
```

---

## Docker Deployment

### Development

```bash
# Build and run API
docker-compose up

# With blockchain services
docker-compose --profile blockchain up

# With monitoring
docker-compose --profile monitoring up
```

### Production

```bash
# Build production image
docker build -t microai-governance:latest --target production .

# Run container
docker run -d \
  --name microai-api \
  -p 8000:8000 \
  -e EPI_THRESHOLD=0.7 \
  -e LOG_LEVEL=INFO \
  microai-governance:latest
```

### Full Stack

```bash
# All services including database and monitoring
docker-compose \
  --profile blockchain \
  --profile cache \
  --profile database \
  --profile monitoring \
  up -d
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |
| `EPI_THRESHOLD` | `0.7` | Minimum EPI score for proposals |
| `TREASURY_BALANCE` | `5000000` | Initial treasury balance |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENABLE_BLOCKCHAIN_INTEGRATION` | `false` | Enable blockchain features |

---

## CI/CD Pipeline

The GitHub Actions workflow runs automatically on push:

1. **Python Tests** - Linting (flake8, black) and pytest
2. **Ethereum Tests** - Hardhat compile and test
3. **Solana Build** - Anchor build verification
4. **Security Audit** - Bandit and dependency scanning
5. **Docker Build** - Image build verification

To deploy to testnet manually:
1. Go to Actions tab
2. Select "CI/CD Pipeline"
3. Click "Run workflow"
4. Select "deploy-testnet" job

---

## Troubleshooting

### Python Issues

```bash
# Clear cache and reinstall
pip cache purge
pip install -r requirements.txt --force-reinstall
```

### Ethereum Issues

```bash
# Clear Hardhat cache
cd contracts/ethereum
npx hardhat clean
rm -rf cache artifacts
npx hardhat compile
```

### Solana Issues

```bash
# Rebuild from scratch
cd contracts/solana
anchor clean
anchor build
```

### Docker Issues

```bash
# Rebuild without cache
docker-compose build --no-cache
docker-compose up --force-recreate
```

---

## Security Checklist

Before mainnet deployment:

- [ ] Audit smart contracts (external audit recommended)
- [ ] Review all environment variables
- [ ] Secure private keys (use hardware wallet or secrets manager)
- [ ] Enable rate limiting in production
- [ ] Configure CORS appropriately
- [ ] Set up monitoring and alerts
- [ ] Test disaster recovery procedures
- [ ] Document incident response plan
