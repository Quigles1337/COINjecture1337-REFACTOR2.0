# COINjecture Institutional-Grade Refactor Architecture

**Version:** 4.0.0-REFACTOR
**Date:** 2025-11-04
**Lead:** Multi-Agent Refactor Team
**Target:** Bank/FI-Class Requirements

---

## Executive Summary

This document defines the complete architectural transformation of COINjecture from a Python monolith to a multi-language, institutional-grade system with:

- **Rust Core**: Consensus-critical logic (deterministic, verifiable, reproducible)
- **Go Networking/API**: Concurrent, isolated, observable, rate-limited
- **Python Shims**: Backwards compatibility + legacy glue
- **Quality Gates**: Golden vectors, parity testing, determinism, SBOM, signing

---

## Architectural Overview

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Interface<br/>coinjecture-cli]
        WebUI[Web Frontend<br/>React SPA]
        SDK[SDK Libraries<br/>Python/JS/Rust]
    end

    subgraph "Go Service Layer - Operational"
        API[REST API Server<br/>pkg/api<br/>gin/fiber]
        P2P[P2P Networking<br/>pkg/p2p<br/>Equilibrium Gossip]
        Limiter[Rate Limiter<br/>pkg/limiter<br/>Token Buckets]
        IPFS[IPFS Manager<br/>pkg/ipfs<br/>Pinning Quorum]
        Metrics[Metrics Exporter<br/>pkg/metrics<br/>Prometheus]
    end

    subgraph "Rust Core - Consensus Critical"
        Types[Types & Schema<br/>types.rs<br/>repr-C]
        Codec[Canonical Codec<br/>codec.rs<br/>msgpack+JSON]
        Hash[Hashing Engine<br/>hash.rs<br/>SHA-256]
        Merkle[Merkle Trees<br/>merkle.rs<br/>Deterministic]
        Commit[Commitment Logic<br/>commitment.rs<br/>HMAC Binding]
        Verify[Verification Engine<br/>verify.rs<br/>Budget-Limited]
    end

    subgraph "Python Shim Layer - Compatibility"
        PyShim[BC Shims<br/>legacy_compat.py]
        PyTypes[Type Mirrors<br/>types.py]
        PyCodec[Codec Delegate<br/>consensus/codec.py]
        PyAdmit[Admission Control<br/>consensus/admission.py]
    end

    subgraph "Bindings & FFI"
        PyO3[PyO3 Bindings<br/>Python ↔ Rust]
        CBindgen[C Headers<br/>cbindgen<br/>Go ↔ Rust]
        CGO[CGO Wrapper<br/>pkg/bindings]
    end

    subgraph "Data & Storage"
        SQLite[(SQLite<br/>blockchain.db)]
        IPFSNet[(IPFS Network<br/>Distributed Storage)]
        Cache[(Cache Layer<br/>Admission TTL)]
    end

    subgraph "Quality Gates & CI"
        Golden[Golden Vectors<br/>Frozen Fixtures]
        Parity[Parity Tests<br/>Dual-Run Validation]
        Determ[Determinism Tests<br/>Cross-Platform Matrix]
        Fuzz[Fuzz Tests<br/>Malformed Inputs]
        Security[Security Scans<br/>audit/SBOM]
    end

    CLI --> API
    WebUI --> API
    SDK --> API

    API --> Limiter
    API --> P2P
    API --> IPFS
    API --> Metrics

    Limiter --> CGO
    P2P --> CGO
    API --> CGO

    CGO --> CBindgen
    CBindgen --> Types
    CBindgen --> Codec
    CBindgen --> Hash
    CBindgen --> Merkle
    CBindgen --> Commit
    CBindgen --> Verify

    PyShim --> PyO3
    PyCodec --> PyO3
    PyAdmit --> PyO3

    PyO3 --> Types
    PyO3 --> Codec
    PyO3 --> Hash
    PyO3 --> Merkle
    PyO3 --> Commit
    PyO3 --> Verify

    API --> SQLite
    IPFS --> IPFSNet
    PyAdmit --> Cache

    Types -.-> Golden
    Codec -.-> Golden
    Hash -.-> Golden
    Merkle -.-> Golden

    PyShim -.-> Parity
    Codec -.-> Determ
    Verify -.-> Fuzz
    API -.-> Security

    style CLI fill:#e1f5ff
    style WebUI fill:#e1f5ff
    style API fill:#fff4e1
    style P2P fill:#fff4e1
    style Limiter fill:#fff4e1
    style IPFS fill:#fff4e1
    style Types fill:#ffe1e1
    style Codec fill:#ffe1e1
    style Hash fill:#ffe1e1
    style Merkle fill:#ffe1e1
    style Commit fill:#ffe1e1
    style Verify fill:#ffe1e1
    style PyShim fill:#e1ffe1
    style Golden fill:#f0e1ff
    style Parity fill:#f0e1ff
