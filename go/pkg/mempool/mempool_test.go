package mempool

import (
	"context"
	"crypto/sha256"
	"testing"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
)

func createTestMempool() *Mempool {
	cfg := DefaultConfig()
	cfg.MaxSize = 10 // Small size for testing
	cfg.MaxTxAge = 1 * time.Second
	cfg.CleanupInterval = 500 * time.Millisecond

	log := logger.NewLogger("error")
	return NewMempool(cfg, log)
}

func createTestTransaction(nonce uint64, gasPrice uint64) *Transaction {
	hash := sha256.Sum256([]byte{byte(nonce), byte(gasPrice)})

	return &Transaction{
		Hash:      hash,
		From:      [32]byte{1, 2, 3},
		To:        [32]byte{4, 5, 6},
		Amount:    1000000,
		Nonce:     nonce,
		GasLimit:  21000,
		GasPrice:  gasPrice,
		Signature: [64]byte{},
		Data:      nil,
		Timestamp: time.Now().Unix(),
		TxType:    1, // Transfer
		Fee:       21000 * gasPrice,
		AddedAt:   time.Now(),
	}
}

func TestMempoolAddTransaction(t *testing.T) {
	m := createTestMempool()

	tx := createTestTransaction(0, 100)

	err := m.AddTransaction(tx)
	if err != nil {
		t.Fatalf("Failed to add transaction: %v", err)
	}

	if m.Size() != 1 {
		t.Fatalf("Expected size 1, got %d", m.Size())
	}
}

func TestMempoolDuplicateTransaction(t *testing.T) {
	m := createTestMempool()

	tx := createTestTransaction(0, 100)

	// Add first time
	err := m.AddTransaction(tx)
	if err != nil {
		t.Fatalf("Failed to add transaction: %v", err)
	}

	// Try to add again (should fail)
	err = m.AddTransaction(tx)
	if err == nil {
		t.Fatal("Expected error when adding duplicate transaction")
	}
}

func TestMempoolNonceOrdering(t *testing.T) {
	m := createTestMempool()

	// Add transaction with nonce 5
	tx1 := createTestTransaction(5, 100)
	err := m.AddTransaction(tx1)
	if err != nil {
		t.Fatalf("Failed to add tx1: %v", err)
	}

	// Try to add transaction with nonce 3 (should fail - too old)
	tx2 := createTestTransaction(3, 100)
	tx2.Hash = sha256.Sum256([]byte{99}) // Different hash
	err = m.AddTransaction(tx2)
	if err == nil {
		t.Fatal("Expected error when adding tx with old nonce")
	}

	// Add transaction with nonce 6 (should succeed)
	tx3 := createTestTransaction(6, 100)
	tx3.Hash = sha256.Sum256([]byte{98}) // Different hash
	err = m.AddTransaction(tx3)
	if err != nil {
		t.Fatalf("Failed to add tx3: %v", err)
	}

	if m.Size() != 2 {
		t.Fatalf("Expected size 2, got %d", m.Size())
	}
}

func TestMempoolPriorityOrdering(t *testing.T) {
	m := createTestMempool()

	// Add transactions with different gas prices
	tx1 := createTestTransaction(0, 100) // Low priority
	tx2 := createTestTransaction(1, 500) // High priority
	tx3 := createTestTransaction(2, 300) // Medium priority

	m.AddTransaction(tx1)
	m.AddTransaction(tx2)
	m.AddTransaction(tx3)

	// Get top 3 transactions
	top := m.GetTopTransactions(3)

	if len(top) != 3 {
		t.Fatalf("Expected 3 transactions, got %d", len(top))
	}

	// Should be ordered by priority (highest first)
	if top[0].GasPrice < top[1].GasPrice || top[1].GasPrice < top[2].GasPrice {
		t.Fatal("Transactions not ordered by priority")
	}

	// Highest priority should be tx2 (gas_price = 500)
	if top[0].Nonce != 1 {
		t.Fatalf("Expected highest priority tx to have nonce 1, got %d", top[0].Nonce)
	}
}

