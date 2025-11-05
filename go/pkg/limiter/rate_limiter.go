// Token bucket rate limiter for defense against DoS (Layer 2: Network Edge)
//
// This limiter provides defense-in-depth rate limiting with:
// 1. Global limit (total requests/sec across all sources)
// 2. Per-IP limit (prevents single IP flooding)
// 3. Per-Peer-ID limit (prevents malicious peers)
// 4. Early reject (before expensive verification)
// 5. Backpressure (queue full → reject immediately)
// 6. Prometheus metrics
package limiter

import (
	"fmt"
	"net"
	"sync"
	"sync/atomic"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/config"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"golang.org/x/time/rate"
)

// Prometheus metrics
var (
	rateLimitRejected = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "coinjecture_rate_limit_rejected_total",
			Help: "Total requests rejected by rate limiter",
		},
		[]string{"type"}, // type: ip, peer, global, queue_full
	)

	rateLimitAccepted = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "coinjecture_rate_limit_accepted_total",
			Help: "Total requests accepted by rate limiter",
		},
		[]string{"type"},
	)

	queueSize = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "coinjecture_verifier_queue_size",
			Help: "Current size of verification queue",
		},
	)

	activeLimiters = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "coinjecture_active_limiters",
			Help: "Number of active rate limiters",
		},
		[]string{"type"}, // type: ip, peer
	)
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

	// Backpressure: queue size tracking
	currentQueueSize  int64 // atomic
	maxQueueSize      int64
	queueFullRejected uint64 // atomic counter

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
		cleanupInterval:  5 * time.Minute,
		stopChan:         make(chan struct{}),
		currentQueueSize: 0,
		maxQueueSize:     1000, // Default max queue size
	}

	// Start cleanup goroutine
	go rl.cleanupStale()

	return rl
}

// CheckIP checks if request from IP is allowed
func (rl *RateLimiter) CheckIP(ip string) (bool, error) {
	if !rl.config.Enabled {
		rateLimitAccepted.WithLabelValues("disabled").Inc()
		return true, nil
	}

	// Check backpressure first (early reject before expensive operations)
	currentQueue := atomic.LoadInt64(&rl.currentQueueSize)
	if currentQueue >= rl.maxQueueSize {
		atomic.AddUint64(&rl.queueFullRejected, 1)
		rateLimitRejected.WithLabelValues("queue_full").Inc()
		rl.log.WithField("ip", ip).WithField("queue_size", currentQueue).Warn("Queue full, rejecting request")
		return false, fmt.Errorf("queue full: verification queue at capacity")
	}

	// Check global limit (early reject)
	if !rl.globalLimiter.Allow() {
		rateLimitRejected.WithLabelValues("global").Inc()
		rl.log.WithField("ip", ip).Warn("Global rate limit exceeded")
		return false, fmt.Errorf("global rate limit exceeded")
	}

	// Get or create IP limiter
	limiter := rl.getIPLimiter(ip)

	if !limiter.Allow() {
		rateLimitRejected.WithLabelValues("ip").Inc()
		rl.log.WithField("ip", ip).Warn("IP rate limit exceeded")
		return false, fmt.Errorf("IP rate limit exceeded")
	}

	rateLimitAccepted.WithLabelValues("ip").Inc()
	return true, nil
}

// CheckPeerID checks if request from peer ID is allowed
func (rl *RateLimiter) CheckPeerID(peerID string) (bool, error) {
	if !rl.config.Enabled {
		rateLimitAccepted.WithLabelValues("disabled").Inc()
		return true, nil
	}

	// Check backpressure first (early reject)
	currentQueue := atomic.LoadInt64(&rl.currentQueueSize)
	if currentQueue >= rl.maxQueueSize {
		atomic.AddUint64(&rl.queueFullRejected, 1)
		rateLimitRejected.WithLabelValues("queue_full").Inc()
		rl.log.WithField("peer_id", peerID).WithField("queue_size", currentQueue).Warn("Queue full, rejecting request")
		return false, fmt.Errorf("queue full: verification queue at capacity")
	}

	// Check global limit first
	if !rl.globalLimiter.Allow() {
		rateLimitRejected.WithLabelValues("global").Inc()
		rl.log.WithField("peer_id", peerID).Warn("Global rate limit exceeded")
		return false, fmt.Errorf("global rate limit exceeded")
	}

	// Get or create peer limiter
	limiter := rl.getPeerLimiter(peerID)

	if !limiter.Allow() {
		rateLimitRejected.WithLabelValues("peer").Inc()
		rl.log.WithField("peer_id", peerID).Warn("Peer rate limit exceeded")
		return false, fmt.Errorf("peer rate limit exceeded")
	}

	rateLimitAccepted.WithLabelValues("peer").Inc()
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

	// Update Prometheus metrics
	activeLimiters.WithLabelValues("ip").Set(float64(ipCount))
	activeLimiters.WithLabelValues("peer").Set(float64(peerCount))
	queueSize.Set(float64(atomic.LoadInt64(&rl.currentQueueSize)))

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
		"enabled":             rl.config.Enabled,
		"ip_limiters":         ipCount,
		"peer_limiters":       peerCount,
		"global_limit":        rl.config.GlobalLimit,
		"ip_limit":            rl.config.IPLimit,
		"peer_id_limit":       rl.config.PeerIDLimit,
		"current_queue_size":  atomic.LoadInt64(&rl.currentQueueSize),
		"max_queue_size":      rl.maxQueueSize,
		"queue_full_rejected": atomic.LoadUint64(&rl.queueFullRejected),
	}
}

// SetQueueSize updates the current verification queue size (called by verifier)
func (rl *RateLimiter) SetQueueSize(size int64) {
	atomic.StoreInt64(&rl.currentQueueSize, size)
	queueSize.Set(float64(size))
}

// GetQueueSize returns the current queue size
func (rl *RateLimiter) GetQueueSize() int64 {
	return atomic.LoadInt64(&rl.currentQueueSize)
}

// SetMaxQueueSize sets the maximum allowed queue size for backpressure
func (rl *RateLimiter) SetMaxQueueSize(maxSize int64) {
	rl.maxQueueSize = maxSize
}

// CheckBackpressure checks if queue is near capacity (for early warning)
func (rl *RateLimiter) CheckBackpressure() (bool, float64) {
	current := float64(atomic.LoadInt64(&rl.currentQueueSize))
	max := float64(rl.maxQueueSize)

	if max == 0 {
		return false, 0.0
	}

	utilization := current / max
	nearCapacity := utilization > 0.8 // 80% threshold

	return nearCapacity, utilization
}