```

---

## Data Flow: Block Submission & Verification

```mermaid
sequenceDiagram
    participant Miner
    participant GoAPI as Go API Layer
    participant RustCore as Rust Core
    participant RateLimiter as Rate Limiter
    participant IPFS as IPFS Quorum
    participant DB as SQLite DB
    participant P2P as P2P Network

    Miner->>GoAPI: POST /submit_proof<br/>{header, reveal, proof}

    GoAPI->>RateLimiter: Check IP/PeerID limits
    alt Rate limit exceeded
        RateLimiter-->>Miner: 429 Too Many Requests
    end

    GoAPI->>GoAPI: Early syntactic checks<br/>(schema, tier, signature)
    alt Syntactic failure
        GoAPI-->>Miner: 400 Bad Request<br/>(before heavy verification)
    end

    GoAPI->>RustCore: verify_header(bytes)<br/>via CGO binding
    RustCore->>RustCore: Decode strict (deny unknown fields)
    RustCore->>RustCore: Verify commitment binding<br/>(epoch_salt, parent_hash, miner_salt)

    alt Commitment invalid
        RustCore-->>GoAPI: VerificationError::CommitmentMismatch
        GoAPI-->>Miner: 400 Invalid Commitment
    end

    RustCore->>RustCore: verify_subset_sum(proof, budget)<br/>VerifyBudget{max_ops, max_ms}

    alt Budget exceeded
        RustCore-->>GoAPI: VerificationBudgetExceeded
        GoAPI-->>Miner: 400 Proof Too Expensive
    end

    RustCore-->>GoAPI: VerifyResult::Valid

    GoAPI->>IPFS: Pin proof bundle (CID)<br/>to ≥2/3 quorum

    alt Pin quorum failed
        IPFS-->>GoAPI: QuorumNotMet
        GoAPI-->>Miner: 503 IPFS Unavailable
    end

    IPFS-->>GoAPI: Pinned CID + manifest

    GoAPI->>DB: INSERT block<br/>(header_hash, cid, verified_at)
    DB-->>GoAPI: Committed

    GoAPI->>P2P: Broadcast CID<br/>(equilibrium gossip λ=0.7071)
    P2P-->>P2P: Fan-out with backpressure

    GoAPI-->>Miner: 201 Created<br/>{block_hash, cid, height}

    Note over GoAPI,P2P: Prometheus metrics exported:<br/>- verify_duration_ms<br/>- pin_quorum_success<br/>- gossip_fan_out_count
