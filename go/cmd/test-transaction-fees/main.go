// Transaction Fee Testing Node for Network A
// Starts a validator and injects test transactions to verify fee distribution
package main

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
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

const Version = "1.0.0"

func main() {
	// Parse flags
	dbPath := flag.String("db", "./data/fee-test.db", "Database path")
	validatorKeyHex := flag.String("validator-key", "", "Validator public key (32 hex chars)")
	numTxs := flag.Int("num-txs", 10, "Number of test transactions to create")
	blockTime := flag.Duration("block-time", 2*time.Second, "Block production interval")
	flag.Parse()

	fmt.Printf("═══════════════════════════════════════════\n")
	fmt.Printf("  Network A Fee Testing Node v%s\n", Version)
	fmt.Printf("  Critical Complex Equilibrium Verification\n")
	fmt.Printf("═══════════════════════════════════════════\n\n")

	// Create logger
	log := logger.NewLogger("info")

	// Decode or generate validator key
	var validatorKey [32]byte
	if *validatorKeyHex == "" {
		log.Warn("No validator key provided, generating random key...")
		rand.Read(validatorKey[:])
	} else {
		keyBytes, err := hex.DecodeString(*validatorKeyHex)
		if err != nil || len(keyBytes) != 32 {
			log.WithError(err).Fatal("Invalid validator key")
		}
		copy(validatorKey[:], keyBytes)
	}
	fmt.Printf("✓ Validator key: %x\n", validatorKey)

	// Initialize database schema
	if err := state.InitializeDB(*dbPath); err != nil {
		log.WithError(err).Fatal("Failed to initialize database schema")
	}
	fmt.Printf("✓ Database schema initialized\n")

	// Create state manager
	stateManager, err := state.NewStateManager(*dbPath, log)
	if err != nil {
		log.WithError(err).Fatal("Failed to create state manager")
	}
	defer stateManager.Close()
	fmt.Printf("✓ State manager initialized\n")

	// Create mempool
	mempoolCfg := mempool.Config{
		MaxSize:           10000,
		MaxTxAge:          1 * time.Hour,
		CleanupInterval:   1 * time.Minute,
		PriorityThreshold: 0.0,
	}
	mp := mempool.NewMempool(mempoolCfg, log)
	fmt.Printf("✓ Mempool ready (capacity: %d)\n", mempoolCfg.MaxSize)

	// Create test accounts and fund them
	fmt.Printf("\n📝 Creating test accounts...\n")
	testAccounts := createTestAccounts(*numTxs, stateManager, log)
	fmt.Printf("✓ Created %d test accounts with initial balance\n", len(testAccounts))

	// Create consensus config
	consensusCfg := consensus.ConsensusConfig{
		BlockTime:    *blockTime,
		Validators:   [][32]byte{validatorKey},
		ValidatorKey: validatorKey,
		IsValidator:  true,
	}

	// Create consensus engine
	engine := consensus.NewEngine(consensusCfg, mp, stateManager, log)
	fmt.Printf("✓ Consensus engine created\n")
	fmt.Printf("  Block time: %v\n\n", *blockTime)

	// Start consensus engine
	fmt.Println("Starting consensus engine...")
	if err := engine.Start(); err != nil {
		log.WithError(err).Fatal("Failed to start consensus engine")
	}
	fmt.Println("✓ Consensus engine started\n")

	// Wait a moment for genesis block
	time.Sleep(3 * time.Second)

	// Inject test transactions into mempool
	fmt.Printf("🔬 Injecting %d test transactions...\n", *numTxs)
	txHashes := injectTestTransactions(*numTxs, testAccounts, mp, stateManager, log)
	fmt.Printf("✓ Injected %d transactions into mempool\n", len(txHashes))

	// Display fee information
	var totalFees uint64
	for _, tx := range mp.GetTopTransactions(*numTxs) {
		totalFees += tx.Fee
		fmt.Printf("  TX %x... → Fee: %d wei (%.9f $BEANS)\n", tx.Hash[:4], tx.Fee, float64(tx.Fee)/1e9)
	}
	fmt.Printf("\n💰 Total fees from all transactions: %d wei (%.9f $BEANS)\n", totalFees, float64(totalFees)/1e9)

	// Calculate expected distribution
	validatorShare := uint64(float64(totalFees) * 0.4142)
	burnShare := uint64(float64(totalFees) * 0.2929)
	treasuryShare := uint64(float64(totalFees) * 0.2929)

	fmt.Printf("\n📐 Expected Fee Distribution (Critical Complex Equilibrium):\n")
	fmt.Printf("  Validator: %d wei (41.42%%) → %.9f $BEANS\n", validatorShare, float64(validatorShare)/1e9)
	fmt.Printf("  Burn:      %d wei (29.29%%) → %.9f $BEANS\n", burnShare, float64(burnShare)/1e9)
	fmt.Printf("  Treasury:  %d wei (29.29%%) → %.9f $BEANS\n\n", treasuryShare, float64(treasuryShare)/1e9)

	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("  Validator is running and processing TXs")
	fmt.Println("  Wait for ~4-6 seconds for blocks to be produced")
	fmt.Println("  Press Ctrl+C to stop and check results")
	fmt.Println("═══════════════════════════════════════════\n")

	// Wait for shutdown signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	fmt.Println("\n\n═══════════════════════════════════════════")
	fmt.Println("  Shutting down and analyzing results...")
	fmt.Println("═══════════════════════════════════════════\n")

	// Close state manager
	if err := stateManager.Close(); err != nil {
		log.WithError(err).Error("Error closing state manager")
	}

	// Analyze final state
	fmt.Printf("✓ Run completed!\n")
	fmt.Printf("  Use the test-fees utility to analyze results:\n")
	fmt.Printf("  ./bin/test-fees.exe --db %s\n\n", *dbPath)
}

