use anchor_lang::prelude::*;

declare_id!("MicroAiGovernance11111111111111111111111111");

/// MicroAI Governance Program
///
/// This program implements EPI-enforced governance for autonomous AI decision validation.
/// Key features:
/// - EPI threshold validation for proposals
/// - Voting with configurable periods
/// - Guardian veto mechanism (Class A stakeholders)
/// - On-chain thought logging for transparency
#[program]
pub mod governance {
    use super::*;

    /// Initialize the governance program with EPI threshold
    pub fn initialize(
        ctx: Context<Initialize>,
        epi_threshold: u64,
        voting_period: u64,
        quorum_percentage: u64,
    ) -> Result<()> {
        let governance = &mut ctx.accounts.governance;
        governance.authority = ctx.accounts.authority.key();
        governance.epi_threshold = epi_threshold;
        governance.voting_period = voting_period;
        governance.quorum_percentage = quorum_percentage;
        governance.proposal_count = 0;
        governance.total_voting_power = 0;
        governance.is_paused = false;
        governance.bump = ctx.bumps.governance;

        msg!("Governance initialized with EPI threshold: {}", epi_threshold);
        emit!(GovernanceInitialized {
            authority: governance.authority,
            epi_threshold,
            voting_period,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }

    /// Submit a proposal with EPI validation
    pub fn submit_proposal(
        ctx: Context<SubmitProposal>,
        title: String,
        description: String,
        epi_score: u64,
        profit_score: u64,
        ethics_score: u64,
        ipfs_hash: [u8; 32],
        thought_hash: [u8; 32],
    ) -> Result<()> {
        require!(
            epi_score >= ctx.accounts.governance.epi_threshold,
            GovernanceError::EPIBelowThreshold
        );
        require!(title.len() <= 64, GovernanceError::TitleTooLong);
        require!(description.len() <= 256, GovernanceError::DescriptionTooLong);
        require!(profit_score <= 1_000_000, GovernanceError::InvalidScore);
        require!(ethics_score <= 1_000_000, GovernanceError::InvalidScore);

        let governance = &mut ctx.accounts.governance;
        let proposal = &mut ctx.accounts.proposal;
        let clock = Clock::get()?;

        proposal.id = governance.proposal_count;
        proposal.proposer = ctx.accounts.proposer.key();
        proposal.title = title.clone();
        proposal.description = description;
        proposal.epi_score = epi_score;
        proposal.profit_score = profit_score;
        proposal.ethics_score = ethics_score;
        proposal.ipfs_hash = ipfs_hash;
        proposal.thought_hash = thought_hash;
        proposal.votes_for = 0;
        proposal.votes_against = 0;
        proposal.votes_abstain = 0;
        proposal.start_slot = clock.slot;
        proposal.end_slot = clock.slot + governance.voting_period;
        proposal.status = ProposalStatus::Active;
        proposal.created_at = clock.unix_timestamp;
        proposal.executed_at = 0;
        proposal.bump = ctx.bumps.proposal;

        governance.proposal_count += 1;

        emit!(ProposalSubmitted {
            proposal_id: proposal.id,
            proposer: proposal.proposer,
            title,
            epi_score,
            start_slot: proposal.start_slot,
            end_slot: proposal.end_slot,
            timestamp: proposal.created_at,
        });

        msg!("Proposal {} submitted with EPI score: {}", proposal.id, epi_score);
        Ok(())
    }

    /// Cast a vote on a proposal
    pub fn vote(
        ctx: Context<Vote>,
        proposal_id: u64,
        support: u8,
        reason: String,
    ) -> Result<()> {
        let proposal = &mut ctx.accounts.proposal;
        let vote_record = &mut ctx.accounts.vote_record;
        let voter_account = &ctx.accounts.voter_account;
        let clock = Clock::get()?;

        require!(
            proposal.status == ProposalStatus::Active,
            GovernanceError::ProposalNotActive
        );
        require!(proposal.id == proposal_id, GovernanceError::InvalidProposal);
        require!(clock.slot >= proposal.start_slot, GovernanceError::VotingNotStarted);
        require!(clock.slot <= proposal.end_slot, GovernanceError::VotingEnded);
        require!(support <= 2, GovernanceError::InvalidVoteType);

        let voting_power = voter_account.voting_power;
        require!(voting_power > 0, GovernanceError::NoVotingPower);

        vote_record.voter = ctx.accounts.voter.key();
        vote_record.proposal_id = proposal_id;
        vote_record.support = support;
        vote_record.voting_power = voting_power;
        vote_record.timestamp = clock.unix_timestamp;
        vote_record.bump = ctx.bumps.vote_record;

        match support {
            0 => proposal.votes_against += voting_power,
            1 => proposal.votes_for += voting_power,
            2 => proposal.votes_abstain += voting_power,
            _ => return Err(GovernanceError::InvalidVoteType.into()),
        }

        emit!(VoteCast {
            proposal_id,
            voter: ctx.accounts.voter.key(),
            support,
            voting_power,
            reason,
            timestamp: clock.unix_timestamp,
        });

        msg!("Vote cast on proposal {}: support={} power={}", proposal_id, support, voting_power);
        Ok(())
    }

    /// Execute a proposal if it has passed
    pub fn execute_proposal(ctx: Context<ExecuteProposal>, proposal_id: u64) -> Result<()> {
        let proposal = &mut ctx.accounts.proposal;
        let governance = &ctx.accounts.governance;
        let clock = Clock::get()?;

        require!(proposal.id == proposal_id, GovernanceError::InvalidProposal);
        require!(clock.slot > proposal.end_slot, GovernanceError::VotingNotEnded);
        require!(
            proposal.status == ProposalStatus::Active,
            GovernanceError::ProposalNotActive
        );

        let total_votes = proposal.votes_for + proposal.votes_against + proposal.votes_abstain;
        let quorum_votes = (governance.total_voting_power * governance.quorum_percentage) / 10000;
        require!(total_votes >= quorum_votes, GovernanceError::QuorumNotReached);
        require!(proposal.votes_for > proposal.votes_against, GovernanceError::ProposalNotPassed);

        proposal.status = ProposalStatus::Executed;
        proposal.executed_at = clock.unix_timestamp;

        emit!(ProposalExecuted {
            proposal_id,
            executor: ctx.accounts.executor.key(),
            votes_for: proposal.votes_for,
            votes_against: proposal.votes_against,
            timestamp: clock.unix_timestamp,
        });

        msg!("Proposal {} executed", proposal_id);
        Ok(())
    }

    /// Guardian veto power (Class A stakeholders)
    pub fn veto_proposal(
        ctx: Context<VetoProposal>,
        proposal_id: u64,
        reason: String,
    ) -> Result<()> {
        let proposal = &mut ctx.accounts.proposal;
        let guardian = &mut ctx.accounts.guardian_account;
        let clock = Clock::get()?;

        require!(proposal.id == proposal_id, GovernanceError::InvalidProposal);
        require!(guardian.is_active, GovernanceError::NotGuardian);
        require!(
            proposal.status == ProposalStatus::Active ||
            proposal.status == ProposalStatus::Succeeded,
            GovernanceError::CannotVeto
        );

        proposal.status = ProposalStatus::Vetoed;
        guardian.veto_count += 1;

        emit!(ProposalVetoed {
            proposal_id,
            guardian: ctx.accounts.guardian.key(),
            reason,
            timestamp: clock.unix_timestamp,
        });

        msg!("Proposal {} vetoed by guardian", proposal_id);
        Ok(())
    }

    /// Log AI thought process
    pub fn log_thought(
        ctx: Context<LogThought>,
        agent_id: String,
        action: String,
        epi_score: u64,
        reasoning_hash: [u8; 32],
        inputs_hash: [u8; 32],
        outputs_hash: [u8; 32],
    ) -> Result<()> {
        let thought_log = &mut ctx.accounts.thought_log;
        let clock = Clock::get()?;

        require!(agent_id.len() <= 32, GovernanceError::AgentIdTooLong);
        require!(action.len() <= 64, GovernanceError::ActionTooLong);

        thought_log.agent_id = agent_id.clone();
        thought_log.action = action;
        thought_log.epi_score = epi_score;
        thought_log.reasoning_hash = reasoning_hash;
        thought_log.inputs_hash = inputs_hash;
        thought_log.outputs_hash = outputs_hash;
        thought_log.timestamp = clock.unix_timestamp;
        thought_log.logger = ctx.accounts.logger.key();
        thought_log.bump = ctx.bumps.thought_log;

        emit!(ThoughtLogged {
            proposal_id: 0,
            agent_id,
            thought_hash: reasoning_hash,
            timestamp: thought_log.timestamp,
        });

        msg!("Thought logged for agent: {}", thought_log.agent_id);
        Ok(())
    }

    /// Register a voter with voting power
    pub fn register_voter(ctx: Context<RegisterVoter>, voting_power: u64) -> Result<()> {
        let voter_account = &mut ctx.accounts.voter_account;
        let governance = &mut ctx.accounts.governance;

        voter_account.voter = ctx.accounts.voter.key();
        voter_account.voting_power = voting_power;
        voter_account.registered_at = Clock::get()?.unix_timestamp;
        voter_account.bump = ctx.bumps.voter_account;

        governance.total_voting_power += voting_power;

        emit!(VoterRegistered {
            voter: ctx.accounts.voter.key(),
            voting_power,
            timestamp: voter_account.registered_at,
        });

        msg!("Voter registered with power: {}", voting_power);
        Ok(())
    }

    /// Add a guardian
    pub fn add_guardian(ctx: Context<AddGuardian>) -> Result<()> {
        let guardian_account = &mut ctx.accounts.guardian_account;
        let clock = Clock::get()?;

        guardian_account.guardian = ctx.accounts.new_guardian.key();
        guardian_account.is_active = true;
        guardian_account.veto_count = 0;
        guardian_account.added_at = clock.unix_timestamp;
        guardian_account.bump = ctx.bumps.guardian_account;

        emit!(GuardianAdded {
            guardian: ctx.accounts.new_guardian.key(),
            timestamp: clock.unix_timestamp,
        });

        msg!("Guardian added: {}", ctx.accounts.new_guardian.key());
        Ok(())
    }

    /// Update EPI threshold
    pub fn update_epi_threshold(ctx: Context<UpdateGovernance>, new_threshold: u64) -> Result<()> {
        let governance = &mut ctx.accounts.governance;
        let old_threshold = governance.epi_threshold;
        governance.epi_threshold = new_threshold;

        emit!(EPIThresholdUpdated {
            old_threshold,
            new_threshold,
            timestamp: Clock::get()?.unix_timestamp,
        });

        msg!("EPI threshold updated: {} -> {}", old_threshold, new_threshold);
        Ok(())
    }
}

// ============ Account Contexts ============

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + Governance::INIT_SPACE,
        seeds = [b"governance"],
        bump
    )]
    pub governance: Account<'info, Governance>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SubmitProposal<'info> {
    #[account(mut)]
    pub governance: Account<'info, Governance>,
    #[account(
        init,
        payer = proposer,
        space = 8 + Proposal::INIT_SPACE,
        seeds = [b"proposal", governance.proposal_count.to_le_bytes().as_ref()],
        bump
    )]
    pub proposal: Account<'info, Proposal>,
    #[account(mut)]
    pub proposer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(proposal_id: u64)]
