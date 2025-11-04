//! Consensus-critical type definitions with deterministic representation.
//!
//! ALL types are #[repr(C)] for ABI stability across FFI boundaries (Python/Go).
//! Field order is EXPLICIT and FROZEN - changes require golden vector updates.
//! Serialization is CANONICAL - msgpack and JSON must produce identical hashes.

use serde::{Deserialize, Serialize};
use std::fmt;

/// Codec version for forward/backward compatibility
pub const CODEC_VERSION: u8 = 1;

/// Maximum block size (10 MB)
pub const MAX_BLOCK_SIZE: usize = 10 * 1024 * 1024;

/// Maximum transaction count per block
pub const MAX_TX_PER_BLOCK: usize = 10_000;

/// Maximum proof element count (tier 5 max)
pub const MAX_PROOF_ELEMENTS: usize = 32;

// ==================== HARDWARE TIERS ====================

/// Hardware tiers for mining - NOT reward brackets, but resource limits
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum HardwareTier {
    Mobile = 1,      // 8-12 elements, 60s, 256MB
    Desktop = 2,     // 12-16 elements, 300s, 1GB
    Workstation = 3, // 16-20 elements, 900s, 4GB
    Server = 4,      // 20-24 elements, 1800s, 16GB
    Cluster = 5,     // 24-32 elements, 3600s, 64GB
}

impl HardwareTier {
    pub fn from_u8(value: u8) -> Option<Self> {
        match value {
            1 => Some(Self::Mobile),
            2 => Some(Self::Desktop),
            3 => Some(Self::Workstation),
            4 => Some(Self::Server),
            5 => Some(Self::Cluster),
            _ => None,
        }
    }

    pub fn element_range(&self) -> (usize, usize) {
        match self {
            Self::Mobile => (8, 12),
            Self::Desktop => (12, 16),
            Self::Workstation => (16, 20),
            Self::Server => (20, 24),
            Self::Cluster => (24, 32),
        }
    }

    pub fn time_limit_ms(&self) -> u64 {
        match self {
            Self::Mobile => 60_000,
            Self::Desktop => 300_000,
            Self::Workstation => 900_000,
            Self::Server => 1_800_000,
            Self::Cluster => 3_600_000,
        }
    }

    pub fn memory_limit_mb(&self) -> u64 {
        match self {
            Self::Mobile => 256,
            Self::Desktop => 1024,
            Self::Workstation => 4096,
            Self::Server => 16384,
            Self::Cluster => 65536,
        }
    }

    pub fn max_verify_ops(&self) -> u64 {
        let (_, max_elem) = self.element_range();
        2u64.pow(max_elem as u32)
    }
}

// ==================== PROBLEM TYPES ====================

/// NP-Complete problem types supported for PoW
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum ProblemType {
    SubsetSum = 1,
    Knapsack = 2,
    GraphColoring = 3,
    SAT = 4,
    TSP = 5,
    Factorization = 6,
    LatticeProblems = 7,
}

impl ProblemType {
    pub fn from_u8(value: u8) -> Option<Self> {
        match value {
            1 => Some(Self::SubsetSum),
            2 => Some(Self::Knapsack),
            3 => Some(Self::GraphColoring),
            4 => Some(Self::SAT),
            5 => Some(Self::TSP),
            6 => Some(Self::Factorization),
            7 => Some(Self::LatticeProblems),
            _ => None,
        }
    }

    pub fn is_production_ready(&self) -> bool {
        matches!(self, Self::SubsetSum)
    }
}

// ==================== BLOCK HEADER ====================

/// Block header - consensus-critical, deterministic hash
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct BlockHeader {
    /// Codec version for compatibility (MUST BE FIRST FIELD)
    pub codec_version: u8,

    /// Block index (height)
    pub block_index: u64,

    /// Timestamp (seconds since Unix epoch)
    pub timestamp: i64,

    /// Parent block hash (32 bytes, SHA-256)
    #[serde(with = "serde_bytes")]
    pub parent_hash: [u8; 32],

    /// Merkle root of transactions (32 bytes)
    #[serde(with = "serde_bytes")]
    pub merkle_root: [u8; 32],

    /// Miner address (32 bytes, derived from pubkey)
    #[serde(with = "serde_bytes")]
    pub miner_address: [u8; 32],

    /// Commitment hash (32 bytes)
    #[serde(with = "serde_bytes")]
    pub commitment: [u8; 32],

    /// Difficulty target (cumulative work threshold)
    pub difficulty_target: u64,

    /// Nonce for mining randomness
    pub nonce: u64,

    /// Extra data (max 256 bytes, for future use)
    #[serde(with = "serde_bytes")]
    pub extra_data: Vec<u8>,
}

