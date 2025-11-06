// Fork choice and chain reorganization for PoA consensus
package consensus

import (
	"fmt"
	"sync"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
)

// ChainTip represents a potential chain head
type ChainTip struct {
	Block       *Block
	Height      uint64
	TotalWeight uint64 // For PoA, weight = height (all blocks have same difficulty)
}

// ForkChoice manages competing chains and selects the canonical chain
type ForkChoice struct {
	// Current canonical chain
	canonicalTip *ChainTip

	// Competing chain tips (block_hash -> ChainTip)
	competingTips map[[32]byte]*ChainTip

	// Block cache for chain traversal (block_hash -> Block)
	blockCache map[[32]byte]*Block

	log  *logger.Logger
	lock sync.RWMutex
}

// NewForkChoice creates a new fork choice manager
func NewForkChoice(genesisBlock *Block, log *logger.Logger) *ForkChoice {
	fc := &ForkChoice{
		canonicalTip: &ChainTip{
			Block:       genesisBlock,
			Height:      0,
			TotalWeight: 0,
		},
		competingTips: make(map[[32]byte]*ChainTip),
		blockCache:    make(map[[32]byte]*Block),
		log:           log,
	}

	// Cache genesis block
	if genesisBlock != nil {
		fc.blockCache[genesisBlock.BlockHash] = genesisBlock
	}

	return fc
}

// AddBlock adds a block to fork choice consideration
// Returns true if this block becomes the new canonical tip (triggering reorg)
func (fc *ForkChoice) AddBlock(block *Block) (bool, error) {
	fc.lock.Lock()
	defer fc.lock.Unlock()

	// Check if we already have this block
	if _, exists := fc.blockCache[block.BlockHash]; exists {
		fc.log.WithField("block_hash", fmt.Sprintf("%x", block.BlockHash[:8])).Debug("Block already in fork choice")
		return false, nil
	}

	// Validate block
	if !block.IsValid() {
		return false, fmt.Errorf("invalid block")
	}

	// Cache block
	fc.blockCache[block.BlockHash] = block

	// Verify parent exists
	if _, err := fc.findChainTip(block.ParentHash); err != nil {
		return false, fmt.Errorf("failed to find parent chain tip: %w", err)
	}

	newTip := &ChainTip{
		Block:       block,
		Height:      block.BlockNumber,
		TotalWeight: block.BlockNumber, // For PoA, weight = height
	}

	// Add to competing tips
	fc.competingTips[block.BlockHash] = newTip

	// Check if this is a better chain than current canonical
	shouldReorg := fc.shouldReorganize(newTip)

	if shouldReorg {
		fc.log.WithFields(logger.Fields{
			"old_height": fc.canonicalTip.Height,
			"new_height": newTip.Height,
			"block_hash": fmt.Sprintf("%x", block.BlockHash[:8]),
		}).Info("Fork choice: selecting new canonical chain")

		fc.canonicalTip = newTip

		// Clean up old competing tips that are now clearly not canonical
		fc.pruneCompetingTips()
	} else {
		fc.log.WithFields(logger.Fields{
			"canonical_height": fc.canonicalTip.Height,
			"block_height":     newTip.Height,
			"block_hash":       fmt.Sprintf("%x", block.BlockHash[:8]),
		}).Debug("Fork choice: keeping current canonical chain")
	}

	return shouldReorg, nil
}

// shouldReorganize determines if we should switch to a new chain
// Fork choice rule: Longest valid chain (highest block number)
func (fc *ForkChoice) shouldReorganize(newTip *ChainTip) bool {
	// Rule 1: New chain must be longer (or equal but with better hash)
	if newTip.Height > fc.canonicalTip.Height {
		return true
	}

	// Rule 2: If same height, use block hash as tiebreaker (lower hash wins)
	if newTip.Height == fc.canonicalTip.Height {
		for i := 0; i < 32; i++ {
			if newTip.Block.BlockHash[i] < fc.canonicalTip.Block.BlockHash[i] {
				return true
			} else if newTip.Block.BlockHash[i] > fc.canonicalTip.Block.BlockHash[i] {
				return false
			}
		}
	}

	return false
}

