# Network A Testing Guide
**Version:** 4.5.0+
**Status:** Production-Ready
**Date:** 2025-11-06

---

## Quick Start Commands

### 1. Check Running Validator Status

```powershell
# View latest 20 blocks
Get-Content -Path .\bin\network-a-node.log -Wait -Tail 20

# Count total blocks produced
sqlite3 ./data/validator1.db "SELECT COUNT(*) as total_blocks FROM blocks;"

# View latest 10 blocks
sqlite3 ./data/validator1.db "SELECT height, hash, validator, timestamp FROM blocks ORDER BY height DESC LIMIT 10;"

# Check account balances
sqlite3 ./data/validator1.db "SELECT * FROM accounts;"
```

### 2. Submit Test Transactions

The institutional-grade `submit-tx` utility is now available:

```powershell
# Test dry-run mode (validate only, don't submit)
.\bin\submit-tx.exe `
  --from-key <YOUR_PRIVATE_KEY_HEX> `
  --to <RECIPIENT_ADDRESS_HEX> `
  --amount 1000000 `
  --dry-run

# Submit single transaction
.\bin\submit-tx.exe `
  --from-key <YOUR_PRIVATE_KEY_HEX> `
  --to <RECIPIENT_ADDRESS_HEX> `
  --amount 1000000 `
  --gas-price 100 `
  --gas-limit 21000

# Submit batch of 10 transactions with 500ms interval
.\bin\submit-tx.exe `
  --from-key <YOUR_PRIVATE_KEY_HEX> `
  --to <RECIPIENT_ADDRESS_HEX> `
  --amount 500000 `
  --count 10 `
  --interval 500ms `
  --verbose

# Verify transactions without submitting
.\bin\submit-tx.exe `
  --from-key <YOUR_PRIVATE_KEY_HEX> `
  --to <RECIPIENT_ADDRESS_HEX> `
  --amount 1000000 `
  --verify
```

**Note:** You'll need to generate test keys first using `coinjecture-keygen`:

```powershell
# Generate test keys
.\bin\coinjecture-keygen.exe --count 2 --output ./test-keys

# Keys will be in:
# ./test-keys/validator1.priv (64-byte hex)
# ./test-keys/validator1.pub (32-byte hex)
# ./test-keys/validator2.priv
# ./test-keys/validator2.pub
```

### 3. Start Additional Validators (Multi-Validator Consensus)

See `scripts/start-validators.ps1` for automated multi-validator startup.

```powershell
# Validator 2
.\bin\network-a-node.exe `
  --validator-key <VALIDATOR2_PUBKEY> `
  --db ./data/validator2.db `
  --block-time 2s

# Validator 3
.\bin\network-a-node.exe `
  --validator-key <VALIDATOR3_PUBKEY> `
  --db ./data/validator3.db `
  --block-time 2s
```

### 4. Monitor Block Production

```powershell
# Watch block production in real-time
Get-Content -Path .\bin\network-a-node.log -Wait | Select-String "New block produced"

# Check fork choice decisions
Get-Content -Path .\bin\network-a-node.log -Wait | Select-String "Fork choice"

# Monitor slashing events
Get-Content -Path .\bin\network-a-node.log -Wait | Select-String "slashed"
```

### 5. Query Blockchain State

```powershell
# Get latest block height
sqlite3 ./data/validator1.db "SELECT MAX(height) as latest_block FROM blocks;"

# Get block by height
sqlite3 ./data/validator1.db "SELECT * FROM blocks WHERE height = 100;"

# Get transaction count
sqlite3 ./data/validator1.db "SELECT COUNT(*) as total_txs FROM transactions;"

# Get account nonce
sqlite3 ./data/validator1.db "SELECT address, nonce, balance FROM accounts WHERE address = '<ADDRESS_HEX>';"

# Check for chain reorgs
sqlite3 ./data/validator1.db "SELECT * FROM reorg_log ORDER BY timestamp DESC LIMIT 10;"
```

---

## Institutional-Grade Features

### Transaction Utility Security

The `submit-tx` utility includes:

✓ **Ed25519 Signing** - Cryptographically secure signatures
✓ **Replay Protection** - Nonce validation with 1000-block window
✓ **Balance Validation** - Pre-flight balance checks
✓ **Gas Limit Enforcement** - Max 10M gas per transaction
✓ **Batch Submission** - Up to 1000 transactions with rate limiting
✓ **Dry-Run Mode** - Validate without submitting
✓ **Comprehensive Logging** - Structured logs with context
✓ **Error Recovery** - Graceful handling of failures

### Validation Levels

1. **Configuration Validation** - CLI args, key formats, addresses
2. **State Validation** - Account balance, nonce, existence
3. **Transaction Validation** - Amount, gas, signature
4. **Submission Validation** - Mempool acceptance, replay protection

---

## Testing Scenarios

### Scenario 1: Single Transaction Test

```powershell
# 1. Generate test keys
.\bin\coinjecture-keygen.exe --count 2 --output ./test-keys

