# COINjecture Load Testing Framework

High-performance load testing tool for measuring blockchain TPS (Transactions Per Second) and consensus performance.

## Features

- **Realistic Transaction Generation**: Creates valid transactions with proper nonces and balances
- **TPS Measurement**: Real-time and average transactions per second tracking
- **Block Production Monitoring**: Tracks block rate and transaction inclusion
- **Configurable Load**: Adjustable transaction rate, duration, and network size
- **Live Progress Reports**: Periodic statistics during test execution
- **Graceful Shutdown**: Ctrl+C for clean termination with final results

## Usage

### Basic Test (60 seconds, 100 TPS)

```bash
go run cmd/loadtest/main.go
```

### Custom Configuration

```bash
go run cmd/loadtest/main.go \
  -duration 5m \
  -txrate 500 \
  -accounts 1000 \
  -blocktime 2s \
  -validators 3 \
  -report 10s
```

### Build and Run

```bash
# Build the tool
go build -o loadtest cmd/loadtest/main.go

# Run load test
./loadtest -duration 2m -txrate 1000
```

## Command-Line Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-duration` | 60s | Test duration (e.g., 5m, 2h) |
| `-txrate` | 100 | Target transactions per second |
| `-accounts` | 100 | Number of test accounts |
| `-blocktime` | 2s | Consensus block time |
| `-validators` | 1 | Number of validators |
| `-report` | 5s | Statistics report interval |

## Output Metrics

### Real-time Progress

```
[  10.0s] TxSubmitted:  1000 | TxInBlocks:   950 | Blocks:   5 | TPS:  100.0 (recent:  100.0) | BlockRate: 0.50/s
[  15.0s] TxSubmitted:  1500 | TxInBlocks:  1425 | Blocks:   7 | TPS:  100.0 (recent:  100.0) | BlockRate: 0.47/s
[  20.0s] TxSubmitted:  2000 | TxInBlocks:  1900 | Blocks:  10 | TPS:  100.0 (recent:  100.0) | BlockRate: 0.50/s
```

- **TxSubmitted**: Total transactions sent to mempool
- **TxInBlocks**: Transactions confirmed in blocks
- **Blocks**: Total blocks produced
- **TPS**: Average transactions per second
- **Recent TPS**: TPS since last report
- **BlockRate**: Blocks produced per second

### Final Results

```
=== Final Results ===
Test Duration: 60.012s
Transactions Submitted: 6000
Transactions in Blocks: 5700
Blocks Produced: 30

Average TPS (submitted): 100.00
Average TPS (confirmed): 95.00
Block Production Rate: 0.50 blocks/sec
Average Tx per Block: 190.0

Transaction Inclusion Rate: 95.0%
Block Production Efficiency: 100.0% (30/30 expected)
```

## Performance Benchmarks

### Target Performance

- **TPS**: 500+ transactions per second
- **Block Time**: 2 seconds (configurable)
- **Inclusion Rate**: >95% (mempool to block)
- **Block Efficiency**: >95% (expected vs actual blocks)

### Example Benchmarks

#### Low Load (100 TPS, 1 Validator)
```bash
go run cmd/loadtest/main.go -duration 1m -txrate 100
```
**Expected**: ~6000 tx submitted, ~5700 confirmed, 30 blocks

#### Medium Load (500 TPS, 1 Validator)
```bash
go run cmd/loadtest/main.go -duration 1m -txrate 500
```
**Expected**: ~30000 tx submitted, ~28500 confirmed, 30 blocks

#### High Load (1000 TPS, 3 Validators)
```bash
go run cmd/loadtest/main.go -duration 1m -txrate 1000 -validators 3
```
**Expected**: ~60000 tx submitted, ~57000 confirmed, 30 blocks

## Measuring Peak TPS

To find the maximum TPS your system can handle:

```bash
# Start with baseline
go run cmd/loadtest/main.go -duration 30s -txrate 100

# Increase gradually
go run cmd/loadtest/main.go -duration 30s -txrate 500
go run cmd/loadtest/main.go -duration 30s -txrate 1000
go run cmd/loadtest/main.go -duration 30s -txrate 2000

# Find the rate where inclusion drops below 90%
```

## Limitations

- **In-Memory Only**: Uses `:memory:` database (no disk I/O bottleneck)
- **Single Node**: Tests one consensus engine (no P2P overhead)
- **No Signature Verification**: Transactions skip Ed25519 verification
- **Simplified State**: Basic account transfers only

## Interpreting Results

### Good Performance Indicators

- ✅ Inclusion Rate > 95%
- ✅ Block Efficiency > 95%
- ✅ Consistent TPS (recent ≈ average)
- ✅ Low tx accumulation in mempool

### Performance Issues

- ❌ Inclusion Rate < 90% → Mempool overflow
- ❌ Block Efficiency < 90% → Consensus delays
- ❌ Declining TPS → Resource saturation
- ❌ Growing mempool → Processing bottleneck

## Production Considerations

This tool measures **best-case performance**:

- No network latency
- No disk I/O
- No signature verification
- No P2P gossip overhead

**Real-world TPS** will be 30-50% of load test results due to:
- Network propagation delays
- Signature verification CPU cost
- Database write latency
- P2P message overhead

## Examples

### Quick Smoke Test (10 seconds)
```bash
go run cmd/loadtest/main.go -duration 10s -txrate 50
```

### Standard Benchmark (5 minutes, 500 TPS)
```bash
go run cmd/loadtest/main.go -duration 5m -txrate 500 -accounts 500
```

### Stress Test (10 minutes, 2000 TPS)
```bash
go run cmd/loadtest/main.go -duration 10m -txrate 2000 -accounts 2000 -validators 3
```

### Marathon Test (1 hour, sustained load)
```bash
go run cmd/loadtest/main.go -duration 1h -txrate 300 -accounts 1000 -report 60s
```

## Troubleshooting

### Low Inclusion Rate

**Symptom**: Transaction Inclusion Rate < 90%

**Causes**:
- Transaction rate exceeds block capacity
- Nonce conflicts (account reuse too fast)
- Insufficient account balances

**Solutions**:
- Increase `-accounts` flag
- Lower `-txrate`
- Increase block gas limit

### Missing Blocks

**Symptom**: Block Production Efficiency < 90%

**Causes**:
- Block production delays
- Consensus engine overload

**Solutions**:
- Lower transaction rate
- Increase block time
- Check CPU usage

## Integration with CI/CD

```yaml
# GitHub Actions example
- name: Run TPS Benchmark
  run: |
    cd go
    go run cmd/loadtest/main.go -duration 30s -txrate 500 > results.txt

- name: Check Performance
  run: |
    TPS=$(grep "Average TPS" results.txt | awk '{print $4}')
    if (( $(echo "$TPS < 450" | bc -l) )); then
      echo "Performance regression: TPS = $TPS"
      exit 1
    fi
```

## Future Enhancements

- [ ] Histogram latency tracking (p50, p95, p99)
- [ ] Memory usage profiling
- [ ] CPU utilization metrics
- [ ] Concurrent validator testing
- [ ] P2P network simulation
- [ ] Transaction type diversity (escrow, bounties)
- [ ] Grafana dashboard export