pub struct Vote<'info> {
    pub governance: Account<'info, Governance>,
    #[account(mut, seeds = [b"proposal", proposal_id.to_le_bytes().as_ref()], bump = proposal.bump)]
    pub proposal: Account<'info, Proposal>,
    #[account(seeds = [b"voter", voter.key().as_ref()], bump = voter_account.bump)]
    pub voter_account: Account<'info, VoterAccount>,
    #[account(
        init,
        payer = voter,
        space = 8 + VoteRecord::INIT_SPACE,
        seeds = [b"vote", proposal_id.to_le_bytes().as_ref(), voter.key().as_ref()],
        bump
    )]
    pub vote_record: Account<'info, VoteRecord>,
    #[account(mut)]
    pub voter: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(proposal_id: u64)]
pub struct ExecuteProposal<'info> {
    pub governance: Account<'info, Governance>,
    #[account(mut, seeds = [b"proposal", proposal_id.to_le_bytes().as_ref()], bump = proposal.bump)]
    pub proposal: Account<'info, Proposal>,
    pub executor: Signer<'info>,
}

#[derive(Accounts)]
#[instruction(proposal_id: u64)]
pub struct VetoProposal<'info> {
    pub governance: Account<'info, Governance>,
    #[account(mut, seeds = [b"proposal", proposal_id.to_le_bytes().as_ref()], bump = proposal.bump)]
    pub proposal: Account<'info, Proposal>,
    #[account(mut, seeds = [b"guardian", guardian.key().as_ref()], bump = guardian_account.bump)]
    pub guardian_account: Account<'info, GuardianAccount>,
    pub guardian: Signer<'info>,
}

