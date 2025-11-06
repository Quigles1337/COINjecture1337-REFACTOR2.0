// API handlers for financial primitives (transactions, accounts, escrows)
package api

import (
	"encoding/hex"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/bindings"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
	"github.com/gin-gonic/gin"
)

// ==================== TRANSACTION ENDPOINTS ====================

// handleSubmitTransaction submits a transaction to the mempool and broadcasts to network
func (s *Server) handleSubmitTransaction(c *gin.Context) {
	var txReq struct {
		From      string `json:"from" binding:"required"`      // Hex-encoded sender address (64 chars)
		To        string `json:"to" binding:"required"`        // Hex-encoded recipient address (64 chars)
		Amount    uint64 `json:"amount" binding:"required"`    // Amount in wei
		Nonce     uint64 `json:"nonce" binding:"required"`     // Transaction nonce
		GasLimit  uint64 `json:"gas_limit" binding:"required"` // Gas limit (21000 for transfer)
		GasPrice  uint64 `json:"gas_price" binding:"required"` // Gas price in wei
		Signature string `json:"signature" binding:"required"` // Hex-encoded signature (128 chars)
		Data      string `json:"data"`                         // Optional hex-encoded data
	}

	if err := c.ShouldBindJSON(&txReq); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "invalid transaction format",
			"details": err.Error(),
		})
		return
	}

	// Parse addresses
	from, err := hexToBytes32(txReq.From)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid from address"})
		return
	}

	to, err := hexToBytes32(txReq.To)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid to address"})
		return
	}

	// Parse signature
	signature, err := hexToBytes64(txReq.Signature)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid signature"})
		return
	}

	// Parse data (if provided)
	var data []byte
	if txReq.Data != "" {
		data, err = hex.DecodeString(txReq.Data)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid data hex"})
			return
		}
	}

	// Create transaction for validation
	tx := &bindings.Transaction{
		CodecVersion: 1,
		TxType:       bindings.TxTypeTransfer,
		From:         from,
		To:           to,
		Amount:       txReq.Amount,
		Nonce:        txReq.Nonce,
		GasLimit:     txReq.GasLimit,
		GasPrice:     txReq.GasPrice,
		Signature:    signature,
		Data:         data,
		Timestamp:    time.Now().Unix(),
	}

	// Get sender account state
	senderAccount, err := s.stateManager.GetAccount(from)
	if err != nil {
		s.log.WithError(err).Error("Failed to get sender account")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}

	senderState := &bindings.AccountState{
		Balance: senderAccount.Balance,
		Nonce:   senderAccount.Nonce,
	}

	// Validate transaction via Rust FFI
	result, err := bindings.VerifyTransaction(tx, senderState)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "transaction validation failed",
			"details": err.Error(),
		})
		return
	}

	if !result.Valid {
		c.JSON(http.StatusBadRequest, gin.H{"error": "transaction invalid"})
		return
	}

	// Compute transaction hash
	txHash := computeTxHash(tx)

	// Create mempool transaction
	mempoolTx := &mempool.Transaction{
		Hash:      txHash,
		From:      tx.From,
		To:        tx.To,
		Amount:    tx.Amount,
		Nonce:     tx.Nonce,
		GasLimit:  tx.GasLimit,
		GasPrice:  tx.GasPrice,
		Signature: tx.Signature,
		Data:      tx.Data,
		Timestamp: tx.Timestamp,
		TxType:    tx.TxType,
		Fee:       result.Fee,
		AddedAt:   time.Now(),
	}

	// Add to mempool
	if err := s.mempool.AddTransaction(mempoolTx); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "failed to add to mempool",
			"details": err.Error(),
		})
		return
	}

	// Broadcast to P2P network
	s.p2pManager.BroadcastTransaction(mempoolTx)

	// Broadcast to WebSocket clients
	s.BroadcastTransaction(txHash, from, to, tx.Amount, result.Fee)

	s.log.WithFields(logger.Fields{
		"tx_hash": fmt.Sprintf("%x", txHash[:8]),
		"from":    fmt.Sprintf("%x", from[:8]),
		"to":      fmt.Sprintf("%x", to[:8]),
		"amount":  tx.Amount,
		"fee":     result.Fee,
	}).Info("Transaction submitted")

	c.JSON(http.StatusAccepted, gin.H{
		"status":     "accepted",
		"tx_hash":    fmt.Sprintf("%x", txHash),
		"total_cost": result.TotalCost,
		"fee":        result.Fee,
		"gas_used":   result.GasUsed,
	})
}

