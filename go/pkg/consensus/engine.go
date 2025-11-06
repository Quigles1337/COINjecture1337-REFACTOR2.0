// Proof-of-Authority consensus engine for COINjecture blockchain
package consensus

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

// ConsensusConfig holds consensus engine configuration
type ConsensusConfig struct {
	BlockTime    time.Duration // Target time between blocks
	Validators   [][32]byte    // List of authorized validator addresses
	ValidatorKey [32]byte      // This node's validator key (if a validator)
	IsValidator  bool          // Whether this node is a validator
}

// Engine is the Proof-of-Authority consensus engine
type Engine struct {
	config       ConsensusConfig
	builder      *BlockBuilder
	stateManager *state.StateManager
	log          *logger.Logger

	// Current chain state
	currentBlock *Block
	blockHeight  uint64
	chainLock    sync.RWMutex

	// Fork choice and chain reorganization
	forkChoice *ForkChoice

	// Block production
	blockTimer *time.Ticker
	ctx        context.Context
	cancel     context.CancelFunc

	// Callbacks
	onNewBlock func(*Block) // Called when a new block is produced
	onReorg    func(oldTip *Block, newTip *Block, reorgDepth int) // Called on chain reorg
}

// NewEngine creates a new PoA consensus engine
func NewEngine(
	cfg ConsensusConfig,
	mp *mempool.Mempool,
	sm *state.StateManager,
	log *logger.Logger,
) *Engine {
	ctx, cancel := context.WithCancel(context.Background())

	builder := NewBlockBuilder(mp, sm, log)

	return &Engine{
		config:       cfg,
		builder:      builder,
		stateManager: sm,
		log:          log,
		blockHeight:  0,
		ctx:          ctx,
		cancel:       cancel,
	}
}

// Start starts the consensus engine
func (e *Engine) Start() error {
	e.log.WithFields(logger.Fields{
		"is_validator": e.config.IsValidator,
		"block_time":   e.config.BlockTime,
		"validators":   len(e.config.Validators),
	}).Info("Starting PoA consensus engine")

	// Initialize genesis block if needed
	if e.currentBlock == nil {
		if err := e.initializeGenesis(); err != nil {
			return fmt.Errorf("failed to initialize genesis: %w", err)
		}
	}

	// Start block production if we're a validator
	if e.config.IsValidator {
		go e.blockProductionLoop()
	}

	return nil
}

// Stop stops the consensus engine
func (e *Engine) Stop() {
	e.log.Info("Stopping PoA consensus engine")

	if e.blockTimer != nil {
		e.blockTimer.Stop()
	}

	e.cancel()
}

// initializeGenesis initializes the genesis block
func (e *Engine) initializeGenesis() error {
	e.log.Info("Initializing genesis block")

	// Check if genesis already exists in database
	// TODO: Load from state manager

	// Create genesis block
	genesis := NewGenesisBlock(e.config.ValidatorKey)

	e.chainLock.Lock()
	e.currentBlock = genesis
	e.blockHeight = 0

	// Initialize fork choice with genesis
	e.forkChoice = NewForkChoice(genesis, e.log)
	e.chainLock.Unlock()

	e.log.WithFields(logger.Fields{
		"block_hash":   fmt.Sprintf("%x", genesis.BlockHash[:8]),
		"validator":    fmt.Sprintf("%x", genesis.Validator[:8]),
		"timestamp":    genesis.Timestamp,
	}).Info("Genesis block initialized")

	// TODO: Save to database

	return nil
}

// blockProductionLoop produces blocks at regular intervals
func (e *Engine) blockProductionLoop() {
	e.log.Info("Starting block production loop")

	e.blockTimer = time.NewTicker(e.config.BlockTime)
	defer e.blockTimer.Stop()

	for {
		select {
		case <-e.ctx.Done():
			e.log.Info("Block production loop stopped")
			return

		case <-e.blockTimer.C:
			if err := e.produceBlock(); err != nil {
				e.log.WithError(err).Error("Failed to produce block")
			}
		}
	}
}

// produceBlock produces a new block
func (e *Engine) produceBlock() error {
	e.chainLock.Lock()
	defer e.chainLock.Unlock()

	// Check if it's our turn to validate
	if !e.isOurTurn(e.blockHeight + 1) {
		e.log.Debug("Not our turn to validate, skipping block production")
		return nil
	}

	e.log.WithField("block_number", e.blockHeight+1).Info("Producing new block")

	// Get parent block
	parentHash := [32]byte{}
	if e.currentBlock != nil {
		parentHash = e.currentBlock.BlockHash
	}

	// Build block
	block, err := e.builder.BuildBlock(parentHash, e.blockHeight+1, e.config.ValidatorKey)
	if err != nil {
		return fmt.Errorf("failed to build block: %w", err)
	}

	// Apply block to state
	stateRoot, err := e.builder.ApplyBlock(block)
	if err != nil {
		return fmt.Errorf("failed to apply block: %w", err)
	}

	// Update block with state root
	block.StateRoot = stateRoot
	block.Finalize() // Recompute hash with new state root

	// Add to fork choice
	if e.forkChoice != nil {
		_, err := e.forkChoice.AddBlock(block)
		if err != nil {
			e.log.WithError(err).Warn("Failed to add produced block to fork choice")
		}
	}

	// Update chain state
	e.currentBlock = block
	e.blockHeight++

	e.log.WithFields(logger.Fields{
		"block_number": block.BlockNumber,
		"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		"tx_count":     len(block.Transactions),
		"gas_used":     block.GasUsed,
		"state_root":   fmt.Sprintf("%x", stateRoot[:8]),
	}).Info("New block produced")

	// Trigger callback if set
	if e.onNewBlock != nil {
		go e.onNewBlock(block)
	}

	// TODO: Save block to database

	return nil
}

