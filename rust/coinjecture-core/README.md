# COINjecture Core

**Institutional-grade consensus-critical blockchain logic in Rust**

Version: 4.0.0 | Codec Version: 1

---

## Overview

`coinjecture-core` is the consensus-critical foundation of the COINjecture blockchain, providing:

- ✅ **Deterministic** serialization (msgpack + JSON with cross-path verification)
- ✅ **Verifiable** proof-of-work (subset sum with O(n) verification)
- ✅ **Reproducible** builds (pinned dependencies, locked Cargo.toml)
- ✅ **Secure** by design (budget limits, strict validation, typed errors)
- ✅ **FFI-ready** (Python bindings via PyO3, C headers via cbindgen)

---

## Features

### Core Modules

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `types` | Canonical data structures (`#[repr(C)]`) | `BlockHeader`, `Transaction`, `Problem`, `Solution` |
| `codec` | Deterministic msgpack + JSON encoding | `encode_block`, `compute_header_hash` |
| `hash` | SHA-256 primitives | `sha256`, `compute_epoch_salt` |
| `merkle` | Deterministic Merkle trees | `compute_merkle_root`, `verify_merkle_proof` |
| `commitment` | Commit-reveal protocol (SEC-002) | `create_commitment`, `verify_commitment` |
| `verify` | Budget-limited proof verification | `verify_solution`, `VerifyBudget` |
| `errors` | Typed error handling (no panics) | `ConsensusError` with error codes |
| `python` | PyO3 bindings for Python | `coinjecture_core` module |

---

## Installation

### Rust Library

```bash
cargo add coinjecture-core
```

### Python Extension

```bash
pip install coinjecture-core
# or
maturin develop --release
```

---

## Usage

### Rust

```rust
use coinjecture_core::*;

// Create and hash a block header
let header = BlockHeader {
    codec_version: CODEC_VERSION,
    block_index: 1,
    timestamp: 1609459200,
    ..Default::default()
};

let hash = codec::compute_header_hash(&header)?;
println!("Block hash: {}", hex::encode(hash));

// Verify a subset sum proof
let problem = Problem { /* ... */ };
let solution = Solution { /* ... */ };
let budget = VerifyBudget::strict_desktop();

let result = verify::verify_solution(&problem, &solution, &budget)?;
assert!(result.valid);
```

### Python

```python
import coinjecture_core as cc

# Compute header hash
header = {
    "codec_version": 1,
    "block_index": 1,
    "timestamp": 1609459200,
    # ...
}
hash_bytes = cc.compute_header_hash_py(header)

# Verify subset sum
valid = cc.verify_subset_sum_py(problem, solution, budget)
```

---

## Quality Gates

### Determinism

All operations produce **identical results** across:
- Operating systems (Linux, macOS, Windows)
- Architectures (x86_64, ARM64)
- Python versions (3.10, 3.11, 3.12)

Verified by:
```bash
cargo test --test golden_tests
cargo test --test determinism_tests
```

### Cross-Path Equivalence (SEC-001)

Msgpack and JSON encoding paths produce **identical hashes**:

```rust
let msgpack_hash = codec::compute_hash_msgpack(&header)?;
let json_hash = codec::compute_hash_json(&header)?;
assert_eq!(msgpack_hash, json_hash); // MUST pass
```

### Security

- **No panics** in consensus path (all errors typed)
- **Budget limits** on verification (ops, time, memory)
- **Strict decode** (rejects unknown fields, extra data)
- **Tier validation** (element count, time limits enforced)

---

## Testing

```bash
# All tests
cargo test

# Golden vectors only
cargo test --test golden_tests

# Property-based tests
cargo test --features quickcheck

# Benchmarks
cargo bench

# With coverage
cargo tarpaulin --out Html
```

---

## Building

### Release Build (Reproducible)

```bash
cargo build --release
```

Optimizations:
- LTO enabled
- Single codegen unit
- Symbols stripped

### Python Wheel

```bash
maturin build --release
```

### Static Library + C Headers

```bash
cargo build --release
cbindgen --config cbindgen.toml --crate coinjecture-core --output coinjecture_core.h
```

---

## Architecture

### Type System

All types are `#[repr(C)]` for FFI stability:

```rust
#[repr(C)]
pub struct BlockHeader {
    pub codec_version: u8,     // MUST be first
    pub block_index: u64,
    pub timestamp: i64,
    pub parent_hash: [u8; 32],
    // ...
}
```

### Error Handling

```rust
pub enum ConsensusError {
    CodecError(String),                      // E1000
    BudgetOpsExceeded { max_ops, actual },   // E2000
    CommitmentMismatch,                      // E3000
    // ...
}

impl ConsensusError {
    pub fn error_code(&self) -> &'static str;
    pub fn is_recoverable(&self) -> bool;
    pub fn is_critical(&self) -> bool;
}
```

---

## Security Considerations

### SEC-001: Codec Divergence

**Mitigation**: Cross-path equivalence tests enforce msgpack == JSON hashing.

### SEC-002: Epoch Replay

**Mitigation**: Commitment binding to `epoch_salt = SHA-256(parent_hash || block_index)`.

### SEC-005: CID Integrity

**Mitigation**: Pin quorum (≥2/3), size/hash verification, audit manifest.

---

## Hardware Tiers

| Tier | Elements | Time Limit | Memory | Verify Ops |
|------|----------|------------|--------|------------|
| Mobile | 8-12 | 60s | 256MB | 2^12 |
| Desktop | 12-16 | 300s | 1GB | 2^16 |
| Workstation | 16-20 | 900s | 4GB | 2^20 |
| Server | 20-24 | 1800s | 16GB | 2^24 |
| Cluster | 24-32 | 3600s | 64GB | 2^32 |

---

## Contributing

1. All changes must pass `cargo test` + `cargo clippy`
2. Golden vector changes require labeled PR: `golden-vector-change`
3. Code owners must approve all consensus changes
4. See [CODEOWNERS](../../docs/CODEOWNERS) for review assignments

---

## License

MIT License - see [LICENSE](../../LICENSE)

---

## Links

- **Repository**: https://github.com/Quigles1337/COINjecture1337-REFACTOR
- **Documentation**: https://docs.coinjecture.com
- **Issues**: https://github.com/Quigles1337/COINjecture1337-REFACTOR/issues

---

**Built with ❤️ for institutional-grade blockchain security**
