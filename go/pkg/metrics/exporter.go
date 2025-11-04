// Prometheus metrics exporter
package metrics

import (
	"context"
	"fmt"
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Exporter provides Prometheus metrics
type Exporter struct {
	port   int
	server *http.Server

	// Metrics
	BlocksSubmitted    *prometheus.CounterVec
	VerificationTime   *prometheus.HistogramVec
	PinQuorumSuccess   prometheus.Counter
	PinQuorumFailures  prometheus.Counter
	RateLimitExceeded  *prometheus.CounterVec
	ParityMatches      prometheus.Counter
	ParityDrifts       prometheus.Counter
}

// NewExporter creates a new Prometheus exporter
func NewExporter(port int) *Exporter {
	e := &Exporter{
		port: port,
		BlocksSubmitted: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "coinjecture_blocks_submitted_total",
				Help: "Total number of blocks submitted",
			},
			[]string{"status"},
		),
		VerificationTime: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "coinjecture_verification_duration_ms",
				Help:    "Block verification duration in milliseconds",
				Buckets: prometheus.ExponentialBuckets(1, 2, 10),
			},
			[]string{"tier"},
		),
		PinQuorumSuccess: prometheus.NewCounter(
			prometheus.CounterOpts{
				Name: "coinjecture_pin_quorum_success_total",
				Help: "Total successful pin quorum operations",
			},
		),
		PinQuorumFailures: prometheus.NewCounter(
			prometheus.CounterOpts{
				Name: "coinjecture_pin_quorum_failures_total",
				Help: "Total failed pin quorum operations",
			},
		),
		RateLimitExceeded: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "coinjecture_rate_limit_exceeded_total",
				Help: "Total rate limit exceeded events",
			},
			[]string{"type"},
		),
		ParityMatches: prometheus.NewCounter(
			prometheus.CounterOpts{
				Name: "coinjecture_parity_matches_total",
				Help: "Total legacy vs refactored hash matches",
			},
		),
		ParityDrifts: prometheus.NewCounter(
			prometheus.CounterOpts{
				Name: "coinjecture_parity_drifts_total",
				Help: "Total legacy vs refactored hash mismatches",
			},
		),
	}

	// Register metrics
	prometheus.MustRegister(
		e.BlocksSubmitted,
		e.VerificationTime,
		e.PinQuorumSuccess,
		e.PinQuorumFailures,
		e.RateLimitExceeded,
		e.ParityMatches,
		e.ParityDrifts,
	)

	return e
}

// Start starts the metrics HTTP server
func (e *Exporter) Start() error {
	mux := http.NewServeMux()
	mux.Handle("/metrics", promhttp.Handler())

	e.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", e.port),
		Handler: mux,
	}

	return e.server.ListenAndServe()
}

// Shutdown gracefully shuts down the metrics server
func (e *Exporter) Shutdown(ctx context.Context) error {
	if e.server != nil {
		return e.server.Shutdown(ctx)
	}
	return nil
}
