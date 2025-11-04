//! Deterministic Merkle tree implementation for transaction batching.
//!
//! Merkle trees allow efficient proof of transaction inclusion in blocks.
//! Implementation is deterministic: same transactions → same root hash.

use crate::errors::{ConsensusError, Result};
use crate::hash::sha256;
use crate::types::{MerkleProof, Transaction};
use crate::codec::compute_transaction_hash;

/// Merkle tree node
#[derive(Debug, Clone, PartialEq, Eq)]
enum MerkleNode {
    Leaf([u8; 32]),
    Internal([u8; 32], Box<MerkleNode>, Box<MerkleNode>),
}

impl MerkleNode {
    fn hash(&self) -> &[u8; 32] {
        match self {
            Self::Leaf(h) => h,
            Self::Internal(h, _, _) => h,
        }
    }
}

/// Compute Merkle root from transaction hashes
///
/// Empty list → all-zeros hash (edge case)
/// Single hash → hash itself (no duplication)
/// Multiple hashes → binary tree with deterministic ordering
pub fn compute_merkle_root(tx_hashes: &[[u8; 32]]) -> [u8; 32] {
    if tx_hashes.is_empty() {
        return [0u8; 32];
    }

    if tx_hashes.len() == 1 {
        return tx_hashes[0];
    }

    // Build tree bottom-up
    let mut level: Vec<[u8; 32]> = tx_hashes.to_vec();

    while level.len() > 1 {
        let mut next_level = Vec::new();

        for chunk in level.chunks(2) {
            let hash = if chunk.len() == 2 {
                // Combine two hashes: SHA-256(left || right)
                combine_hashes(&chunk[0], &chunk[1])
            } else {
                // Odd number: don't duplicate, just promote
                chunk[0]
            };
            next_level.push(hash);
        }

        level = next_level;
    }

    level[0]
}

/// Compute Merkle root from transactions (convenience wrapper)
pub fn compute_merkle_root_from_txs(transactions: &[Transaction]) -> Result<[u8; 32]> {
    let hashes: Result<Vec<[u8; 32]>> = transactions
        .iter()
        .map(compute_transaction_hash)
        .collect();

    Ok(compute_merkle_root(&hashes?))
}

/// Combine two hashes into parent hash
fn combine_hashes(left: &[u8; 32], right: &[u8; 32]) -> [u8; 32] {
    let mut combined = [0u8; 64];
    combined[..32].copy_from_slice(left);
    combined[32..].copy_from_slice(right);
    sha256(&combined)
}

/// Generate Merkle proof for transaction at index
pub fn generate_merkle_proof(tx_hashes: &[[u8; 32]], tx_index: usize) -> Result<MerkleProof> {
    if tx_index >= tx_hashes.len() {
        return Err(ConsensusError::IndexOutOfBounds {
            index: tx_index as u32,
            max: tx_hashes.len(),
        });
    }

    let mut path = Vec::new();
    let mut directions = Vec::new();

    let mut level = tx_hashes.to_vec();
    let mut current_index = tx_index;

    while level.len() > 1 {
        let mut next_level = Vec::new();
        let mut next_index = 0;

        for (i, chunk) in level.chunks(2).enumerate() {
            if chunk.len() == 2 {
                // Pair exists
                let (left, right) = (&chunk[0], &chunk[1]);

                // If current_index is in this chunk, record sibling
                if i * 2 == current_index {
                    path.push(*right);
                    directions.push(false); // Current is left
                    next_index = i;
                } else if i * 2 + 1 == current_index {
                    path.push(*left);
                    directions.push(true); // Current is right
                    next_index = i;
                } else if i == current_index / 2 {
                    next_index = i;
                }

                next_level.push(combine_hashes(left, right));
            } else {
                // Odd node, promote without sibling
                next_level.push(chunk[0]);
                if i == current_index / 2 {
                    next_index = i;
                }
            }
        }

        level = next_level;
        current_index = next_index;
    }

    Ok(MerkleProof {
        tx_index: tx_index as u64,
        path,
        directions,
    })
}

