// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

/**
 * @title MicroAiGovernance
 * @author MicroAI Studios
 * @notice EPI-enforced governance contract for autonomous AI decision validation
 * @dev Implements the Ethical Profitability Index (EPI) constraint mechanism
 *      with Chainlink oracle integration for off-chain EPI computation
 */
contract MicroAiGovernance is Ownable, ReentrancyGuard, Pausable {
    // ============ Constants ============

    /// @notice EPI scaling factor (6 decimals for precision)
    uint256 public constant EPI_DECIMALS = 1e6;

    /// @notice Minimum voting period in blocks (~1 day at 12s blocks)
    uint256 public constant MIN_VOTING_PERIOD = 7200;

    /// @notice Maximum voting period in blocks (~7 days)
    uint256 public constant MAX_VOTING_PERIOD = 50400;

    // ============ State Variables ============

    /// @notice Chainlink-compatible EPI oracle
    AggregatorV3Interface public epiOracle;

    /// @notice Minimum EPI score required for proposal submission (scaled by 1e6)
    uint256 public epiThreshold;

    /// @notice Voting period duration in blocks
    uint256 public votingPeriod;

    /// @notice Quorum required for proposal execution (as percentage, scaled by 1e4)
    uint256 public quorumPercentage;

    /// @notice Total proposals created
    uint256 public proposalCount;

    /// @notice Total voting power in the system
    uint256 public totalVotingPower;

    // ============ Structs ============

    /// @notice Proposal status enum
    enum ProposalStatus {
        Pending,    // Awaiting voting
        Active,     // Voting in progress
        Defeated,   // Failed to reach quorum or majority
        Succeeded,  // Passed vote
        Executed,   // Successfully executed
        Vetoed,     // Vetoed by guardian
        Cancelled   // Cancelled by proposer
    }

    /// @notice Proposal data structure
    struct Proposal {
        uint256 id;
        address proposer;
        string title;
        string description;
        bytes32 ipfsHash;           // IPFS hash for detailed proposal data
        uint256 epiScore;           // EPI score at submission (scaled by 1e6)
        uint256 profitScore;        // Profit component (scaled by 1e6)
        uint256 ethicsScore;        // Ethics component (scaled by 1e6)
        uint256 forVotes;           // Votes in favor
        uint256 againstVotes;       // Votes against
        uint256 abstainVotes;       // Abstention votes
        uint256 startBlock;         // Voting start block
        uint256 endBlock;           // Voting end block
        ProposalStatus status;
        bytes32 thoughtHash;        // Hash of AI reasoning (for audit trail)
        uint256 createdAt;
        uint256 executedAt;
    }

    /// @notice Vote receipt structure
    struct VoteReceipt {
        bool hasVoted;
        uint8 support;      // 0 = Against, 1 = For, 2 = Abstain
        uint256 votes;
    }

    /// @notice Guardian structure for Class A stakeholders
    struct Guardian {
        bool isActive;
        uint256 vetoCount;
        uint256 addedAt;
    }

    // ============ Mappings ============

    /// @notice Proposal ID => Proposal data
    mapping(uint256 => Proposal) public proposals;

    /// @notice Proposal ID => Voter => Vote receipt
    mapping(uint256 => mapping(address => VoteReceipt)) public voteReceipts;

    /// @notice Address => Voting power
    mapping(address => uint256) public votingPower;

    /// @notice Address => Guardian status
    mapping(address => Guardian) public guardians;

    /// @notice Proposal ID => Execution hash (for reentrancy protection)
    mapping(uint256 => bool) public proposalExecuted;

    // ============ Events ============

    event ProposalCreated(
        uint256 indexed proposalId,
        address indexed proposer,
        string title,
        uint256 epiScore,
        uint256 startBlock,
        uint256 endBlock
    );

    event VoteCast(
        address indexed voter,
        uint256 indexed proposalId,
        uint8 support,
        uint256 votes,
        string reason
    );

    event ProposalExecuted(
        uint256 indexed proposalId,
        address indexed executor,
        uint256 timestamp
    );

    event ProposalVetoed(
        uint256 indexed proposalId,
        address indexed guardian,
        string reason
    );

    event ProposalCancelled(
        uint256 indexed proposalId,
        address indexed proposer
    );

    event EPIThresholdUpdated(
        uint256 oldThreshold,
        uint256 newThreshold
    );

    event GuardianAdded(address indexed guardian);
    event GuardianRemoved(address indexed guardian);
    event VotingPowerUpdated(address indexed account, uint256 oldPower, uint256 newPower);
    event OracleUpdated(address indexed oldOracle, address indexed newOracle);

    event ThoughtLogged(
        uint256 indexed proposalId,
        bytes32 thoughtHash,
        string agentId,
        uint256 timestamp
    );

    // ============ Errors ============

    error EPIBelowThreshold(uint256 provided, uint256 required);
    error ProposalNotActive(uint256 proposalId, ProposalStatus status);
    error VotingNotStarted(uint256 proposalId, uint256 startBlock);
    error VotingEnded(uint256 proposalId, uint256 endBlock);
    error AlreadyVoted(address voter, uint256 proposalId);
    error NoVotingPower(address voter);
    error ProposalNotSucceeded(uint256 proposalId);
    error AlreadyExecuted(uint256 proposalId);
    error NotGuardian(address account);
    error NotProposer(address account);
    error InvalidVoteType(uint8 support);
    error InvalidEPIScore(uint256 score);
    error ZeroAddress();
    error InvalidVotingPeriod(uint256 period);

    // ============ Modifiers ============

    modifier onlyGuardian() {
        if (!guardians[msg.sender].isActive) revert NotGuardian(msg.sender);
        _;
    }

    modifier validProposal(uint256 proposalId) {
        require(proposalId > 0 && proposalId <= proposalCount, "Invalid proposal ID");
        _;
    }

    // ============ Constructor ============

    /**
     * @notice Initialize the governance contract
     * @param _epiOracle Address of the EPI oracle contract
     */
    constructor(address _epiOracle) Ownable(msg.sender) {
        if (_epiOracle == address(0)) revert ZeroAddress();

        epiOracle = AggregatorV3Interface(_epiOracle);
        epiThreshold = 700000;  // 0.7 * 1e6
        votingPeriod = 14400;   // ~2 days at 12s blocks
        quorumPercentage = 400; // 4% quorum (scaled by 1e4)

        // Add deployer as initial guardian
        guardians[msg.sender] = Guardian({
            isActive: true,
            vetoCount: 0,
            addedAt: block.timestamp
        });

        emit GuardianAdded(msg.sender);
    }

    // ============ External Functions ============

    /**
     * @notice Submit a new proposal with EPI validation
     * @param title Proposal title
     * @param description Proposal description
     * @param ipfsHash IPFS hash for detailed proposal data
     * @param profitScore Profit component score (scaled by 1e6)
     * @param ethicsScore Ethics component score (scaled by 1e6)
     * @param thoughtHash Hash of AI reasoning for audit trail
     * @return proposalId The ID of the created proposal
     */
    function submitProposal(
        string calldata title,
        string calldata description,
        bytes32 ipfsHash,
        uint256 profitScore,
        uint256 ethicsScore,
        bytes32 thoughtHash
    ) external whenNotPaused returns (uint256 proposalId) {
        // Validate scores
        if (profitScore > EPI_DECIMALS || ethicsScore > EPI_DECIMALS) {
            revert InvalidEPIScore(profitScore > ethicsScore ? profitScore : ethicsScore);
        }

        // Fetch current EPI from oracle
        (, int256 epiRaw,,,) = epiOracle.latestRoundData();
        uint256 epiScore = uint256(epiRaw);

        // Validate EPI threshold
        if (epiScore < epiThreshold) {
            revert EPIBelowThreshold(epiScore, epiThreshold);
        }

        // Create proposal
        proposalCount++;
        proposalId = proposalCount;

        uint256 startBlock = block.number + 1;
        uint256 endBlock = startBlock + votingPeriod;

        proposals[proposalId] = Proposal({
            id: proposalId,
            proposer: msg.sender,
            title: title,
            description: description,
            ipfsHash: ipfsHash,
            epiScore: epiScore,
            profitScore: profitScore,
            ethicsScore: ethicsScore,
            forVotes: 0,
            againstVotes: 0,
            abstainVotes: 0,
            startBlock: startBlock,
            endBlock: endBlock,
            status: ProposalStatus.Active,
            thoughtHash: thoughtHash,
            createdAt: block.timestamp,
            executedAt: 0
        });

        emit ProposalCreated(
            proposalId,
            msg.sender,
            title,
            epiScore,
            startBlock,
            endBlock
        );

        emit ThoughtLogged(proposalId, thoughtHash, "PROPOSER", block.timestamp);

        return proposalId;
    }

    /**
     * @notice Cast a vote on a proposal
     * @param proposalId The ID of the proposal
     * @param support Vote type: 0 = Against, 1 = For, 2 = Abstain
     * @param reason Optional reason for the vote
     */
    function castVote(
        uint256 proposalId,
        uint8 support,
        string calldata reason
    ) external validProposal(proposalId) whenNotPaused {
        Proposal storage proposal = proposals[proposalId];

        // Validate proposal status
        if (proposal.status != ProposalStatus.Active) {
            revert ProposalNotActive(proposalId, proposal.status);
        }

        // Validate voting period
        if (block.number < proposal.startBlock) {
            revert VotingNotStarted(proposalId, proposal.startBlock);
        }
        if (block.number > proposal.endBlock) {
            revert VotingEnded(proposalId, proposal.endBlock);
        }

        // Validate vote
        if (support > 2) revert InvalidVoteType(support);

        VoteReceipt storage receipt = voteReceipts[proposalId][msg.sender];
        if (receipt.hasVoted) revert AlreadyVoted(msg.sender, proposalId);

        uint256 votes = votingPower[msg.sender];
        if (votes == 0) revert NoVotingPower(msg.sender);

        // Record vote
        receipt.hasVoted = true;
        receipt.support = support;
        receipt.votes = votes;

        // Tally vote
        if (support == 0) {
            proposal.againstVotes += votes;
        } else if (support == 1) {
            proposal.forVotes += votes;
        } else {
            proposal.abstainVotes += votes;
        }

        emit VoteCast(msg.sender, proposalId, support, votes, reason);
    }

    /**
     * @notice Execute a successful proposal
     * @param proposalId The ID of the proposal to execute
     */
    function executeProposal(uint256 proposalId)
        external
        validProposal(proposalId)
        nonReentrant
        whenNotPaused
    {
        Proposal storage proposal = proposals[proposalId];

        // Validate proposal can be executed
        if (block.number <= proposal.endBlock) {
            revert VotingNotStarted(proposalId, proposal.endBlock);
        }

        if (proposalExecuted[proposalId]) {
            revert AlreadyExecuted(proposalId);
        }

        // Calculate results
        uint256 totalVotes = proposal.forVotes + proposal.againstVotes + proposal.abstainVotes;
        uint256 quorumVotes = (totalVotingPower * quorumPercentage) / 10000;

        // Check quorum and majority
        bool quorumReached = totalVotes >= quorumVotes;
        bool majorityFor = proposal.forVotes > proposal.againstVotes;

        if (!quorumReached || !majorityFor) {
            proposal.status = ProposalStatus.Defeated;
            revert ProposalNotSucceeded(proposalId);
        }

        // Execute
        proposal.status = ProposalStatus.Executed;
        proposal.executedAt = block.timestamp;
        proposalExecuted[proposalId] = true;

        emit ProposalExecuted(proposalId, msg.sender, block.timestamp);
    }

    /**
     * @notice Guardian veto power - can veto any active proposal
     * @param proposalId The ID of the proposal to veto
     * @param reason Reason for the veto
     */
    function vetoProposal(uint256 proposalId, string calldata reason)
        external
        validProposal(proposalId)
        onlyGuardian
    {
        Proposal storage proposal = proposals[proposalId];

        if (proposal.status != ProposalStatus.Active &&
            proposal.status != ProposalStatus.Succeeded) {
            revert ProposalNotActive(proposalId, proposal.status);
        }

        proposal.status = ProposalStatus.Vetoed;
        guardians[msg.sender].vetoCount++;

        emit ProposalVetoed(proposalId, msg.sender, reason);
    }

    /**
     * @notice Cancel a proposal (only by proposer, before voting ends)
     * @param proposalId The ID of the proposal to cancel
     */
    function cancelProposal(uint256 proposalId)
        external
        validProposal(proposalId)
    {
        Proposal storage proposal = proposals[proposalId];

        if (proposal.proposer != msg.sender) revert NotProposer(msg.sender);
        if (proposal.status != ProposalStatus.Active) {
            revert ProposalNotActive(proposalId, proposal.status);
        }

        proposal.status = ProposalStatus.Cancelled;

        emit ProposalCancelled(proposalId, msg.sender);
    }

    // ============ Admin Functions ============

    /**
     * @notice Update the EPI threshold
     * @param newThreshold New threshold value (scaled by 1e6)
     */
    function setEPIThreshold(uint256 newThreshold) external onlyOwner {
        require(newThreshold <= EPI_DECIMALS, "Threshold too high");

        uint256 oldThreshold = epiThreshold;
        epiThreshold = newThreshold;

        emit EPIThresholdUpdated(oldThreshold, newThreshold);
    }

    /**
     * @notice Update the EPI oracle address
     * @param newOracle New oracle address
     */
    function setOracle(address newOracle) external onlyOwner {
        if (newOracle == address(0)) revert ZeroAddress();

        address oldOracle = address(epiOracle);
        epiOracle = AggregatorV3Interface(newOracle);

        emit OracleUpdated(oldOracle, newOracle);
    }

    /**
     * @notice Update voting period
     * @param newPeriod New voting period in blocks
     */
    function setVotingPeriod(uint256 newPeriod) external onlyOwner {
        if (newPeriod < MIN_VOTING_PERIOD || newPeriod > MAX_VOTING_PERIOD) {
            revert InvalidVotingPeriod(newPeriod);
        }
        votingPeriod = newPeriod;
    }

    /**
     * @notice Add a new guardian
     * @param guardian Address to add as guardian
     */
    function addGuardian(address guardian) external onlyOwner {
        if (guardian == address(0)) revert ZeroAddress();

        guardians[guardian] = Guardian({
            isActive: true,
            vetoCount: 0,
            addedAt: block.timestamp
        });

        emit GuardianAdded(guardian);
    }

    /**
     * @notice Remove a guardian
     * @param guardian Address to remove
     */
    function removeGuardian(address guardian) external onlyOwner {
        guardians[guardian].isActive = false;
        emit GuardianRemoved(guardian);
    }

    /**
     * @notice Set voting power for an account
     * @param account Address to update
     * @param power New voting power
     */
    function setVotingPower(address account, uint256 power) external onlyOwner {
        if (account == address(0)) revert ZeroAddress();

        uint256 oldPower = votingPower[account];
        totalVotingPower = totalVotingPower - oldPower + power;
        votingPower[account] = power;

        emit VotingPowerUpdated(account, oldPower, power);
    }

    /**
     * @notice Pause the contract (emergency)
     */
    function pause() external onlyGuardian {
        _pause();
    }

    /**
     * @notice Unpause the contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // ============ View Functions ============

    /**
     * @notice Get proposal details
     * @param proposalId The ID of the proposal
     * @return Proposal struct
     */
    function getProposal(uint256 proposalId)
        external
        view
        validProposal(proposalId)
        returns (Proposal memory)
    {
        return proposals[proposalId];
    }

    /**
     * @notice Get vote receipt for a voter
     * @param proposalId The ID of the proposal
     * @param voter Address of the voter
     * @return VoteReceipt struct
     */
    function getVoteReceipt(uint256 proposalId, address voter)
        external
        view
        returns (VoteReceipt memory)
    {
        return voteReceipts[proposalId][voter];
    }

    /**
     * @notice Check if an address is a guardian
     * @param account Address to check
     * @return bool True if account is an active guardian
     */
    function isGuardian(address account) external view returns (bool) {
        return guardians[account].isActive;
    }

    /**
     * @notice Get current EPI from oracle
     * @return epiScore Current EPI value
     */
    function getCurrentEPI() external view returns (uint256 epiScore) {
        (, int256 epiRaw,,,) = epiOracle.latestRoundData();
        return uint256(epiRaw);
    }

    /**
     * @notice Get proposal state
     * @param proposalId The ID of the proposal
     * @return status Current proposal status
     */
    function state(uint256 proposalId)
        external
        view
        validProposal(proposalId)
        returns (ProposalStatus)
    {
        Proposal storage proposal = proposals[proposalId];

        if (proposal.status == ProposalStatus.Vetoed ||
            proposal.status == ProposalStatus.Cancelled ||
            proposal.status == ProposalStatus.Executed) {
            return proposal.status;
        }

        if (block.number <= proposal.endBlock) {
            return ProposalStatus.Active;
        }

        // Voting ended - determine outcome
        uint256 totalVotes = proposal.forVotes + proposal.againstVotes + proposal.abstainVotes;
        uint256 quorumVotes = (totalVotingPower * quorumPercentage) / 10000;

        if (totalVotes < quorumVotes || proposal.forVotes <= proposal.againstVotes) {
            return ProposalStatus.Defeated;
        }

        return ProposalStatus.Succeeded;
    }
}
