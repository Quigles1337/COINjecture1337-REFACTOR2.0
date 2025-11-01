"""
Module: consensus.codec
Canonical serialization codec for consensus-critical data structures.

Uses msgspec for deterministic msgpack encoding with strict field ordering
and type validation. All consensus objects (headers, transactions, blocks)
must use this codec to ensure hash stability across implementations.
"""

from __future__ import annotations
import hashlib
import json
from typing import Any, Dict
from ..types import (
    BlockHeader,
    Transaction,
    ProofReveal,
    ComplexityMetrics,
    BlockWireFormat,
    BlockHash,
    TxHash,
    CommitmentMismatch,
)

# Try to import msgspec for high-performance deterministic encoding
try:
    import msgspec  # type: ignore
    HAS_MSGSPEC = True
except ImportError:
    msgspec = None
    HAS_MSGSPEC = False


# ============================================================================
# Canonical Encoding Functions
# ============================================================================

def encode_header(header: BlockHeader) -> bytes:
    """
    Encode block header to canonical msgpack format.

    Field order MUST be stable across versions:
    1. index
    2. timestamp
    3. previous_hash
    4. merkle_root
    5. problem_commitment
    6. work_score
    7. cumulative_work
    8. tier

    Args:
        header: BlockHeader to encode

    Returns:
        Canonical msgpack bytes
    """
    if HAS_MSGSPEC:
        # msgspec preserves dict order and provides deterministic encoding
        data = {
            "index": header.index,
            "timestamp": header.timestamp,
            "previous_hash": header.previous_hash,
            "merkle_root": header.merkle_root,
            "problem_commitment": header.problem_commitment,
            "work_score": header.work_score,
            "cumulative_work": header.cumulative_work,
            "tier": header.tier.value,  # Encode enum as string value
        }
        return msgspec.msgpack.encode(data)
    else:
        # Fallback: JSON with sorted keys (less efficient, but deterministic)
        data = {
            "index": header.index,
            "timestamp": header.timestamp,
            "previous_hash": header.previous_hash,
            "merkle_root": header.merkle_root,
            "problem_commitment": header.problem_commitment,
            "work_score": header.work_score,
            "cumulative_work": header.cumulative_work,
            "tier": header.tier.value,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def decode_header(data: bytes) -> BlockHeader:
    """
    Decode canonical msgpack to BlockHeader.

    Args:
        data: Canonical msgpack bytes

    Returns:
        BlockHeader instance

    Raises:
        ValueError: If data is malformed
    """
    from ..types import ProblemTierEnum, BlockHash, MerkleRoot

    if HAS_MSGSPEC:
        obj = msgspec.msgpack.decode(data)
    else:
        obj = json.loads(data.decode())

    return BlockHeader(
        index=obj["index"],
        timestamp=obj["timestamp"],
        previous_hash=BlockHash(obj["previous_hash"]),
        merkle_root=MerkleRoot(obj["merkle_root"]),
        problem_commitment=obj["problem_commitment"],
        work_score=obj["work_score"],
        cumulative_work=obj["cumulative_work"],
        tier=ProblemTierEnum(obj["tier"]),
    )


def encode_transaction(tx: Transaction) -> bytes:
    """
    Encode transaction to canonical msgpack format.

    Field order:
    1. sender
    2. recipient
    3. amount
    4. fee
    5. nonce
    6. timestamp
    7. signature
    8. public_key

    Args:
        tx: Transaction to encode

    Returns:
        Canonical msgpack bytes
    """
    data = {
        "sender": tx.sender,
        "recipient": tx.recipient,
        "amount": tx.amount,
        "fee": tx.fee,
        "nonce": tx.nonce,
        "timestamp": tx.timestamp,
        "signature": tx.signature,
        "public_key": tx.public_key,
    }

    if HAS_MSGSPEC:
        return msgspec.msgpack.encode(data)
    else:
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def decode_transaction(data: bytes) -> Transaction:
    """
    Decode canonical msgpack to Transaction.

    Args:
        data: Canonical msgpack bytes

    Returns:
        Transaction instance
    """
    from ..types import Address, Signature, PublicKey

    if HAS_MSGSPEC:
        obj = msgspec.msgpack.decode(data)
    else:
        obj = json.loads(data.decode())

    return Transaction(
        sender=Address(obj["sender"]),
        recipient=Address(obj["recipient"]),
        amount=obj["amount"],
        fee=obj["fee"],
        nonce=obj["nonce"],
        timestamp=obj["timestamp"],
        signature=Signature(obj["signature"]),
        public_key=PublicKey(obj["public_key"]),
    )


def encode_proof_reveal(reveal: ProofReveal) -> bytes:
    """
    Encode proof reveal to canonical msgpack format.

    Args:
        reveal: ProofReveal to encode

    Returns:
        Canonical msgpack bytes
    """
    data = {
        "problem_type": reveal.problem_type,
        "problem_params": reveal.problem_params,
        "problem_size": reveal.problem_size,
        "tier": reveal.tier.value,
        "solution": reveal.solution,
        "solution_hash": reveal.solution_hash.hex(),
        "miner_salt": reveal.miner_salt.hex(),
        "epoch_salt": reveal.epoch_salt.hex(),
        "commitment": reveal.commitment.hex(),
        "timestamp": reveal.timestamp,
    }

    if HAS_MSGSPEC:
        return msgspec.msgpack.encode(data)
    else:
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def decode_proof_reveal(data: bytes) -> ProofReveal:
    """Decode canonical msgpack to ProofReveal."""
    from ..types import ProblemTierEnum, SolutionHash, MinerSalt, EpochSalt, Commitment

    if HAS_MSGSPEC:
        obj = msgspec.msgpack.decode(data)
    else:
        obj = json.loads(data.decode())

    return ProofReveal(
        problem_type=obj["problem_type"],
        problem_params=obj["problem_params"],
        problem_size=obj["problem_size"],
        tier=ProblemTierEnum(obj["tier"]),
        solution=obj["solution"],
        solution_hash=SolutionHash(bytes.fromhex(obj["solution_hash"])),
        miner_salt=MinerSalt(bytes.fromhex(obj["miner_salt"])),
        epoch_salt=EpochSalt(bytes.fromhex(obj["epoch_salt"])),
        commitment=Commitment(bytes.fromhex(obj["commitment"])),
        timestamp=obj["timestamp"],
    )


# ============================================================================
# Hash Computation Functions
# ============================================================================

def compute_header_hash(header: BlockHeader) -> BlockHash:
    """
    Compute deterministic hash of block header.

    CRITICAL: This function defines consensus. Any change to encoding
    or hash algorithm creates a hard fork.

    Args:
        header: BlockHeader to hash

    Returns:
        32-byte hex-encoded SHA-256 hash
    """
    canonical_bytes = encode_header(header)
    hash_bytes = hashlib.sha256(canonical_bytes).digest()
    return BlockHash(hash_bytes.hex())


def compute_transaction_hash(tx: Transaction) -> TxHash:
    """
    Compute deterministic hash of transaction.

    Uses the tx.tx_hash() method for consistency.

    Args:
        tx: Transaction to hash

    Returns:
        32-byte hex-encoded SHA-256 hash
    """
    return tx.tx_hash()


def compute_merkle_root(tx_hashes: list[TxHash]) -> str:
    """
    Compute Merkle tree root from transaction hashes.

    Uses Bitcoin-style Merkle tree:
    - If odd number of leaves, duplicate last hash
    - Recursively hash pairs until single root remains

    Args:
        tx_hashes: List of transaction hashes

    Returns:
        Hex-encoded Merkle root
    """
    if not tx_hashes:
        # Empty tree: hash of empty string
        return hashlib.sha256(b"").hexdigest()

    if len(tx_hashes) == 1:
        return tx_hashes[0]

    # Convert to binary hashes
    current_level = [bytes.fromhex(h) for h in tx_hashes]

    while len(current_level) > 1:
        next_level = []

        # Process pairs
        for i in range(0, len(current_level), 2):
            left = current_level[i]

            # If odd number, duplicate last hash
            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                right = left

            # Hash concatenated pair
            parent = hashlib.sha256(left + right).digest()
            next_level.append(parent)

        current_level = next_level

    return current_level[0].hex()


# ============================================================================
# Commitment Verification
# ============================================================================

def verify_reveal_commitment(reveal: ProofReveal) -> bool:
    """
    Verify that ProofReveal commitment binds to problem + solution.

    Uses the commit-reveal protocol from pow.py:
    commitment = SHA256(problem_params || miner_salt || epoch_salt || solution_hash)

    Args:
        reveal: ProofReveal to verify

    Returns:
        True if commitment is valid, False otherwise
    """
    # Serialize problem params deterministically
    if HAS_MSGSPEC:
        problem_bytes = msgspec.msgpack.encode(reveal.problem_params)
    else:
        problem_bytes = json.dumps(reveal.problem_params, sort_keys=True).encode()

    # Reconstruct commitment
    commitment_data = (
        problem_bytes
        + reveal.miner_salt
        + reveal.epoch_salt
        + reveal.solution_hash
    )
    expected_commitment = hashlib.sha256(commitment_data).digest()

    return reveal.commitment == expected_commitment


def create_commitment(
    problem_params: Dict[str, Any],
    miner_salt: bytes,
    epoch_salt: bytes,
    solution_hash: bytes,
) -> bytes:
    """
    Create cryptographic commitment to problem + solution.

    Args:
        problem_params: Problem specification dict
        miner_salt: 32-byte unique miner salt
        epoch_salt: 32-byte epoch salt
        solution_hash: 32-byte hash of solution

    Returns:
        32-byte commitment hash
    """
    if HAS_MSGSPEC:
        problem_bytes = msgspec.msgpack.encode(problem_params)
    else:
        problem_bytes = json.dumps(problem_params, sort_keys=True).encode()

    commitment_data = problem_bytes + miner_salt + epoch_salt + solution_hash
    return hashlib.sha256(commitment_data).digest()


# ============================================================================
# Wire Format Encoding/Decoding
# ============================================================================

def encode_block(block: BlockWireFormat) -> bytes:
    """
    Encode complete block to wire format.

    Structure:
    - header (canonical msgpack)
    - transaction count (varint)
    - transactions (array of canonical msgpack)
    - has_proof_reveal (bool)
    - proof_reveal (optional canonical msgpack)
    - has_offchain_cid (bool)
    - offchain_cid (optional UTF-8 string)
    - complexity (canonical msgpack)

    Args:
        block: BlockWireFormat to encode

    Returns:
        Complete wire format bytes
    """
    parts = []

    # Header
    parts.append(encode_header(block.header))

    # Transactions
    tx_count = len(block.transactions)
    parts.append(tx_count.to_bytes(4, 'little'))  # 4-byte count
    for tx in block.transactions:
        tx_bytes = encode_transaction(tx)
        parts.append(len(tx_bytes).to_bytes(4, 'little'))  # Length prefix
        parts.append(tx_bytes)

    # Proof reveal (optional)
    if block.proof_reveal is not None:
        parts.append(b'\x01')  # Has proof
        reveal_bytes = encode_proof_reveal(block.proof_reveal)
        parts.append(len(reveal_bytes).to_bytes(4, 'little'))
        parts.append(reveal_bytes)
    else:
        parts.append(b'\x00')  # No proof

    # Offchain CID (optional)
    if block.offchain_cid is not None:
        parts.append(b'\x01')  # Has CID
        cid_bytes = block.offchain_cid.encode('utf-8')
        parts.append(len(cid_bytes).to_bytes(4, 'little'))
        parts.append(cid_bytes)
    else:
        parts.append(b'\x00')  # No CID

    # Complexity metrics (always present)
    complexity_data = {
        "time_solve_O": block.complexity.time_solve_O,
        "time_verify_O": block.complexity.time_verify_O,
        "space_solve_O": block.complexity.space_solve_O,
        "space_verify_O": block.complexity.space_verify_O,
        "problem_class": block.complexity.problem_class.value,
        "problem_size": block.complexity.problem_size,
        "solution_size": block.complexity.solution_size,
        "asymmetry_ratio": block.complexity.asymmetry_ratio,
        "measured_solve_time": block.complexity.measured_solve_time,
        "measured_verify_time": block.complexity.measured_verify_time,
        "measured_solve_space": block.complexity.measured_solve_space,
        "measured_verify_space": block.complexity.measured_verify_space,
    }

    if HAS_MSGSPEC:
        complexity_bytes = msgspec.msgpack.encode(complexity_data)
    else:
        complexity_bytes = json.dumps(complexity_data, sort_keys=True).encode()

    parts.append(len(complexity_bytes).to_bytes(4, 'little'))
    parts.append(complexity_bytes)

    return b''.join(parts)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "HAS_MSGSPEC",
    "encode_header",
    "decode_header",
    "encode_transaction",
    "decode_transaction",
    "encode_proof_reveal",
    "decode_proof_reveal",
    "compute_header_hash",
    "compute_transaction_hash",
    "compute_merkle_root",
    "verify_reveal_commitment",
    "create_commitment",
    "encode_block",
]