#[derive(Accounts)]
pub struct LogThought<'info> {
    #[account(
        init,
        payer = logger,
        space = 8 + ThoughtLog::INIT_SPACE,
        seeds = [b"thought", logger.key().as_ref(), &Clock::get()?.unix_timestamp.to_le_bytes()],
        bump
    )]
    pub thought_log: Account<'info, ThoughtLog>,
    #[account(mut)]
    pub logger: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RegisterVoter<'info> {
    #[account(mut)]
    pub governance: Account<'info, Governance>,
    #[account(
        init,
        payer = authority,
        space = 8 + VoterAccount::INIT_SPACE,
        seeds = [b"voter", voter.key().as_ref()],
        bump
    )]
    pub voter_account: Account<'info, VoterAccount>,
    /// CHECK: Voter being registered
    pub voter: UncheckedAccount<'info>,
    #[account(mut, constraint = authority.key() == governance.authority @ GovernanceError::Unauthorized)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AddGuardian<'info> {
    #[account(constraint = governance.authority == authority.key() @ GovernanceError::Unauthorized)]
    pub governance: Account<'info, Governance>,
    #[account(
        init,
        payer = authority,
        space = 8 + GuardianAccount::INIT_SPACE,
        seeds = [b"guardian", new_guardian.key().as_ref()],
        bump
    )]
    pub guardian_account: Account<'info, GuardianAccount>,
    /// CHECK: New guardian
    pub new_guardian: UncheckedAccount<'info>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateGovernance<'info> {
    #[account(mut, constraint = governance.authority == authority.key() @ GovernanceError::Unauthorized)]
    pub governance: Account<'info, Governance>,
    pub authority: Signer<'info>,
}

