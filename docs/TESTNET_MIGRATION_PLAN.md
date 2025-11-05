# Live Testnet Migration: Legacy Python → v4.0.0 Rust Core

**Current State**: 2 DigitalOcean nodes running LEGACY Python consensus
**Target State**: Same 2 nodes using NEW Rust consensus core
**Constraint**: ZERO downtime, no chain fork

---

## Current Testnet Architecture

```
Node 1 (DigitalOcean)          Node 2 (DigitalOcean)
├─ src/node.py                 ├─ src/node.py
├─ src/consensus.py (OLD)      ├─ src/consensus.py (OLD)
├─ src/network.py (libp2p)     ├─ src/network.py (libp2p)
├─ src/storage.py (SQLite)     ├─ src/storage.py (SQLite)
├─ src/pow.py (mining)         ├─ src/pow.py (mining)
└─ Multiple users connected    └─ Multiple users connected

Status: ✅ LIVE and WORKING
Chain: Active with real blocks
Users: Multiple active users
```

---

## Migration Strategy: Phased Cutover

### Phase 1: Shadow Mode (Week 1-2)
**Goal**: Run both old and new consensus, compare outputs

```python
# src/consensus_wrapper.py (NEW FILE)

from enum import Enum
from typing import Optional
import logging

class ConsensusMode(Enum):
    LEGACY_ONLY = "legacy"      # Use old Python consensus only
    SHADOW = "shadow"           # Run both, use legacy, log diffs
    REFACTORED_PRIMARY = "rust" # Use Rust, fallback to legacy on error
    REFACTORED_ONLY = "final"   # Use Rust only, remove legacy

class DualRunConsensus:
    """
    Wrapper that runs both legacy and Rust consensus for migration.

    Modes:
    1. LEGACY_ONLY - Current production (safe)
    2. SHADOW - Run both, compare, use legacy (validates Rust)
    3. REFACTORED_PRIMARY - Use Rust, fallback to legacy (test Rust in prod)
    4. REFACTORED_ONLY - Remove legacy (final state)
    """

    def __init__(self, mode: ConsensusMode = ConsensusMode.LEGACY_ONLY):
        self.mode = mode
        self.logger = logging.getLogger("DualRunConsensus")

        # Legacy consensus (always loaded in shadow/legacy modes)
        from .consensus import ConsensusEngine as LegacyConsensus
        self.legacy = LegacyConsensus(...)

        # Rust consensus (loaded when mode != LEGACY_ONLY)
        if mode != ConsensusMode.LEGACY_ONLY:
            from coinjecture._core import (
                sha256_hash,
                compute_header_hash_py,
                verify_subset_sum_py
            )
            self.rust_sha256 = sha256_hash
            self.rust_header_hash = compute_header_hash_py
            self.rust_verify = verify_subset_sum_py

    def verify_block(self, block):
        """Verify block with appropriate consensus mode."""

        if self.mode == ConsensusMode.LEGACY_ONLY:
            # Current production behavior
            return self.legacy.verify_block(block)

        elif self.mode == ConsensusMode.SHADOW:
            # Run BOTH, use legacy result, log differences
            legacy_result = self.legacy.verify_block(block)
            rust_result = self._rust_verify_block(block)

            if legacy_result != rust_result:
                self.logger.error(
                    f"CONSENSUS DIVERGENCE! Block {block.index}: "
                    f"Legacy={legacy_result}, Rust={rust_result}"
                )
                # Alert to monitoring system
                self._alert_divergence(block, legacy_result, rust_result)

            # ALWAYS return legacy result (safe)
            return legacy_result

        elif self.mode == ConsensusMode.REFACTORED_PRIMARY:
            # Try Rust first, fallback to legacy on error
            try:
                rust_result = self._rust_verify_block(block)

                # Also run legacy for comparison
                legacy_result = self.legacy.verify_block(block)
                if legacy_result != rust_result:
                    self.logger.warning(
                        f"Divergence detected, using Rust result: {rust_result}"
                    )

                return rust_result
            except Exception as e:
                self.logger.error(f"Rust consensus failed, using legacy: {e}")
                return self.legacy.verify_block(block)

        elif self.mode == ConsensusMode.REFACTORED_ONLY:
            # Rust only, no fallback
            return self._rust_verify_block(block)

    def _rust_verify_block(self, block):
        """Verify block using Rust consensus."""
        # Delegate to Rust
        # TODO: Implement full Rust delegation
        pass

    def _alert_divergence(self, block, legacy, rust):
        """Send alert when consensus diverges (critical bug)."""
        # TODO: Integrate with monitoring (Sentry, Datadog, etc.)
        pass
```

**Deployment**:
1. Deploy shadow mode to Node 1
2. Monitor for 48 hours
3. If no divergences, deploy to Node 2
4. Run for 1 week

**Success Criteria**: Zero divergences between legacy and Rust

---

### Phase 2: Rust Primary (Week 3)
**Goal**: Use Rust consensus, keep legacy as safety fallback

**Changes**:
```python
# Update node.py to use DualRunConsensus
from consensus_wrapper import DualRunConsensus, ConsensusMode

# In Node.__init__()
self.consensus = DualRunConsensus(
    mode=ConsensusMode.REFACTORED_PRIMARY  # Rust first, legacy fallback
)
```

**Deployment**:
1. Deploy to Node 1
2. Monitor for 24 hours
3. If stable, deploy to Node 2
4. Run for 1 week

