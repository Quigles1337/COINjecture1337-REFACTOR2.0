//! Commitment binding for commit-reveal protocol (SEC-002).
//!
//! Anti-grinding: miner commits to (problem, solution) before revealing.
//! Epoch binding: commitment tied to parent_hash + block_index (epoch_salt).
//! Miner binding: HMAC with miner's private key prevents impersonation.

use crate::codec::{compute_problem_hash, compute_solution_hash};
use crate::errors::{ConsensusError, Result};
use crate::hash::{compute_epoch_salt, sha256, sha256_multi};
use crate::types::{Commitment, Problem, Reveal, Solution};
use hmac::{Hmac, Mac};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

/// Compute miner salt from private key and epoch context (SEC-002)
///
/// miner_salt = HMAC-SHA256(
///     key = miner_private_key,
///     msg = epoch_salt || parent_hash || block_index
/// )
///
/// This binds the commitment to:
/// - The miner's identity (private key)
/// - The specific epoch (parent_hash + block_index)
/// - Prevents reuse across epochs
pub fn compute_miner_salt(
    miner_private_key: &[u8; 32],
    epoch_salt: &[u8; 32],
    parent_hash: &[u8; 32],
    block_index: u64,
) -> Result<[u8; 32]> {
    let mut mac = HmacSha256::new_from_slice(miner_private_key)
        .map_err(|e| ConsensusError::HmacError(e.to_string()))?;

    mac.update(epoch_salt);
    mac.update(parent_hash);
    mac.update(&block_index.to_le_bytes());

    let result = mac.finalize();
    Ok(result.into_bytes().into())
}

/// Create commitment from problem and solution (commit phase)
pub fn create_commitment(
    problem: &Problem,
    solution: &Solution,
    miner_salt: &[u8; 32],
    parent_hash: &[u8; 32],
    block_index: u64,
) -> Result<Commitment> {
    let epoch_salt = compute_epoch_salt(parent_hash, block_index);
    let problem_hash = compute_problem_hash(problem)?;
    let solution_hash = compute_solution_hash(solution)?;

    Ok(Commitment {
        epoch_salt,
        problem_hash,
        solution_hash,
        miner_salt: *miner_salt,
    })
}

/// Compute commitment hash (for block header)
pub fn compute_commitment_hash(commitment: &Commitment) -> [u8; 32] {
    sha256_multi(&[
        &commitment.epoch_salt,
        &commitment.problem_hash,
        &commitment.solution_hash,
        &commitment.miner_salt,
    ])
}

/// Verify commitment matches reveal (reveal phase)
pub fn verify_commitment(
    commitment: &Commitment,
    reveal: &Reveal,
    parent_hash: &[u8; 32],
    block_index: u64,
) -> Result<()> {
    // 1. Verify epoch salt binding
    let expected_epoch_salt = compute_epoch_salt(parent_hash, block_index);
    if commitment.epoch_salt != expected_epoch_salt {
        return Err(ConsensusError::EpochBindingFailed);
    }

    // 2. Verify problem hash
    let computed_problem_hash = compute_problem_hash(&reveal.problem)?;
    if commitment.problem_hash != computed_problem_hash {
        return Err(ConsensusError::ProblemHashMismatch {
            expected: hex::encode(commitment.problem_hash),
            computed: hex::encode(computed_problem_hash),
        });
    }

    // 3. Verify solution hash
    let computed_solution_hash = compute_solution_hash(&reveal.solution)?;
    if commitment.solution_hash != computed_solution_hash {
        return Err(ConsensusError::SolutionHashMismatch {
            expected: hex::encode(commitment.solution_hash),
            computed: hex::encode(computed_solution_hash),
        });
    }

    // 4. Verify miner salt matches reveal
    if commitment.miner_salt != reveal.miner_salt {
        return Err(ConsensusError::MinerSaltInvalid);
    }

    Ok(())
}

