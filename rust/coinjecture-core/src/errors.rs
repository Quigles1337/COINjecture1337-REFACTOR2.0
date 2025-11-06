//! Typed error definitions for consensus-critical operations.
//!
//! NO PANICS in consensus path - all errors are typed and recoverable.
//! Defense-in-depth: explicit error codes for observability and debugging.

use thiserror::Error;

/// Result type alias for consensus operations
pub type Result<T> = std::result::Result<T, ConsensusError>;

/// Consensus-critical errors - NEVER panic, always return typed error
#[derive(Error, Debug, Clone, PartialEq, Eq)]
pub enum ConsensusError {
    // ==================== CODEC ERRORS (SEC-001) ====================
    #[error("Codec error: {0}")]
    CodecError(String),

    #[error("Unknown field in strict decode: {field}")]
    UnknownField { field: String },

    #[error("Missing required field: {field}")]
    MissingField { field: String },

    #[error("Invalid field type: expected {expected}, got {actual}")]
    InvalidFieldType { expected: String, actual: String },

    #[error("Codec version mismatch: expected {expected}, got {actual}")]
    CodecVersionMismatch { expected: u8, actual: u8 },

    #[error("Overlong varint encoding detected")]
    OverlongVarint,

    #[error("NaN or Inf float value not allowed")]
    InvalidFloatValue,

    #[error("Cross-path codec mismatch: msgpack hash {msgpack} != json hash {json}")]
    CrossPathMismatch { msgpack: String, json: String },

    // ==================== VERIFICATION ERRORS ====================
    #[error("Verification budget exceeded: max_ops={max_ops}, actual={actual_ops}")]
    BudgetOpsExceeded { max_ops: u64, actual_ops: u64 },

    #[error("Verification timeout: max_ms={max_ms}, actual={actual_ms}")]
    BudgetTimeExceeded { max_ms: u64, actual_ms: u64 },

    #[error("Subset sum verification failed: solution does not match target")]
    SubsetSumInvalid,

    #[error("Invalid proof size: tier={tier}, elements={elements}, max={max}")]
    InvalidProofSize {
        tier: u8,
        elements: usize,
        max: usize,
    },

    #[error("Solution indices out of bounds: index={index}, max={max}")]
    IndexOutOfBounds { index: u32, max: usize },

    #[error("Duplicate solution indices: index={index}")]
    DuplicateIndex { index: u32 },

    // ==================== COMMITMENT ERRORS (SEC-002) ====================
    #[error("Commitment binding verification failed")]
    CommitmentMismatch,

    #[error("Epoch salt binding failed: commitment does not match epoch")]
    EpochBindingFailed,

    #[error("Miner salt HMAC verification failed")]
    MinerSaltInvalid,

    #[error("Problem hash mismatch: expected {expected}, computed {computed}")]
    ProblemHashMismatch { expected: String, computed: String },

    #[error("Solution hash mismatch: expected {expected}, computed {computed}")]
    SolutionHashMismatch { expected: String, computed: String },

    // ==================== EPOCH REPLAY ERRORS (SEC-002) ====================
    #[error("Epoch replay detected: commitment {commitment} already used in epoch {epoch}")]
    EpochReplay { commitment: String, epoch: u64 },

    #[error("Epoch too old: current={current}, block={block}, max_age={max_age}")]
    EpochTooOld {
        current: u64,
        block: u64,
        max_age: u64,
    },

    #[error("Epoch too far in future: current={current}, block={block}, max_skew={max_skew}")]
    EpochTooFuture {
        current: u64,
        block: u64,
        max_skew: u64,
    },

    // ==================== CRYPTOGRAPHIC ERRORS ====================
    #[error("Hash computation failed: {0}")]
    HashError(String),

    #[error("Invalid signature")]
    InvalidSignature,

    #[error("Invalid signature: {0}")]
    SignatureError(String),

    #[error("Invalid public key")]
    InvalidPublicKey,

    #[error("Invalid public key: {0}")]
    PublicKeyError(String),

    #[error("HMAC computation failed: {0}")]
    HmacError(String),

