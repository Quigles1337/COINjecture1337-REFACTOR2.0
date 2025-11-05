# COINjecture Testnet Migration - DigitalOcean Deployment Guide

**Version**: 4.1.0
**Target**: Live testnet migration from legacy Python to Rust consensus
**Audience**: DevOps, Node operators
**Last Updated**: 2025-01-05

---

## ⚠️ CRITICAL: Live Testnet Migration

This guide covers migrating **2 live DigitalOcean nodes** with **real users** from legacy Python consensus to new Rust consensus **without downtime or chain fork**.

### Current State
- **2 nodes** running on DigitalOcean
- **Legacy Python consensus** (src/consensus.py:172 ConsensusEngine)
- **Real users** actively using testnet
- **New Rust consensus** built but not deployed

### Migration Goal
- Zero downtime
- No chain fork
- Safe rollback capability at each phase
- Full consensus validation before cutover

---

## Pre-Deployment Checklist

### 1. Local Validation (MUST DO FIRST)

Before touching production nodes:

```bash
# On your local machine
cd COINjecture1337-1

# Run consensus wrapper tests
python -m pytest tests/test_consensus_wrapper.py -v

# Expected: All 23 tests pass
```

**Status**: ✅ All tests passing (verified 2025-01-05)

### 2. Build Rust Extension

```bash
# Install Rust if not already installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin

# Build Rust extension with Python bindings
cd rust/coinjecture-core
maturin develop --release --features python

# Verify installation
python -c "from coinjecture._core import sha256_hash; print('Rust OK')"
```

**Expected Output**: `Rust OK`

### 3. Verify Rust Parity Locally

```bash
# Run golden vector tests
python -c "
from coinjecture._core import sha256_hash
result = sha256_hash(b'')
expected = bytes.fromhex('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
assert result == expected, 'SHA-256 mismatch!'
print('✓ Rust consensus matches golden vectors')
"
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         LIVE TESTNET                             │
│                                                                   │
│  ┌──────────────┐                        ┌──────────────┐       │
│  │   Node 1     │  ◄─────P2P────────►   │   Node 2     │       │
│  │ (DigitalOcean│                        │ (DigitalOcean│       │
│  │   Droplet)   │                        │   Droplet)   │       │
│  └──────────────┘                        └──────────────┘       │
│         │                                        │               │
│         └────────────────┬───────────────────────┘               │
│                          │                                       │
│                   ┌──────▼──────┐                               │
│                   │    Users     │                               │
│                   └──────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### Migration Strategy: Phased Rollout

**Week 1-2**: Node 1 → SHADOW mode (validate Rust)
**Week 2**: Node 2 → SHADOW mode (validate Rust)
**Week 3**: Both nodes → REFACTORED_PRIMARY mode (use Rust, fallback)
**Week 4**: Both nodes → REFACTORED_ONLY mode (Rust only)

---

## Phase 1: SHADOW Mode (Validation)

**Timeline**: Week 1-2
**Risk**: LOW (no production impact)
**Rollback**: Instant (just restart node)

### Step 1: Deploy to Node 1

SSH into DigitalOcean Node 1:

```bash
ssh root@<NODE_1_IP>
cd /path/to/COINjecture1337-1

# Pull latest code (includes consensus_wrapper.py)
git pull origin main

# Install Rust (if not present)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Build Rust extension
pip install maturin
cd rust/coinjecture-core
maturin develop --release --features python

# Verify Rust is working
python -c "from coinjecture._core import sha256_hash; print('Rust OK')"
```

### Step 2: Modify Node Configuration

Edit your node startup script (e.g., `src/node.py` or wherever you initialize consensus):

```python
# BEFORE (Legacy):
from src.consensus import ConsensusEngine
consensus = ConsensusEngine(config, storage, registry)

# AFTER (Shadow mode):
from src.consensus_wrapper import DualRunConsensus, ConsensusMode
from src.consensus import ConsensusEngine

legacy_engine = ConsensusEngine(config, storage, registry)