```

---

## Consensus-Critical Type System

```mermaid
classDiagram
    class BlockHeader {
        +codec_version: u8
        +block_index: u64
        +timestamp: i64
        +parent_hash: [u8; 32]
        +merkle_root: [u8; 32]
        +miner_address: [u8; 32]
        +commitment: [u8; 32]
        +difficulty_target: u64
        +nonce: u64
        +compute_hash() [u8; 32]
    }

    class Commitment {
        +epoch_salt: [u8; 32]
        +problem_hash: [u8; 32]
        +solution_hash: [u8; 32]
        +compute() [u8; 32]
        +verify(reveal: Reveal) bool
    }

    class Reveal {
        +problem: Problem
        +solution: Solution
        +miner_salt: [u8; 32]
        +verify_binding(commitment, epoch_salt, parent_hash) bool
    }

    class Problem {
        +problem_type: ProblemType
        +tier: HardwareTier
        +elements: Vec~i64~
        +target: i64
        +compute_hash() [u8; 32]
    }

    class Solution {
        +indices: Vec~u32~
        +verify(problem: Problem) VerifyResult
    }

    class VerifyBudget {
        +max_ops: u64
        +max_duration_ms: u64
        +check() Result
    }

    class Transaction {
        +tx_type: TxType
        +from: [u8; 32]
        +to: [u8; 32]
        +amount: u64
        +nonce: u64
        +signature: [u8; 64]
        +gas_limit: u64
        +compute_hash() [u8; 32]
    }

    class MerkleTree {
        +leaves: Vec~[u8; 32]~
        +compute_root() [u8; 32]
        +prove(index: u64) MerkleProof
    }

    class CanonicalCodec {
        +encode_msgpack(T) Vec~u8~
        +encode_json(T) String
        +decode_strict(bytes) Result~T~
        +cross_path_verify(T) bool
    }

    BlockHeader --> Commitment
    BlockHeader --> MerkleTree
    Commitment --> Reveal
    Reveal --> Problem
    Reveal --> Solution
    Solution --> VerifyBudget
    MerkleTree --> Transaction
    CanonicalCodec --> BlockHeader
    CanonicalCodec --> Transaction
```

---

## Security Architecture: Defense-in-Depth

```mermaid
graph LR
    subgraph "Layer 1: Network Edge"
        A1[IP Rate Limit<br/>100 req/min]
        A2[Peer Scoring<br/>Reputation]
        A3[DDoS Detection<br/>Burst Limits]
    end

    subgraph "Layer 2: Early Reject"
        B1[Schema Validation<br/>Deny Unknown Fields]
        B2[Tier Check<br/>Element Count]
        B3[Signature Verify<br/>Ed25519]
        B4[Timestamp Window<br/>±2h max skew]
    end

    subgraph "Layer 3: Admission Control"
        C1[Epoch Replay Cache<br/>commitment, epoch TTL]
        C2[Nonce Sequence<br/>Per-Address]
        C3[Gas Estimation<br/>Pre-compute]
    end

    subgraph "Layer 4: Consensus Verification"
        D1[Commitment Binding<br/>HMAC parent_hash, epoch_salt]
        D2[Subset Sum Verify<br/>VerifyBudget max_ops, max_ms]
        D3[Merkle Root Check<br/>Deterministic]
        D4[Difficulty Target<br/>Cumulative Work]
    end

    subgraph "Layer 5: IPFS Integrity"
        E1[Pin Quorum<br/>≥2/3 nodes]
        E2[CID Audit<br/>Size/Hash Match]
        E3[Manifest Signing<br/>Provenance]
    end

    subgraph "Layer 6: State Transition"
        F1[Balance Invariants<br/>No Inflation]
        F2[Reorg Protection<br/>Max Depth 100]
        F3[State Root<br/>Post-Block]
    end

    A1 --> A2
    A2 --> A3
    A3 --> B1

    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> C1

    C1 --> C2
    C2 --> C3
    C3 --> D1

    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> E1

    E1 --> E2
    E2 --> E3
    E3 --> F1

    F1 --> F2
    F2 --> F3

    F3 --> G[Accept Block]

    A1 -.->|429| Reject1[Reject:<br/>Rate Limited]
    B1 -.->|400| Reject2[Reject:<br/>Malformed]
    C1 -.->|409| Reject3[Reject:<br/>Replay]
    D2 -.->|400| Reject4[Reject:<br/>Budget Exceeded]
    E1 -.->|503| Reject5[Reject:<br/>IPFS Unavailable]
    F1 -.->|500| Reject6[Reject:<br/>State Violation]

    style A1 fill:#ffcccc
    style A2 fill:#ffcccc
    style A3 fill:#ffcccc
    style B1 fill:#ffe6cc
    style B2 fill:#ffe6cc
    style B3 fill:#ffe6cc
    style B4 fill:#ffe6cc
    style C1 fill:#ffffcc
    style C2 fill:#ffffcc
    style C3 fill:#ffffcc
    style D1 fill:#ccffcc
    style D2 fill:#ccffcc
    style D3 fill:#ccffcc
    style D4 fill:#ccffcc
    style E1 fill:#cce6ff
    style E2 fill:#cce6ff
    style E3 fill:#cce6ff
    style F1 fill:#e6ccff
    style F2 fill:#e6ccff
    style F3 fill:#e6ccff
    style G fill:#ccffcc