/// Verify Merkle proof against root hash
pub fn verify_merkle_proof(
    tx_hash: &[u8; 32],
    proof: &MerkleProof,
    expected_root: &[u8; 32],
) -> Result<()> {
    if proof.path.len() != proof.directions.len() {
        return Err(ConsensusError::MerkleProofInvalid);
    }

    let mut current_hash = *tx_hash;

    for (sibling_hash, is_right) in proof.path.iter().zip(proof.directions.iter()) {
        current_hash = if *is_right {
            // Current is on right, sibling on left
            combine_hashes(sibling_hash, &current_hash)
        } else {
            // Current is on left, sibling on right
            combine_hashes(&current_hash, sibling_hash)
        };
    }

    if &current_hash != expected_root {
        return Err(ConsensusError::MerkleRootMismatch {
            expected: hex::encode(expected_root),
            computed: hex::encode(current_hash),
        });
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_hash(val: u8) -> [u8; 32] {
        let mut h = [0u8; 32];
        h[0] = val;
        h
    }

    #[test]
    fn test_empty_merkle_root() {
        let root = compute_merkle_root(&[]);
        assert_eq!(root, [0u8; 32]);
    }

    #[test]
    fn test_single_hash_merkle_root() {
        let hash = make_hash(1);
        let root = compute_merkle_root(&[hash]);
        assert_eq!(root, hash);
    }

    #[test]
    fn test_two_hashes_merkle_root() {
        let h1 = make_hash(1);
        let h2 = make_hash(2);
        let root = compute_merkle_root(&[h1, h2]);

        // Root should be SHA-256(h1 || h2)
        let expected = combine_hashes(&h1, &h2);
        assert_eq!(root, expected);
    }

    #[test]
    fn test_four_hashes_merkle_root() {
        let h1 = make_hash(1);
        let h2 = make_hash(2);
        let h3 = make_hash(3);
        let h4 = make_hash(4);

        let root = compute_merkle_root(&[h1, h2, h3, h4]);

        // Build expected tree manually
        let left = combine_hashes(&h1, &h2);
        let right = combine_hashes(&h3, &h4);
        let expected = combine_hashes(&left, &right);

        assert_eq!(root, expected);
    }

    #[test]
    fn test_odd_hashes_merkle_root() {
        // With 3 hashes, should not duplicate the last one
        let h1 = make_hash(1);
        let h2 = make_hash(2);
        let h3 = make_hash(3);

        let root = compute_merkle_root(&[h1, h2, h3]);

        // Build expected: (h1+h2) and h3, then combine
        let left = combine_hashes(&h1, &h2);
        let expected = combine_hashes(&left, &h3);

        assert_eq!(root, expected);
    }

    #[test]
    fn test_deterministic_merkle_root() {
        let hashes = vec![make_hash(1), make_hash(2), make_hash(3), make_hash(4)];

        let root1 = compute_merkle_root(&hashes);
        let root2 = compute_merkle_root(&hashes);

        assert_eq!(root1, root2);
    }

    #[test]
    fn test_merkle_proof_generation() {
        let hashes = vec![make_hash(1), make_hash(2), make_hash(3), make_hash(4)];

        let proof = generate_merkle_proof(&hashes, 1).unwrap();

        assert_eq!(proof.tx_index, 1);
        assert!(!proof.path.is_empty());
        assert_eq!(proof.path.len(), proof.directions.len());
    }

    #[test]
    fn test_merkle_proof_verification() {
        let hashes = vec![make_hash(1), make_hash(2), make_hash(3), make_hash(4)];
        let root = compute_merkle_root(&hashes);

        // Generate and verify proof for each transaction
        for (i, tx_hash) in hashes.iter().enumerate() {
            let proof = generate_merkle_proof(&hashes, i).unwrap();
            let result = verify_merkle_proof(tx_hash, &proof, &root);
            assert!(result.is_ok(), "Proof verification failed for index {}", i);
        }
    }

    #[test]
    fn test_merkle_proof_wrong_root_fails() {
        let hashes = vec![make_hash(1), make_hash(2)];
        let proof = generate_merkle_proof(&hashes, 0).unwrap();

        let wrong_root = make_hash(99);
        let result = verify_merkle_proof(&hashes[0], &proof, &wrong_root);

        assert!(result.is_err());
    }

    #[test]
    fn test_merkle_proof_out_of_bounds() {
        let hashes = vec![make_hash(1), make_hash(2)];
        let result = generate_merkle_proof(&hashes, 10);

        assert!(result.is_err());
    }
}