// findChainTip finds the chain tip for a given parent hash
func (fc *ForkChoice) findChainTip(parentHash [32]byte) (*ChainTip, error) {
	// Check if parent is in competing tips
	if tip, exists := fc.competingTips[parentHash]; exists {
		return tip, nil
	}

	// Check if parent is the canonical tip
	if fc.canonicalTip.Block.BlockHash == parentHash {
		return fc.canonicalTip, nil
	}

	// Check if parent is in block cache
	if block, exists := fc.blockCache[parentHash]; exists {
		return &ChainTip{
			Block:       block,
			Height:      block.BlockNumber,
			TotalWeight: block.BlockNumber,
		}, nil
	}

	return nil, fmt.Errorf("parent block not found: %x", parentHash[:8])
}

// pruneCompetingTips removes old tips that are clearly not canonical
// Keeps tips within 10 blocks of canonical height
func (fc *ForkChoice) pruneCompetingTips() {
	const maxDepth = 10

	for hash, tip := range fc.competingTips {
		if tip.Height+maxDepth < fc.canonicalTip.Height {
			delete(fc.competingTips, hash)
			fc.log.WithFields(logger.Fields{
				"block_hash":  fmt.Sprintf("%x", hash[:8]),
				"block_height": tip.Height,
			}).Debug("Pruned old competing tip")
		}
	}

	// Prune old blocks from cache (keep 100 blocks)
	if len(fc.blockCache) > 100 {
		// Simple pruning: remove blocks older than canonical - 50
		for hash, block := range fc.blockCache {
			if block.BlockNumber+50 < fc.canonicalTip.Height {
				delete(fc.blockCache, hash)
			}
		}
	}
}

// GetCanonicalTip returns the current canonical chain tip
func (fc *ForkChoice) GetCanonicalTip() *ChainTip {
	fc.lock.RLock()
	defer fc.lock.RUnlock()
	return fc.canonicalTip
}

// GetCanonicalBlock returns the current canonical chain head block
func (fc *ForkChoice) GetCanonicalBlock() *Block {
	fc.lock.RLock()
	defer fc.lock.RUnlock()
	return fc.canonicalTip.Block
}

// GetBlock retrieves a block by hash from the cache
func (fc *ForkChoice) GetBlock(blockHash [32]byte) (*Block, bool) {
	fc.lock.RLock()
	defer fc.lock.RUnlock()
	block, exists := fc.blockCache[blockHash]
	return block, exists
}

// GetChainPath returns the path from fork point to new tip
// Used for chain reorganization
func (fc *ForkChoice) GetChainPath(fromHash, toHash [32]byte) ([]*Block, error) {
	fc.lock.RLock()
	defer fc.lock.RUnlock()

	path := []*Block{}
	currentHash := toHash

	// Walk backwards from toHash to fromHash
	for i := 0; i < 1000; i++ { // Safety limit
		if currentHash == fromHash {
			// Found common ancestor, reverse path
			for i, j := 0, len(path)-1; i < j; i, j = i+1, j-1 {
				path[i], path[j] = path[j], path[i]
			}
			return path, nil
		}

		block, exists := fc.blockCache[currentHash]
		if !exists {
			return nil, fmt.Errorf("block not found in cache: %x", currentHash[:8])
		}

		path = append(path, block)
		currentHash = block.ParentHash
	}

	return nil, fmt.Errorf("chain path too long or no common ancestor")
}

// GetStats returns fork choice statistics
func (fc *ForkChoice) GetStats() map[string]interface{} {
	fc.lock.RLock()
	defer fc.lock.RUnlock()

	return map[string]interface{}{
		"canonical_height":  fc.canonicalTip.Height,
		"canonical_hash":    fmt.Sprintf("%x", fc.canonicalTip.Block.BlockHash[:8]),
		"competing_tips":    len(fc.competingTips),
		"cached_blocks":     len(fc.blockCache),
		"canonical_weight":  fc.canonicalTip.TotalWeight,
	}
}
