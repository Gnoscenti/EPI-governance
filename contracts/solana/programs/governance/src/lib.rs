use anchor_lang::prelude::*;

declare_id!("MicroAiGovernance11111111111111111111111111");

#[program]
pub mod governance {
    use super::*;

    /// Initialize the governance program with EPI threshold
    pub fn initialize(ctx: Context<Initialize>, epi_threshold: u64) -> Result<()> {
        let governance = &mut ctx.accounts.governance;
        governance.authority = ctx.accounts.authority.key();
        governance.epi_threshold = epi_threshold;
        governance.proposal_count = 0;
        governance.bump = *ctx.bumps.get("governance").unwrap();
        
        msg!("Governance initialized with EPI threshold: {}", epi_threshold);
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
    ) -> Result<()> {
        require!(
            epi_score >= ctx.accounts.governance.epi_threshold,
            GovernanceError::EPIBelowThreshold
        );

        let governance = &mut ctx.accounts.governance;
        let proposal = &mut ctx.accounts.proposal;
        
        proposal.id = governance.proposal_count;
        proposal.proposer = ctx.accounts.proposer.key();
        proposal.title = title;
        proposal.description = description;
        proposal.epi_score = epi_score;
        proposal.profit_score = profit_score;
        proposal.ethics_score = ethics_score;
        proposal.votes_for = 0;
        proposal.votes_against = 0;
        proposal.status = ProposalStatus::Active;
        proposal.created_at = Clock::get()?.unix_timestamp;
        proposal.executed = false;
        
        governance.proposal_count += 1;
        
        emit!(ProposalSubmitted {
            proposal_id: proposal.id,
            proposer: proposal.proposer,
            epi_score,
            timestamp: proposal.created_at,
        });
        
        msg!("Proposal {} submitted with EPI score: {}", proposal.id, epi_score);
        Ok(())
    }

    /// Cast a vote on a proposal
    pub fn vote(
        ctx: Context<Vote>,
        proposal_id: u64,
        vote_for: bool,
        voting_power: u64,
    ) -> Result<()> {
        let proposal = &mut ctx.accounts.proposal;
        
        require!(
            proposal.status == ProposalStatus::Active,
            GovernanceError::ProposalNotActive
        );
        
        require!(
            proposal.id == proposal_id,
            GovernanceError::InvalidProposal
        );
        
        if vote_for {
            proposal.votes_for += voting_power;
        } else {
            proposal.votes_against += voting_power;
        }
        
        emit!(VoteCast {
            proposal_id,
            voter: ctx.accounts.voter.key(),
            vote_for,
            voting_power,
        });
        
        msg!("Vote cast on proposal {}: {} with power {}", proposal_id, vote_for, voting_power);
        Ok(())
    }

    /// Execute a proposal if it has passed
    pub fn execute_proposal(ctx: Context<ExecuteProposal>, proposal_id: u64) -> Result<()> {
        let proposal = &mut ctx.accounts.proposal;
        
        require!(
            proposal.id == proposal_id,
            GovernanceError::InvalidProposal
        );
        
        require!(
            proposal.status == ProposalStatus::Active,
            GovernanceError::ProposalNotActive
        );
        
        require!(
            !proposal.executed,
            GovernanceError::AlreadyExecuted
        );
        
        // Check if proposal has passed (simple majority)
        let total_votes = proposal.votes_for + proposal.votes_against;
        require!(
            total_votes > 0 && proposal.votes_for > proposal.votes_against,
            GovernanceError::ProposalNotPassed
        );
        
        proposal.status = ProposalStatus::Executed;
        proposal.executed = true;
        
        emit!(ProposalExecuted {
            proposal_id,
            executor: ctx.accounts.executor.key(),
            timestamp: Clock::get()?.unix_timestamp,
        });
        
        msg!("Proposal {} executed", proposal_id);
        Ok(())
    }

    /// Guardian veto power (Class A stakeholders)
    pub fn veto_proposal(ctx: Context<VetoProposal>, proposal_id: u64) -> Result<()> {
        let proposal = &mut ctx.accounts.proposal;
        
        require!(
            proposal.id == proposal_id,
            GovernanceError::InvalidProposal
        );
        
        require!(
            ctx.accounts.guardian.key() == ctx.accounts.governance.authority,
            GovernanceError::Unauthorized
        );
        
        proposal.status = ProposalStatus::Vetoed;
        proposal.executed = false;
        
        emit!(ProposalVetoed {
            proposal_id,
            guardian: ctx.accounts.guardian.key(),
            timestamp: Clock::get()?.unix_timestamp,
        });
        
        msg!("Proposal {} vetoed by guardian", proposal_id);
        Ok(())
    }