```

---

## CI/CD Quality Gates Pipeline

```mermaid
graph TD
    Start[Code Push] --> Lint[Linting & Formatting<br/>black, ruff, clippy, gofmt]

    Lint --> Type[Type Checking<br/>mypy, cargo check, go vet]

    Type --> Unit[Unit Tests<br/>pytest, cargo test, go test]

    Unit --> Coverage{Coverage ≥70%<br/>new code?}
    Coverage -->|No| Fail1[❌ FAIL: Coverage]
    Coverage -->|Yes| Golden[Golden Vector Tests<br/>Frozen fixtures]

    Golden --> GoldenCheck{Hashes match<br/>frozen?}
    GoldenCheck -->|No| Fail2[❌ FAIL: Golden Drift<br/>Requires labeled PR]
    GoldenCheck -->|Yes| Determ[Determinism Matrix<br/>Py 3.10/3.11/3.12<br/>x86_64/arm64]

    Determ --> DetermCheck{All platforms<br/>identical hash?}
    DetermCheck -->|No| Fail3[❌ FAIL: Determinism]
    DetermCheck -->|Yes| Parity[Parity Test<br/>Dual-run 100 blocks]

    Parity --> ParityCheck{New hash ==<br/>Old hash?}
    ParityCheck -->|No| Fail4[❌ FAIL: Parity Drift<br/>Post diff to PR]
    ParityCheck -->|Yes| Property[Property Tests<br/>Hypothesis, quickcheck]

    Property --> Fuzz[Fuzz Tests<br/>Malformed inputs]

    Fuzz --> E2E[E2E Tests<br/>3-node simulation]

    E2E --> Security[Security Scans<br/>pip-audit, cargo audit<br/>govulncheck]

    Security --> SecurityCheck{Vulnerabilities<br/>found?}
    SecurityCheck -->|Yes| Fail5[❌ FAIL: Security<br/>CVEs detected]
    SecurityCheck -->|No| SBOM[Generate SBOM<br/>CycloneDX]

    SBOM --> Sign[Sign Artifacts<br/>Sigstore/GPG]

    Sign --> Metrics[Performance Metrics<br/>header_hash < 1ms<br/>encode_block < 10ms]

    Metrics --> MetricsCheck{Performance<br/>acceptable?}
    MetricsCheck -->|No| Fail6[❌ FAIL: Perf Regression]
    MetricsCheck -->|Yes| Success[✅ PASS: Ready to Merge]

    Success --> Deploy{Main branch?}
    Deploy -->|Yes| Release[Create Release<br/>Attach SBOMs<br/>Sign artifacts]
    Deploy -->|No| End[End]

    Release --> End

    style Start fill:#e1f5ff
    style Success fill:#ccffcc
    style Release fill:#ccffcc
    style Fail1 fill:#ffcccc
    style Fail2 fill:#ffcccc
    style Fail3 fill:#ffcccc
    style Fail4 fill:#ffcccc
    style Fail5 fill:#ffcccc
    style Fail6 fill:#ffcccc
    style Golden fill:#ffffcc
    style Determ fill:#ffffcc
    style Parity fill:#ffffcc
