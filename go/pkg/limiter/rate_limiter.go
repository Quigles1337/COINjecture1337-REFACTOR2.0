// Token bucket rate limiter for defense against DoS
package limiter

import (
	"fmt"
	"net"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/config"
	"golang.org/x/time/rate"
)

// RateLimiter provides multi-tier rate limiting
type RateLimiter struct {
	config      config.RateLimiterConfig
	log         *logger.Logger

	// IP-based limiters
	ipLimiters  map[string]*rate.Limiter
	ipMutex     sync.RWMutex

	// Peer-ID-based limiters
	peerLimiters map[string]*rate.Limiter
	peerMutex    sync.RWMutex

	// Global limiter
	globalLimiter *rate.Limiter

	// Cleanup
	cleanupInterval time.Duration
	stopChan        chan struct{}
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(cfg config.RateLimiterConfig, log *logger.Logger) *RateLimiter {
	rl := &RateLimiter{
		config:       cfg,
		log:          log,
		ipLimiters:   make(map[string]*rate.Limiter),
		peerLimiters: make(map[string]*rate.Limiter),
		globalLimiter: rate.NewLimiter(
			rate.Limit(cfg.GlobalLimit),
			int(float64(cfg.GlobalLimit)*cfg.BurstMultiplier),
		),
		cleanupInterval: 5 * time.Minute,
		stopChan:        make(chan struct{}),
	}

	// Start cleanup goroutine
	go rl.cleanupStale()

	return rl
}

// CheckIP checks if request from IP is allowed
func (rl *RateLimiter) CheckIP(ip string) (bool, error) {
	if !rl.config.Enabled {
		return true, nil
	}

	// Check global limit first (early reject)
	if !rl.globalLimiter.Allow() {
		return false, fmt.Errorf("global rate limit exceeded")
	}

	// Get or create IP limiter
	limiter := rl.getIPLimiter(ip)

	if !limiter.Allow() {
		rl.log.WithField("ip", ip).Warn("IP rate limit exceeded")
		return false, fmt.Errorf("IP rate limit exceeded")
	}

	return true, nil
}

// CheckPeerID checks if request from peer ID is allowed
func (rl *RateLimiter) CheckPeerID(peerID string) (bool, error) {
	if !rl.config.Enabled {
		return true, nil
	}

	// Check global limit first
	if !rl.globalLimiter.Allow() {
		return false, fmt.Errorf("global rate limit exceeded")
	}

	// Get or create peer limiter
	limiter := rl.getPeerLimiter(peerID)

	if !limiter.Allow() {
		rl.log.WithField("peer_id", peerID).Warn("Peer rate limit exceeded")
		return false, fmt.Errorf("peer rate limit exceeded")
	}

	return true, nil
}

// CheckRequest checks both IP and global limits for an HTTP request
func (rl *RateLimiter) CheckRequest(remoteAddr string) (bool, error) {
	if !rl.config.Enabled {
		return true, nil
	}

	// Extract IP from remote address
	ip, _, err := net.SplitHostPort(remoteAddr)
	if err != nil {
		// If no port, assume it's just the IP
		ip = remoteAddr
	}

	return rl.CheckIP(ip)
}

// getIPLimiter gets or creates limiter for IP
func (rl *RateLimiter) getIPLimiter(ip string) *rate.Limiter {
	rl.ipMutex.RLock()
	limiter, exists := rl.ipLimiters[ip]
	rl.ipMutex.RUnlock()

	if exists {
		return limiter
	}

	// Create new limiter
	rl.ipMutex.Lock()
	defer rl.ipMutex.Unlock()

	// Double-check after acquiring write lock
	if limiter, exists := rl.ipLimiters[ip]; exists {
		return limiter
	}

	limiter = rate.NewLimiter(
		rate.Limit(rl.config.IPLimit),
		int(float64(rl.config.IPLimit)*rl.config.BurstMultiplier),
	)
	rl.ipLimiters[ip] = limiter

	return limiter
}

// getPeerLimiter gets or creates limiter for peer ID
func (rl *RateLimiter) getPeerLimiter(peerID string) *rate.Limiter {
	rl.peerMutex.RLock()
	limiter, exists := rl.peerLimiters[peerID]
	rl.peerMutex.RUnlock()

	if exists {
		return limiter
	}

	// Create new limiter
	rl.peerMutex.Lock()
	defer rl.peerMutex.Unlock()

	// Double-check
	if limiter, exists := rl.peerLimiters[peerID]; exists {
		return limiter
	}

	limiter = rate.NewLimiter(
		rate.Limit(rl.config.PeerIDLimit),
		int(float64(rl.config.PeerIDLimit)*rl.config.BurstMultiplier),
	)
	rl.peerLimiters[peerID] = limiter

	return limiter
}

// cleanupStale removes inactive limiters periodically
func (rl *RateLimiter) cleanupStale() {
	ticker := time.NewTicker(rl.cleanupInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			rl.cleanup()
		case <-rl.stopChan:
			return
		}
	}
}

func (rl *RateLimiter) cleanup() {
	// Clean IP limiters
	rl.ipMutex.Lock()
	for ip, limiter := range rl.ipLimiters {
		// Remove if limiter hasn't been used (has full tokens)
		if limiter.Tokens() == float64(limiter.Burst()) {
			delete(rl.ipLimiters, ip)
		}
	}
	ipCount := len(rl.ipLimiters)
	rl.ipMutex.Unlock()

	// Clean peer limiters
	rl.peerMutex.Lock()
	for peerID, limiter := range rl.peerLimiters {
		if limiter.Tokens() == float64(limiter.Burst()) {
			delete(rl.peerLimiters, peerID)
		}
	}
	peerCount := len(rl.peerLimiters)
	rl.peerMutex.Unlock()

	rl.log.WithField("ip_limiters", ipCount).
		WithField("peer_limiters", peerCount).
		Debug("Rate limiter cleanup completed")
}

// Stop stops the cleanup goroutine
func (rl *RateLimiter) Stop() {
	close(rl.stopChan)
}

// Stats returns current rate limiter statistics
func (rl *RateLimiter) Stats() map[string]interface{} {
	rl.ipMutex.RLock()
	ipCount := len(rl.ipLimiters)
	rl.ipMutex.RUnlock()

	rl.peerMutex.RLock()
	peerCount := len(rl.peerLimiters)
	rl.peerMutex.RUnlock()

	return map[string]interface{}{
		"enabled":        rl.config.Enabled,
		"ip_limiters":    ipCount,
		"peer_limiters":  peerCount,
		"global_limit":   rl.config.GlobalLimit,
		"ip_limit":       rl.config.IPLimit,
		"peer_id_limit":  rl.config.PeerIDLimit,
	}
}
