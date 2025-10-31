# Production Testing Protocol

## Pre-Deployment Checklist
- [ ] All unit tests pass
- [ ] Local simulation shows equilibrium
- [ ] Stress tests pass
- [ ] Code review complete
- [ ] Monitoring dashboard ready

## Staged Rollout

### Stage 1: Single Node (1 hour)
- Deploy to coinjecture.com only
- Monitor: λ, η, CID propagation
- Success criteria: No errors, metrics stable

### Stage 2: 3 Bootstrap Nodes (6 hours)
- Deploy to 3 trusted nodes
- Monitor: Inter-node gossip, equilibrium
- Success criteria: λ ≈ η ≈ 0.7071

### Stage 3: 10 Miner Nodes (24 hours)
- Invite 10 miners to test
- Monitor: Network load, CID success rate
- Success criteria: >95% CID propagation success

### Stage 4: Public Beta (1 week)
- Open to all miners
- Monitor: Network stability under real load
- Success criteria: Equilibrium maintained >90% of time

## Metrics to Track

### Equilibrium Metrics:
- λ value (should be ~0.7071)
- η value (should be ~0.7071)
- λ/η ratio (should be ~1.0)
- Deviation from equilibrium (<5%)

### Performance Metrics:
- CID propagation time (avg, p50, p95, p99)
- CID success rate (% successfully gossiped)
- Peer count (active peers over time)
- Broadcast queue size (should stay small)

### Network Health:
- Peer churn rate
- Connection failures
- Timeout rate
- Stale peer count

## Rollback Criteria
Rollback if ANY of these occur:
- [ ] Equilibrium deviation >20% for >10 minutes
- [ ] CID propagation success rate <80%
- [ ] Network crashes or hangs
- [ ] >50% of nodes report errors

## Data Collection

### Log Format for Analysis
```json
{
  "timestamp": "2025-10-30T12:00:00Z",
  "node_id": "node123",
  "lambda_state": 0.7071,
  "eta_state": 0.7071,
  "ratio": 1.0000,
  "peers_active": 15,
  "cids_queued": 3,
  "cids_broadcast": 10,
  "cids_failed": 0
}
```

### Monitoring Queries

```bash
# Watch equilibrium in real-time
journalctl -u coinjecture-api -f | grep "⚖️  Equilibrium"

# Calculate average equilibrium over last hour
journalctl -u coinjecture-api --since "1 hour ago" | grep "⚖️" | \
  awk '{print $NF}' | awk -F'=' '{sum+=$2} END {print sum/NR}'

# Check CID propagation rate
journalctl -u coinjecture-api --since "1 hour ago" | \
  grep "📡 Broadcasting" | wc -l

# Monitor peer count
journalctl -u coinjecture-api --since "1 hour ago" | \
  grep "📊 Network:" | tail -1
```

## Test Execution

### Run All Tests
```bash
# Unit tests
pytest tests/test_network_equilibrium.py -v

# Simulation (requires numpy)
pytest tests/test_network_simulation.py -v -m simulation

# Stress tests
pytest tests/test_network_stress.py -v -m stress

# All tests
pytest tests/ -v
```

### Quick Smoke Test
```bash
# Just run unit tests (fast)
pytest tests/test_network_equilibrium.py -v -k "test_constants or test_intervals"
```