    /// Log AI thought process (for transparency)
    pub fn log_thought(
        ctx: Context<LogThought>,
        agent_id: String,
        action: String,
        epi_score: u64,
        reasoning_hash: [u8; 32],
    ) -> Result<()> {
        let thought_log = &mut ctx.accounts.thought_log;
        
        thought_log.agent_id = agent_id;
        thought_log.action = action;
        thought_log.epi_score = epi_score;
        thought_log.reasoning_hash = reasoning_hash;
        thought_log.timestamp = Clock::get()?.unix_timestamp;
        thought_log.logger = ctx.accounts.logger.key();
        
        emit!(ThoughtLogged {
            agent_id: thought_log.agent_id.clone(),
            action: thought_log.action.clone(),
            epi_score,
            timestamp: thought_log.timestamp,
        });
        
        msg!("Thought logged for agent: {}", thought_log.agent_id);
        Ok(())
    }
}

// Account structures

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
pub struct Vote<'info> {
    #[account(mut)]
    pub proposal: Account<'info, Proposal>,
    
    pub voter: Signer<'info>,
}

#[derive(Accounts)]
pub struct ExecuteProposal<'info> {
    #[account(mut)]
    pub proposal: Account<'info, Proposal>,
    
    pub executor: Signer<'info>,
}

#[derive(Accounts)]
pub struct VetoProposal<'info> {
    pub governance: Account<'info, Governance>,
    
    #[account(mut)]
    pub proposal: Account<'info, Proposal>,
    
    pub guardian: Signer<'info>,
}

#[derive(Accounts)]
pub struct LogThought<'info> {
    #[account(
        init,
        payer = logger,
        space = 8 + ThoughtLog::INIT_SPACE
    )]
    pub thought_log: Account<'info, ThoughtLog>,
    
    #[account(mut)]
    pub logger: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

// State structures

#[account]
#[derive(InitSpace)]
pub struct Governance {
    pub authority: Pubkey,
    pub epi_threshold: u64,  // Scaled by 1e6 (e.g., 700000 = 0.7)
    pub proposal_count: u64,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct Proposal {
    pub id: u64,
    pub proposer: Pubkey,
    #[max_len(100)]
    pub title: String,
    #[max_len(500)]
    pub description: String,
    pub epi_score: u64,
    pub profit_score: u64,
    pub ethics_score: u64,
    pub votes_for: u64,
    pub votes_against: u64,
    pub status: ProposalStatus,
    pub created_at: i64,
    pub executed: bool,
}

#[account]
#[derive(InitSpace)]
pub struct ThoughtLog {
    #[max_len(50)]
    pub agent_id: String,
    #[max_len(100)]
    pub action: String,
    pub epi_score: u64,
    pub reasoning_hash: [u8; 32],  // Hash of full reasoning (stored on IPFS/Arweave)
    pub timestamp: i64,
    pub logger: Pubkey,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq, InitSpace)]
pub enum ProposalStatus {
    Active,
    Executed,
    Vetoed,
    Expired,
}

// Events

#[event]
pub struct ProposalSubmitted {
    pub proposal_id: u64,
    pub proposer: Pubkey,
    pub epi_score: u64,
    pub timestamp: i64,
}

#[event]
pub struct VoteCast {
    pub proposal_id: u64,
    pub voter: Pubkey,
    pub vote_for: bool,
    pub voting_power: u64,
}

#[event]
pub struct ProposalExecuted {
    pub proposal_id: u64,
    pub executor: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct ProposalVetoed {
    pub proposal_id: u64,
    pub guardian: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct ThoughtLogged {
    pub agent_id: String,
    pub action: String,
    pub epi_score: u64,
    pub timestamp: i64,
}

// Errors

#[error_code]
pub enum GovernanceError {
    #[msg("EPI score below threshold")]
    EPIBelowThreshold,
    
    #[msg("Proposal is not active")]
    ProposalNotActive,
    
    #[msg("Invalid proposal ID")]
    InvalidProposal,
    
    #[msg("Proposal already executed")]
    AlreadyExecuted,
    
    #[msg("Proposal has not passed")]
    ProposalNotPassed,
    
    #[msg("Unauthorized action")]
    Unauthorized,
}
