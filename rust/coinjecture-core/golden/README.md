# Golden Test Vectors

**Version:** v4.0.0
**Status:** FROZEN
**Last Updated:** 2025-11-04

---

## Purpose

These golden vectors are **frozen reference values** that MUST NOT change without:
1. Labeled PR with `consensus-change` or `golden-vector-change`
2. Code owner approval (see CODEOWNERS)
3. Post-mortem explaining why consensus changed

**Any change to golden vectors is a CONSENSUS BREAKING CHANGE.**

---

## Files

| File | Description | Hash Algorithm | Frozen Date |
|------|-------------|----------------|-------------|
| `genesis_v4_0_0.json` | Genesis block (block 0) | SHA-256 | 2025-11-04 |
| `headers_v4_0_0.json` | Sample block headers | SHA-256 | 2025-11-04 |
| `transactions_v4_0_0.json` | Sample transactions | SHA-256 | 2025-11-04 |
| `merkle_v4_0_0.json` | Merkle root test cases | SHA-256 | 2025-11-04 |
| `commitments_v4_0_0.json` | Commitment binding tests | HMAC-SHA256 | 2025-11-04 |
| `codec_v4_0_0.json` | Codec serialization tests | - | 2025-11-04 |

---

## Usage

### Rust Tests

```rust
use coinjecture_core::test_utils::load_golden;

#[test]
fn test_genesis_hash() {
    let golden = load_golden("genesis_v4_0_0.json");
    let computed_hash = compute_header_hash(&golden.header);
    assert_eq!(
        computed_hash.to_hex(),
        golden.expected_hash,
        "Genesis hash must match frozen golden vector"
    );
}
```

### Python Tests

```python
from coinjecture.test_utils import load_golden
from coinjecture.consensus.codec import compute_header_hash

def test_genesis_hash():
    golden = load_golden("genesis_v4_0_0.json")
    computed = compute_header_hash(golden["header"])
    assert computed.hex() == golden["expected_hash"], \
        "Genesis hash must match frozen golden vector"
```

---

## Validation

All golden vectors are validated in CI:
- `rust/coinjecture-core/tests/golden_tests.rs`
- `python/tests/golden/test_golden_vectors.py`

**CI MUST pass on ALL platforms:**
- Linux x86_64
- Linux arm64
- macOS (Intel + ARM)
- Windows x86_64

**Determinism requirement:** Identical hashes across all platforms.

---

## Modification Procedure

**DO NOT modify golden vectors without following this procedure:**

1. **Create Issue**
   - Title: `[CONSENSUS CHANGE] Reason for golden vector update`
   - Label: `consensus-change`
   - Explain: Why is consensus changing?

2. **Create PR**
   - Title: `[BREAKING] Update golden vectors: <reason>`
   - Label: `golden-vector-change`
   - Include: Migration guide for existing nodes
   - Tag: `@code-owner` for review

3. **Code Owner Review**
   - Code owner MUST approve
   - At least 2 other maintainers MUST review
   - Security team MUST sign off

4. **Update Vectors**
   - Compute new hashes using current code
   - Update `expected_hash` fields
   - Increment version (e.g., `genesis_v4_0_0.json` → `genesis_v4_1_0.json`)
   - Keep old vectors for backward compatibility tests

5. **Post-Merge**
   - Announce breaking change on Discord
   - Update CHANGELOG.md
   - Tag release with new version

---

## Hash Computation

All hashes MUST be computed using canonical encoding:

**Header Hash:**
```
hash = SHA-256(canonical_msgpack(header))
```

**Merkle Root:**
```
tree = build_tree([SHA-256(canonical_msgpack(tx)) for tx in transactions])
merkle_root = tree.root
```

**Commitment:**
```
epoch_salt = SHA-256(parent_hash || block_index)
commitment = SHA-256(epoch_salt || problem_hash || solution_hash || miner_salt)
```

---

## Determinism Guarantee

These vectors guarantee:
✅ Same input → same hash (deterministic)
✅ Same hash on all platforms (cross-platform)
✅ Same hash on all Python versions (3.10, 3.11, 3.12)
✅ Same hash for msgpack AND JSON codecs

**Any divergence = CI failure = consensus bug**

---

## Version History

| Version | Date | Changes | Migration Required? |
|---------|------|---------|---------------------|
| v4.0.0 | 2025-11-04 | Initial frozen vectors | N/A (first release) |

---

**REMEMBER: Changing golden vectors = changing consensus = hard fork**

Only do this with extreme caution and proper governance!
