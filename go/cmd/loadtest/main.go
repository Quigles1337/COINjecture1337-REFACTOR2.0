// Load testing tool for COINjecture blockchain
package main

import (
	"crypto/rand"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/consensus"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

// TestConfig holds load test configuration
type TestConfig struct {
	Duration       time.Duration // How long to run the test
	TxRate         int           // Target transactions per second
	NumAccounts    int           // Number of test accounts
	BlockTime      time.Duration // Consensus block time
	NumValidators  int           // Number of validators
	ReportInterval time.Duration // How often to report statistics
}

// TestMetrics holds test results
type TestMetrics struct {
	TxSubmitted     int64
	TxInBlocks      int64
	BlocksProduced  int64
	StartTime       time.Time
	LastReportTime  time.Time
	TxSinceReport   int64
	BlocksSinceReport int64
}

func main() {
	// Parse command-line flags
	duration := flag.Duration("duration", 60*time.Second, "Test duration")
	txRate := flag.Int("txrate", 100, "Target transactions per second")
	numAccounts := flag.Int("accounts", 100, "Number of test accounts")
	blockTime := flag.Duration("blocktime", 2*time.Second, "Block time")
	numValidators := flag.Int("validators", 1, "Number of validators")
	reportInterval := flag.Duration("report", 5*time.Second, "Report interval")

	flag.Parse()

	config := TestConfig{
		Duration:       *duration,
		TxRate:         *txRate,
		NumAccounts:    *numAccounts,
		BlockTime:      *blockTime,
		NumValidators:  *numValidators,
		ReportInterval: *reportInterval,
	}

	fmt.Println("=== COINjecture Load Test ===")
	fmt.Printf("Duration: %v\n", config.Duration)
	fmt.Printf("Target TPS: %d\n", config.TxRate)
	fmt.Printf("Accounts: %d\n", config.NumAccounts)
	fmt.Printf("Block Time: %v\n", config.BlockTime)
	fmt.Printf("Validators: %d\n", config.NumValidators)
	fmt.Printf("Report Interval: %v\n", config.ReportInterval)
	fmt.Println()

	// Run load test
	if err := runLoadTest(config); err != nil {
		fmt.Fprintf(os.Stderr, "Load test failed: %v\n", err)
		os.Exit(1)
	}
}

func runLoadTest(config TestConfig) error {
	log := logger.NewLogger("info")

	// Create in-memory state manager
	sm, err := state.NewStateManager(":memory:", log)
	if err != nil {
		return fmt.Errorf("failed to create state manager: %w", err)
	}
	defer sm.Close()

	// Create mempool
	mempoolCfg := mempool.Config{
		MaxSize:           10000,
		MaxTxAge:          time.Hour,
		CleanupInterval:   time.Minute,
		PriorityThreshold: 0.0,
	}
	mp := mempool.NewMempool(mempoolCfg, log)

	// Create validators
	validators := make([][32]byte, config.NumValidators)
	for i := 0; i < config.NumValidators; i++ {
		rand.Read(validators[i][:])
	}

	// Create consensus engine
	consensusCfg := consensus.ConsensusConfig{
		BlockTime:    config.BlockTime,
		Validators:   validators,
		ValidatorKey: validators[0], // First validator
		IsValidator:  true,
	}

	engine := consensus.NewEngine(consensusCfg, mp, sm, log)

	// Set up metrics tracking
	metrics := &TestMetrics{
		StartTime:      time.Now(),
		LastReportTime: time.Now(),
	}

	// Track blocks produced
	engine.SetNewBlockCallback(func(block *consensus.Block) {
		metrics.BlocksProduced++
		metrics.BlocksSinceReport++
		metrics.TxInBlocks += int64(len(block.Transactions))
	})

	// Start consensus engine
	if err := engine.Start(); err != nil {
		return fmt.Errorf("failed to start engine: %w", err)
	}
	defer engine.Stop()

	fmt.Println("Starting load test...")
	fmt.Println()

	// Set up test accounts
	accounts := make([][32]byte, config.NumAccounts)
	for i := 0; i < config.NumAccounts; i++ {
		rand.Read(accounts[i][:])
		// Initialize with balance
		if err := sm.CreateAccount(accounts[i], 1000000); err != nil {
			return fmt.Errorf("failed to create account: %w", err)
		}
	}

	// Set up signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Transaction generation ticker
	txTicker := time.NewTicker(time.Second / time.Duration(config.TxRate))
	defer txTicker.Stop()

	// Report ticker
	reportTicker := time.NewTicker(config.ReportInterval)
	defer reportTicker.Stop()

	// Test duration timer
	testTimer := time.NewTimer(config.Duration)
	defer testTimer.Stop()

	// Main load test loop
	running := true
	for running {
		select {
		case <-txTicker.C:
			// Generate transaction
			if err := generateTransaction(mp, accounts, sm); err != nil {
				log.WithError(err).Warn("Failed to generate transaction")
			} else {
				metrics.TxSubmitted++
				metrics.TxSinceReport++
			}

		case <-reportTicker.C:
			// Print progress report
			printReport(metrics, config)
			metrics.LastReportTime = time.Now()
			metrics.TxSinceReport = 0
			metrics.BlocksSinceReport = 0

		case <-testTimer.C:
			// Test duration completed
			running = false

		case <-sigChan:
			// User interrupted
			fmt.Println("\nTest interrupted by user")
			running = false
		}
	}

	// Final report
	fmt.Println("\n=== Final Results ===")
	printFinalReport(metrics, config)

	return nil
}

func generateTransaction(mp *mempool.Mempool, accounts [][32]byte, sm *state.StateManager) error {
	// Pick random sender and recipient
	senderIdx := randomInt(len(accounts))
	recipientIdx := randomInt(len(accounts))
	if senderIdx == recipientIdx {
		recipientIdx = (recipientIdx + 1) % len(accounts)
	}

	sender := accounts[senderIdx]
	recipient := accounts[recipientIdx]

	// Get sender account to get correct nonce
	account, err := sm.GetAccount(sender)
	if err != nil {
		return err
	}

	// Check balance
	if account.Balance < 110 {
		return fmt.Errorf("insufficient balance")
	}

	// Create transaction
	var txHash [32]byte
	rand.Read(txHash[:])

	tx := &mempool.Transaction{
		Hash:      txHash,
		From:      sender,
		To:        recipient,
		Amount:    100,
		Nonce:     account.Nonce,
		Fee:       10,
		GasLimit:  21000,
		GasPrice:  1,
		Timestamp: time.Now().Unix(),
		TxType:    1, // Transfer
		Priority:  10.0,
	}

	// Add to mempool
	return mp.AddTransaction(tx)
}

func randomInt(max int) int {
	var buf [8]byte
	rand.Read(buf[:])
	n := uint64(buf[0]) | uint64(buf[1])<<8 | uint64(buf[2])<<16 | uint64(buf[3])<<24 |
		uint64(buf[4])<<32 | uint64(buf[5])<<40 | uint64(buf[6])<<48 | uint64(buf[7])<<56
	return int(n % uint64(max))
}

func printReport(metrics *TestMetrics, config TestConfig) {
	elapsed := time.Since(metrics.StartTime)
	elapsedSeconds := elapsed.Seconds()

	// Calculate rates
	avgTPS := float64(metrics.TxSubmitted) / elapsedSeconds

	// Recent rates (since last report)
	reportElapsed := time.Since(metrics.LastReportTime).Seconds()
	recentTPS := float64(metrics.TxSinceReport) / reportElapsed
	recentBlockRate := float64(metrics.BlocksSinceReport) / reportElapsed

	// Mempool stats would go here if available

	fmt.Printf("[%6.1fs] TxSubmitted: %5d | TxInBlocks: %5d | Blocks: %3d | ",
		elapsedSeconds,
		metrics.TxSubmitted,
		metrics.TxInBlocks,
		metrics.BlocksProduced,
	)
	fmt.Printf("TPS: %6.1f (recent: %6.1f) | BlockRate: %.2f/s\n",
		avgTPS,
		recentTPS,
		recentBlockRate,
	)
}

func printFinalReport(metrics *TestMetrics, config TestConfig) {
	elapsed := time.Since(metrics.StartTime)
	elapsedSeconds := elapsed.Seconds()

	fmt.Printf("Test Duration: %v\n", elapsed.Round(time.Millisecond))
	fmt.Printf("Transactions Submitted: %d\n", metrics.TxSubmitted)
	fmt.Printf("Transactions in Blocks: %d\n", metrics.TxInBlocks)
	fmt.Printf("Blocks Produced: %d\n", metrics.BlocksProduced)
	fmt.Println()

	// Calculate throughput
	avgTPS := float64(metrics.TxSubmitted) / elapsedSeconds
	confirmedTPS := float64(metrics.TxInBlocks) / elapsedSeconds
	avgBlockRate := float64(metrics.BlocksProduced) / elapsedSeconds
	avgTxPerBlock := float64(metrics.TxInBlocks) / float64(metrics.BlocksProduced)

	fmt.Printf("Average TPS (submitted): %.2f\n", avgTPS)
	fmt.Printf("Average TPS (confirmed): %.2f\n", confirmedTPS)
	fmt.Printf("Block Production Rate: %.2f blocks/sec\n", avgBlockRate)
	fmt.Printf("Average Tx per Block: %.1f\n", avgTxPerBlock)
	fmt.Println()

	// Calculate efficiency
	efficiency := float64(metrics.TxInBlocks) / float64(metrics.TxSubmitted) * 100
	fmt.Printf("Transaction Inclusion Rate: %.1f%%\n", efficiency)

	// Expected vs actual
	expectedBlocks := int64(elapsedSeconds / config.BlockTime.Seconds())
	blockEfficiency := float64(metrics.BlocksProduced) / float64(expectedBlocks) * 100
	fmt.Printf("Block Production Efficiency: %.1f%% (%d/%d expected)\n",
		blockEfficiency, metrics.BlocksProduced, expectedBlocks)
}