**Success Criteria**:
- No Rust errors
- Performance better or equal to legacy
- All blocks verified successfully

---

### Phase 3: Rust Only (Week 4)
**Goal**: Remove legacy consensus entirely

**Changes**:
```python
# Update to REFACTORED_ONLY mode
self.consensus = DualRunConsensus(
    mode=ConsensusMode.REFACTORED_ONLY
)

# OR replace with direct Rust usage
from coinjecture._core import (
    sha256_hash,
    compute_header_hash_py,
    verify_subset_sum_py
)
# Remove legacy consensus.py imports
```

**Deployment**:
1. Deploy to Node 1
2. Monitor for 72 hours
3. Deploy to Node 2
4. Declare v4.0.0 migration complete

**Success Criteria**:
- Testnet runs smoothly on Rust only
- No legacy code running
- Performance improved (Rust is faster)

---

## Rollback Strategy

### If Divergence Detected (Phase 1)
1. Keep running in SHADOW mode
2. Investigate divergence (compare block hashes)
3. Fix Rust implementation
4. Redeploy and restart Phase 1

### If Rust Errors (Phase 2)
1. Automatic fallback to legacy (built into REFACTORED_PRIMARY mode)
2. Investigate error
3. Fix Rust implementation
4. Redeploy

### If Critical Issue (Phase 3)
1. Immediate rollback to REFACTORED_PRIMARY mode
2. Restart nodes with legacy fallback enabled
3. Investigate
4. Fix and re-attempt Phase 3

---

## Implementation Checklist

### Pre-Migration (This Week)
- [ ] Create `src/consensus_wrapper.py` with DualRunConsensus
- [ ] Build Rust extension on DigitalOcean nodes (`maturin develop`)
- [ ] Add monitoring/alerting for divergences
- [ ] Test shadow mode locally
- [ ] Document rollback procedures

### Phase 1: Shadow Mode (Week 1-2)
- [ ] Deploy DualRunConsensus to Node 1 (SHADOW mode)
- [ ] Monitor for divergences (48 hours)
- [ ] If clean, deploy to Node 2
- [ ] Run for 1 week
- [ ] Review metrics: divergence count = 0?

### Phase 2: Rust Primary (Week 3)
- [ ] Switch Node 1 to REFACTORED_PRIMARY mode
- [ ] Monitor for errors (24 hours)
- [ ] If stable, switch Node 2
- [ ] Run for 1 week
- [ ] Review metrics: error rate = 0?

### Phase 3: Rust Only (Week 4)
- [ ] Switch Node 1 to REFACTORED_ONLY mode
- [ ] Monitor (72 hours)
- [ ] Switch Node 2 to REFACTORED_ONLY mode
- [ ] Remove legacy consensus code
- [ ] Declare v4.0.0 complete

---

## Monitoring & Metrics

### Critical Metrics
```
consensus_divergence_count (Phase 1)
  Alert if > 0

rust_consensus_errors (Phase 2-3)
  Alert if > 0.1% of blocks

rust_consensus_latency_ms (Phase 2-3)
  Alert if > legacy baseline

block_verification_success_rate (All phases)
  Alert if < 100%
```

### Logs to Watch
```
ERROR: CONSENSUS DIVERGENCE
WARNING: Rust consensus failed, using legacy
ERROR: Rust verification error
```

### Grafana Dashboard
- Consensus mode (legacy/shadow/rust/final)
- Divergence count over time
- Rust vs legacy latency comparison
- Error rates by phase

---

## Code Migration After Testnet

Once testnet is running on Rust consensus:

### Replace in src/
```
src/consensus.py         → DELETE (legacy Python)
src/consensus_wrapper.py → KEEP (for future migrations)
src/node.py              → UPDATE (use Rust directly)
src/pow.py               → MIGRATE to Rust (Phase 5)
src/network.py           → KEEP (libp2p works fine)
src/storage.py           → KEEP (SQLite works fine)
```

### Add to python/
```
python/src/coinjecture/consensus.py (NEW)
  └─ High-level Python API that delegates to Rust
```

---

## Timeline

| Week | Phase | Action | Risk |
|------|-------|--------|------|
| 1-2  | Shadow | Deploy dual-run mode | LOW - No behavior change |
| 3    | Primary | Switch to Rust-first | MEDIUM - New code path |
| 4    | Only | Remove legacy | HIGH - No fallback |

**Total**: 4 weeks to complete migration

---

## Success Criteria

✅ **Migration Complete When**:
1. Both DigitalOcean nodes running Rust consensus
2. Zero divergences from legacy behavior
3. Zero Rust errors in production
4. Performance equal or better than legacy
5. All users migrated seamlessly (no downtime)
6. Legacy consensus.py can be deleted

---

## Current Blocker

❌ **`src/consensus_wrapper.py` does not exist yet**

This is the critical missing piece for live migration. Without it, you risk:
- Breaking the live testnet
- Forking the chain
- Losing user data

**Next Step**: Create the wrapper and test in shadow mode locally before touching DigitalOcean nodes.

---

## Questions to Answer

1. **Do both DigitalOcean nodes have Rust toolchain installed?**
   - Need to build `coinjecture._core` extension

2. **Can you afford 1-2 hours of downtime per node?**
   - For Rust extension build + deployment

3. **Do you have monitoring/alerting set up?**
   - Need to catch divergences immediately

4. **What's the rollback procedure if something breaks?**
   - Can you redeploy previous code quickly?

5. **Are there any critical users who need advance notice?**
   - Testnet might have slight latency changes