    // ==================== MERKLE TREE ERRORS ====================
    #[error("Merkle tree construction failed: {0}")]
    MerkleError(String),

    #[error("Invalid Merkle proof: path length mismatch")]
    MerkleProofInvalid,

    #[error("Merkle root mismatch: expected {expected}, computed {computed}")]
    MerkleRootMismatch { expected: String, computed: String },

    // ==================== TIER VALIDATION ERRORS ====================
    #[error("Invalid hardware tier: {tier}")]
    InvalidTier { tier: u8 },

    #[error("Tier constraint violation: tier {tier} requires {min_elem}..{max_elem} elements, got {actual}")]
    TierConstraintViolation {
        tier: u8,
        min_elem: usize,
        max_elem: usize,
        actual: usize,
    },

    #[error("Tier time limit exceeded: tier {tier} max {max_ms}ms, actual {actual_ms}ms")]
    TierTimeLimitExceeded {
        tier: u8,
        max_ms: u64,
        actual_ms: u64,
    },

    #[error("Tier memory limit exceeded: tier {tier} max {max_mb}MB, actual {actual_mb}MB")]
    TierMemoryLimitExceeded {
        tier: u8,
        max_mb: u64,
        actual_mb: u64,
    },

    // ==================== CID INTEGRITY ERRORS (SEC-005) ====================
    #[error("CID missing: required for block {block_hash}")]
    CidMissing { block_hash: String },

    #[error("CID size mismatch: expected {expected}, actual {actual}")]
    CidSizeMismatch { expected: u64, actual: u64 },

    #[error("CID hash mismatch: manifest {manifest}, computed {computed}")]
    CidHashMismatch { manifest: String, computed: String },

    #[error("Pin quorum not met: required {required}/{total}, got {actual}/{total}")]
    PinQuorumFailed {
        required: u32,
        actual: u32,
        total: u32,
    },

    // ==================== STATE TRANSITION ERRORS ====================
    #[error("Balance overflow: address {address}")]
    BalanceOverflow { address: String },

    #[error("Insufficient balance: required {required} wei, available {available} wei")]
    InsufficientBalance {
        required: u64,
        available: u64,
    },

    #[error("Nonce mismatch: expected {expected}, got {actual}")]
    NonceMismatch { expected: u64, actual: u64 },

    #[error("Invalid nonce: expected {expected}, got {got}")]
    InvalidNonce { expected: u64, got: u64 },

    #[error("Fee too low: required {required} wei, provided {provided} wei")]
    FeeTooLow { required: u64, provided: u64 },

    #[error("Amount overflow when computing transaction cost")]
    AmountOverflow,

    #[error("Gas limit too low: required {required}, provided {provided}")]
    GasLimitTooLow { required: u64, provided: u64 },

    #[error("State root mismatch: expected {expected}, computed {computed}")]
    StateRootMismatch { expected: String, computed: String },

    #[error("Inflation detected: total supply exceeded")]
    InflationDetected,

    // ==================== GENERAL ERRORS ====================
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Internal error: {0}")]
    Internal(String),

    #[error("Not implemented: {0}")]
    NotImplemented(String),
}