```

---

## Rust-Python-Go Binding Architecture

```mermaid
graph TB
    subgraph "Python Application Layer"
        PyApp[Python Application<br/>src/cli.py<br/>src/node.py]
        PyShim[Compatibility Shims<br/>legacy_compat.py]
        PyTypes[Type Definitions<br/>types.py<br/>frozen dataclasses]
    end

    subgraph "PyO3 Binding Layer"
        PyO3Mod[coinjecture_core module<br/>Rust → Python]
        PyO3Fn1[compute_header_hash bytes → bytes]
        PyO3Fn2[encode_block dict → bytes]
        PyO3Fn3[verify_subset_sum dict, budget → Result]
        PyO3Fn4[compute_merkle_root List bytes → bytes]
    end

    subgraph "Rust Core Library"
        RustLib[libcoinjecture_core.a<br/>Static Library]
        RustTypes[types.rs<br/>repr-C structs]
        RustCodec[codec.rs<br/>msgpack + JSON]
        RustVerify[verify.rs<br/>Budget-limited]
    end

    subgraph "C Header Layer"
        CHeader[coinjecture_core.h<br/>cbindgen generated]
        CFunc1[cjc_compute_header_hash]
        CFunc2[cjc_encode_block]
        CFunc3[cjc_verify_subset_sum]
    end

    subgraph "Go CGO Binding Layer"
        CGOWrapper[pkg/bindings/core.go<br/>/*#include coinjecture_core.h*/]
        GoFunc1[ComputeHeaderHash]
        GoFunc2[EncodeBlock]
        GoFunc3[VerifySubsetSum]
    end

    subgraph "Go Application Layer"
        GoAPI[REST API Server<br/>cmd/coinjectured]
        GoP2P[P2P Network<br/>pkg/p2p]
        GoLimiter[Rate Limiter<br/>pkg/limiter]
    end

    PyApp --> PyShim
    PyShim --> PyO3Mod
    PyTypes --> PyO3Mod

    PyO3Mod --> PyO3Fn1
    PyO3Mod --> PyO3Fn2
    PyO3Mod --> PyO3Fn3
    PyO3Mod --> PyO3Fn4

    PyO3Fn1 --> RustLib
    PyO3Fn2 --> RustLib
    PyO3Fn3 --> RustLib
    PyO3Fn4 --> RustLib

    RustLib --> RustTypes
    RustLib --> RustCodec
    RustLib --> RustVerify

    RustLib --> CHeader
    CHeader --> CFunc1
    CHeader --> CFunc2
    CHeader --> CFunc3

    CFunc1 --> CGOWrapper
    CFunc2 --> CGOWrapper
    CFunc3 --> CGOWrapper

    CGOWrapper --> GoFunc1
    CGOWrapper --> GoFunc2
    CGOWrapper --> GoFunc3

    GoFunc1 --> GoAPI
    GoFunc2 --> GoAPI
    GoFunc3 --> GoAPI

    GoAPI --> GoP2P
    GoAPI --> GoLimiter

    style PyApp fill:#e1ffe1
    style PyO3Mod fill:#e1ffe1
    style RustLib fill:#ffe1e1
    style CHeader fill:#fff4e1
    style CGOWrapper fill:#fff4e1
    style GoAPI fill:#fff4e1
```

---

## Feature Flag & Cutover Strategy

```mermaid
stateDiagram-v2
    [*] --> LegacyOnly: Initial State

    LegacyOnly --> DualRun: Deploy Rust+Go<br/>CODEC_MODE=legacy_only

    state DualRun {
        [*] --> ValidateLegacy
        ValidateLegacy --> ValidateRefactored: Compute with both
        ValidateRefactored --> LogParity: Compare hashes
        LogParity --> RecordMetrics: Prometheus counters
        RecordMetrics --> [*]
    }

    DualRun --> ParityVerified: 1000+ blocks<br/>100% parity

    ParityVerified --> ShadowMode: CODEC_MODE=shadow<br/>Log diffs, no reject

    state ShadowMode {
        [*] --> UseLegacy
        UseLegacy --> ComputeRefactored: Primary path
        ComputeRefactored --> CompareResults
        CompareResults --> AlertOnDrift: If hash mismatch
        AlertOnDrift --> [*]
    }

    ShadowMode --> RefactoredPrimary: 7 days soak<br/>No drift alerts

    RefactoredPrimary --> CODEC_MODE=refactored_primary

    state RefactoredPrimary {
        [*] --> UseRefactored
        UseRefactored --> FallbackLegacy: On verification error
        FallbackLegacy --> LogFallback
        LogFallback --> [*]
    }

    RefactoredPrimary --> RefactoredOnly: 30 days stable<br/>Zero fallbacks

    RefactoredOnly --> [*]: CODEC_MODE=refactored_only<br/>Remove legacy code

    note right of DualRun
        Parity metrics:
        - parity_match_total
        - parity_drift_total
        - legacy_duration_ms
        - refactored_duration_ms
    end note

    note right of ShadowMode
        Shadow alerts:
        - Slack notification
        - PagerDuty if >1%
        - Auto-rollback trigger
    end note

    note right of RefactoredPrimary
        Fallback triggers:
        - VerificationError
        - BudgetExceeded
        - CodecDecodeFailed
    end note
