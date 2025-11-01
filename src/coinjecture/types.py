"""
Module: types
Canonical type definitions for COINjecture blockchain.

Separates on-wire protocol types from internal representation types.
All on-wire types use frozen dataclasses for immutability and safety.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, NewType
from enum import Enum
import hashlib
import json

# ============================================================================
# Type Aliases and Newtypes for Domain Modeling
# ============================================================================

BlockHash = NewType("BlockHash", str)
"""32-byte hex-encoded SHA-256 hash of block"""

TxHash = NewType("TxHash", str)
"""32-byte hex-encoded SHA-256 hash of transaction"""

MerkleRoot = NewType("MerkleRoot", str)
"""32-byte hex-encoded Merkle tree root"""

Address = NewType("Address", str)
"""BEANS-prefixed address derived from Ed25519 public key"""

PublicKey = NewType("PublicKey", str)
"""Hex-encoded Ed25519 public key"""

Signature = NewType("Signature", str)
"""Hex-encoded Ed25519 signature"""

CID = NewType("CID", str)
"""IPFS Content Identifier (base58 multihash)"""

Commitment = NewType("Commitment", bytes)
"""32-byte cryptographic commitment hash"""

EpochSalt = NewType("EpochSalt", bytes)
"""32-byte epoch salt for time-locked problems"""

MinerSalt = NewType("MinerSalt", bytes)
"""32-byte unique miner salt for commit-reveal"""

SolutionHash = NewType("SolutionHash", bytes)
"""32-byte hash of problem solution"""


# ============================================================================
# Enums
# ============================================================================

class ProblemTierEnum(str, Enum):
    """Hardware capacity tiers - all use Subset Sum with different sizes."""
    TIER_1_MOBILE = "mobile"  # 8-12 elements
    TIER_2_DESKTOP = "desktop"  # 12-16 elements
    TIER_3_WORKSTATION = "workstation"  # 16-20 elements
    TIER_4_SERVER = "server"  # 20-24 elements
    TIER_5_CLUSTER = "cluster"  # 24-32 elements

    def get_size_range(self) -> tuple[int, int]:
        """Returns (min_size, max_size) for this tier."""
        ranges = {
            self.TIER_1_MOBILE: (8, 12),
            self.TIER_2_DESKTOP: (12, 16),
            self.TIER_3_WORKSTATION: (16, 20),
            self.TIER_4_SERVER: (20, 24),
            self.TIER_5_CLUSTER: (24, 32),
        }
        return ranges[self]

    def max_elements(self) -> int:
        """Maximum problem size for this tier."""
        return self.get_size_range()[1]

    def min_elements(self) -> int:
        """Minimum problem size for this tier."""
        return self.get_size_range()[0]


class ProblemClassEnum(str, Enum):
    """Computational complexity classes."""
    P = "P"  # Polynomial time
    NP = "NP"  # Nondeterministic polynomial
    NP_COMPLETE = "NP-Complete"  # Hardest problems in NP
    NP_HARD = "NP-Hard"  # At least as hard as NP-Complete
    PSPACE = "PSPACE"  # Polynomial space
    EXPTIME = "EXPTIME"  # Exponential time


# ============================================================================
# On-Wire Protocol Types (Frozen, Immutable)
# ============================================================================

@dataclass(frozen=True)
class BlockHeader:
    """
    On-wire block header for network propagation.
    Minimal fields needed for header-first sync.
    """
    index: int
    timestamp: float
    previous_hash: BlockHash
    merkle_root: MerkleRoot
    problem_commitment: str  # Hex commitment to problem+solution
    work_score: float
    cumulative_work: float
    tier: ProblemTierEnum

    def header_hash(self) -> BlockHash:
        """Compute deterministic hash of this header."""
        from .consensus import codec
        return codec.compute_header_hash(self)


@dataclass(frozen=True)
class Transaction:
    """
    On-wire transaction format.
    Immutable once signed.
    """
    sender: Address
    recipient: Address
    amount: float
    fee: float
    nonce: int
    timestamp: float
    signature: Signature
    public_key: PublicKey

    def tx_hash(self) -> TxHash:
        """Compute deterministic hash of this transaction."""
        tx_data = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "fee": self.fee,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }
        tx_json = json.dumps(tx_data, sort_keys=True, separators=(",", ":"))
        return TxHash(hashlib.sha256(tx_json.encode()).hexdigest())


@dataclass(frozen=True)
class ProofReveal:
    """
    On-wire reveal package sent after commitment.
    Contains full problem, solution, and binding proof.
    """
    # Problem specification
    problem_type: str  # "subset_sum"
    problem_params: Dict[str, Any]  # {"elements": [...], "target": ...}
    problem_size: int
    tier: ProblemTierEnum

    # Solution
    solution: List[int]  # Indices of selected elements
    solution_hash: SolutionHash

    # Commitment binding
    miner_salt: MinerSalt
    epoch_salt: EpochSalt
    commitment: Commitment

    # Metadata
    timestamp: float

    def verify_commitment_binding(self) -> bool:
        """Verify that commitment binds to this problem+solution."""
        from .consensus import codec
        return codec.verify_reveal_commitment(self)


@dataclass(frozen=True)
class ComplexityMetrics:
    """
    On-wire complexity metrics for proof validation.
    Based on theoretical bounds and measured performance.
    """
    # Asymptotic time complexity
    time_solve_O: str  # e.g., "O(2^n)"
    time_verify_O: str  # e.g., "O(n)"

    # Asymptotic space complexity
    space_solve_O: str  # e.g., "O(n)"
    space_verify_O: str  # e.g., "O(1)"

    # Problem classification
    problem_class: ProblemClassEnum
    problem_size: int
    solution_size: int

    # Asymmetry measure
    asymmetry_ratio: float  # solve_time / verify_time

    # Measured performance
    measured_solve_time: float  # seconds
    measured_verify_time: float  # seconds
    measured_solve_space: int  # bytes
    measured_verify_space: int  # bytes


@dataclass(frozen=True)
class BlockWireFormat:
    """
    Complete on-wire block format for network transmission.
    Frozen to prevent mutation after creation.
    """
    # Header (propagated first for header-first sync)
    header: BlockHeader

    # Transactions
    transactions: tuple[Transaction, ...]  # Immutable tuple

    # Proof reveal (may be offchain via IPFS)
    proof_reveal: Optional[ProofReveal]
    offchain_cid: Optional[CID]  # IPFS CID if proof is offloaded

    # Complexity attestation
    complexity: ComplexityMetrics

    def block_hash(self) -> BlockHash:
        """Block hash is header hash."""
        return self.header.header_hash()


# ============================================================================
# Internal Representation Types (Mutable, for Processing)
# ============================================================================

@dataclass
class BlockNode:
    """
    Internal block tree node for fork choice.
    Mutable for adding children and updating state.
    """
    block_hash: BlockHash
    header: BlockHeader
    parent_hash: BlockHash
    cumulative_work: float
    height: int
    receipt_time: float
    children: List[BlockHash] = field(default_factory=list)
    validated: bool = False
    finalized: bool = False

    def __hash__(self) -> int:
        return hash(self.block_hash)


@dataclass
class PeerInfo:
    """
    Internal peer connection state.
    Mutable for connection lifecycle management.
    """
    peer_id: str
    address: str
    port: int
    protocol_version: str
    last_seen: float
    latency_ms: float
    sync_height: int
    is_syncing: bool = False
    reputation_score: float = 1.0
    failed_requests: int = 0


@dataclass
class ChainTip:
    """
    Internal chain tip tracking.
    Mutable for chain updates.
    """
    block_hash: BlockHash
    height: int
    cumulative_work: float
    timestamp: float
    last_update: float


@dataclass
class MempoolEntry:
    """
    Internal mempool entry.
    Mutable for fee/priority updates.
    """
    tx: Transaction
    received_time: float
    fee_per_byte: float
    priority_score: float
    validated: bool = False


# ============================================================================
# Configuration Types
# ============================================================================

@dataclass
class ConsensusConfig:
    """Consensus engine configuration."""
    network_id: str = "coinjecture-testnet-v1"
    confirmation_depth: int = 20
    max_reorg_depth: int = 100
    max_headers_per_second: int = 100
    max_proof_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    genesis_timestamp: float = 1609459200.0  # 2021-01-01 00:00:00 UTC
    genesis_seed: str = "coinjecture_genesis_seed"


@dataclass
class NetworkConfig:
    """Network protocol configuration."""
    listen_port: int = 8333
    max_peers: int = 125
    max_inbound: int = 100
    max_outbound: int = 25
    peer_timeout_seconds: int = 30
    sync_batch_size: int = 500
    max_message_size_bytes: int = 1024 * 1024  # 1 MB
    protocol_version: str = "coinjecture/1.0"

    # Equilibrium gossip parameters (v3.17.0)
    broadcast_interval_seconds: float = 14.14  # »-coupling
    listen_interval_seconds: float = 14.14  # ·-damping
    cleanup_interval_seconds: float = 70.7  # network maintenance
    satoshi_constant: float = 0.7071  # 1/2


@dataclass
class StorageConfig:
    """Storage backend configuration."""
    db_path: str = "./coinjecture.db"
    ipfs_gateway: str = "http://localhost:5001"
    cache_size_mb: int = 512
    enable_pruning: bool = False
    pruning_keep_blocks: int = 1000


# ============================================================================
# Validation Error Types
# ============================================================================

class ValidationError(Exception):
    """Base validation error."""
    pass


class HeaderValidationError(ValidationError):
    """Header validation failed."""
    pass


class RevealValidationError(ValidationError):
    """Reveal validation failed."""
    pass


class TierLimitExceeded(ValidationError):
    """Proof exceeds tier resource limits."""
    pass


class CommitmentMismatch(ValidationError):
    """Commitment does not bind to revealed proof."""
    pass


class InvalidSignature(ValidationError):
    """Cryptographic signature verification failed."""
    pass


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Type aliases
    "BlockHash",
    "TxHash",
    "MerkleRoot",
    "Address",
    "PublicKey",
    "Signature",
    "CID",
    "Commitment",
    "EpochSalt",
    "MinerSalt",
    "SolutionHash",
    # Enums
    "ProblemTierEnum",
    "ProblemClassEnum",
    # On-wire types
    "BlockHeader",
    "Transaction",
    "ProofReveal",
    "ComplexityMetrics",
    "BlockWireFormat",
    # Internal types
    "BlockNode",
    "PeerInfo",
    "ChainTip",
    "MempoolEntry",
    # Config types
    "ConsensusConfig",
    "NetworkConfig",
    "StorageConfig",
    # Errors
    "ValidationError",
    "HeaderValidationError",
    "RevealValidationError",
    "TierLimitExceeded",
    "CommitmentMismatch",
    "InvalidSignature",
]