// ============ State Accounts ============

#[account]
#[derive(InitSpace)]
pub struct Governance {
    pub authority: Pubkey,
    pub epi_threshold: u64,
    pub voting_period: u64,
    pub quorum_percentage: u64,
    pub proposal_count: u64,
    pub total_voting_power: u64,
    pub is_paused: bool,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct Proposal {
    pub id: u64,
    pub proposer: Pubkey,
    #[max_len(64)]
    pub title: String,
    #[max_len(256)]
    pub description: String,
    pub epi_score: u64,
    pub profit_score: u64,
    pub ethics_score: u64,
    pub ipfs_hash: [u8; 32],
    pub thought_hash: [u8; 32],
    pub votes_for: u64,
    pub votes_against: u64,
    pub votes_abstain: u64,
    pub start_slot: u64,
    pub end_slot: u64,
    pub status: ProposalStatus,
    pub created_at: i64,
    pub executed_at: i64,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct VoterAccount {
    pub voter: Pubkey,
    pub voting_power: u64,
    pub registered_at: i64,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct VoteRecord {
    pub voter: Pubkey,
    pub proposal_id: u64,
    pub support: u8,
    pub voting_power: u64,
    pub timestamp: i64,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct GuardianAccount {
    pub guardian: Pubkey,
    pub is_active: bool,
    pub veto_count: u64,
    pub added_at: i64,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct ThoughtLog {
    #[max_len(32)]
    pub agent_id: String,
    #[max_len(64)]
    pub action: String,
    pub epi_score: u64,
    pub reasoning_hash: [u8; 32],
    pub inputs_hash: [u8; 32],
    pub outputs_hash: [u8; 32],
    pub timestamp: i64,
    pub logger: Pubkey,
    pub bump: u8,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, PartialEq, Eq, InitSpace)]
pub enum ProposalStatus {
    Active,
    Defeated,
    Succeeded,
    Executed,
    Vetoed,
    Cancelled,
}

// ============ Events ============

#[event]
pub struct GovernanceInitialized {
    pub authority: Pubkey,
    pub epi_threshold: u64,
    pub voting_period: u64,
    pub timestamp: i64,
}

#[event]
pub struct ProposalSubmitted {
    pub proposal_id: u64,
    pub proposer: Pubkey,
    pub title: String,
    pub epi_score: u64,
    pub start_slot: u64,
    pub end_slot: u64,
    pub timestamp: i64,
}

#[event]
pub struct VoteCast {
    pub proposal_id: u64,
    pub voter: Pubkey,
    pub support: u8,
    pub voting_power: u64,
    pub reason: String,
    pub timestamp: i64,
}

#[event]
pub struct ProposalExecuted {
    pub proposal_id: u64,
    pub executor: Pubkey,
    pub votes_for: u64,
    pub votes_against: u64,
    pub timestamp: i64,
}

#[event]
pub struct ProposalVetoed {
    pub proposal_id: u64,
    pub guardian: Pubkey,
    pub reason: String,
    pub timestamp: i64,
}

#[event]
pub struct ThoughtLogged {
    pub proposal_id: u64,
    pub agent_id: String,
    pub thought_hash: [u8; 32],
    pub timestamp: i64,
}

#[event]
pub struct VoterRegistered {
    pub voter: Pubkey,
    pub voting_power: u64,
    pub timestamp: i64,
}

#[event]
pub struct GuardianAdded {
    pub guardian: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct EPIThresholdUpdated {
    pub old_threshold: u64,
    pub new_threshold: u64,
    pub timestamp: i64,
}

// ============ Errors ============

#[error_code]
pub enum GovernanceError {
    #[msg("EPI score is below the required threshold")]
    EPIBelowThreshold,
    #[msg("Proposal is not in active status")]
    ProposalNotActive,
    #[msg("Invalid proposal ID")]
    InvalidProposal,
    #[msg("Voting has not started yet")]
    VotingNotStarted,
    #[msg("Voting period has ended")]
    VotingEnded,
    #[msg("Voting period has not ended yet")]
    VotingNotEnded,
    #[msg("Proposal did not pass")]
    ProposalNotPassed,
    #[msg("Quorum not reached")]
    QuorumNotReached,
    #[msg("Unauthorized")]
    Unauthorized,
    #[msg("Not a guardian")]
    NotGuardian,
    #[msg("Cannot veto this proposal")]
    CannotVeto,
    #[msg("Invalid vote type")]
    InvalidVoteType,
    #[msg("No voting power")]
    NoVotingPower,
    #[msg("Invalid score value")]
    InvalidScore,
    #[msg("Title too long (max 64 chars)")]
    TitleTooLong,
    #[msg("Description too long (max 256 chars)")]
    DescriptionTooLong,
    #[msg("Agent ID too long (max 32 chars)")]
    AgentIdTooLong,
    #[msg("Action too long (max 64 chars)")]
    ActionTooLong,
}
