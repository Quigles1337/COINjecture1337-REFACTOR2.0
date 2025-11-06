// Validator slashing for malicious behavior in PoA consensus
package consensus

import (
	"fmt"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
)

// SlashingOffense represents different types of slashable offenses
type SlashingOffense uint8

const (
	// OffenseInvalidBlock: Validator produced an invalid block (bad hash, bad state root, etc.)
	OffenseInvalidBlock SlashingOffense = 1

	// OffenseDoubleSign: Validator signed two different blocks at the same height (equivocation)
	OffenseDoubleSign SlashingOffense = 2

	// OffenseWrongTurn: Validator produced block out of turn (violated round-robin)
	OffenseWrongTurn SlashingOffense = 3

	// OffenseLiveness: Validator failed to produce blocks when it was their turn (downtime)
	OffenseLiveness SlashingOffense = 4
)

// SlashingEvent records a slashable offense
type SlashingEvent struct {
	Validator   [32]byte        // Offending validator address
	Offense     SlashingOffense // Type of offense
	BlockNumber uint64          // Block height where offense occurred
	Evidence    []byte          // Proof of offense (serialized block data, etc.)
	Timestamp   int64           // When offense was detected
	Severity    uint8           // Severity score (1=minor, 10=critical)
}

// ValidatorStatus tracks validator reputation and slashing history
type ValidatorStatus struct {
	Address         [32]byte
	IsActive        bool    // Whether validator is currently active
	SlashCount      int     // Number of times slashed
	TotalSeverity   int     // Cumulative severity score
	LastSlashTime   int64   // Timestamp of last slash
	MissedBlocks    int     // Consecutive missed blocks (for liveness tracking)
	ProducedBlocks  int     // Total blocks successfully produced
	InvalidBlocks   int     // Total invalid blocks produced
	ReputationScore float64 // 0.0 (banned) to 1.0 (perfect)
}

// SlashingConfig holds slashing parameters
type SlashingConfig struct {
	EnableSlashing       bool    // Master switch for slashing
	BanThreshold         int     // Total severity score before permanent ban
	JailThreshold        int     // Severity score for temporary jail
	JailDuration         time.Duration // How long validators are jailed
	LivenessWindow       int     // How many blocks to track for liveness
	LivenessThreshold    int     // Max missed blocks before slashing
	ReputationDecayRate  float64 // How fast reputation recovers (per block)
	MinReputationToValidate float64 // Minimum reputation to remain active validator
}

// DefaultSlashingConfig returns sensible slashing defaults
func DefaultSlashingConfig() SlashingConfig {
	return SlashingConfig{
		EnableSlashing:          true,
		BanThreshold:            100,  // Permanent ban after 100 severity points
		JailThreshold:           30,   // Temporary jail after 30 severity points
		JailDuration:            1 * time.Hour,
		LivenessWindow:          100,  // Track last 100 blocks
		LivenessThreshold:       10,   // Max 10 consecutive missed blocks
		ReputationDecayRate:     0.01, // Reputation recovers 1% per block
		MinReputationToValidate: 0.6,  // Need 60% reputation to validate
	}
}

// SlashingManager manages validator slashing and reputation
type SlashingManager struct {
	config SlashingConfig
	log    *logger.Logger

	// Validator tracking
	validators map[[32]byte]*ValidatorStatus
	jailedUntil map[[32]byte]int64 // validator -> jail release timestamp
	mu         sync.RWMutex

	// Slashing events (for audit trail)
	events     []*SlashingEvent
	eventsLock sync.RWMutex
}

// NewSlashingManager creates a new slashing manager
func NewSlashingManager(config SlashingConfig, log *logger.Logger) *SlashingManager {
	return &SlashingManager{
		config:      config,
		log:         log,
		validators:  make(map[[32]byte]*ValidatorStatus),
		jailedUntil: make(map[[32]byte]int64),
		events:      make([]*SlashingEvent, 0),
	}
}

