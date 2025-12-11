#!/bin/bash

# MicroAI Governance Framework Deployment Script
# Usage: ./deploy.sh [local|testnet|mainnet]

set -e

ENVIRONMENT=${1:-local}

echo "🚀 MicroAI Governance Framework Deployment"
echo "Environment: $ENVIRONMENT"
echo "=========================================="

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm is required but not installed."; exit 1; }

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f "pyproject.toml" ]; then
    if command -v poetry >/dev/null 2>&1; then
        poetry install
    else
        pip install -r requirements.txt
    fi
else
    pip install -r requirements.txt
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Run Python tests
echo "🧪 Running Python tests..."
pytest src/epi/tests/ -v || echo "⚠️  Some tests failed"

# Compile Ethereum contracts
echo "🔨 Compiling Ethereum contracts..."
cd contracts/ethereum
npx hardhat compile
cd ../..

# Deploy based on environment
case $ENVIRONMENT in
    local)
        echo "🏠 Starting local Hardhat node..."
        cd contracts/ethereum
        npx hardhat node &
        HARDHAT_PID=$!
        sleep 5
        echo "📤 Deploying to local network..."
        npx hardhat run scripts/deploy.js --network localhost
        echo "✅ Local deployment complete!"
        echo "💡 Hardhat node running (PID: $HARDHAT_PID)"
        echo "   Stop with: kill $HARDHAT_PID"
        cd ../..
        ;;
    testnet)
        echo "🌐 Deploying to testnet..."
        if [ ! -f ".env" ]; then
            echo "❌ .env file not found. Please create one with PRIVATE_KEY and RPC_URL"
            exit 1
        fi
        cd contracts/ethereum
        npx hardhat run scripts/deploy.js --network sepolia
        cd ../..
        echo "✅ Testnet deployment complete!"
        ;;
    mainnet)
        echo "⚠️  MAINNET DEPLOYMENT - This will use real funds!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "❌ Deployment cancelled"
            exit 1
        fi
        cd contracts/ethereum
        npx hardhat run scripts/deploy.js --network mainnet
        cd ../..
        echo "✅ Mainnet deployment complete!"
        ;;
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        echo "Usage: ./deploy.sh [local|testnet|mainnet]"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "✨ Deployment process completed!"
echo "=========================================="