# 2. Get validator key (has genesis balance)
$validatorKey = "9a13376b2950c90c1a9c89c5bd6b5051b9b4ca3a730bba78efe6fbf15eaeb424"

# 3. Get test recipient key
$recipientPubKey = Get-Content ./test-keys/validator1.pub

# 4. Submit transaction
.\bin\submit-tx.exe `
  --from-key $validatorKey `
  --to $recipientPubKey `
  --amount 5000000 `
  --verbose

# 5. Wait 2 seconds for next block
Start-Sleep -Seconds 2

# 6. Verify transaction was included
sqlite3 ./data/validator1.db "SELECT * FROM transactions ORDER BY id DESC LIMIT 1;"
```

### Scenario 2: Batch Transaction Test

```powershell
# Submit 50 transactions over 10 seconds
.\bin\submit-tx.exe `
  --from-key <SENDER_PRIVKEY> `
  --to <RECIPIENT_ADDRESS> `
  --amount 100000 `
  --count 50 `
  --interval 200ms `
  --verbose

# Monitor mempool size
while ($true) {
    $count = sqlite3 ./data/validator1.db "SELECT COUNT(*) FROM mempool;"
    Write-Host "Mempool size: $count"
    Start-Sleep -Seconds 1
}
```

### Scenario 3: Multi-Validator Consensus Test

```powershell
# Terminal 1: Start Validator 1
.\bin\network-a-node.exe --validator-key <VAL1_KEY> --db ./data/validator1.db

# Terminal 2: Start Validator 2
.\bin\network-a-node.exe --validator-key <VAL2_KEY> --db ./data/validator2.db

# Terminal 3: Start Validator 3
.\bin\network-a-node.exe --validator-key <VAL3_KEY> --db ./data/validator3.db

# Terminal 4: Monitor consensus
Get-Content -Path .\bin\network-a-node.log -Wait | Select-String "consensus|validator"
```

### Scenario 4: Load Testing

```powershell
# Use existing load test framework
cd go
go run ./cmd/loadtest/main.go `
  --duration 60s `
  --tps 100 `
  --validators 3

# Monitor TPS
Get-Content -Path .\logs\loadtest.log -Wait | Select-String "TPS|transactions"
```

### Scenario 5: Chain Reorganization Test

```powershell
# 1. Start validator with blocks
# 2. Stop validator
# 3. Start with different chain (longer)
# 4. Observe reorg in logs

Get-Content -Path .\bin\network-a-node.log | Select-String "reorg|rollback"
```

---

## Performance Benchmarks

Expected performance (single validator):

| Metric | Target | Actual (v4.5.0+) |
|--------|--------|------------------|
| Block Time | 2s | ✓ 2.000s (stable) |
| TPS (Empty Blocks) | 30 blocks/min | ✓ 30 blocks/min |
| TPS (Full Blocks) | 1000+ | (Testing) |
| Block Size | 1 MB max | ✓ Enforced |
| Gas Limit/Block | 30M | ✓ Configured |
| Mempool Capacity | 10,000 txs | ✓ Configured |
| State Read Latency | <10ms | (Testing) |
| State Write Latency | <50ms | (Testing) |

---

## Troubleshooting

### Issue: Transaction Rejected

```
ERROR: insufficient balance
```

**Solution:** Check sender balance and total cost (amount + fee)

```powershell
sqlite3 ./data/validator1.db "SELECT balance FROM accounts WHERE address = '<ADDRESS>';"
```

### Issue: Nonce Too Old

```
ERROR: nonce too old: tx=5, account=10 (replay protection)
```

**Solution:** Query current nonce and use nonce+1

```powershell
sqlite3 ./data/validator1.db "SELECT nonce FROM accounts WHERE address = '<ADDRESS>';"
```

### Issue: Validator Not Producing Blocks

**Check:**
1. Validator key is in validator set
2. Database is writable
3. No file permission errors

```powershell
# Check logs
Get-Content -Path .\bin\network-a-node.log -Tail 50

# Check validator set
sqlite3 ./data/validator1.db "SELECT * FROM validators;"
```

---

## Security Checklist

Before production deployment:

- [ ] All validator private keys use HSM or secure enclave
- [ ] Database backups enabled (configs/network-a/validator-*.yaml)
- [ ] TLS enabled for API endpoints
- [ ] Rate limiting configured
- [ ] Firewall rules applied (ports 9000, 8080, 9090 only)
- [ ] Audit logging enabled
- [ ] Slashing thresholds reviewed
- [ ] Checkpoint interval configured
- [ ] Peer authentication enabled
- [ ] Resource limits set (CPU, memory, disk)

---

## Next Steps

1. ✓ **Transaction Testing** - Use `submit-tx` utility
2. **Multi-Validator Setup** - Use `start-validators.ps1`
3. **Chain Reorg Testing** - Use reorg test utility
4. **Checkpoint Testing** - Test fast sync from checkpoint
5. **Load Testing** - Measure TPS with `loadtest` tool

---

**End of Network A Testing Guide**