// RegisterValidator registers a validator for tracking
func (sm *SlashingManager) RegisterValidator(address [32]byte) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if _, exists := sm.validators[address]; exists {
		return
	}

	sm.validators[address] = &ValidatorStatus{
		Address:         address,
		IsActive:        true,
		ReputationScore: 1.0, // Start with perfect reputation
	}

	sm.log.WithField("validator", fmt.Sprintf("%x", address[:8])).Info("Validator registered for slashing tracking")
}

// Slash records a slashing event for a validator
func (sm *SlashingManager) Slash(validator [32]byte, offense SlashingOffense, blockNumber uint64, evidence []byte) error {
	if !sm.config.EnableSlashing {
		return nil // Slashing disabled
	}

	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Get or create validator status
	status, exists := sm.validators[validator]
	if !exists {
		status = &ValidatorStatus{
			Address:         validator,
			IsActive:        true,
			ReputationScore: 1.0,
		}
		sm.validators[validator] = status
	}

	// Calculate severity based on offense type
	severity := sm.getSeverity(offense)

	// Create slashing event
	event := &SlashingEvent{
		Validator:   validator,
		Offense:     offense,
		BlockNumber: blockNumber,
		Evidence:    evidence,
		Timestamp:   time.Now().Unix(),
		Severity:    severity,
	}

	// Record event
	sm.eventsLock.Lock()
	sm.events = append(sm.events, event)
	sm.eventsLock.Unlock()

	// Update validator status
	status.SlashCount++
	status.TotalSeverity += int(severity)
	status.LastSlashTime = event.Timestamp

	// Update specific counters
	if offense == OffenseInvalidBlock {
		status.InvalidBlocks++
	}

	// Calculate new reputation (more severe = bigger drop)
	reputationPenalty := float64(severity) / 10.0 // Severity 10 = 100% reputation loss
	status.ReputationScore -= reputationPenalty
	if status.ReputationScore < 0 {
		status.ReputationScore = 0
	}

	sm.log.WithFields(logger.Fields{
		"validator":   fmt.Sprintf("%x", validator[:8]),
		"offense":     offense,
		"severity":    severity,
		"block":       blockNumber,
		"slash_count": status.SlashCount,
		"reputation":  fmt.Sprintf("%.2f", status.ReputationScore),
	}).Warn("Validator slashed")

	// Check if validator should be banned
	if status.TotalSeverity >= sm.config.BanThreshold {
		status.IsActive = false
		sm.log.WithFields(logger.Fields{
			"validator": fmt.Sprintf("%x", validator[:8]),
			"severity":  status.TotalSeverity,
		}).Error("Validator permanently banned")
		return fmt.Errorf("validator banned for excessive slashing")
	}

	// Check if validator should be jailed
	if status.TotalSeverity >= sm.config.JailThreshold {
		jailUntil := time.Now().Add(sm.config.JailDuration).Unix()
		sm.jailedUntil[validator] = jailUntil
		sm.log.WithFields(logger.Fields{
			"validator":  fmt.Sprintf("%x", validator[:8]),
			"jail_until": time.Unix(jailUntil, 0),
		}).Warn("Validator jailed")
	}

	// Check if reputation too low
	if status.ReputationScore < sm.config.MinReputationToValidate {
		status.IsActive = false
		sm.log.WithFields(logger.Fields{
			"validator":  fmt.Sprintf("%x", validator[:8]),
			"reputation": fmt.Sprintf("%.2f", status.ReputationScore),
		}).Warn("Validator deactivated due to low reputation")
	}

	return nil
}

// getSeverity returns severity score for an offense type
func (sm *SlashingManager) getSeverity(offense SlashingOffense) uint8 {
	switch offense {
	case OffenseDoubleSign:
		return 10 // Critical: Intentional attack
	case OffenseInvalidBlock:
		return 5 // Serious: Either malicious or buggy
	case OffenseWrongTurn:
		return 3 // Medium: Protocol violation
	case OffenseLiveness:
		return 1 // Minor: Could be network issues
	default:
		return 1
	}
}

