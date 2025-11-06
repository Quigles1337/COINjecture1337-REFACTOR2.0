// Mempool manager for pending transactions
package mempool

import (
	"container/heap"
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
)

// Transaction represents a pending transaction
type Transaction struct {
	Hash      [32]byte    // SHA-256 hash of transaction
	From      [32]byte    // Sender address (Ed25519 public key)
	To        [32]byte    // Recipient address
	Amount    uint64      // Amount in wei
	Nonce     uint64      // Nonce for replay protection
	GasLimit  uint64      // Gas limit
	GasPrice  uint64      // Gas price (wei per gas)
	Signature [64]byte    // Ed25519 signature
	Data      []byte      // Transaction data (problem submissions, etc.)
	Timestamp int64       // Transaction timestamp
	TxType    uint8       // 1=Transfer, 2=ProblemSubmission, 3=BountyPayment
	Fee       uint64      // Calculated fee (gas_limit * gas_price)
	AddedAt   time.Time   // When tx was added to mempool
	Priority  float64     // Priority score for ordering
}

// Config holds mempool configuration
type Config struct {
	MaxSize          int           // Maximum number of transactions
	MaxTxAge         time.Duration // Maximum age before eviction (e.g., 1 hour)
	CleanupInterval  time.Duration // How often to clean up expired txs
	PriorityThreshold float64      // Minimum priority to accept
}

// DefaultConfig returns sensible defaults
func DefaultConfig() Config {
	return Config{
		MaxSize:          10000,                // 10k pending transactions
		MaxTxAge:         1 * time.Hour,        // 1 hour max age
		CleanupInterval:  5 * time.Minute,      // Cleanup every 5 minutes
		PriorityThreshold: 0.0,                 // Accept all valid txs
	}
}

// Mempool manages pending transactions with priority ordering
type Mempool struct {
	config Config
	log    *logger.Logger

	mu    sync.RWMutex
	txs   map[[32]byte]*Transaction      // Hash → Transaction
	queue priorityQueue                   // Priority queue for ordering
	nonce map[[32]byte]uint64             // Address → highest nonce seen

	stopChan chan struct{}
}

// NewMempool creates a new mempool manager
func NewMempool(cfg Config, log *logger.Logger) *Mempool {
	m := &Mempool{
		config:   cfg,
		log:      log,
		txs:      make(map[[32]byte]*Transaction),
		queue:    make(priorityQueue, 0, cfg.MaxSize),
		nonce:    make(map[[32]byte]uint64),
		stopChan: make(chan struct{}),
	}

	heap.Init(&m.queue)
	return m
}

// Start starts background cleanup goroutine
func (m *Mempool) Start(ctx context.Context) error {
	m.log.WithField("max_size", m.config.MaxSize).Info("Starting mempool")

	go m.cleanupLoop()

	return nil
}

// Stop stops the mempool
func (m *Mempool) Stop() {
	close(m.stopChan)
	m.log.Info("Mempool stopped")
}

// AddTransaction adds a validated transaction to the mempool
//
// Returns error if:
// - Transaction already exists
// - Mempool is full (and tx priority is too low)
// - Nonce is too old (replay protection)
func (m *Mempool) AddTransaction(tx *Transaction) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Check if already in mempool
	if _, exists := m.txs[tx.Hash]; exists {
		return fmt.Errorf("transaction already in mempool: %x", tx.Hash[:8])
	}

	// Check nonce ordering (must be >= current highest)
	highestNonce, exists := m.nonce[tx.From]
	if exists && tx.Nonce < highestNonce {
		return fmt.Errorf("nonce too old: got %d, expected >= %d", tx.Nonce, highestNonce)
	}

	// Calculate priority (higher fee = higher priority)
	tx.Priority = calculatePriority(tx)
	tx.AddedAt = time.Now()

	// Check priority threshold
	if tx.Priority < m.config.PriorityThreshold {
		return fmt.Errorf("priority too low: %.2f < %.2f", tx.Priority, m.config.PriorityThreshold)
	}

	// Evict lowest priority tx if mempool is full
	if len(m.txs) >= m.config.MaxSize {
		if err := m.evictLowestPriority(tx.Priority); err != nil {
			return fmt.Errorf("mempool full and tx priority too low: %w", err)
		}
	}

	// Add to mempool
	m.txs[tx.Hash] = tx
	heap.Push(&m.queue, tx)
	m.nonce[tx.From] = tx.Nonce

	m.log.WithFields(logger.Fields{
		"hash":     fmt.Sprintf("%x", tx.Hash[:8]),
		"from":     fmt.Sprintf("%x", tx.From[:8]),
		"to":       fmt.Sprintf("%x", tx.To[:8]),
		"amount":   tx.Amount,
		"nonce":    tx.Nonce,
		"priority": tx.Priority,
		"size":     len(m.txs),
	}).Debug("Transaction added to mempool")

	return nil
}