// createTestAccounts creates funded test accounts for sending transactions
func createTestAccounts(count int, sm *state.StateManager, log *logger.Logger) [][32]byte {
	accounts := make([][32]byte, count)

	for i := 0; i < count; i++ {
		var addr [32]byte
		rand.Read(addr[:])
		accounts[i] = addr

		// Fund account with enough for transaction + fees
		// Each tx needs: 1 gwei amount + 21000 gwei fee = 21001 gwei
		// Fund with 1 million gwei to be safe
		balance := uint64(1000000000000000) // 1 million gwei = 1000 $BEANS
		if err := sm.UpdateAccount(addr, balance, 0); err != nil {
			log.WithError(err).Fatal("Failed to create test account")
		}
	}

	return accounts
}

// injectTestTransactions creates and injects test transactions into the mempool
func injectTestTransactions(count int, accounts [][32]byte, mp *mempool.Mempool, sm *state.StateManager, log *logger.Logger) [][32]byte {
	txHashes := make([][32]byte, 0, count)

	for i := 0; i < count; i++ {
		from := accounts[i]

		// Create random recipient
		var to [32]byte
		rand.Read(to[:])

		// Standard transfer gas parameters
		gasLimit := uint64(21000)
		gasPrice := uint64(1000000000) // 1 gwei

		// Get current nonce
		account, err := sm.GetAccount(from)
		if err != nil {
			log.WithError(err).Warn("Failed to get account for transaction creation")
			continue
		}

		// Create transaction
		tx := &mempool.Transaction{
			From:      from,
			To:        to,
			Amount:    1000000000, // 0.000000001 $BEANS (1 gwei)
			Nonce:     account.Nonce,
			GasLimit:  gasLimit,
			GasPrice:  gasPrice,
			Fee:       gasLimit * gasPrice, // 21000 gwei
			Timestamp: time.Now().Unix(),
			TxType:    1, // Transfer
		}

		// Compute hash
		hashData := make([]byte, 0, 256)
		hashData = append(hashData, from[:]...)
		hashData = append(hashData, to[:]...)
		hashData = append(hashData, uint64ToBytes(tx.Amount)...)
		hashData = append(hashData, uint64ToBytes(tx.Nonce)...)
		hashData = append(hashData, uint64ToBytes(tx.GasLimit)...)
		hashData = append(hashData, uint64ToBytes(tx.GasPrice)...)

		tx.Hash = sha256.Sum256(hashData)

		// Add to mempool
		if err := mp.AddTransaction(tx); err != nil {
			log.WithError(err).WithField("tx_hash", fmt.Sprintf("%x", tx.Hash[:8])).Warn("Failed to add transaction to mempool")
			continue
		}

		txHashes = append(txHashes, tx.Hash)
	}

	return txHashes
}

func uint64ToBytes(n uint64) []byte {
	b := make([]byte, 8)
	b[0] = byte(n >> 56)
	b[1] = byte(n >> 48)
	b[2] = byte(n >> 40)
	b[3] = byte(n >> 32)
	b[4] = byte(n >> 24)
	b[5] = byte(n >> 16)
	b[6] = byte(n >> 8)
	b[7] = byte(n)
	return b
}