// IsValidatorActive checks if a validator can currently validate
func (sm *SlashingManager) IsValidatorActive(validator [32]byte) bool {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	status, exists := sm.validators[validator]
	if !exists {
		return true // Unknown validators are allowed (will be registered on first block)
	}

	// Check if banned
	if !status.IsActive {
		return false
	}

	// Check if jailed
	if jailUntil, jailed := sm.jailedUntil[validator]; jailed {
		if time.Now().Unix() < jailUntil {
			return false // Still jailed
		}
		// Jail expired, remove from jail
		delete(sm.jailedUntil, validator)
		sm.log.WithField("validator", fmt.Sprintf("%x", validator[:8])).Info("Validator released from jail")
	}

	return true
}

// RecordBlockProduced records a successfully produced block (increases reputation)
func (sm *SlashingManager) RecordBlockProduced(validator [32]byte) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	status, exists := sm.validators[validator]
	if !exists {
		return
	}

	status.ProducedBlocks++
	status.MissedBlocks = 0 // Reset missed blocks counter

	// Slowly recover reputation with good behavior
	if status.ReputationScore < 1.0 {
		status.ReputationScore += sm.config.ReputationDecayRate
		if status.ReputationScore > 1.0 {
			status.ReputationScore = 1.0
		}
	}

	// Reactivate if reputation recovered
	if !status.IsActive && status.ReputationScore >= sm.config.MinReputationToValidate {
		status.IsActive = true
		sm.log.WithFields(logger.Fields{
			"validator":  fmt.Sprintf("%x", validator[:8]),
			"reputation": fmt.Sprintf("%.2f", status.ReputationScore),
		}).Info("Validator reactivated after reputation recovery")
	}
}

// RecordMissedBlock records a missed block (for liveness tracking)
func (sm *SlashingManager) RecordMissedBlock(validator [32]byte, blockNumber uint64) error {
	if !sm.config.EnableSlashing {
		return nil
	}

	sm.mu.Lock()
	defer sm.mu.Unlock()

	status, exists := sm.validators[validator]
	if !exists {
		return nil // Unknown validator, ignore
	}

	status.MissedBlocks++

	// Check if exceeded liveness threshold
	if status.MissedBlocks >= sm.config.LivenessThreshold {
		sm.mu.Unlock() // Unlock before calling Slash (which locks)
		err := sm.Slash(validator, OffenseLiveness, blockNumber, nil)
		sm.mu.Lock()
		return err
	}

	return nil
}

// GetValidatorStatus returns the current status of a validator
func (sm *SlashingManager) GetValidatorStatus(validator [32]byte) *ValidatorStatus {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	status, exists := sm.validators[validator]
	if !exists {
		return nil
	}

	// Return a copy to prevent external mutation
	statusCopy := *status
	return &statusCopy
}

// GetSlashingEvents returns all slashing events (for audit)
func (sm *SlashingManager) GetSlashingEvents() []*SlashingEvent {
	sm.eventsLock.RLock()
	defer sm.eventsLock.RUnlock()

	// Return copy
	events := make([]*SlashingEvent, len(sm.events))
	copy(events, sm.events)
	return events
}

// GetStats returns slashing manager statistics
func (sm *SlashingManager) GetStats() map[string]interface{} {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	activeCount := 0
	jailedCount := 0
	bannedCount := 0
	totalSlashes := 0

	for _, status := range sm.validators {
		totalSlashes += status.SlashCount
		if !status.IsActive {
			bannedCount++
		} else if _, jailed := sm.jailedUntil[status.Address]; jailed {
			jailedCount++
		} else {
			activeCount++
		}
	}

	sm.eventsLock.RLock()
	eventCount := len(sm.events)
	sm.eventsLock.RUnlock()

	return map[string]interface{}{
		"total_validators": len(sm.validators),
		"active_validators": activeCount,
		"jailed_validators": jailedCount,
		"banned_validators": bannedCount,
		"total_slashing_events": eventCount,
		"total_slashes": totalSlashes,
	}
}