// isOurTurn determines if it's this validator's turn to produce a block
// Uses round-robin validator rotation for simplicity
func (e *Engine) isOurTurn(blockNumber uint64) bool {
	if len(e.config.Validators) == 0 {
		return false
	}

	// Round-robin: block_number % num_validators
	validatorIndex := int(blockNumber % uint64(len(e.config.Validators)))
	expectedValidator := e.config.Validators[validatorIndex]

	return expectedValidator == e.config.ValidatorKey
}

// ProcessBlock processes a block received from the P2P network
func (e *Engine) ProcessBlock(block *Block) error {
	e.chainLock.Lock()
	defer e.chainLock.Unlock()

	e.log.WithFields(logger.Fields{
		"block_number": block.BlockNumber,
		"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		"validator":    fmt.Sprintf("%x", block.Validator[:8]),
	}).Info("Processing received block")

	// Validate block
	if !block.IsValid() {
		return fmt.Errorf("invalid block")
	}

	// Check if validator is authorized
	if !e.isAuthorizedValidator(block.Validator) {
		return fmt.Errorf("unauthorized validator")
	}

	// Add block to fork choice
	shouldReorg, err := e.forkChoice.AddBlock(block)
	if err != nil {
		return fmt.Errorf("fork choice rejected block: %w", err)
	}

	// If fork choice says we should reorganize, do it
	if shouldReorg {
		oldTip := e.currentBlock
		if err := e.handleChainReorganization(oldTip, block); err != nil {
			return fmt.Errorf("chain reorganization failed: %w", err)
		}
	} else {
		e.log.WithFields(logger.Fields{
			"block_number": block.BlockNumber,
			"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		}).Debug("Block accepted but not canonical (fork)")
	}

	return nil
}

// handleChainReorganization handles switching to a new canonical chain
func (e *Engine) handleChainReorganization(oldTip *Block, newTip *Block) error {
	e.log.WithFields(logger.Fields{
		"old_height": oldTip.BlockNumber,
		"old_hash":   fmt.Sprintf("%x", oldTip.BlockHash[:8]),
		"new_height": newTip.BlockNumber,
		"new_hash":   fmt.Sprintf("%x", newTip.BlockHash[:8]),
	}).Warn("Chain reorganization triggered")

	// For now, simple approach: if new chain is longer, accept it
	// TODO: Implement full state rollback and reapply
	// This requires:
	// 1. Find common ancestor
	// 2. Rollback state to ancestor
	// 3. Replay blocks from new chain

	// Update current block and height
	e.currentBlock = newTip
	e.blockHeight = newTip.BlockNumber

	reorgDepth := int(oldTip.BlockNumber) - int(newTip.BlockNumber)
	if reorgDepth < 0 {
		reorgDepth = -reorgDepth
	}

	// Trigger reorg callback if set
	if e.onReorg != nil {
		go e.onReorg(oldTip, newTip, reorgDepth)
	}

	e.log.WithFields(logger.Fields{
		"new_height": newTip.BlockNumber,
		"new_hash":   fmt.Sprintf("%x", newTip.BlockHash[:8]),
		"reorg_depth": reorgDepth,
	}).Info("Chain reorganization complete")

	return nil
}

// isAuthorizedValidator checks if an address is an authorized validator
func (e *Engine) isAuthorizedValidator(address [32]byte) bool {
	for _, validator := range e.config.Validators {
		if validator == address {
			return true
		}
	}
	return false
}

// GetCurrentBlock returns the current block
func (e *Engine) GetCurrentBlock() *Block {
	e.chainLock.RLock()
	defer e.chainLock.RUnlock()
	return e.currentBlock
}

// GetBlockHeight returns the current block height
func (e *Engine) GetBlockHeight() uint64 {
	e.chainLock.RLock()
	defer e.chainLock.RUnlock()
	return e.blockHeight
}

// SetNewBlockCallback sets a callback for when new blocks are produced
func (e *Engine) SetNewBlockCallback(callback func(*Block)) {
	e.onNewBlock = callback
}

// GetStats returns consensus engine statistics
func (e *Engine) GetStats() map[string]interface{} {
	e.chainLock.RLock()
	defer e.chainLock.RUnlock()

	stats := map[string]interface{}{
		"block_height":   e.blockHeight,
		"is_validator":   e.config.IsValidator,
		"validator_count": len(e.config.Validators),
		"block_time":     e.config.BlockTime.String(),
	}

	if e.currentBlock != nil {
		stats["current_block_hash"] = fmt.Sprintf("%x", e.currentBlock.BlockHash[:8])
		stats["current_block_txs"] = len(e.currentBlock.Transactions)
		stats["current_block_gas_used"] = e.currentBlock.GasUsed
	}

	return stats
}