// handleGetTransaction retrieves a transaction by hash
func (s *Server) handleGetTransaction(c *gin.Context) {
	txHashHex := c.Param("hash")

	txHash, err := hexToBytes32(txHashHex)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid transaction hash"})
		return
	}

	// Check mempool first
	tx, err := s.mempool.GetTransaction(txHash)
	if err == nil {
		c.JSON(http.StatusOK, gin.H{
			"status":     "pending",
			"tx_hash":    fmt.Sprintf("%x", tx.Hash),
			"from":       fmt.Sprintf("%x", tx.From),
			"to":         fmt.Sprintf("%x", tx.To),
			"amount":     tx.Amount,
			"nonce":      tx.Nonce,
			"gas_limit":  tx.GasLimit,
			"gas_price":  tx.GasPrice,
			"fee":        tx.Fee,
			"timestamp":  tx.Timestamp,
			"added_at":   tx.AddedAt.Unix(),
			"priority":   tx.Priority,
		})
		return
	}

	// TODO: Check database for confirmed transaction

	c.JSON(http.StatusNotFound, gin.H{"error": "transaction not found"})
}

// handleMempoolStats returns mempool statistics
func (s *Server) handleMempoolStats(c *gin.Context) {
	stats := gin.H{
		"size":         s.mempool.Size(),
		"max_size":     10000, // TODO: Get from config
		"utilization":  float64(s.mempool.Size()) / 10000.0,
	}

	// Get top transactions (by priority)
	topTxs := s.mempool.GetTopTransactions(10)
	topHashes := make([]string, len(topTxs))
	for i, tx := range topTxs {
		topHashes[i] = fmt.Sprintf("%x", tx.Hash[:8])
	}
	stats["top_transactions"] = topHashes

	c.JSON(http.StatusOK, stats)
}

// ==================== ACCOUNT ENDPOINTS ====================

// handleGetAccount retrieves account balance and nonce
func (s *Server) handleGetAccount(c *gin.Context) {
	addressHex := c.Param("address")

	address, err := hexToBytes32(addressHex)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid address"})
		return
	}

	account, err := s.stateManager.GetAccount(address)
	if err != nil {
		s.log.WithError(err).Error("Failed to get account")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"address":    fmt.Sprintf("%x", address),
		"balance":    account.Balance,
		"nonce":      account.Nonce,
		"created_at": account.CreatedAt.Unix(),
		"updated_at": account.UpdatedAt.Unix(),
	})
}

// handleGetAccountNonce retrieves just the account nonce
func (s *Server) handleGetAccountNonce(c *gin.Context) {
	addressHex := c.Param("address")

	address, err := hexToBytes32(addressHex)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid address"})
		return
	}

	account, err := s.stateManager.GetAccount(address)
	if err != nil {
		s.log.WithError(err).Error("Failed to get account")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"address": fmt.Sprintf("%x", address),
		"nonce":   account.Nonce,
	})
}

// ==================== ESCROW ENDPOINTS ====================