impl ConsensusError {
    /// Error code for monitoring and alerting
    pub fn error_code(&self) -> &'static str {
        match self {
            // Codec errors: 1xxx
            Self::CodecError(_) => "E1000",
            Self::UnknownField { .. } => "E1001",
            Self::MissingField { .. } => "E1002",
            Self::InvalidFieldType { .. } => "E1003",
            Self::CodecVersionMismatch { .. } => "E1004",
            Self::OverlongVarint => "E1005",
            Self::InvalidFloatValue => "E1006",
            Self::CrossPathMismatch { .. } => "E1007",

            // Verification errors: 2xxx
            Self::BudgetOpsExceeded { .. } => "E2000",
            Self::BudgetTimeExceeded { .. } => "E2001",
            Self::SubsetSumInvalid => "E2002",
            Self::InvalidProofSize { .. } => "E2003",
            Self::IndexOutOfBounds { .. } => "E2004",
            Self::DuplicateIndex { .. } => "E2005",

            // Commitment errors: 3xxx
            Self::CommitmentMismatch => "E3000",
            Self::EpochBindingFailed => "E3001",
            Self::MinerSaltInvalid => "E3002",
            Self::ProblemHashMismatch { .. } => "E3003",
            Self::SolutionHashMismatch { .. } => "E3004",

            // Epoch replay errors: 4xxx
            Self::EpochReplay { .. } => "E4000",
            Self::EpochTooOld { .. } => "E4001",
            Self::EpochTooFuture { .. } => "E4002",

            // Cryptographic errors: 5xxx
            Self::HashError(_) => "E5000",
            Self::InvalidSignature => "E5001",
            Self::SignatureError(_) => "E5002",
            Self::InvalidPublicKey => "E5003",
            Self::PublicKeyError(_) => "E5004",
            Self::HmacError(_) => "E5005",

            // Merkle errors: 6xxx
            Self::MerkleError(_) => "E6000",
            Self::MerkleProofInvalid => "E6001",
            Self::MerkleRootMismatch { .. } => "E6002",

            // Tier errors: 7xxx
            Self::InvalidTier { .. } => "E7000",
            Self::TierConstraintViolation { .. } => "E7001",
            Self::TierTimeLimitExceeded { .. } => "E7002",
            Self::TierMemoryLimitExceeded { .. } => "E7003",

            // CID integrity errors: 8xxx
            Self::CidMissing { .. } => "E8000",
            Self::CidSizeMismatch { .. } => "E8001",
            Self::CidHashMismatch { .. } => "E8002",
            Self::PinQuorumFailed { .. } => "E8003",

            // State transition errors: 9xxx
            Self::BalanceOverflow { .. } => "E9000",
            Self::InsufficientBalance { .. } => "E9001",
            Self::NonceMismatch { .. } => "E9002",
            Self::InvalidNonce { .. } => "E9003",
            Self::FeeTooLow { .. } => "E9004",
            Self::AmountOverflow => "E9005",
            Self::GasLimitTooLow { .. } => "E9006",
            Self::StateRootMismatch { .. } => "E9007",
            Self::InflationDetected => "E9008",

            // General: 0xxx
            Self::InvalidInput(_) => "E0001",
            Self::Internal(_) => "E0002",
            Self::NotImplemented(_) => "E0003",
        }
    }

    /// Is this error recoverable? (for fallback logic)
    pub fn is_recoverable(&self) -> bool {
        matches!(
            self,
            Self::BudgetOpsExceeded { .. }
                | Self::BudgetTimeExceeded { .. }
                | Self::PinQuorumFailed { .. }
                | Self::CodecError(_)
        )
    }

    /// Should this error trigger an alert?
    pub fn is_critical(&self) -> bool {
        matches!(
            self,
            Self::InflationDetected
                | Self::StateRootMismatch { .. }
                | Self::CrossPathMismatch { .. }
                | Self::CodecVersionMismatch { .. }
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_codes_unique() {
        // Ensure all error codes are unique
        let errors = vec![
            ConsensusError::CodecError("test".into()).error_code(),
            ConsensusError::UnknownField {
                field: "test".into(),
            }
            .error_code(),
            ConsensusError::BudgetOpsExceeded {
                max_ops: 100,
                actual_ops: 200,
            }
            .error_code(),
            ConsensusError::CommitmentMismatch.error_code(),
            ConsensusError::InflationDetected.error_code(),
        ];

        // Check uniqueness
        let mut seen = std::collections::HashSet::new();
        for code in errors {
            assert!(seen.insert(code), "Duplicate error code: {}", code);
        }
    }

    #[test]
    fn test_error_recoverability() {
        assert!(
            ConsensusError::BudgetOpsExceeded {
                max_ops: 100,
                actual_ops: 200
            }
            .is_recoverable()
        );
        assert!(!ConsensusError::InflationDetected.is_recoverable());
    }

    #[test]
    fn test_error_criticality() {
        assert!(ConsensusError::InflationDetected.is_critical());
        assert!(!ConsensusError::InvalidInput("test".into()).is_critical());
    }
}
