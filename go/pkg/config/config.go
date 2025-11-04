// Configuration management for COINjecture daemon
package config

import (
	"fmt"
	"time"

	"github.com/spf13/viper"
)

// Config holds all daemon configuration
type Config struct {
	API         APIConfig         `mapstructure:"api"`
	P2P         P2PConfig         `mapstructure:"p2p"`
	IPFS        IPFSConfig        `mapstructure:"ipfs"`
	RateLimiter RateLimiterConfig `mapstructure:"rate_limiter"`
	Metrics     MetricsConfig     `mapstructure:"metrics"`
	Features    FeaturesConfig    `mapstructure:"features"`
}

// APIConfig for REST API server
type APIConfig struct {
	Port            int           `mapstructure:"port"`
	Host            string        `mapstructure:"host"`
	ReadTimeout     time.Duration `mapstructure:"read_timeout"`
	WriteTimeout    time.Duration `mapstructure:"write_timeout"`
	MaxRequestSize  int64         `mapstructure:"max_request_size"`
	EnableCORS      bool          `mapstructure:"enable_cors"`
	TrustedProxies  []string      `mapstructure:"trusted_proxies"`
}

// P2PConfig for peer-to-peer networking
type P2PConfig struct {
	Port                int      `mapstructure:"port"`
	BootstrapPeers      []string `mapstructure:"bootstrap_peers"`
	MaxPeers            int      `mapstructure:"max_peers"`
	EquilibriumLambda   float64  `mapstructure:"equilibrium_lambda"`
	BroadcastInterval   int      `mapstructure:"broadcast_interval_ms"`
	PeerScoringEnabled  bool     `mapstructure:"peer_scoring_enabled"`
	QuarantineThreshold int      `mapstructure:"quarantine_threshold"`
}

// IPFSConfig for IPFS client
type IPFSConfig struct {
	Nodes             []string      `mapstructure:"nodes"`
	PinQuorum         string        `mapstructure:"pin_quorum"` // e.g., "2/3"
	PinTimeout        time.Duration `mapstructure:"pin_timeout"`
	AuditInterval     time.Duration `mapstructure:"audit_interval"`
	EnableManifests   bool          `mapstructure:"enable_manifests"`
	ColdStorageMirror string        `mapstructure:"cold_storage_mirror"`
}

// RateLimiterConfig for request rate limiting
type RateLimiterConfig struct {
	Enabled          bool          `mapstructure:"enabled"`
	IPLimit          int           `mapstructure:"ip_limit"`
	IPWindow         time.Duration `mapstructure:"ip_window"`
	PeerIDLimit      int           `mapstructure:"peer_id_limit"`
	PeerIDWindow     time.Duration `mapstructure:"peer_id_window"`
	GlobalLimit      int           `mapstructure:"global_limit"`
	GlobalWindow     time.Duration `mapstructure:"global_window"`
	BurstMultiplier  float64       `mapstructure:"burst_multiplier"`
}

// MetricsConfig for Prometheus metrics
type MetricsConfig struct {
	Port    int    `mapstructure:"port"`
	Path    string `mapstructure:"path"`
	Enabled bool   `mapstructure:"enabled"`
}

// FeaturesConfig for feature flags (cutover strategy)
type FeaturesConfig struct {
	CodecMode              string `mapstructure:"codec_mode"` // legacy_only, shadow, refactored_primary, refactored_only
	ValidateAgainstLegacy  bool   `mapstructure:"validate_against_legacy"`
	StrictCIDEnforcement   bool   `mapstructure:"strict_cid_enforcement"`
	EnablePinQuorum        bool   `mapstructure:"enable_pin_quorum"`
	EnableAdmissionControl bool   `mapstructure:"enable_admission_control"`
}

// Default configuration
func DefaultConfig() *Config {
	return &Config{
		API: APIConfig{
			Port:           12346,
			Host:           "0.0.0.0",
			ReadTimeout:    10 * time.Second,
			WriteTimeout:   10 * time.Second,
			MaxRequestSize: 10 * 1024 * 1024, // 10MB
			EnableCORS:     true,
			TrustedProxies: []string{},
		},
		P2P: P2PConfig{
			Port:                5000,
			BootstrapPeers:      []string{},
			MaxPeers:            50,
			EquilibriumLambda:   0.7071, // √2/2
			BroadcastInterval:   14140,  // 14.14s in milliseconds
			PeerScoringEnabled:  true,
			QuarantineThreshold: 10,
		},
		IPFS: IPFSConfig{
			Nodes:             []string{"localhost:5001"},
			PinQuorum:         "2/3",
			PinTimeout:        30 * time.Second,
			AuditInterval:     6 * time.Hour,
			EnableManifests:   true,
			ColdStorageMirror: "",
		},
		RateLimiter: RateLimiterConfig{
			Enabled:         true,
			IPLimit:         100,
			IPWindow:        time.Minute,
			PeerIDLimit:     200,
			PeerIDWindow:    time.Minute,
			GlobalLimit:     10000,
			GlobalWindow:    time.Minute,
			BurstMultiplier: 1.5,
		},
		Metrics: MetricsConfig{
			Port:    9090,
			Path:    "/metrics",
			Enabled: true,
		},
		Features: FeaturesConfig{
			CodecMode:              "shadow", // Start in shadow mode
			ValidateAgainstLegacy:  true,
			StrictCIDEnforcement:   true,
			EnablePinQuorum:        true,
			EnableAdmissionControl: true,
		},
	}
}

// LoadConfig loads configuration from file or returns defaults
func LoadConfig(path string) (*Config, error) {
	cfg := DefaultConfig()

	if path == "" {
		return cfg, nil
	}

	viper.SetConfigFile(path)
	viper.SetConfigType("yaml")

	// Set defaults
	setDefaults(viper.GetViper())

	// Read config file
	if err := viper.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	// Unmarshal into struct
	if err := viper.Unmarshal(cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	// Validate configuration
	if err := cfg.Validate(); err != nil {
		return nil, fmt.Errorf("invalid configuration: %w", err)
	}

	return cfg, nil
}

// Validate checks configuration for errors
func (c *Config) Validate() error {
	// Validate codec mode
	validCodecModes := map[string]bool{
		"legacy_only":         true,
		"shadow":              true,
		"refactored_primary":  true,
		"refactored_only":     true,
	}
	if !validCodecModes[c.Features.CodecMode] {
		return fmt.Errorf("invalid codec_mode: %s", c.Features.CodecMode)
	}

	// Validate pin quorum format (e.g., "2/3")
	// TODO: Parse and validate quorum string

	// Validate ports
	if c.API.Port < 1 || c.API.Port > 65535 {
		return fmt.Errorf("invalid API port: %d", c.API.Port)
	}
	if c.P2P.Port < 1 || c.P2P.Port > 65535 {
		return fmt.Errorf("invalid P2P port: %d", c.P2P.Port)
	}
	if c.Metrics.Port < 1 || c.Metrics.Port > 65535 {
		return fmt.Errorf("invalid metrics port: %d", c.Metrics.Port)
	}

	return nil
}

func setDefaults(v *viper.Viper) {
	v.SetDefault("api.port", 12346)
	v.SetDefault("api.host", "0.0.0.0")
	v.SetDefault("p2p.port", 5000)
	v.SetDefault("p2p.equilibrium_lambda", 0.7071)
	v.SetDefault("ipfs.pin_quorum", "2/3")
	v.SetDefault("rate_limiter.enabled", true)
	v.SetDefault("metrics.enabled", true)
	v.SetDefault("features.codec_mode", "shadow")
}
