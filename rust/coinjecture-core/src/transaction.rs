//! Transaction validation - Consensus-critical financial primitives
//!
//! This module implements deterministic transaction validation for the $BEANS token economy.
//! All validation rules are consensus-critical and must be identical across all platforms.
//!
//! # Security Model
//!
//! - Ed25519 signature verification (RFC 8032)
//! - Nonce-based replay protection
//! - Balance overflow prevention
//! - Fee minimum enforcement (spam prevention)
//! - Deterministic error codes (no platform-dependent errors)
//!
//! # Fee Structure
//!
//! - Base fee: 0.01% of transfer amount (minimum 1000 wei)
//! - Fee distribution: 60% miners, 20% burn, 15% treasury, 5% validators
//! - Gas model: Compatible with Ethereum-style gas limits/prices
//!
//! Version: 4.2.0

use crate::errors::{ConsensusError, Result};
use crate::types::{Transaction, TxType};
use ed25519_dalek::{Signature, Verifier, VerifyingKey};

/// Minimum transaction fee (1000 wei = 0.000000000000001 BEANS)
pub const MIN_TX_FEE: u64 = 1000;

/// Fee percentage (0.01% = 1/10000)
pub const FEE_PERCENT_DENOMINATOR: u64 = 10_000;

/// Standard gas limit for simple transfer
pub const GAS_LIMIT_TRANSFER: u64 = 21_000;

/// Standard gas limit for escrow operations
pub const GAS_LIMIT_ESCROW: u64 = 50_000;

/// Wei per BEANS (10^18)
pub const WEI_PER_BEANS: u64 = 1_000_000_000_000_000_000;

/// Account state snapshot (needed for validation)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AccountState {
    /// Current balance in wei
    pub balance: u64,

    /// Current nonce (number of transactions sent)
    pub nonce: u64,
}

impl Default for AccountState {
    fn default() -> Self {
        Self {
            balance: 0,
            nonce: 0,
        }
    }
}

/// Transaction validation result
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ValidationResult {
    /// Is transaction valid?
    pub valid: bool,

    /// Total cost (amount + fees)
    pub total_cost: u64,

    /// Gas used
    pub gas_used: u64,

    /// Calculated fee
    pub fee: u64,
}

impl ValidationResult {
    pub fn invalid() -> Self {
        Self {
            valid: false,
            total_cost: 0,
            gas_used: 0,
            fee: 0,
        }
    }

    pub fn valid(total_cost: u64, gas_used: u64, fee: u64) -> Self {
        Self {
            valid: true,
            total_cost,
            gas_used,
            fee,
        }
    }
}

/// Verify transaction signature (Ed25519)
///
/// # Security
///
/// - Uses ed25519-dalek for RFC 8032 compliance
/// - Signature must be over canonical transaction bytes
/// - Public key derived from sender address (first 32 bytes)
///
/// # Errors
///
/// - `InvalidSignature`: Signature verification failed
/// - `InvalidPublicKey`: Cannot parse public key from address
pub fn verify_signature(tx: &Transaction) -> Result<()> {
    // Parse public key from sender address
    let public_key = VerifyingKey::from_bytes(&tx.from)
        .map_err(|_| ConsensusError::InvalidPublicKey)?;

    // Parse signature
    let signature = Signature::from_bytes(&tx.signature);

    // Compute message to sign (all fields except signature)
    let message = compute_signing_message(tx);

    // Verify signature
    public_key
        .verify(&message, &signature)
        .map_err(|_| ConsensusError::InvalidSignature)?;

    Ok(())
}

/// Compute canonical message for transaction signing
///
/// Message format (deterministic, platform-independent):
/// - codec_version: u8
/// - tx_type: u8
/// - from: [u8; 32]
/// - to: [u8; 32]
/// - amount: u64 (little-endian)
/// - nonce: u64 (little-endian)
/// - gas_limit: u64 (little-endian)
/// - gas_price: u64 (little-endian)
/// - data_len: u32 (little-endian)
/// - data: [u8]
/// - timestamp: i64 (little-endian)
fn compute_signing_message(tx: &Transaction) -> Vec<u8> {
    let mut message = Vec::with_capacity(
        1 + 1 + 32 + 32 + 8 + 8 + 8 + 8 + 4 + tx.data.len() + 8
    );

    message.push(tx.codec_version);
    message.push(tx.tx_type as u8);
    message.extend_from_slice(&tx.from);
    message.extend_from_slice(&tx.to);
    message.extend_from_slice(&tx.amount.to_le_bytes());
    message.extend_from_slice(&tx.nonce.to_le_bytes());
    message.extend_from_slice(&tx.gas_limit.to_le_bytes());
    message.extend_from_slice(&tx.gas_price.to_le_bytes());
    message.extend_from_slice(&(tx.data.len() as u32).to_le_bytes());
    message.extend_from_slice(&tx.data);
    message.extend_from_slice(&tx.timestamp.to_le_bytes());

    message
}

