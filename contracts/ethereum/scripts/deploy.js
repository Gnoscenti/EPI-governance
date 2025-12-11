const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying MicroAI Governance contracts...");

  // Get the deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("📝 Deploying with account:", deployer.address);

  // Deploy EPIOracle (mock for testing - replace with actual Chainlink oracle address)
  console.log("\n📡 Deploying EPIOracle...");
  const EPIOracle = await hre.ethers.getContractFactory("EPIOracle");
  const epiOracle = await EPIOracle.deploy();
  await epiOracle.waitForDeployment();
  const epiOracleAddress = await epiOracle.getAddress();
  console.log("✅ EPIOracle deployed to:", epiOracleAddress);

  // Deploy Governance contract
  console.log("\n🏛️  Deploying Governance contract...");
  const Governance = await hre.ethers.getContractFactory("MicroAiGovernance");
  const governance = await Governance.deploy(epiOracleAddress);
  await governance.waitForDeployment();
  const governanceAddress = await governance.getAddress();
  console.log("✅ Governance deployed to:", governanceAddress);

  // Verify deployment
  console.log("\n📋 Deployment Summary:");
  console.log("========================");
  console.log("EPIOracle:   ", epiOracleAddress);
  console.log("Governance:  ", governanceAddress);
  console.log("Deployer:    ", deployer.address);
  console.log("Network:     ", hre.network.name);
  console.log("========================");

  // Save deployment addresses
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    deployer: deployer.address,
    contracts: {
      EPIOracle: epiOracleAddress,
      Governance: governanceAddress
    },
    timestamp: new Date().toISOString()
  };

  const deploymentsDir = "../../deployments";
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  fs.writeFileSync(
    `${deploymentsDir}/${hre.network.name}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("\n💾 Deployment info saved to deployments/" + hre.network.name + ".json");

  // Verification instructions
  if (hre.network.name !== "localhost" && hre.network.name !== "hardhat") {
    console.log("\n🔍 To verify contracts on Etherscan, run:");
    console.log(`npx hardhat verify --network ${hre.network.name} ${epiOracleAddress}`);
    console.log(`npx hardhat verify --network ${hre.network.name} ${governanceAddress} ${epiOracleAddress}`);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