// handleCreateEscrow creates a new bounty escrow
func (s *Server) handleCreateEscrow(c *gin.Context) {
	var escrowReq struct {
		Submitter   string `json:"submitter" binding:"required"`    // Hex address
		Amount      uint64 `json:"amount" binding:"required"`       // Wei
		ProblemHash string `json:"problem_hash" binding:"required"` // Hex hash
		ExpiryBlock uint64 `json:"expiry_block" binding:"required"` // Block number
	}

	if err := c.ShouldBindJSON(&escrowReq); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "invalid escrow request",
			"details": err.Error(),
		})
		return
	}

	// Parse submitter
	submitter, err := hexToBytes32(escrowReq.Submitter)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid submitter address"})
		return
	}

	// Parse problem hash
	problemHash, err := hexToBytes32(escrowReq.ProblemHash)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid problem hash"})
		return
	}

	// Get current block number (TODO: from consensus)
	currentBlock := uint64(1000) // Placeholder

	// Validate escrow parameters via Rust FFI
	err = bindings.ValidateEscrowCreation(escrowReq.Amount, currentBlock, escrowReq.ExpiryBlock)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "invalid escrow parameters",
			"details": err.Error(),
		})
		return
	}

	// Compute escrow ID
	escrowID, err := bindings.ComputeEscrowID(submitter, problemHash, currentBlock)
	if err != nil {
		s.log.WithError(err).Error("Failed to compute escrow ID")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}

	// Create escrow
	escrow := &state.Escrow{
		ID:           escrowID,
		Submitter:    submitter,
		Amount:       escrowReq.Amount,
		ProblemHash:  problemHash,
		CreatedBlock: currentBlock,
		ExpiryBlock:  escrowReq.ExpiryBlock,
		State:        state.EscrowLocked,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	err = s.stateManager.CreateEscrow(escrow)
	if err != nil {
		s.log.WithError(err).Error("Failed to create escrow")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create escrow"})
		return
	}

	// Broadcast to WebSocket clients
	s.BroadcastEscrow(escrowID, "created", gin.H{
		"submitter":     fmt.Sprintf("%x", submitter),
		"amount":        escrowReq.Amount,
		"created_block": currentBlock,
		"expiry_block":  escrowReq.ExpiryBlock,
	})

	s.log.WithFields(logger.Fields{
		"escrow_id":    fmt.Sprintf("%x", escrowID[:8]),
		"submitter":    fmt.Sprintf("%x", submitter[:8]),
		"amount":       escrowReq.Amount,
		"expiry_block": escrowReq.ExpiryBlock,
	}).Info("Escrow created")

	c.JSON(http.StatusCreated, gin.H{
		"status":        "created",
		"escrow_id":     fmt.Sprintf("%x", escrowID),
		"submitter":     fmt.Sprintf("%x", submitter),
		"amount":        escrowReq.Amount,
		"created_block": currentBlock,
		"expiry_block":  escrowReq.ExpiryBlock,
	})
}

// handleGetEscrow retrieves escrow details
func (s *Server) handleGetEscrow(c *gin.Context) {
	escrowIDHex := c.Param("id")

	escrowID, err := hexToBytes32(escrowIDHex)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid escrow ID"})
		return
	}

	escrow, err := s.stateManager.GetEscrow(escrowID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "escrow not found"})
		return
	}

	response := gin.H{
		"escrow_id":     fmt.Sprintf("%x", escrow.ID),
		"submitter":     fmt.Sprintf("%x", escrow.Submitter),
		"amount":        escrow.Amount,
		"problem_hash":  fmt.Sprintf("%x", escrow.ProblemHash),
		"created_block": escrow.CreatedBlock,
		"expiry_block":  escrow.ExpiryBlock,
		"state":         escrowStateToString(escrow.State),
		"created_at":    escrow.CreatedAt.Unix(),
		"updated_at":    escrow.UpdatedAt.Unix(),
	}

	if escrow.Recipient != nil {
		response["recipient"] = fmt.Sprintf("%x", *escrow.Recipient)
	}
	if escrow.SettledBlock != nil {
		response["settled_block"] = *escrow.SettledBlock
	}
	if escrow.SettlementTx != nil {
		response["settlement_tx"] = fmt.Sprintf("%x", *escrow.SettlementTx)
	}

	c.JSON(http.StatusOK, response)
}

// ==================== HELPER FUNCTIONS ====================

// hexToBytes32 converts hex string to [32]byte
func hexToBytes32(hexStr string) ([32]byte, error) {
	var result [32]byte

	// Remove 0x prefix if present
	if len(hexStr) >= 2 && hexStr[:2] == "0x" {
		hexStr = hexStr[2:]
	}

	if len(hexStr) != 64 {
		return result, fmt.Errorf("hex string must be 64 characters")
	}

	bytes, err := hex.DecodeString(hexStr)
	if err != nil {
		return result, err
	}

	copy(result[:], bytes)
	return result, nil
}

// hexToBytes64 converts hex string to [64]byte
func hexToBytes64(hexStr string) ([64]byte, error) {
	var result [64]byte

	// Remove 0x prefix if present
	if len(hexStr) >= 2 && hexStr[:2] == "0x" {
		hexStr = hexStr[2:]
	}

	if len(hexStr) != 128 {
		return result, fmt.Errorf("hex string must be 128 characters")
	}

	bytes, err := hex.DecodeString(hexStr)
	if err != nil {
		return result, err
	}

	copy(result[:], bytes)
	return result, nil
}