/// Calculate minimum fee for transaction
///
/// # Fee Calculation
///
/// - Base: 0.01% of transfer amount
/// - Minimum: 1000 wei (prevents dust/spam)
/// - Gas-based: max(base_fee, gas_limit * gas_price)
///
/// # Examples
///
/// ```
/// # use coinjecture_core::transaction::calculate_minimum_fee;
/// # use coinjecture_core::types::Transaction;
/// let tx = Transaction {
///     amount: 1_000_000_000_000_000_000, // 1 BEANS
///     gas_limit: 21_000,
///     gas_price: 1,
///     ..Default::default()
/// };
/// let fee = calculate_minimum_fee(&tx);
/// assert!(fee >= 1000); // At least minimum
/// ```
pub fn calculate_minimum_fee(tx: &Transaction) -> u64 {
    // Calculate percentage-based fee (0.01%)
    let percent_fee = tx.amount
        .checked_div(FEE_PERCENT_DENOMINATOR)
        .unwrap_or(0);

    // Calculate gas-based fee
    let gas_fee = tx.gas_limit
        .checked_mul(tx.gas_price)
        .unwrap_or(u64::MAX);

    // Take maximum of (percent_fee, gas_fee, MIN_TX_FEE)
    percent_fee.max(gas_fee).max(MIN_TX_FEE)
}

/// Verify transaction semantics (balance, nonce, fee)
///
/// # Validation Rules
///
/// 1. **Nonce check**: tx.nonce must equal sender.nonce (prevents replay)
/// 2. **Balance check**: sender.balance >= amount + fee (prevents overdraft)
/// 3. **Fee check**: Calculated fee meets minimum (prevents spam)
/// 4. **Overflow check**: amount + fee doesn't overflow u64
/// 5. **Gas check**: gas_limit >= minimum for tx_type
///
/// # Errors
///
/// - `InvalidNonce`: Nonce mismatch (replay attack or out-of-order)
/// - `InsufficientBalance`: Sender cannot afford transaction
/// - `FeeTooLow`: Fee below minimum threshold
/// - `AmountOverflow`: Amount + fee exceeds u64::MAX
/// - `GasLimitTooLow`: Gas limit insufficient for operation
pub fn verify_transaction_semantics(
    tx: &Transaction,
    sender_state: &AccountState,
) -> Result<ValidationResult> {
    // 1. Verify nonce (replay protection)
    if tx.nonce != sender_state.nonce {
        return Err(ConsensusError::InvalidNonce {
            expected: sender_state.nonce,
            got: tx.nonce,
        });
    }

    // 2. Calculate minimum fee
    let min_fee = calculate_minimum_fee(tx);
    let actual_fee = tx.gas_limit
        .checked_mul(tx.gas_price)
        .ok_or(ConsensusError::AmountOverflow)?;

    if actual_fee < min_fee {
        return Err(ConsensusError::FeeTooLow {
            required: min_fee,
            provided: actual_fee,
        });
    }

    // 3. Check for amount overflow (amount + fee)
    let total_cost = tx.amount
        .checked_add(actual_fee)
        .ok_or(ConsensusError::AmountOverflow)?;

    // 4. Verify sufficient balance
    if sender_state.balance < total_cost {
        return Err(ConsensusError::InsufficientBalance {
            available: sender_state.balance,
            required: total_cost,
        });
    }

    // 5. Verify gas limit is sufficient for operation
    let min_gas = match tx.tx_type {
        TxType::Transfer => GAS_LIMIT_TRANSFER,
        TxType::BountyPayment => GAS_LIMIT_ESCROW,
        TxType::ProblemSubmission => GAS_LIMIT_ESCROW,
    };

    if tx.gas_limit < min_gas {
        return Err(ConsensusError::GasLimitTooLow {
            required: min_gas,
            provided: tx.gas_limit,
        });
    }

    Ok(ValidationResult::valid(total_cost, tx.gas_limit, actual_fee))
}

