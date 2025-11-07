// Transaction Fee Testing Utility for Network A
// Tests Critical Complex Equilibrium fee distribution
package main

import (
	"crypto/rand"
	"crypto/sha256"
	"database/sql"
	"flag"
	"fmt"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
	_ "github.com/mattn/go-sqlite3"
)

const Version = "1.0.0"

func main() {
	// Parse flags
	dbPath := flag.String("db", "./data/network-a.db", "Database path to query")
	flag.Parse()

	fmt.Printf("═══════════════════════════════════════════\n")
	fmt.Printf("  Transaction Fee Testing v%s\n", Version)
	fmt.Printf("  Critical Complex Equilibrium Verification\n")
	fmt.Printf("═══════════════════════════════════════════\n\n")

	// Create logger
	log := logger.NewLogger("info")

	// Open database
	db, err := sql.Open("sqlite3", *dbPath)
	if err != nil {
		log.WithError(err).Fatal("Failed to open database")
	}
	defer db.Close()

	// Create state manager to access accounts
	stateManager, err := state.NewStateManager(*dbPath, log)
	if err != nil {
		log.WithError(err).Fatal("Failed to create state manager")
	}
	defer stateManager.Close()

	fmt.Println("📊 Analyzing Network A Fee Distribution...\n")

	// Get account snapshot
	accountSnapshot, err := stateManager.GetAccountSnapshot()
	if err != nil {
		log.WithError(err).Fatal("Failed to get account snapshot")
	}

	// Find validator, treasury, and burn accounts
	var validatorBalance, treasuryBalance, burnBalance uint64
	var treasuryAddr, burnAddr [32]byte

	// Treasury is 0xFFFF...FF, Burn is 0x0000...00
	for i := 0; i < 32; i++ {
		treasuryAddr[i] = 0xFF
		burnAddr[i] = 0x00
	}

	totalSupply := uint64(0)
	for addr, account := range accountSnapshot {
		balance := account.Balance
		totalSupply += balance

		if addr == treasuryAddr {
			treasuryBalance = balance
			fmt.Printf("💰 Treasury: %x... → %d wei (%.4f $BEANS)\n", addr[:4], balance, float64(balance)/1e9)
		} else if addr == burnAddr {
			burnBalance = balance
			fmt.Printf("🔥 Burn:     %x... → %d wei (%.4f $BEANS)\n", addr[:4], balance, float64(balance)/1e9)
		} else {
			validatorBalance = balance
			fmt.Printf("✅ Validator: %x... → %d wei (%.4f $BEANS)\n", addr[:4], balance, float64(balance)/1e9)
		}
	}

	fmt.Printf("\n📈 Total Supply: %d wei (%.4f $BEANS)\n\n", totalSupply, float64(totalSupply)/1e9)

	// Calculate theoretical rewards based on blocks
	fmt.Println("🧮 Theoretical Calculations (assuming no transaction fees yet):")
	fmt.Println("   Block Reward: 3.125 $BEANS per block")
	fmt.Printf("   Estimated Blocks: ~%.0f\n", float64(totalSupply)/(3.125e9))
	fmt.Printf("   Expected Supply: %.4f $BEANS\n\n", float64(totalSupply)/1e9)

	// Verify Critical Complex Equilibrium if fees exist
	if treasuryBalance > 0 || burnBalance > 0 {
		fmt.Println("✨ Critical Complex Equilibrium Verification:")
		fmt.Println("   Expected: 41.42% validator, 29.29% burn, 29.29% treasury")

		if validatorBalance > 0 {
			// Calculate what portion went where
			validatorFeePortion := float64(validatorBalance) / float64(totalSupply) * 100
			burnPortion := float64(burnBalance) / float64(totalSupply) * 100
			treasuryPortion := float64(treasuryBalance) / float64(totalSupply) * 100

			fmt.Printf("   Validator: %.2f%% of supply\n", validatorFeePortion)
			fmt.Printf("   Burn:      %.2f%% of supply\n", burnPortion)
			fmt.Printf("   Treasury:  %.2f%% of supply\n\n", treasuryPortion)
		}
	} else {
		fmt.Println("ℹ️  No transaction fees detected yet (pure emission model)")
		fmt.Println("   All supply comes from block rewards")
		fmt.Println("   Fee distribution will activate when transactions are processed\n")
	}

	// Create sample transactions for testing
	fmt.Println("🔬 Creating Sample Transactions for Testing...\n")

	// Generate test transaction with fees
	tx := createTestTransaction()
	fmt.Printf("Sample Transaction:\n")
	fmt.Printf("  Hash:      %x\n", tx.Hash[:8])
	fmt.Printf("  From:      %x...\n", tx.From[:4])
	fmt.Printf("  To:        %x...\n", tx.To[:4])
	fmt.Printf("  Amount:    %d wei\n", tx.Amount)
	fmt.Printf("  Gas Limit: %d\n", tx.GasLimit)
	fmt.Printf("  Gas Price: %d wei/gas\n", tx.GasPrice)
	fmt.Printf("  Total Fee: %d wei (%.9f $BEANS)\n\n", tx.Fee, float64(tx.Fee)/1e9)

	// Calculate expected fee distribution
	fmt.Println("📐 Expected Fee Distribution (Critical Complex Equilibrium):")
	validatorFee := uint64(float64(tx.Fee) * 0.4142)
	burnFee := uint64(float64(tx.Fee) * 0.2929)
	treasuryFee := uint64(float64(tx.Fee) * 0.2929)

	fmt.Printf("  Validator: %d wei (41.42%%)\n", validatorFee)
	fmt.Printf("  Burn:      %d wei (29.29%%)\n", burnFee)
	fmt.Printf("  Treasury:  %d wei (29.29%%)\n", treasuryFee)
	fmt.Printf("  Total:     %d wei\n\n", validatorFee+burnFee+treasuryFee)

	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("✅ Fee testing utility complete!")
	fmt.Println("═══════════════════════════════════════════\n")
}

// createTestTransaction creates a sample transaction for testing
func createTestTransaction() *mempool.Transaction {
	var from, to [32]byte
	rand.Read(from[:])
	rand.Read(to[:])

	// Create transaction with realistic gas parameters
	gasLimit := uint64(21000) // Standard transfer gas limit
	gasPrice := uint64(1000000000) // 1 gwei

	tx := &mempool.Transaction{
		From:      from,
		To:        to,
		Amount:    1000000000000, // 0.001 $BEANS
		Nonce:     1,
		GasLimit:  gasLimit,
		GasPrice:  gasPrice,
		Fee:       gasLimit * gasPrice, // 21000 * 1 gwei = 21000 gwei = 0.000021 $BEANS
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

	return tx
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