// computeTxHash computes transaction hash (same as in transactions.go)
func computeTxHash(tx *bindings.Transaction) [32]byte {
	message := make([]byte, 0, 256)
	message = append(message, tx.CodecVersion)
	message = append(message, tx.TxType)
	message = append(message, tx.From[:]...)
	message = append(message, tx.To[:]...)
	message = append(message, uint64ToBytes(tx.Amount)...)
	message = append(message, uint64ToBytes(tx.Nonce)...)
	message = append(message, uint64ToBytes(tx.GasLimit)...)
	message = append(message, uint64ToBytes(tx.GasPrice)...)
	message = append(message, uint32ToBytes(uint32(len(tx.Data)))...)
	message = append(message, tx.Data...)
	message = append(message, int64ToBytes(tx.Timestamp)...)

	hash, _ := bindings.SHA256(message)
	return hash
}

func uint64ToBytes(n uint64) []byte {
	b := make([]byte, 8)
	b[0] = byte(n)
	b[1] = byte(n >> 8)
	b[2] = byte(n >> 16)
	b[3] = byte(n >> 24)
	b[4] = byte(n >> 32)
	b[5] = byte(n >> 40)
	b[6] = byte(n >> 48)
	b[7] = byte(n >> 56)
	return b
}

func uint32ToBytes(n uint32) []byte {
	b := make([]byte, 4)
	b[0] = byte(n)
	b[1] = byte(n >> 8)
	b[2] = byte(n >> 16)
	b[3] = byte(n >> 24)
	return b
}

func int64ToBytes(n int64) []byte {
	return uint64ToBytes(uint64(n))
}

func escrowStateToString(escrowState uint8) string {
	switch escrowState {
	case state.EscrowLocked:
		return "locked"
	case state.EscrowReleased:
		return "released"
	case state.EscrowRefunded:
		return "refunded"
	default:
		return "unknown"
	}
}

// ==================== BLOCK ENDPOINTS ====================

// handleGetBlock retrieves a block by hash
func (s *Server) handleGetBlock(c *gin.Context) {
	blockHashHex := c.Param("hash")

	blockHash, err := hexToBytes32(blockHashHex)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid block hash"})
		return
	}

	// TODO: Retrieve from state manager once block storage is implemented
	// For now, check if it's in P2P cache or return not found

	s.log.WithField("block_hash", fmt.Sprintf("%x", blockHash[:8])).Debug("Block lookup (storage not yet implemented)")

	c.JSON(http.StatusNotFound, gin.H{
		"error":  "block not found",
		"reason": "block storage not yet implemented",
		"hint":   "blocks are propagated via P2P but not persisted to database yet",
	})
}

// handleGetLatestBlock retrieves the latest block
func (s *Server) handleGetLatestBlock(c *gin.Context) {
	// TODO: Retrieve latest block from state manager once implemented
	// For now, return placeholder response with expected structure

	s.log.Debug("Latest block lookup (storage not yet implemented)")

	c.JSON(http.StatusOK, gin.H{
		"status": "operational",
		"message": "block storage not yet implemented",
		"hint":    "latest block will be available once consensus and block persistence are added",
		"expected_fields": gin.H{
			"block_number": "uint64",
			"block_hash":   "hex string",
			"parent_hash":  "hex string",
			"state_root":   "hex string",
			"tx_root":      "hex string",
			"timestamp":    "unix timestamp",
			"miner":        "hex address",
			"difficulty":   "uint64",
			"tx_count":     "number of transactions",
		},
	})
}

// handleGetBlockByNumber retrieves a block by number
func (s *Server) handleGetBlockByNumber(c *gin.Context) {
	blockNumberStr := c.Param("number")

	blockNumber, err := strconv.ParseUint(blockNumberStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid block number"})
		return
	}

	// TODO: Retrieve from state manager once block storage is implemented

	s.log.WithField("block_number", blockNumber).Debug("Block lookup by number (storage not yet implemented)")

	c.JSON(http.StatusNotFound, gin.H{
		"error":  "block not found",
		"reason": "block storage not yet implemented",
		"hint":   "blocks are propagated via P2P but not persisted to database yet",
	})
}
