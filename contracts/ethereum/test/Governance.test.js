const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-toolbox/network-helpers");

describe("MicroAiGovernance", function () {
  // Fixture for deploying contracts
  async function deployGovernanceFixture() {
    const [owner, proposer, voter1, voter2, guardian] = await ethers.getSigners();

    // Deploy mock EPI Oracle
    const EPIOracle = await ethers.getContractFactory("EPIOracle");
    const epiOracle = await EPIOracle.deploy();
    await epiOracle.waitForDeployment();

    // Deploy Governance
    const Governance = await ethers.getContractFactory("MicroAiGovernance");
    const governance = await Governance.deploy(await epiOracle.getAddress());
    await governance.waitForDeployment();

    // Set up voting power for voters
    await governance.setVotingPower(voter1.address, 1000n);
    await governance.setVotingPower(voter2.address, 2000n);

    return { governance, epiOracle, owner, proposer, voter1, voter2, guardian };
  }

  describe("Deployment", function () {
    it("Should set the correct owner", async function () {
      const { governance, owner } = await loadFixture(deployGovernanceFixture);
      expect(await governance.owner()).to.equal(owner.address);
    });

    it("Should set the correct EPI oracle", async function () {
      const { governance, epiOracle } = await loadFixture(deployGovernanceFixture);
      expect(await governance.epiOracle()).to.equal(await epiOracle.getAddress());
    });

    it("Should set default EPI threshold to 0.7", async function () {
      const { governance } = await loadFixture(deployGovernanceFixture);
      expect(await governance.epiThreshold()).to.equal(700000n);
    });

    it("Should set deployer as initial guardian", async function () {
      const { governance, owner } = await loadFixture(deployGovernanceFixture);
      expect(await governance.isGuardian(owner.address)).to.be.true;
    });

    it("Should start with zero proposals", async function () {
      const { governance } = await loadFixture(deployGovernanceFixture);
      expect(await governance.proposalCount()).to.equal(0n);
    });
  });

  describe("Proposal Submission", function () {
    it("Should allow submitting a proposal with valid EPI", async function () {
      const { governance, proposer } = await loadFixture(deployGovernanceFixture);

      const tx = await governance.connect(proposer).submitProposal(
        "Test Proposal",
        "A test proposal for unit testing",
        ethers.zeroPadValue("0x1234", 32),  // IPFS hash
        800000n,  // profit score
        850000n,  // ethics score
        ethers.zeroPadValue("0x5678", 32)   // thought hash
      );

      await expect(tx).to.emit(governance, "ProposalCreated");

      expect(await governance.proposalCount()).to.equal(1n);
    });

    it("Should reject proposal if EPI is below threshold", async function () {
      const { governance, epiOracle, proposer } = await loadFixture(deployGovernanceFixture);

      // Set EPI to below threshold
      await epiOracle.updateAnswer(500000);  // 0.5 < 0.7

      await expect(
        governance.connect(proposer).submitProposal(
          "Low EPI Proposal",
          "This should be rejected",
          ethers.zeroPadValue("0x1234", 32),
          800000n,
          850000n,
          ethers.zeroPadValue("0x5678", 32)
        )
      ).to.be.revertedWithCustomError(governance, "EPIBelowThreshold");
    });

    it("Should reject proposal with invalid score", async function () {
      const { governance, proposer } = await loadFixture(deployGovernanceFixture);

      await expect(
        governance.connect(proposer).submitProposal(
          "Invalid Score Proposal",
          "Score exceeds 1.0",
          ethers.zeroPadValue("0x1234", 32),
          1500000n,  // > 1e6
          850000n,
          ethers.zeroPadValue("0x5678", 32)
        )
      ).to.be.revertedWithCustomError(governance, "InvalidEPIScore");
    });

    it("Should emit ThoughtLogged event on proposal", async function () {
      const { governance, proposer } = await loadFixture(deployGovernanceFixture);
      const thoughtHash = ethers.zeroPadValue("0xabcd", 32);

      await expect(
        governance.connect(proposer).submitProposal(
          "Logged Proposal",
          "Testing thought logging",
          ethers.zeroPadValue("0x1234", 32),
          800000n,
          850000n,
          thoughtHash
        )
      ).to.emit(governance, "ThoughtLogged");
    });
  });

  describe("Voting", function () {
    async function deployWithProposal() {
      const fixture = await deployGovernanceFixture();
      const { governance, proposer } = fixture;

      await governance.connect(proposer).submitProposal(
        "Votable Proposal",
        "A proposal ready for voting",
        ethers.zeroPadValue("0x1234", 32),
        800000n,
        850000n,
        ethers.zeroPadValue("0x5678", 32)
      );

      // Mine a block to start voting period
      await ethers.provider.send("evm_mine", []);

      return { ...fixture, proposalId: 1n };
    }

    it("Should allow voting with voting power", async function () {
      const { governance, voter1, proposalId } = await loadFixture(deployWithProposal);

      await expect(
        governance.connect(voter1).castVote(proposalId, 1, "I support this")
      ).to.emit(governance, "VoteCast");
    });

    it("Should reject voting without voting power", async function () {
      const { governance, proposer, proposalId } = await loadFixture(deployWithProposal);

      // Proposer has no voting power set
      await expect(
        governance.connect(proposer).castVote(proposalId, 1, "Support")
      ).to.be.revertedWithCustomError(governance, "NoVotingPower");
    });

    it("Should reject double voting", async function () {
      const { governance, voter1, proposalId } = await loadFixture(deployWithProposal);

      await governance.connect(voter1).castVote(proposalId, 1, "First vote");

      await expect(
        governance.connect(voter1).castVote(proposalId, 0, "Second vote")
      ).to.be.revertedWithCustomError(governance, "AlreadyVoted");
    });

    it("Should reject invalid vote type", async function () {
      const { governance, voter1, proposalId } = await loadFixture(deployWithProposal);

      await expect(
        governance.connect(voter1).castVote(proposalId, 5, "Invalid")
      ).to.be.revertedWithCustomError(governance, "InvalidVoteType");
    });

    it("Should correctly tally for votes", async function () {
      const { governance, voter1, voter2, proposalId } = await loadFixture(deployWithProposal);

      await governance.connect(voter1).castVote(proposalId, 1, "Support");
      await governance.connect(voter2).castVote(proposalId, 1, "Also support");

      const proposal = await governance.getProposal(proposalId);
      expect(proposal.forVotes).to.equal(3000n);  // 1000 + 2000
    });

    it("Should correctly tally against votes", async function () {
      const { governance, voter1, voter2, proposalId } = await loadFixture(deployWithProposal);

      await governance.connect(voter1).castVote(proposalId, 0, "Against");
      await governance.connect(voter2).castVote(proposalId, 0, "Also against");

      const proposal = await governance.getProposal(proposalId);
      expect(proposal.againstVotes).to.equal(3000n);
    });

    it("Should correctly tally abstain votes", async function () {
      const { governance, voter1, proposalId } = await loadFixture(deployWithProposal);

      await governance.connect(voter1).castVote(proposalId, 2, "Abstain");

      const proposal = await governance.getProposal(proposalId);
      expect(proposal.abstainVotes).to.equal(1000n);
    });
  });

  describe("Proposal Execution", function () {
    async function deployWithVotedProposal() {
      const fixture = await deployGovernanceFixture();
      const { governance, proposer, voter1, voter2, owner } = fixture;

      // Submit proposal
      await governance.connect(proposer).submitProposal(
        "Executable Proposal",
        "A proposal that can be executed",
        ethers.zeroPadValue("0x1234", 32),
        800000n,
        850000n,
        ethers.zeroPadValue("0x5678", 32)
      );

      // Start voting
      await ethers.provider.send("evm_mine", []);

      // Vote for the proposal
      await governance.connect(voter1).castVote(1n, 1, "Support");
      await governance.connect(voter2).castVote(1n, 1, "Support");

      // Mine blocks to end voting (default is 14400 blocks)
      const votingPeriod = await governance.votingPeriod();
      for (let i = 0; i < Number(votingPeriod) + 1; i++) {
        await ethers.provider.send("evm_mine", []);
      }

      return { ...fixture, proposalId: 1n };
    }

    it("Should allow execution of passed proposal", async function () {
      const { governance, proposalId } = await loadFixture(deployWithVotedProposal);

      await expect(
        governance.executeProposal(proposalId)
      ).to.emit(governance, "ProposalExecuted");

      const proposal = await governance.getProposal(proposalId);
      expect(proposal.status).to.equal(4n);  // Executed status
    });

    it("Should reject execution during voting period", async function () {
      const fixture = await deployGovernanceFixture();
      const { governance, proposer, voter1 } = fixture;

      await governance.connect(proposer).submitProposal(
        "Early Execution",
        "Should not be executable yet",
        ethers.zeroPadValue("0x1234", 32),
        800000n,
        850000n,
        ethers.zeroPadValue("0x5678", 32)
      );

      await ethers.provider.send("evm_mine", []);
      await governance.connect(voter1).castVote(1n, 1, "Support");

      await expect(
        governance.executeProposal(1n)
      ).to.be.revertedWithCustomError(governance, "VotingNotStarted");
    });

    it("Should reject double execution", async function () {
      const { governance, proposalId } = await loadFixture(deployWithVotedProposal);

      await governance.executeProposal(proposalId);

      await expect(
        governance.executeProposal(proposalId)
      ).to.be.revertedWithCustomError(governance, "AlreadyExecuted");
    });
  });

  describe("Guardian Veto", function () {
    async function deployWithActiveProposal() {
      const fixture = await deployGovernanceFixture();
      const { governance, proposer, guardian, owner } = fixture;

      // Add guardian
      await governance.addGuardian(guardian.address);

      // Submit proposal
      await governance.connect(proposer).submitProposal(
        "Vetoable Proposal",
        "A proposal that can be vetoed",
        ethers.zeroPadValue("0x1234", 32),
        800000n,
        850000n,
        ethers.zeroPadValue("0x5678", 32)
      );

      return { ...fixture, proposalId: 1n };
    }

    it("Should allow guardian to veto active proposal", async function () {
      const { governance, guardian, proposalId } = await loadFixture(deployWithActiveProposal);

      await expect(
        governance.connect(guardian).vetoProposal(proposalId, "Ethics concern")
      ).to.emit(governance, "ProposalVetoed");

      const proposal = await governance.getProposal(proposalId);
      expect(proposal.status).to.equal(5n);  // Vetoed status
    });

    it("Should reject veto from non-guardian", async function () {
      const { governance, proposer, proposalId } = await loadFixture(deployWithActiveProposal);

      await expect(
        governance.connect(proposer).vetoProposal(proposalId, "Not allowed")
      ).to.be.revertedWithCustomError(governance, "NotGuardian");
    });

    it("Should increment guardian veto count", async function () {
      const { governance, guardian, proposalId } = await loadFixture(deployWithActiveProposal);

      await governance.connect(guardian).vetoProposal(proposalId, "First veto");

      const guardianInfo = await governance.guardians(guardian.address);
      expect(guardianInfo.vetoCount).to.equal(1n);
    });
  });

  describe("Proposal Cancellation", function () {
    async function deployWithProposerProposal() {
      const fixture = await deployGovernanceFixture();
      const { governance, proposer } = fixture;

      await governance.connect(proposer).submitProposal(
        "Cancellable Proposal",
        "A proposal that can be cancelled",
        ethers.zeroPadValue("0x1234", 32),
        800000n,
        850000n,
        ethers.zeroPadValue("0x5678", 32)
      );

      return { ...fixture, proposalId: 1n };
    }

    it("Should allow proposer to cancel their proposal", async function () {
      const { governance, proposer, proposalId } = await loadFixture(deployWithProposerProposal);

      await expect(
        governance.connect(proposer).cancelProposal(proposalId)
      ).to.emit(governance, "ProposalCancelled");

      const proposal = await governance.getProposal(proposalId);
      expect(proposal.status).to.equal(6n);  // Cancelled status
    });

    it("Should reject cancellation by non-proposer", async function () {
      const { governance, voter1, proposalId } = await loadFixture(deployWithProposerProposal);

      await expect(
        governance.connect(voter1).cancelProposal(proposalId)
      ).to.be.revertedWithCustomError(governance, "NotProposer");
    });
  });

  describe("Admin Functions", function () {
    it("Should allow owner to update EPI threshold", async function () {
      const { governance, owner } = await loadFixture(deployGovernanceFixture);

      await expect(
        governance.setEPIThreshold(800000n)
      ).to.emit(governance, "EPIThresholdUpdated");

      expect(await governance.epiThreshold()).to.equal(800000n);
    });

    it("Should allow owner to add guardian", async function () {
      const { governance, guardian } = await loadFixture(deployGovernanceFixture);

      await expect(
        governance.addGuardian(guardian.address)
      ).to.emit(governance, "GuardianAdded");

      expect(await governance.isGuardian(guardian.address)).to.be.true;
    });

    it("Should allow owner to remove guardian", async function () {
      const { governance, guardian, owner } = await loadFixture(deployGovernanceFixture);

      await governance.addGuardian(guardian.address);
      await governance.removeGuardian(guardian.address);

      expect(await governance.isGuardian(guardian.address)).to.be.false;
    });

    it("Should allow guardian to pause contract", async function () {
      const { governance, owner } = await loadFixture(deployGovernanceFixture);

      // Owner is guardian by default
      await governance.pause();

      expect(await governance.paused()).to.be.true;
    });

    it("Should reject operations when paused", async function () {
      const { governance, owner, proposer } = await loadFixture(deployGovernanceFixture);

      await governance.pause();

      await expect(
        governance.connect(proposer).submitProposal(
          "Paused Proposal",
          "Should be rejected",
          ethers.zeroPadValue("0x1234", 32),
          800000n,
          850000n,
          ethers.zeroPadValue("0x5678", 32)
        )
      ).to.be.revertedWithCustomError(governance, "EnforcedPause");
    });
  });

  describe("View Functions", function () {
    it("Should return current EPI from oracle", async function () {
      const { governance, epiOracle } = await loadFixture(deployGovernanceFixture);

      await epiOracle.updateAnswer(800000);

      expect(await governance.getCurrentEPI()).to.equal(800000n);
    });

    it("Should return correct proposal state", async function () {
      const { governance, proposer, voter1 } = await loadFixture(deployGovernanceFixture);

      await governance.connect(proposer).submitProposal(
        "State Test",
        "Testing state",
        ethers.zeroPadValue("0x1234", 32),
        800000n,
        850000n,
        ethers.zeroPadValue("0x5678", 32)
      );

      // Should be Active (1) during voting period
      expect(await governance.state(1n)).to.equal(1n);
    });

    it("Should return vote receipt", async function () {
      const { governance, proposer, voter1 } = await loadFixture(deployGovernanceFixture);

      await governance.connect(proposer).submitProposal(
        "Vote Receipt Test",
        "Testing vote receipt",
        ethers.zeroPadValue("0x1234", 32),
        800000n,
        850000n,
        ethers.zeroPadValue("0x5678", 32)
      );

      await ethers.provider.send("evm_mine", []);
      await governance.connect(voter1).castVote(1n, 1, "Support");

      const receipt = await governance.getVoteReceipt(1n, voter1.address);
      expect(receipt.hasVoted).to.be.true;
      expect(receipt.support).to.equal(1n);
      expect(receipt.votes).to.equal(1000n);
    });
  });
});

