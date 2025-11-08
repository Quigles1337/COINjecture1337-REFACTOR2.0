// Block Validator
// Comprehensive block and transaction validation

use coinject_core::{Block, Hash};
use coinject_state::AccountState;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ValidationError {
    #[error("Invalid block height: expected {expected}, got {actual}")]
    InvalidHeight { expected: u64, actual: u64 },
    #[error("Invalid previous hash")]
    InvalidPrevHash,
    #[error("Invalid solution: does not solve the problem")]
    InvalidSolution,
    #[error("Invalid commitment")]
    InvalidCommitment,
    #[error("Insufficient work score: {0}")]
    InsufficientWorkScore(f64),
    #[error("Invalid block hash: does not meet difficulty target")]
    InsufficientDifficulty,
    #[error("Invalid timestamp: block is from the future")]
    FutureTimestamp,
    #[error("Invalid timestamp: block is too old")]
    TooOldTimestamp,
    #[error("Transaction validation failed: {0}")]
    InvalidTransaction(String),
    #[error("Coinbase amount exceeds maximum")]
    InvalidCoinbase,
    #[error("State error: {0}")]
    StateError(String),
}

/// Block validator with configurable rules
pub struct BlockValidator {
    /// Minimum work score required
    min_work_score: f64,
    /// Minimum difficulty (leading zeros)
    min_difficulty: u32,
    /// Maximum timestamp drift (seconds into future)
    max_timestamp_drift: i64,
    /// Maximum age for blocks (seconds)
    max_block_age: i64,
}

impl BlockValidator {
    pub fn new(min_difficulty: u32) -> Self {
        BlockValidator {
            min_work_score: 1.0,
            min_difficulty,
            max_timestamp_drift: 120, // 2 minutes into future
            max_block_age: 7200,      // 2 hours old
        }
    }

    /// Validate a block completely
    pub fn validate_block(
        &self,
        block: &Block,
        prev_hash: &Hash,
        expected_height: u64,
    ) -> Result<(), ValidationError> {
        // 1. Validate block height
        if block.header.height != expected_height {
            return Err(ValidationError::InvalidHeight {
                expected: expected_height,
                actual: block.header.height,
            });
        }

        // 2. Validate previous hash
        if block.header.prev_hash != *prev_hash {
            return Err(ValidationError::InvalidPrevHash);
        }

        // 3. Validate timestamp
        self.validate_timestamp(block.header.timestamp)?;

        // 4. Validate NP-hard solution
        if !block.solution_reveal.solution.verify(&block.solution_reveal.problem) {
            return Err(ValidationError::InvalidSolution);
        }

        // 5. Validate commitment-reveal
        let epoch_salt = Hash::new(&block.header.height.to_le_bytes());
        if !block.solution_reveal.commitment.verify(
            &block.solution_reveal.problem,
            &block.solution_reveal.solution,
            &epoch_salt,
        ) {
            return Err(ValidationError::InvalidCommitment);
        }

        // 6. Validate work score
        if block.header.work_score < self.min_work_score {
            return Err(ValidationError::InsufficientWorkScore(block.header.work_score));
        }

        // 7. Validate difficulty (block hash)
        self.validate_difficulty(block)?;

        // 8. Validate all transactions
        for tx in &block.transactions {
            if !tx.verify_signature() {
                return Err(ValidationError::InvalidTransaction(
                    "Invalid signature".to_string(),
                ));
            }
        }

        Ok(())
    }

    /// Validate block timestamp
    fn validate_timestamp(&self, timestamp: i64) -> Result<(), ValidationError> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64;

        // Check if block is from the future
        if timestamp > now + self.max_timestamp_drift {
            return Err(ValidationError::FutureTimestamp);
        }

        // Check if block is too old
        if timestamp < now - self.max_block_age {
            return Err(ValidationError::TooOldTimestamp);
        }

        Ok(())
    }

    /// Validate block hash meets difficulty target
    fn validate_difficulty(&self, block: &Block) -> Result<(), ValidationError> {
        let hash = block.header.hash();
        let hash_hex = hex::encode(hash.as_bytes());

        let leading_zeros = hash_hex.chars().take_while(|&c| c == '0').count();

        if leading_zeros < self.min_difficulty as usize {
            return Err(ValidationError::InsufficientDifficulty);
        }

        Ok(())
    }

    /// Apply block to state (execute transactions)
    pub fn apply_block(
        &self,
        block: &Block,
        state: &AccountState,
    ) -> Result<(), ValidationError> {
        // Credit coinbase to miner
        let current_balance = state.get_balance(&block.header.miner);
        state
            .set_balance(&block.header.miner, current_balance + block.coinbase.reward)
            .map_err(|e| ValidationError::StateError(format!("{:?}", e)))?;

        // Execute all transactions
        for tx in &block.transactions {
            // Verify sender has sufficient balance
            let sender_balance = state.get_balance(&tx.from);
            let total_cost = tx.amount + tx.fee;

            if sender_balance < total_cost {
                return Err(ValidationError::InvalidTransaction(format!(
                    "Insufficient balance: has {}, needs {}",
                    sender_balance, total_cost
                )));
            }

            // Verify nonce
            let expected_nonce = state.get_nonce(&tx.from);
            if tx.nonce != expected_nonce {
                return Err(ValidationError::InvalidTransaction(format!(
                    "Invalid nonce: expected {}, got {}",
                    expected_nonce, tx.nonce
                )));
            }

            // Execute transfer
            state
                .transfer(&tx.from, &tx.to, tx.amount)
                .map_err(|e| ValidationError::StateError(format!("{:?}", e)))?;

            // Transfer fee to miner
            let sender_balance_after = state.get_balance(&tx.from);
            state
                .set_balance(&tx.from, sender_balance_after - tx.fee)
                .map_err(|e| ValidationError::StateError(format!("{:?}", e)))?;

            let miner_balance = state.get_balance(&block.header.miner);
            state
                .set_balance(&block.header.miner, miner_balance + tx.fee)
                .map_err(|e| ValidationError::StateError(format!("{:?}", e)))?;

            // Increment nonce
            state
                .increment_nonce(&tx.from)
                .map_err(|e| ValidationError::StateError(format!("{:?}", e)))?;
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::genesis::{create_genesis_block, GenesisConfig};

    #[test]
    fn test_genesis_validation() {
        let genesis = create_genesis_block(GenesisConfig::default());
        let validator = BlockValidator::new(0); // No difficulty for testing

        // Genesis should validate with ZERO prev hash
        let result = validator.validate_block(&genesis, &Hash::ZERO, 0);
        assert!(result.is_ok());
    }

    #[test]
    fn test_invalid_height() {
        let genesis = create_genesis_block(GenesisConfig::default());
        let validator = BlockValidator::new(0);

        // Wrong expected height
        let result = validator.validate_block(&genesis, &Hash::ZERO, 1);
        assert!(matches!(result, Err(ValidationError::InvalidHeight { .. })));
    }

    #[test]
    fn test_invalid_prev_hash() {
        let genesis = create_genesis_block(GenesisConfig::default());
        let validator = BlockValidator::new(0);

        // Wrong prev hash
        let wrong_hash = Hash::new(b"wrong");
        let result = validator.validate_block(&genesis, &wrong_hash, 0);
        assert!(matches!(result, Err(ValidationError::InvalidPrevHash)));
    }
}