```

---

## IPFS Pinning Quorum & CID Audit

```mermaid
sequenceDiagram
    participant Miner
    participant API as Go API
    participant PinMgr as Pin Manager
    participant IPFS1 as IPFS Node 1
    participant IPFS2 as IPFS Node 2
    participant IPFS3 as IPFS Node 3
    participant Audit as CID Audit Job
    participant DB as SQLite

    Miner->>API: Submit proof bundle
    API->>PinMgr: Pin CID to quorum

    par Pin to multiple nodes
        PinMgr->>IPFS1: POST /api/v0/pin/add<br/>CID=Qm...
        PinMgr->>IPFS2: POST /api/v0/pin/add<br/>CID=Qm...
        PinMgr->>IPFS3: POST /api/v0/pin/add<br/>CID=Qm...
    end

    IPFS1-->>PinMgr: Pinned (size: 1.2KB)
    IPFS2-->>PinMgr: Pinned (size: 1.2KB)
    IPFS3-->>PinMgr: Timeout

    PinMgr->>PinMgr: Count successes: 2/3

    alt Quorum met (≥2/3)
        PinMgr->>PinMgr: Generate manifest<br/>{cid, size, nodes, timestamp}
        PinMgr->>DB: Store manifest
        PinMgr-->>API: QuorumSuccess
        API-->>Miner: 201 Created
    else Quorum failed (<2/3)
        PinMgr-->>API: QuorumNotMet
        API-->>Miner: 503 IPFS Unavailable
    end

    Note over Audit: Periodic CID Audit Job<br/>(every 6 hours)

    Audit->>DB: SELECT cid, block_hash<br/>FROM blocks<br/>WHERE created_at > NOW() - 7d
    DB-->>Audit: 1000 CIDs

    loop For each CID
        Audit->>IPFS1: GET /api/v0/block/stat?arg=CID

        alt CID exists
            IPFS1-->>Audit: {Size: 1234}
            Audit->>Audit: Verify size matches manifest

            alt Size mismatch
                Audit->>Audit: Log integrity violation
                Audit->>PinMgr: Re-pin from source
            end
        else CID missing
            Audit->>Audit: Log missing CID
            Audit->>PinMgr: Trigger recovery<br/>(re-compute from block)
        end
    end

    Audit->>DB: UPDATE cid_audit_log<br/>SET last_audit = NOW()

    Audit->>Audit: Export metrics:<br/>- cid_missing_total<br/>- cid_size_mismatch_total<br/>- cid_audit_duration_ms
```

---

## Deployment & Rollback Procedures

```mermaid
graph TB
    Start[Release Candidate] --> PreCheck{Pre-flight checks<br/>✓ All tests pass<br/>✓ SBOM generated<br/>✓ Artifacts signed}

    PreCheck -->|Fail| Abort[❌ Abort Release]
    PreCheck -->|Pass| Stage1[Stage 1: Canary<br/>Deploy to 1 node<br/>10% traffic]

    Stage1 --> Soak1[Soak: 2 hours]

    Soak1 --> Monitor1{Metrics OK?<br/>- Error rate <0.1%<br/>- p95 latency <2x<br/>- No panics}

    Monitor1 -->|Fail| Rollback1[Rollback Canary<br/>Restore previous binary]
    Monitor1 -->|Pass| Stage2[Stage 2: Gradual<br/>Deploy to 25% nodes]

    Stage2 --> Soak2[Soak: 6 hours]

    Soak2 --> Monitor2{Metrics OK?<br/>- Parity 100%<br/>- CID quorum >95%<br/>- Zero state violations}

    Monitor2 -->|Fail| Rollback2[Rollback 25%<br/>Feature flag: legacy_only]
    Monitor2 -->|Pass| Stage3[Stage 3: Majority<br/>Deploy to 75% nodes]

    Stage3 --> Soak3[Soak: 24 hours]

    Soak3 --> Monitor3{Final checks?<br/>- No drift alerts<br/>- Performance improved<br/>- User reports OK}

    Monitor3 -->|Fail| Rollback3[Rollback All<br/>Incident review]
    Monitor3 -->|Pass| Stage4[Stage 4: Full<br/>Deploy to 100%]

    Stage4 --> PostDeploy[Post-Deploy Tasks]

    PostDeploy --> Task1[Update docs<br/>CHANGELOG.md]
    PostDeploy --> Task2[Archive old binaries<br/>S3 cold storage]
    PostDeploy --> Task3[Send release notes<br/>to community]

    Task1 --> Success[✅ Deployment Complete]
    Task2 --> Success
    Task3 --> Success

    Rollback1 --> Incident[Incident Review]
    Rollback2 --> Incident
    Rollback3 --> Incident

    Incident --> RootCause[Root Cause Analysis]
    RootCause --> Hotfix{Hotfix<br/>possible?}

    Hotfix -->|Yes| HotfixPR[Create Hotfix PR<br/>Fast-track review]
    Hotfix -->|No| ScheduleFix[Schedule for<br/>next release]

    HotfixPR --> Start
    ScheduleFix --> End[End]
    Success --> End

    style Start fill:#e1f5ff
    style Success fill:#ccffcc
    style Abort fill:#ffcccc
    style Rollback1 fill:#ffcccc
    style Rollback2 fill:#ffcccc
    style Rollback3 fill:#ffcccc
    style Stage1 fill:#ffffcc
    style Stage2 fill:#ffffcc
    style Stage3 fill:#ffffcc
    style Stage4 fill:#ffffcc
