# COINjecture Institutional-Grade Refactor

**Multi-language blockchain refactor for bank/FI-class compliance**

Version: 4.0.0-REFACTOR | Date: 2025-11-04

---

## Executive Summary

This repository contains the complete architectural refactor of COINjecture from a Python monolith to a multi-language, institutional-grade system that satisfies bank and financial institution requirements.

### Goals

- ✅ **Determinism**: Canonical serialization, reproducible across platforms
- ✅ **Verifiability**: All proofs verifiable in O(n) or better
- ✅ **Reproducibility**: Locked dependencies, reproducible builds, artifact signing
- ✅ **Defense-in-Depth**: 6-layer security architecture
- ✅ **Observability**: Prometheus metrics, SLOs, alerting
- ✅ **Change Control**: Golden vectors, code owners, labeled PRs

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Rust Core (consensus-critical)                        │
│  - types.rs: #[repr(C)] structs                        │
│  - codec.rs: Canonical msgpack + JSON                  │
│  - verify.rs: Budget-limited verification              │
│  - commitment.rs: Epoch binding (SEC-002)              │
│  └─> PyO3 bindings + C headers (cbindgen)              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Go Daemon (networking & operational)                   │
│  - API: gin/fiber HTTP with rate limiting              │
│  - P2P: Equilibrium gossip (λ = 0.7071)                │
│  - IPFS: Pinning quorum (≥2/3)                         │
│  - Metrics: Prometheus exporter                         │
│  └─> CGO → Rust static lib                             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  Python Shims (backwards compatibility)                 │
│  - legacy_compat.py: Dual-run validator                │
│  - admission.py: Epoch replay, nonce checks            │
│  └─> Delegates to Rust via PyO3                        │
└─────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
COINjecture1337-REFACTOR/
│
├── REFACTOR_ARCHITECTURE.md    # Complete architecture with Mermaid diagrams
│
├── rust/coinjecture-core/       # Consensus-critical Rust core
│   ├── src/
│   │   ├── types.rs             # repr(C) structs, enums
│   │   ├── codec.rs             # Canonical msgpack + JSON
│   │   ├── hash.rs              # SHA-256 primitives
│   │   ├── merkle.rs            # Deterministic Merkle trees
│   │   ├── commitment.rs        # HMAC commitment binding
│   │   ├── verify.rs            # Budget-limited verification
│   │   ├── errors.rs            # Typed errors (no panics)
│   │   ├── python.rs            # PyO3 bindings
│   │   └── lib.rs               # Module exports
│   ├── tests/                   # Golden vectors, property tests
│   ├── golden/                  # Frozen test fixtures
│   └── README.md                # Rust documentation
│
├── go/                          # Go daemon
│   ├── cmd/coinjectured/        # Main daemon binary
│   ├── pkg/
│   │   ├── api/                 # REST API server
│   │   ├── p2p/                 # Equilibrium gossip
│   │   ├── limiter/             # Token bucket rate limiter
│   │   ├── ipfs/                # Pinning quorum
│   │   ├── metrics/             # Prometheus exporter
│   │   ├── bindings/            # CGO → Rust
│   │   └── config/              # Configuration management
│   └── internal/logger/         # Structured logging
│
├── python/src/coinjecture/      # Python shims
│   ├── types.py                 # Frozen dataclasses
│   ├── consensus/
│   │   ├── codec.py             # Delegates to Rust
│   │   └── admission.py         # Epoch replay protection
│   └── legacy_compat.py         # Dual-run validator
│
├── .github/workflows/           # CI/CD pipelines
│   ├── ci.yml                   # Main quality gates
│   ├── determinism.yml          # Cross-platform tests
│   ├── parity.yml               # Dual-run validation
│   └── security.yml             # Audits + SBOM generation
│
└── docs/
    ├── CODEOWNERS               # Code review assignments
    ├── RUNBOOKS.md              # Operational procedures
    └── SLO.md                   # Service level objectives
```

---

## Quick Start

### Prerequisites

```bash
# Rust (1.75+)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Go (1.21+)
# Download from https://go.dev/dl/

# Python (3.10+)
python --version  # Should be 3.10 or higher
```

### Build Rust Core

```bash
cd rust/coinjecture-core

# Run tests (including golden vectors)
cargo test

# Build release
cargo build --release

# Build Python wheel
pip install maturin
maturin build --release
```

### Build Go Daemon

```bash
cd go

# Download dependencies
go mod download

# Build daemon
go build -o coinjectured ./cmd/coinjectured

# Run with default config
./coinjectured --log-level info
```

### Run Quality Gates

```bash
# Determinism test (cross-platform)
cargo test --test golden_tests

# Parity test (Rust vs Python)
# (To be implemented)

