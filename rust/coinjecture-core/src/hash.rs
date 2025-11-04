//! SHA-256 hashing utilities for consensus-critical operations.
//!
//! All hashing is deterministic and reproducible across platforms.
//! Uses sha2 crate for audited, constant-time SHA-256 implementation.

use crate::errors::{ConsensusError, Result};
use sha2::{Digest, Sha256};

/// Compute SHA-256 hash of arbitrary bytes
pub fn sha256(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hasher.finalize().into()
}

/// Compute double SHA-256 (Bitcoin-style)
pub fn double_sha256(data: &[u8]) -> [u8; 32] {
    sha256(&sha256(data))
}

/// Compute SHA-256 of multiple byte slices (concatenated)
pub fn sha256_multi(data_slices: &[&[u8]]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    for slice in data_slices {
        hasher.update(slice);
    }
    hasher.finalize().into()
}

/// Hash a string (UTF-8 encoded)
pub fn sha256_str(s: &str) -> [u8; 32] {
    sha256(s.as_bytes())
}

/// Compute hash with domain separation (prefix)
pub fn sha256_domain(domain: &str, data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(domain.as_bytes());
    hasher.update(data);
    hasher.finalize().into()
}

/// Derive address from public key (COINjecture address scheme)
/// address = SHA-256(pubkey)
pub fn derive_address(pubkey: &[u8; 32]) -> [u8; 32] {
    sha256(pubkey)
}

/// Compute epoch salt for commit-reveal (SEC-002)
/// epoch_salt = SHA-256(parent_hash || block_index)
pub fn compute_epoch_salt(parent_hash: &[u8; 32], block_index: u64) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(parent_hash);
    hasher.update(&block_index.to_le_bytes());
    hasher.finalize().into()
}

/// Verify hash matches expected value
pub fn verify_hash(data: &[u8], expected_hash: &[u8; 32]) -> Result<()> {
    let computed = sha256(data);
    if &computed != expected_hash {
        return Err(ConsensusError::HashError(format!(
            "Hash mismatch: expected {}, got {}",
            hex::encode(expected_hash),
            hex::encode(computed)
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sha256_deterministic() {
        let data = b"hello world";
        let hash1 = sha256(data);
        let hash2 = sha256(data);
        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_sha256_known_vector() {
        // echo -n "hello world" | sha256sum
        let data = b"hello world";
        let hash = sha256(data);
        let expected =
            hex::decode("b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9")
                .unwrap();
        assert_eq!(hash.as_slice(), expected.as_slice());
    }

    #[test]
    fn test_double_sha256() {
        let data = b"test";
        let single = sha256(data);
        let double = double_sha256(data);
        let expected_double = sha256(&single);
        assert_eq!(double, expected_double);
    }

    #[test]
    fn test_sha256_multi() {
        let part1 = b"hello";
        let part2 = b" ";
        let part3 = b"world";

        let hash_multi = sha256_multi(&[part1, part2, part3]);
        let hash_concat = sha256(b"hello world");

        assert_eq!(hash_multi, hash_concat);
    }

    #[test]
    fn test_domain_separation() {
        let data = b"test";
        let hash1 = sha256_domain("domain1", data);
        let hash2 = sha256_domain("domain2", data);
        assert_ne!(hash1, hash2);
    }

    #[test]
    fn test_epoch_salt_deterministic() {
        let parent = [42u8; 32];
        let index = 123;

        let salt1 = compute_epoch_salt(&parent, index);
        let salt2 = compute_epoch_salt(&parent, index);
        assert_eq!(salt1, salt2);

        // Different index = different salt
        let salt3 = compute_epoch_salt(&parent, index + 1);
        assert_ne!(salt1, salt3);
    }

    #[test]
    fn test_verify_hash_success() {
        let data = b"test data";
        let hash = sha256(data);
        assert!(verify_hash(data, &hash).is_ok());
    }

    #[test]
    fn test_verify_hash_failure() {
        let data = b"test data";
        let wrong_hash = [0u8; 32];
        assert!(verify_hash(data, &wrong_hash).is_err());
    }
}