// GetTransaction retrieves a transaction by hash
func (m *Mempool) GetTransaction(hash [32]byte) (*Transaction, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	tx, exists := m.txs[hash]
	if !exists {
		return nil, fmt.Errorf("transaction not found: %x", hash[:8])
	}

	return tx, nil
}

// RemoveTransaction removes a transaction from the mempool (e.g., after inclusion in block)
func (m *Mempool) RemoveTransaction(hash [32]byte) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	_, exists := m.txs[hash]
	if !exists {
		return fmt.Errorf("transaction not found: %x", hash[:8])
	}

	delete(m.txs, hash)
	// Note: We don't remove from heap immediately (lazy deletion on Pop)

	m.log.WithFields(logger.Fields{
		"hash": fmt.Sprintf("%x", hash[:8]),
		"size": len(m.txs),
	}).Debug("Transaction removed from mempool")

	return nil
}

// GetTopTransactions returns the N highest-priority transactions
//
// Used by block builders to select transactions for new blocks.
func (m *Mempool) GetTopTransactions(n int) []*Transaction {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if n > len(m.txs) {
		n = len(m.txs)
	}

	// Make a copy of queue to avoid modifying original
	queueCopy := make(priorityQueue, len(m.queue))
	copy(queueCopy, m.queue)
	heap.Init(&queueCopy)

	result := make([]*Transaction, 0, n)
	for i := 0; i < n && len(queueCopy) > 0; i++ {
		tx := heap.Pop(&queueCopy).(*Transaction)

		// Skip if transaction was removed (lazy deletion)
		if _, exists := m.txs[tx.Hash]; !exists {
			i-- // Don't count this iteration
			continue
		}

		result = append(result, tx)
	}

	return result
}

// Size returns the current number of transactions in mempool
func (m *Mempool) Size() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.txs)
}

// Cleanup removes expired transactions
func (m *Mempool) Cleanup() int {
	m.mu.Lock()
	defer m.mu.Unlock()

	now := time.Now()
	removed := 0

	for hash, tx := range m.txs {
		if now.Sub(tx.AddedAt) > m.config.MaxTxAge {
			delete(m.txs, hash)
			removed++
		}
	}

	if removed > 0 {
		m.log.WithFields(logger.Fields{
			"removed": removed,
			"remaining": len(m.txs),
		}).Info("Mempool cleanup completed")
	}

	return removed
}

// cleanupLoop periodically removes expired transactions
func (m *Mempool) cleanupLoop() {
	ticker := time.NewTicker(m.config.CleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			m.Cleanup()
		case <-m.stopChan:
			return
		}
	}
}

// evictLowestPriority removes the lowest-priority transaction
func (m *Mempool) evictLowestPriority(newTxPriority float64) error {
	if len(m.queue) == 0 {
		return fmt.Errorf("cannot evict from empty mempool")
	}

	// Peek at lowest priority tx (at end of heap)
	lowestTx := m.queue[len(m.queue)-1]

	if newTxPriority <= lowestTx.Priority {
		return fmt.Errorf("new tx priority %.2f <= lowest priority %.2f", newTxPriority, lowestTx.Priority)
	}

	// Remove lowest priority tx
	delete(m.txs, lowestTx.Hash)

	m.log.WithFields(logger.Fields{
		"evicted_hash": fmt.Sprintf("%x", lowestTx.Hash[:8]),
		"evicted_priority": lowestTx.Priority,
		"new_priority": newTxPriority,
	}).Debug("Evicted low-priority transaction")

	return nil
}

// calculatePriority computes transaction priority score
//
// Priority = fee_per_gas * age_multiplier
//
// Higher fees and older transactions get higher priority.
func calculatePriority(tx *Transaction) float64 {
	// Base priority: fee per gas unit
	feePerGas := float64(tx.Fee) / float64(tx.GasLimit)

	// Age multiplier (older transactions get slight priority boost)
	ageBoost := 1.0 + (time.Since(tx.AddedAt).Seconds() / 3600.0) // +1.0 per hour

	return feePerGas * ageBoost
}

// ==================== PRIORITY QUEUE IMPLEMENTATION ====================

// priorityQueue implements heap.Interface for transaction ordering
type priorityQueue []*Transaction

func (pq priorityQueue) Len() int { return len(pq) }

func (pq priorityQueue) Less(i, j int) bool {
	// Max-heap: higher priority comes first
	return pq[i].Priority > pq[j].Priority
}

func (pq priorityQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
}

func (pq *priorityQueue) Push(x interface{}) {
	*pq = append(*pq, x.(*Transaction))
}

func (pq *priorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	tx := old[n-1]
	*pq = old[0 : n-1]
	return tx
}