# Security audit
cargo audit
go list -json -m all | nancy sleuth
```

---

## Key Features

### SEC-001: Codec Divergence Mitigation

**Problem**: Msgpack and JSON paths produce different hashes → consensus fork

**Solution**:
- Cross-path equivalence tests
- Strict decode (rejects unknown fields)
- `codec_version` field in all types
- Feature flag `CODEC_MODE` for gradual cutover

```rust
let msgpack_hash = compute_hash_msgpack(&header)?;
let json_hash = compute_hash_json(&header)?;
assert_eq!(msgpack_hash, json_hash); // MUST pass
```

### SEC-002: Epoch Replay Protection

**Problem**: Miners reuse commitments across epochs → grinding attacks

**Solution**:
- Epoch salt: `SHA-256(parent_hash || block_index)`
- Miner salt: `HMAC(priv_key, epoch_salt || parent_hash || block_index)`
- Admission cache persists `(commitment, epoch)` tuples

```rust
let epoch_salt = compute_epoch_salt(&parent_hash, block_index);
let miner_salt = compute_miner_salt(&priv_key, &epoch_salt, &parent_hash, block_index)?;
verify_commitment(&commitment, &reveal, &parent_hash, block_index)?;
```

### SEC-005: CID Integrity

**Problem**: 38.2% missing CIDs in production → data loss

**Solution**:
- Pin quorum: ≥2/3 IPFS nodes must confirm
- Size/hash verification before accepting block
- Audit job checks CIDs every 6 hours
- Pin manifest with provenance signature

```go
manifest, err := ipfsClient.PinWithQuorum(ctx, proofBundle)
if err != nil {
    return fmt.Errorf("pin quorum failed: %w", err)
}
```

### Rate Limiting (Defense-in-Depth Layer 1)

```go
rateLimiter := limiter.NewRateLimiter(config.RateLimiter{
    IPLimit:      100,    // 100 req/min per IP
    PeerIDLimit:  200,    // 200 req/min per peer
    GlobalLimit:  10000,  // 10K req/min global
}, log)

allowed, err := rateLimiter.CheckIP(clientIP)
if !allowed {
    return http.StatusTooManyRequests
}
```

### Equilibrium Gossip (v3.17.0)

```go
p2pManager := p2p.NewManager(config.P2P{
    EquilibriumLambda:   0.7071,  // √2/2 (critical damping)
    BroadcastInterval:   14140,   // 14.14s in ms
}, log)

// Broadcasts CID to floor(λ × N) peers
p2pManager.BroadcastCID(cid)
```

---

## Development

### Running Tests

```bash
# Rust unit tests
cd rust/coinjecture-core
cargo test

# Rust golden vectors
cargo test --test golden_tests

# Go tests
cd go
go test ./...

# Python tests
cd python
pytest
```

### Adding a Golden Vector

1. Create fixture in `rust/coinjecture-core/golden/`
2. Add test in `tests/golden_tests.rs`
3. Run test to populate placeholder hashes
4. Create PR with label `golden-vector-change`
5. Require code owner approval

Example:

```rust
#[test]
fn test_golden_my_new_vector() {
    let header = BlockHeader { /* ... */ };
    let hash = compute_header_hash(&header).unwrap();

    // First run: prints hash
    println!("Hash: {}", hex::encode(hash));

    // After approval: freeze hash
    let expected = hex::decode("...").unwrap();
    assert_eq!(&hash[..], &expected);
}
```

### Feature Flags (Cutover Strategy)

Set `CODEC_MODE` environment variable:

- `legacy_only`: Use old Python codec only
- `shadow`: Compute both, log diffs (no reject)
- `refactored_primary`: Use Rust, fallback to Python on error
- `refactored_only`: Pure Rust (Python removed)

```yaml
# config.yaml
features:
  codec_mode: "shadow"
  validate_against_legacy: true
  strict_cid_enforcement: true
```

---

## Security

### Defense-in-Depth Layers

1. **Network Edge**: IP rate limits (100/min), peer scoring
2. **Early Reject**: Schema validation, tier checks, signature verify
3. **Admission Control**: Epoch replay cache, nonce sequence
4. **Consensus Verification**: Commitment binding, subset sum with budget
5. **IPFS Integrity**: Pin quorum ≥2/3, CID audit
6. **State Transition**: Balance invariants, reorg protection

### Vulnerability Disclosure

Security issues: email adz@alphx.io (GPG key: TBD)

Please include:
- Vulnerability description
- Proof of concept (if applicable)
- Suggested mitigation

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| `compute_header_hash` | < 1ms | Criterion benchmarks |
| `encode_block` | < 10ms | Criterion benchmarks |
| `merkle(1k tx)` | < 50ms | Criterion benchmarks |
| `verify_subset_sum` (tier 2) | < 300s | Budget enforcement |
| API p95 latency | < 100ms | Prometheus metrics |
| Pin quorum success rate | > 95% | IPFS metrics |

---

## Roadmap

### Phase 1: Foundation (Current)
- [x] Rust core with PyO3 bindings
- [x] Go daemon with API, P2P, IPFS
- [x] Rate limiting and admission controls
- [x] Golden vector tests
- [ ] CI/CD pipelines (determinism, parity, security)

### Phase 2: Integration (Next)
- [ ] Python shims with dual-run validator
- [ ] Parity tests (1,000+ blocks)
- [ ] SBOM generation and artifact signing
- [ ] Runbooks and deployment scripts

### Phase 3: Production (Future)
- [ ] Gradual rollout (canary → 100%)
- [ ] 30-day soak test
- [ ] Legacy code removal
- [ ] Mainnet cutover

---

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Review

- All consensus changes require code owner approval
- Golden vector changes require labeled PR: `golden-vector-change`
- CI/CD must pass (tests, linting, security scans)

See [CODEOWNERS](docs/CODEOWNERS) for review assignments.

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Links

- **Original Repo**: https://github.com/Quigles1337/COINjecture1337
- **Refactor Repo**: https://github.com/Quigles1337/COINjecture1337-REFACTOR
- **Documentation**: https://docs.coinjecture.com
- **API**: https://api.coinjecture.com

---

## Acknowledgments

Built with institutional-grade rigor by Quigles1337 with AI assistance from Claude (Anthropic).

**Technologies**: Rust, Go, Python, PyO3, libp2p, IPFS, Prometheus, Gin, SQLite

---

**Status**: 🚧 Active Development | **Version**: 4.0.0-REFACTOR | **Last Updated**: 2025-11-04