impl Default for BlockHeader {
    fn default() -> Self {
        Self {
            codec_version: CODEC_VERSION,
            block_index: 0,
            timestamp: 0,
            parent_hash: [0u8; 32],
            merkle_root: [0u8; 32],
            miner_address: [0u8; 32],
            commitment: [0u8; 32],
            difficulty_target: 0,
            nonce: 0,
            extra_data: Vec::new(),
        }
    }
}

// ==================== COMMITMENT ====================

/// Commitment for commit-reveal protocol (anti-grinding)
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct Commitment {
    /// Epoch salt (from parent_hash || block_index)
    #[serde(with = "serde_bytes")]
    pub epoch_salt: [u8; 32],

    /// Problem hash (SHA-256 of Problem)
    #[serde(with = "serde_bytes")]
    pub problem_hash: [u8; 32],

    /// Solution hash (SHA-256 of Solution)
    #[serde(with = "serde_bytes")]
    pub solution_hash: [u8; 32],

    /// Miner salt (HMAC of epoch_salt || parent_hash || miner_private_key)
    #[serde(with = "serde_bytes")]
    pub miner_salt: [u8; 32],
}

// ==================== PROBLEM ====================

/// Computational problem for PoW
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct Problem {
    /// Problem type
    pub problem_type: ProblemType,

    /// Hardware tier (determines limits)
    pub tier: HardwareTier,

    /// Problem-specific data (for SubsetSum: elements array)
    pub elements: Vec<i64>,

    /// Target value (for SubsetSum: target sum)
    pub target: i64,

    /// Timestamp of problem generation
    pub timestamp: i64,
}

// ==================== SOLUTION ====================

/// Solution to a computational problem
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct Solution {
    /// Indices into problem.elements that form the solution
    pub indices: Vec<u32>,

    /// Timestamp of solution discovery
    pub timestamp: i64,
}

// ==================== REVEAL ====================

/// Reveal phase data (unveils commitment)
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct Reveal {
    /// The problem that was committed to
    pub problem: Problem,

    /// The solution to the problem
    pub solution: Solution,

    /// Miner salt (same as in Commitment)
    #[serde(with = "serde_bytes")]
    pub miner_salt: [u8; 32],

    /// Nonce used in mining
    pub nonce: u64,
}

// ==================== TRANSACTION ====================

/// Transaction types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum TxType {
    Transfer = 1,
    ProblemSubmission = 2,
    BountyPayment = 3,
}

/// Transaction - state transition
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct Transaction {
    /// Codec version
    pub codec_version: u8,

    /// Transaction type
    pub tx_type: TxType,

    /// Sender address (32 bytes)
    #[serde(with = "serde_bytes")]
    pub from: [u8; 32],

    /// Recipient address (32 bytes)
    #[serde(with = "serde_bytes")]
    pub to: [u8; 32],

    /// Amount (in smallest unit, "satoshis" for BEANS)
    pub amount: u64,

    /// Nonce (prevents replay)
    pub nonce: u64,

    /// Gas limit for execution
    pub gas_limit: u64,

    /// Gas price (in smallest unit per gas)
    pub gas_price: u64,

    /// Signature (64 bytes, Ed25519)
    #[serde(with = "serde_bytes")]
    pub signature: [u8; 64],

    /// Transaction data (problem submission, etc.)
    #[serde(with = "serde_bytes")]
    pub data: Vec<u8>,

    /// Timestamp
    pub timestamp: i64,
}

impl Default for Transaction {
    fn default() -> Self {
        Self {
            codec_version: CODEC_VERSION,
            tx_type: TxType::Transfer,
            from: [0u8; 32],
            to: [0u8; 32],
            amount: 0,
            nonce: 0,
            gas_limit: 21000, // Standard transfer gas
            gas_price: 1,
            signature: [0u8; 64],
            data: Vec::new(),
            timestamp: 0,
        }
    }
}

// ==================== BLOCK ====================

/// Complete block (header + transactions + reveal)
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct Block {
    /// Block header
    pub header: BlockHeader,

    /// Transactions (merkle root in header)
    pub transactions: Vec<Transaction>,

    /// Reveal data (unveils commitment in header)
    pub reveal: Reveal,

    /// CID for IPFS storage (optional, but required for new blocks per SEC-005)
    pub cid: Option<String>,
}