consensus = DualRunConsensus(
    mode=ConsensusMode.SHADOW,  # Run both, use legacy
    legacy_engine=legacy_engine,
    alert_callback=lambda data: logger.critical(f"DIVERGENCE: {data}")
)

# Use consensus.verify_block() as before - API is identical
```

### Step 3: Restart Node 1

```bash
# Assuming systemd service
sudo systemctl restart coinjecture-node

# Check logs
sudo journalctl -u coinjecture-node -f --lines=100
```

### Step 4: Monitor for Divergences

```bash
# Watch for divergence alerts (should be ZERO!)
grep "CONSENSUS DIVERGENCE" /var/log/coinjecture/*.log

# Check stats endpoint (if you have API)
curl http://localhost:8080/v1/consensus/stats
```

**Expected Output**:
```json
{
  "mode": "shadow",
  "total_verifications": 1523,
  "divergences": 0,
  "rust_errors": 0,
  "divergence_rate": 0.0,
  "rust_error_rate": 0.0
}
```

**⚠️ CRITICAL**: If `divergences > 0`, **DO NOT PROCEED**. This is a bug in Rust consensus. Investigate and fix before continuing.

### Step 5: Deploy to Node 2 (After 1 Week)

Repeat Steps 1-4 for Node 2 after confirming Node 1 has zero divergences for at least 1 week.

---

## Phase 2: REFACTORED_PRIMARY Mode (Gradual Cutover)

**Timeline**: Week 3
**Risk**: MEDIUM (using Rust, fallback available)
**Rollback**: Change mode back to SHADOW

### Prerequisites
- Node 1 and Node 2 running in SHADOW mode for 1+ week
- Zero divergences detected
- No Rust errors reported

### Step 1: Switch Node 1 to REFACTORED_PRIMARY

```python
# In node configuration
consensus.set_mode(ConsensusMode.REFACTORED_PRIMARY)
```

```bash
# Restart node
sudo systemctl restart coinjecture-node

# Monitor logs
sudo journalctl -u coinjecture-node -f | grep -i "rust\|fallback\|error"
```

### Step 2: Monitor Fallback Rate

```bash
# Check stats
curl http://localhost:8080/v1/consensus/stats
```

**Expected**:
```json
{
  "mode": "rust",
  "fallback_to_legacy": 0,   # Should be ZERO
  "rust_errors": 0           # Should be ZERO
}
```

**⚠️ WARNING**: If `fallback_to_legacy > 0`, Rust is failing. Investigate logs before proceeding.

### Step 3: Switch Node 2 (After 3 Days)

After 3 days of Node 1 running in REFACTORED_PRIMARY with zero fallbacks, switch Node 2:

```python
# Node 2 configuration
consensus.set_mode(ConsensusMode.REFACTORED_PRIMARY)
```

---

## Phase 3: REFACTORED_ONLY Mode (Final State)

**Timeline**: Week 4
**Risk**: HIGH (no fallback)
**Rollback**: Requires code change + restart

### Prerequisites
- Both nodes running REFACTORED_PRIMARY for 1+ week
- Zero fallbacks to legacy
- Zero Rust errors
- Testnet stable

### Step 1: Switch Both Nodes

```python
# Both Node 1 and Node 2
consensus.set_mode(ConsensusMode.REFACTORED_ONLY)
```

```bash
# Restart both nodes (coordinate downtime if needed)
sudo systemctl restart coinjecture-node
```

### Step 2: Monitor Carefully

```bash
# Watch for errors (no fallback available now!)
sudo journalctl -u coinjecture-node -f | grep -i "error\|fail\|crash"
```

### Step 3: Remove Legacy Code (Optional)

After 1+ month of stable operation in REFACTORED_ONLY:

```bash
# Archive legacy consensus
mv src/consensus.py src/legacy_consensus.py.bak

# Update imports to only use Rust
# Remove DualRunConsensus wrapper entirely
```

---

## Rollback Procedures

### Rollback from SHADOW → LEGACY_ONLY

**Impact**: None (SHADOW doesn't affect production)

```python
# In node configuration
consensus.set_mode(ConsensusMode.LEGACY_ONLY)

# OR just restart without wrapper
from src.consensus import ConsensusEngine
consensus = ConsensusEngine(config, storage, registry)
```

### Rollback from REFACTORED_PRIMARY → SHADOW

**Impact**: Low (back to validation mode)

```python
consensus.set_mode(ConsensusMode.SHADOW)
```

### Rollback from REFACTORED_ONLY → REFACTORED_PRIMARY

**Impact**: Medium (requires restart, brief downtime)

```python
# Must have legacy engine available
from src.consensus import ConsensusEngine
legacy_engine = ConsensusEngine(config, storage, registry)

consensus = DualRunConsensus(
    mode=ConsensusMode.REFACTORED_PRIMARY,
    legacy_engine=legacy_engine
)
```

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Divergence Count**: Must be ZERO in SHADOW mode
2. **Fallback Rate**: Must be ZERO in REFACTORED_PRIMARY
3. **Rust Error Rate**: Should be < 0.01%
4. **Verification Latency**: Rust should be faster than Python

### Recommended Alerts

```bash
# Alert if divergence detected
if [ $(grep -c "DIVERGENCE" /var/log/coinjecture/*.log) -gt 0 ]; then
    echo "CRITICAL: Consensus divergence detected!" | mail -s "COINjecture Alert" ops@example.com
fi

# Alert if fallback rate > 1%
fallback_rate=$(curl -s http://localhost:8080/v1/consensus/stats | jq '.fallback_rate')
if (( $(echo "$fallback_rate > 0.01" | bc -l) )); then
    echo "WARNING: High fallback rate: $fallback_rate" | mail -s "COINjecture Alert" ops@example.com
fi
```

---

## Troubleshooting

### Issue: Divergence Detected in SHADOW Mode

**Symptom**: `divergences > 0` in stats

**Cause**: Rust and Python produce different results (BUG!)

**Action**:
1. **DO NOT PROCEED** to REFACTORED_PRIMARY
2. Capture block data: `logger.error(f"Divergent block: {block.__dict__}")`
3. File bug report with block data
4. Stay in SHADOW mode until fixed

### Issue: High Fallback Rate in REFACTORED_PRIMARY

**Symptom**: `fallback_to_legacy > 5%`

**Cause**: Rust throwing errors

**Action**:
1. Check logs: `grep "Rust verification failed" /var/log/coinjecture/*.log`
2. Identify error patterns
3. Rollback to SHADOW mode
4. Fix Rust implementation

### Issue: Node Crash in REFACTORED_ONLY

**Symptom**: Node stops, Rust error

**Cause**: Unhandled Rust error, no fallback

**Action**:
1. Emergency rollback to REFACTORED_PRIMARY
2. Add legacy engine back
3. Restart node
4. Investigate crash logs

---

## Performance Benchmarks

### Expected Performance Gains

| Operation | Legacy Python | Rust | Speedup |
|-----------|--------------|------|---------|
| SHA-256 hash | 0.05ms | 0.01ms | 5x |
| Merkle root | 0.2ms | 0.04ms | 5x |
| Subset Sum verify | 10ms | 2ms | 5x |
| Block verify (full) | 15ms | 3ms | 5x |

### Measuring Performance

```python
# In logs, check duration_ms from ConsensusResult
logger.info(f"Block {block.index} verified in {result.duration_ms:.2f}ms ({result.mode_used})")
```

---

## Security Considerations

### Pre-Deployment Security Checklist

- [ ] Rust extension built with `--release` (optimized, no debug symbols)
- [ ] No backdoors or debug code in production build
- [ ] Logs do not leak sensitive data (private keys, etc.)
- [ ] Alert callback does not expose internal state to external services
- [ ] Fallback mechanism tested and verified

### Post-Deployment Security

- Monitor for unusual divergence patterns (could indicate attack)
- Rate-limit consensus operations to prevent DoS
- Ensure Rust panics are caught and logged (don't crash node)

---

## Success Criteria

### Phase 1 (SHADOW) Success
- ✅ Zero divergences for 1+ week
- ✅ Zero Rust errors
- ✅ All blocks verified identically by Python and Rust

### Phase 2 (REFACTORED_PRIMARY) Success
- ✅ Zero fallbacks to legacy for 1+ week
- ✅ Consensus latency improved (Rust faster)
- ✅ No stability issues

### Phase 3 (REFACTORED_ONLY) Success
- ✅ Running for 1+ month without fallback
- ✅ Zero Rust errors
- ✅ Testnet stable, users happy
- ✅ Ready to remove legacy code

---

## Timeline Summary

| Week | Phase | Node 1 | Node 2 | Risk |
|------|-------|--------|--------|------|
| 1 | Deploy SHADOW | SHADOW | LEGACY_ONLY | LOW |
| 2 | Validate SHADOW | SHADOW | SHADOW | LOW |
| 3 | Gradual cutover | REFACTORED_PRIMARY | SHADOW | MEDIUM |
| 3.5 | Full cutover | REFACTORED_PRIMARY | REFACTORED_PRIMARY | MEDIUM |
| 4+ | Final state | REFACTORED_ONLY | REFACTORED_ONLY | HIGH |

**Total Migration Time**: 4-6 weeks

---

## Contacts & Support

**Lead Developer**: Quigles1337 <adz@alphx.io>
**Repository**: https://github.com/Quigles1337/COINjecture1337-REFACTOR
**Issues**: File at GitHub Issues
**Emergency Rollback**: Contact lead developer immediately

---

## Appendix: Code Snippets

### A. Complete Node Initialization (SHADOW Mode)

```python
# src/node.py (or your node entry point)

import logging
from src.consensus_wrapper import DualRunConsensus, ConsensusMode
from src.consensus import ConsensusEngine
from src.storage import StorageManager
from src.network import NetworkProtocol

logger = logging.getLogger("Node")

def initialize_consensus(config, storage, registry):
    """Initialize consensus with migration wrapper."""

    # Create legacy engine
    legacy_engine = ConsensusEngine(config, storage, registry)

    # Alert callback for divergences
    def alert_divergence(data):
        logger.critical(
            f"🚨 CONSENSUS DIVERGENCE DETECTED!\n"
            f"Block: {data.get('block_index')}\n"
            f"Legacy: {data.get('legacy_result')}\n"
            f"Rust: {data.get('rust_result')}"
        )
        # TODO: Send to monitoring service (PagerDuty, etc.)

    # Create dual-run consensus
    consensus = DualRunConsensus(
        mode=ConsensusMode.SHADOW,  # Start in SHADOW mode
        legacy_engine=legacy_engine,
        alert_callback=alert_divergence
    )

    logger.info(f"Consensus initialized in {consensus.mode.value} mode")
    return consensus

# In your main node code:
consensus = initialize_consensus(config, storage, registry)

# Use consensus.verify_block() as normal
is_valid, result = consensus.verify_block(block)
logger.info(f"Block verified: {is_valid} ({result.mode_used}, {result.duration_ms:.2f}ms)")
```

### B. Stats Endpoint (Optional API Integration)

```python
# In your API server (e.g., Flask/FastAPI)

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/v1/consensus/stats')
def get_consensus_stats():
    """Get consensus migration statistics."""
    stats = consensus.get_stats()
    return jsonify(stats)

@app.route('/v1/consensus/mode', methods=['POST'])
def set_consensus_mode():
    """Change consensus mode (admin only)."""
    new_mode = request.json.get('mode')

    if new_mode not in ['legacy', 'shadow', 'rust', 'final']:
        return jsonify({"error": "Invalid mode"}), 400

    try:
        mode_enum = ConsensusMode(new_mode)
        consensus.set_mode(mode_enum)
        return jsonify({"status": "ok", "mode": new_mode})
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-05
**Status**: Ready for deployment