describe("EPIOracle", function () {
  async function deployOracleFixture() {
    const EPIOracle = await ethers.getContractFactory("EPIOracle");
    const oracle = await EPIOracle.deploy();
    await oracle.waitForDeployment();
    return { oracle };
  }

  it("Should initialize with default EPI of 0.75", async function () {
    const { oracle } = await loadFixture(deployOracleFixture);

    const [, answer, , ,] = await oracle.latestRoundData();
    expect(answer).to.equal(750000n);
  });

  it("Should allow updating the EPI answer", async function () {
    const { oracle } = await loadFixture(deployOracleFixture);

    await oracle.updateAnswer(850000);

    const [, answer, , ,] = await oracle.latestRoundData();
    expect(answer).to.equal(850000n);
  });

  it("Should emit AnswerUpdated event", async function () {
    const { oracle } = await loadFixture(deployOracleFixture);

    await expect(oracle.updateAnswer(900000))
      .to.emit(oracle, "AnswerUpdated");
  });

  it("Should return correct decimals", async function () {
    const { oracle } = await loadFixture(deployOracleFixture);
    expect(await oracle.decimals()).to.equal(6);
  });

  it("Should track round IDs", async function () {
    const { oracle } = await loadFixture(deployOracleFixture);

    await oracle.updateAnswer(800000);
    await oracle.updateAnswer(850000);

    const [roundId, , , ,] = await oracle.latestRoundData();
    expect(roundId).to.equal(3n);  // Initial + 2 updates
  });
});