// ==================== VERIFICATION BUDGET ====================

/// Budget limits for proof verification (defense against DoS)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct VerifyBudget {
    /// Maximum operations allowed (e.g., subset combinations to check)
    pub max_ops: u64,

    /// Maximum time allowed in milliseconds
    pub max_duration_ms: u64,

    /// Maximum memory allowed in bytes
    pub max_memory_bytes: u64,
}

impl VerifyBudget {
    pub fn from_tier(tier: HardwareTier) -> Self {
        Self {
            max_ops: tier.max_verify_ops(),
            max_duration_ms: tier.time_limit_ms(),
            max_memory_bytes: tier.memory_limit_mb() * 1024 * 1024,
        }
    }

    pub fn permissive() -> Self {
        Self {
            max_ops: u64::MAX,
            max_duration_ms: u64::MAX,
            max_memory_bytes: u64::MAX,
        }
    }

    pub fn strict_desktop() -> Self {
        Self::from_tier(HardwareTier::Desktop)
    }
}

// ==================== MERKLE PROOF ====================

/// Merkle proof for transaction inclusion
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct MerkleProof {
    /// Transaction index in block
    pub tx_index: u64,

    /// Merkle path (hashes from leaf to root)
    pub path: Vec<[u8; 32]>,

    /// Directions (false = left, true = right)
    pub directions: Vec<bool>,
}

// ==================== PIN MANIFEST (SEC-005) ====================

/// IPFS pin manifest for CID audit
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[repr(C)]
pub struct PinManifest {
    /// CID
    pub cid: String,

    /// Expected size in bytes
    pub size: u64,

    /// SHA-256 hash of content
    #[serde(with = "serde_bytes")]
    pub content_hash: [u8; 32],

    /// Nodes that successfully pinned (IP:port)
    pub pinned_nodes: Vec<String>,

    /// Quorum requirement (e.g., "2/3")
    pub quorum: String,

    /// Timestamp of pinning
    pub timestamp: i64,

    /// Signature of manifest (by pin coordinator)
    #[serde(with = "serde_bytes")]
    pub signature: [u8; 64],
}

// ==================== HELPER MODULES ====================

/// Serde helper for byte arrays
mod serde_bytes {
    use serde::{Deserialize, Deserializer, Serialize, Serializer};

    pub fn serialize<S, const N: usize>(bytes: &[u8; N], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        if serializer.is_human_readable() {
            hex::encode(bytes).serialize(serializer)
        } else {
            bytes.serialize(serializer)
        }
    }

    pub fn deserialize<'de, D, const N: usize>(deserializer: D) -> Result<[u8; N], D::Error>
    where
        D: Deserializer<'de>,
    {
        if deserializer.is_human_readable() {
            let s = String::deserialize(deserializer)?;
            let bytes = hex::decode(&s).map_err(serde::de::Error::custom)?;
            if bytes.len() != N {
                return Err(serde::de::Error::custom(format!(
                    "Expected {} bytes, got {}",
                    N,
                    bytes.len()
                )));
            }
            let mut arr = [0u8; N];
            arr.copy_from_slice(&bytes);
            Ok(arr)
        } else {
            <[u8; N]>::deserialize(deserializer)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hardware_tier_ranges() {
        assert_eq!(HardwareTier::Mobile.element_range(), (8, 12));
        assert_eq!(HardwareTier::Cluster.element_range(), (24, 32));
    }

    #[test]
    fn test_hardware_tier_limits() {
        assert_eq!(HardwareTier::Mobile.time_limit_ms(), 60_000);
        assert_eq!(HardwareTier::Desktop.memory_limit_mb(), 1024);
    }

    #[test]
    fn test_verify_budget_from_tier() {
        let budget = VerifyBudget::from_tier(HardwareTier::Desktop);
        assert_eq!(budget.max_duration_ms, 300_000);
        assert_eq!(budget.max_memory_bytes, 1024 * 1024 * 1024);
    }

    #[test]
    fn test_codec_version() {
        let header = BlockHeader::default();
        assert_eq!(header.codec_version, CODEC_VERSION);

        let tx = Transaction::default();
        assert_eq!(tx.codec_version, CODEC_VERSION);
    }

    #[test]
    fn test_problem_type_production_ready() {
        assert!(ProblemType::SubsetSum.is_production_ready());
        assert!(!ProblemType::Knapsack.is_production_ready());
    }
}