```

---

## Repository Structure

```
COINjecture1337-REFACTOR/
│
├── rust/
│   └── coinjecture-core/
│       ├── Cargo.toml                      # Dependencies, features, metadata
│       ├── Cargo.lock                      # Pinned dependency versions
│       ├── src/
│       │   ├── lib.rs                      # Crate root, module exports
│       │   ├── types.rs                    # repr(C) structs, enums
│       │   ├── codec.rs                    # Canonical msgpack + JSON codec
│       │   ├── hash.rs                     # SHA-256 hashing engine
│       │   ├── merkle.rs                   # Deterministic Merkle trees
│       │   ├── commitment.rs               # HMAC commitment binding
│       │   ├── verify.rs                   # Subset sum with budget limits
│       │   ├── errors.rs                   # Typed error enums (no panics)
│       │   └── python.rs                   # PyO3 bindings module
│       ├── tests/
│       │   ├── golden_tests.rs             # Golden vector validation
│       │   ├── determinism_tests.rs        # Cross-platform matrix
│       │   ├── codec_tests.rs              # Strict decode, equivalence
│       │   └── property_tests.rs           # quickcheck properties
│       ├── benches/
│       │   └── benchmarks.rs               # Criterion.rs benchmarks
│       └── golden/
│           ├── genesis.json                # Genesis block fixture
│           ├── headers.json                # Header test vectors
│           ├── transactions.json           # Transaction fixtures
│           └── merkle.json                 # Merkle tree vectors
│
├── go/
│   ├── go.mod                              # Go module definition
│   ├── go.sum                              # Dependency checksums
│   ├── cmd/
│   │   └── coinjectured/
│   │       └── main.go                     # Daemon entry point
│   ├── pkg/
│   │   ├── api/
│   │   │   ├── server.go                   # Gin/Fiber HTTP server
│   │   │   ├── handlers.go                 # Endpoint handlers
│   │   │   └── middleware.go               # CORS, auth, logging
│   │   ├── p2p/
│   │   │   ├── network.go                  # Equilibrium gossip
│   │   │   ├── peer_scoring.go             # Reputation system
│   │   │   └── backpressure.go             # Flow control
│   │   ├── limiter/
│   │   │   ├── rate_limiter.go             # Token bucket implementation
│   │   │   ├── ip_limiter.go               # IP-based limits
│   │   │   └── peer_limiter.go             # Peer-ID limits
│   │   ├── ipfs/
│   │   │   ├── client.go                   # IPFS API client
│   │   │   ├── quorum.go                   # Pin quorum logic
│   │   │   ├── audit.go                    # CID audit job
│   │   │   └── manifest.go                 # Manifest generation
│   │   ├── metrics/
│   │   │   ├── exporter.go                 # Prometheus exporter
│   │   │   └── slo.go                      # SLO definitions
│   │   ├── bindings/
│   │   │   └── core.go                     # CGO wrapper to Rust
│   │   └── config/
│   │       └── config.go                   # Configuration structs
│   ├── internal/
│   │   └── logger/
│   │       └── logger.go                   # Structured logging
│   └── scripts/
│       ├── build.sh                        # Build script
│       └── deploy.sh                       # Deployment script
│
├── python/
│   └── src/
│       └── coinjecture/
│           ├── __init__.py                 # Package init, BC shims
│           ├── types.py                    # Frozen dataclasses
│           ├── consensus/
│           │   ├── codec.py                # Delegates to Rust
│           │   └── admission.py            # Epoch replay, nonce checks
│           ├── proofs/
│           │   ├── interface.py            # Solver ABC
│           │   └── limits.py               # Tier validation
│           └── legacy_compat.py            # Dual-run validator
│
├── .github/
│   └── workflows/
│       ├── ci.yml                          # Main CI pipeline
│       ├── determinism.yml                 # Cross-platform matrix
│       ├── parity.yml                      # Dual-run validation
│       └── security.yml                    # Audits + SBOM generation
│
├── docs/
│   ├── REFACTOR_ARCHITECTURE.md            # This document
│   ├── CODEOWNERS                          # Code owner assignments
│   ├── RUNBOOKS.md                         # Operational runbooks
│   ├── SLO.md                              # Service level objectives
│   └── RELEASE_POLICY.md                   # Release procedures
│
├── scripts/
│   ├── generate_golden.py                  # Generate golden vectors
│   ├── run_parity_test.sh                  # Dual-run test harness
│   ├── rollout.sh                          # Gradual rollout script
│   └── rollback.sh                         # Emergency rollback
│
├── SECURITY_AUDIT.md                       # Security findings & mitigations
├── CHANGELOG.md                            # Version history
└── README.md                               # Project overview
```

---

## Success Metrics & SLOs

| Metric | Target | Measurement | Alert Threshold |
|--------|--------|-------------|-----------------|
| **Determinism** | 100% hash parity across platforms | Golden vector tests | Any divergence |
| **Parity** | 100% legacy vs refactored match | Dual-run validation | >0.1% drift |
| **Performance** | `compute_header_hash` < 1ms | Criterion benchmarks | >2ms p95 |
| **Performance** | `encode_block` < 10ms | Criterion benchmarks | >20ms p95 |
| **Performance** | `merkle(1k tx)` < 50ms | Criterion benchmarks | >100ms p95 |
| **Verification** | p95 within tier budgets | Prometheus metrics | >1.5x budget |
| **API Rate Limit** | <2% 429s for legit peers | HTTP response codes | >5% 429s |
| **IPFS Quorum** | >95% pin success | Pin manager metrics | <90% success |
| **CID Integrity** | <1% missing/mismatch | Audit job metrics | >5% missing |
| **Test Coverage** | ≥70% new code, ≥50% overall | `cargo tarpaulin`, `go test -cover` | Below threshold |
| **API Uptime** | 99.5% | Health check endpoint | <99% over 7d |
| **Consensus** | Zero state violations | Invariant checks | Any violation |

---

## Institutional Compliance Checklist

- [ ] **Determinism**: Canonical serialization, field order, strict decode
- [ ] **Reproducible Builds**: Lockfiles, pinned deps, artifact signing
- [ ] **Change Control**: CODEOWNERS, labeled PR for golden changes, code review
- [ ] **Defense-in-Depth**: 6 security layers (network → state transition)
- [ ] **Separation of Concerns**: Rust (pure), Go (operational), Python (glue)
- [ ] **Observability**: Prometheus metrics, SLOs, structured logs
- [ ] **Runbooks**: Rollout, rollback, incident response, soak tests
- [ ] **Compliance**: SBOMs (CycloneDX), security audits, signed releases
- [ ] **Testing**: Golden, property, fuzz, E2E, parity, determinism
- [ ] **Zero Drift**: Feature flags, dual-run, gradual cutover

---

**Document Status:** Living Architecture Document
**Next Review:** Post-Phase 1 Implementation
**Owner:** Multi-Agent Refactor Lead (Claude)