func TestMempoolEviction(t *testing.T) {
	m := createTestMempool()
	// MaxSize = 10

	// Fill mempool with low-priority transactions
	for i := uint64(0); i < 10; i++ {
		tx := createTestTransaction(i, 100) // Low gas price
		tx.Hash = sha256.Sum256([]byte{byte(i)})
		err := m.AddTransaction(tx)
		if err != nil {
			t.Fatalf("Failed to add transaction %d: %v", i, err)
		}
	}

	if m.Size() != 10 {
		t.Fatalf("Expected size 10, got %d", m.Size())
	}

	// Add high-priority transaction (should evict lowest priority)
	highPriorityTx := createTestTransaction(10, 1000) // High gas price
	highPriorityTx.Hash = sha256.Sum256([]byte{99})
	err := m.AddTransaction(highPriorityTx)
	if err != nil {
		t.Fatalf("Failed to add high-priority transaction: %v", err)
	}

	// Size should still be 10 (evicted one, added one)
	if m.Size() != 10 {
		t.Fatalf("Expected size 10 after eviction, got %d", m.Size())
	}

	// High-priority tx should be in mempool
	_, err = m.GetTransaction(highPriorityTx.Hash)
	if err != nil {
		t.Fatal("High-priority transaction was not added")
	}
}

func TestMempoolRemoveTransaction(t *testing.T) {
	m := createTestMempool()

	tx := createTestTransaction(0, 100)
	m.AddTransaction(tx)

	if m.Size() != 1 {
		t.Fatalf("Expected size 1, got %d", m.Size())
	}

	err := m.RemoveTransaction(tx.Hash)
	if err != nil {
		t.Fatalf("Failed to remove transaction: %v", err)
	}

	if m.Size() != 0 {
		t.Fatalf("Expected size 0 after removal, got %d", m.Size())
	}

	// Try to get removed transaction (should fail)
	_, err = m.GetTransaction(tx.Hash)
	if err == nil {
		t.Fatal("Expected error when getting removed transaction")
	}
}

func TestMempoolCleanup(t *testing.T) {
	m := createTestMempool()

	// Add old transaction
	oldTx := createTestTransaction(0, 100)
	oldTx.AddedAt = time.Now().Add(-2 * time.Second) // 2 seconds ago (older than MaxTxAge)
	m.txs[oldTx.Hash] = oldTx
	m.nonce[oldTx.From] = oldTx.Nonce

	// Add recent transaction
	recentTx := createTestTransaction(1, 100)
	recentTx.Hash = sha256.Sum256([]byte{99})
	m.AddTransaction(recentTx)

	if m.Size() != 2 {
		t.Fatalf("Expected size 2, got %d", m.Size())
	}

	// Run cleanup
	removed := m.Cleanup()

	if removed != 1 {
		t.Fatalf("Expected 1 transaction removed, got %d", removed)
	}

	if m.Size() != 1 {
		t.Fatalf("Expected size 1 after cleanup, got %d", m.Size())
	}

	// Old transaction should be gone
	_, err := m.GetTransaction(oldTx.Hash)
	if err == nil {
		t.Fatal("Old transaction should have been removed")
	}

	// Recent transaction should still exist
	_, err = m.GetTransaction(recentTx.Hash)
	if err != nil {
		t.Fatal("Recent transaction should still exist")
	}
}

func TestMempoolStartStop(t *testing.T) {
	m := createTestMempool()

	ctx := context.Background()
	err := m.Start(ctx)
	if err != nil {
		t.Fatalf("Failed to start mempool: %v", err)
	}

	// Add a transaction
	tx := createTestTransaction(0, 100)
	err = m.AddTransaction(tx)
	if err != nil {
		t.Fatalf("Failed to add transaction: %v", err)
	}

	// Wait a bit for cleanup loop to run
	time.Sleep(100 * time.Millisecond)

	// Stop mempool
	m.Stop()
}