/// Verify miner salt binding (optional: if we have miner pubkey)
///
/// This is a FUTURE enhancement - requires miner to prove knowledge of
/// private key that generated miner_salt without revealing the key.
/// Current version: trust miner_salt, verify it matches commitment.
pub fn verify_miner_salt_binding(
    miner_salt: &[u8; 32],
    miner_pubkey: &[u8; 32],
    epoch_salt: &[u8; 32],
    parent_hash: &[u8; 32],
    block_index: u64,
) -> Result<()> {
    // FUTURE: Zero-knowledge proof or signature-based verification
    // For now: placeholder that always succeeds
    // Real implementation would verify HMAC without revealing private key

    // Verify structure is correct
    if miner_salt.len() != 32 || miner_pubkey.len() != 32 {
        return Err(ConsensusError::MinerSaltInvalid);
    }

    // FUTURE: Implement ZK-HMAC or similar proof
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{HardwareTier, ProblemType};

    fn make_test_problem() -> Problem {
        Problem {
            problem_type: ProblemType::SubsetSum,
            tier: HardwareTier::Desktop,
            elements: vec![1, 2, 3, 4, 5],
            target: 9,
            timestamp: 1000,
        }
    }

    fn make_test_solution() -> Solution {
        Solution {
            indices: vec![1, 3],
            timestamp: 1001,
        }
    }

    #[test]
    fn test_miner_salt_deterministic() {
        let priv_key = [1u8; 32];
        let epoch_salt = [2u8; 32];
        let parent_hash = [3u8; 32];
        let block_index = 100;

        let salt1 = compute_miner_salt(&priv_key, &epoch_salt, &parent_hash, block_index).unwrap();
        let salt2 = compute_miner_salt(&priv_key, &epoch_salt, &parent_hash, block_index).unwrap();

        assert_eq!(salt1, salt2);
    }

    #[test]
    fn test_miner_salt_changes_with_epoch() {
        let priv_key = [1u8; 32];
        let epoch_salt = [2u8; 32];
        let parent_hash = [3u8; 32];

        let salt1 = compute_miner_salt(&priv_key, &epoch_salt, &parent_hash, 100).unwrap();
        let salt2 = compute_miner_salt(&priv_key, &epoch_salt, &parent_hash, 101).unwrap();

        assert_ne!(salt1, salt2, "Miner salt should change with block index");
    }

    #[test]
    fn test_miner_salt_changes_with_key() {
        let epoch_salt = [2u8; 32];
        let parent_hash = [3u8; 32];
        let block_index = 100;

        let salt1 = compute_miner_salt(&[1u8; 32], &epoch_salt, &parent_hash, block_index).unwrap();
        let salt2 = compute_miner_salt(&[2u8; 32], &epoch_salt, &parent_hash, block_index).unwrap();

        assert_ne!(salt1, salt2, "Miner salt should change with private key");
    }

    #[test]
    fn test_create_commitment() {
        let problem = make_test_problem();
        let solution = make_test_solution();
        let miner_salt = [42u8; 32];
        let parent_hash = [1u8; 32];
        let block_index = 100;

        let commitment =
            create_commitment(&problem, &solution, &miner_salt, &parent_hash, block_index).unwrap();

        assert_eq!(commitment.miner_salt, miner_salt);
        assert_ne!(commitment.problem_hash, [0u8; 32]);
        assert_ne!(commitment.solution_hash, [0u8; 32]);
    }

    #[test]
    fn test_verify_commitment_success() {
        let problem = make_test_problem();
        let solution = make_test_solution();
        let miner_salt = [42u8; 32];
        let parent_hash = [1u8; 32];
        let block_index = 100;

        let commitment =
            create_commitment(&problem, &solution, &miner_salt, &parent_hash, block_index).unwrap();

        let reveal = Reveal {
            problem,
            solution,
            miner_salt,
            nonce: 0,
        };

        let result = verify_commitment(&commitment, &reveal, &parent_hash, block_index);
        assert!(result.is_ok());
    }

    #[test]
    fn test_verify_commitment_wrong_problem_fails() {
        let problem = make_test_problem();
        let solution = make_test_solution();
        let miner_salt = [42u8; 32];
        let parent_hash = [1u8; 32];
        let block_index = 100;

        let commitment =
            create_commitment(&problem, &solution, &miner_salt, &parent_hash, block_index).unwrap();

        // Wrong problem
        let mut wrong_problem = problem.clone();
        wrong_problem.target = 999;

        let reveal = Reveal {
            problem: wrong_problem,
            solution,
            miner_salt,
            nonce: 0,
        };

        let result = verify_commitment(&commitment, &reveal, &parent_hash, block_index);
        assert!(result.is_err());
    }

    #[test]
    fn test_verify_commitment_wrong_solution_fails() {
        let problem = make_test_problem();
        let solution = make_test_solution();
        let miner_salt = [42u8; 32];
        let parent_hash = [1u8; 32];
        let block_index = 100;

        let commitment =
            create_commitment(&problem, &solution, &miner_salt, &parent_hash, block_index).unwrap();

        // Wrong solution
        let mut wrong_solution = solution.clone();
        wrong_solution.indices = vec![0, 1];

        let reveal = Reveal {
            problem,
            solution: wrong_solution,
            miner_salt,
            nonce: 0,
        };

        let result = verify_commitment(&commitment, &reveal, &parent_hash, block_index);
        assert!(result.is_err());
    }

    #[test]
    fn test_verify_commitment_wrong_epoch_fails() {
        let problem = make_test_problem();
        let solution = make_test_solution();
        let miner_salt = [42u8; 32];
        let parent_hash = [1u8; 32];
        let block_index = 100;

        let commitment =
            create_commitment(&problem, &solution, &miner_salt, &parent_hash, block_index).unwrap();

        let reveal = Reveal {
            problem,
            solution,
            miner_salt,
            nonce: 0,
        };

        // Wrong block index (different epoch)
        let result = verify_commitment(&commitment, &reveal, &parent_hash, block_index + 1);
        assert!(result.is_err());
    }

    #[test]
    fn test_commitment_hash_deterministic() {
        let commitment = Commitment {
            epoch_salt: [1u8; 32],
            problem_hash: [2u8; 32],
            solution_hash: [3u8; 32],
            miner_salt: [4u8; 32],
        };

        let hash1 = compute_commitment_hash(&commitment);
        let hash2 = compute_commitment_hash(&commitment);

        assert_eq!(hash1, hash2);
    }
}