/// Complete transaction validation (signature + semantics)
///
/// This is the main entry point for validating transactions.
/// Used by mempool, block builders, and consensus verification.
///
/// # Process
///
/// 1. Verify Ed25519 signature
/// 2. Verify nonce (replay protection)
/// 3. Verify balance (no overdraft)
/// 4. Verify fee meets minimum
/// 5. Verify gas limit sufficient
///
/// # Examples
///
/// ```ignore
/// use coinjecture_core::transaction::{verify_transaction, AccountState};
/// use coinjecture_core::types::Transaction;
///
/// let tx: Transaction = /* from network */;
/// let sender_state = AccountState {
///     balance: 1_000_000_000_000_000_000, // 1 BEANS
///     nonce: 0,
/// };
///
/// match verify_transaction(&tx, &sender_state) {
///     Ok(result) => {
///         println!("Valid! Cost: {} wei", result.total_cost);
///     }
///     Err(e) => {
///         println!("Invalid: {:?}", e);
///     }
/// }
/// ```
pub fn verify_transaction(
    tx: &Transaction,
    sender_state: &AccountState,
) -> Result<ValidationResult> {
    // Step 1: Verify cryptographic signature
    verify_signature(tx)?;

    // Step 2: Verify transaction semantics
    verify_transaction_semantics(tx, sender_state)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ed25519_dalek::{SigningKey, Signer};
    use rand::{rngs::OsRng, RngCore};

    fn create_test_transaction() -> (Transaction, SigningKey) {
        let mut secret_bytes = [0u8; 32];
        OsRng.fill_bytes(&mut secret_bytes);
        let signing_key = SigningKey::from_bytes(&secret_bytes);
        let verifying_key = signing_key.verifying_key();

        let mut tx = Transaction {
            codec_version: 1,
            tx_type: TxType::Transfer,
            from: verifying_key.to_bytes(),
            to: [1u8; 32],
            amount: 1_000_000, // Small amount so gas fee dominates
            nonce: 0,
            gas_limit: 21_000,
            gas_price: 100, // Higher gas price so fee >= min
            signature: [0u8; 64],
            data: Vec::new(),
            timestamp: 1_000_000,
        };

        // Sign transaction
        let message = compute_signing_message(&tx);
        let signature = signing_key.sign(&message);
        tx.signature = signature.to_bytes();

        (tx, signing_key)
    }

    #[test]
    fn test_verify_signature_valid() {
        let (tx, _) = create_test_transaction();
        assert!(verify_signature(&tx).is_ok());
    }

    #[test]
    fn test_verify_signature_invalid() {
        let (mut tx, _) = create_test_transaction();

        // Tamper with signature
        tx.signature[0] ^= 1;

        assert!(matches!(
            verify_signature(&tx),
            Err(ConsensusError::InvalidSignature)
        ));
    }

    #[test]
    fn test_calculate_minimum_fee() {
        let tx = Transaction {
            amount: 10_000_000_000, // 0.00000001 BEANS
            gas_limit: 21_000,
            gas_price: 1,
            ..Default::default()
        };

        let fee = calculate_minimum_fee(&tx);

        // Should be max(1000, 21000, 10_000_000_000 / 10_000)
        assert_eq!(fee, 1_000_000); // 0.01% of amount
    }

    #[test]
    fn test_calculate_minimum_fee_enforces_minimum() {
        let tx = Transaction {
            amount: 100, // Tiny amount
            gas_limit: 100,
            gas_price: 1,
            ..Default::default()
        };

        let fee = calculate_minimum_fee(&tx);
        assert_eq!(fee, MIN_TX_FEE); // Should enforce minimum
    }

    #[test]
    fn test_verify_transaction_valid() {
        let (tx, _) = create_test_transaction();
        let sender_state = AccountState {
            balance: 1_000_000_000_000, // Plenty
            nonce: 0,
        };

        let result = verify_transaction(&tx, &sender_state).unwrap();
        assert!(result.valid);
        assert!(result.total_cost > 0);
    }

    #[test]
    fn test_verify_transaction_insufficient_balance() {
        let (tx, _) = create_test_transaction();
        // Set balance just below what's needed (amount + fee)
        // Fee = 21_000 * 100 = 2_100_000
        // Amount = 1_000_000
        // Total needed = 3_100_000
        let sender_state = AccountState {
            balance: 3_000_000, // Not enough (need 3_100_000)
            nonce: 0,
        };

        assert!(matches!(
            verify_transaction(&tx, &sender_state),
            Err(ConsensusError::InsufficientBalance { .. })
        ));
    }

    #[test]
    fn test_verify_transaction_invalid_nonce() {
        let (tx, _) = create_test_transaction();
        let sender_state = AccountState {
            balance: 1_000_000_000_000,
            nonce: 5, // Wrong nonce
        };

        assert!(matches!(
            verify_transaction(&tx, &sender_state),
            Err(ConsensusError::InvalidNonce { .. })
        ));
    }

    #[test]
    fn test_verify_transaction_fee_too_low() {
        let (mut tx, signing_key) = create_test_transaction();

        // Set gas price to 0 (fee too low)
        tx.gas_price = 0;
        tx.gas_limit = 0;

        // Re-sign
        let message = compute_signing_message(&tx);
        let signature = signing_key.sign(&message);
        tx.signature = signature.to_bytes();

        let sender_state = AccountState {
            balance: 1_000_000_000_000,
            nonce: 0,
        };

        assert!(matches!(
            verify_transaction(&tx, &sender_state),
            Err(ConsensusError::FeeTooLow { .. })
        ));
    }
}
