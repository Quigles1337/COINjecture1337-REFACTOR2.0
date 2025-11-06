// IPFS pinning quorum for CID integrity (SEC-005)
package ipfs

import (
	"context"
	"crypto/sha256"
	"fmt"
	"io"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/config"
	shell "github.com/ipfs/go-ipfs-api"
)

// IPFSClient manages IPFS operations with quorum pinning
type IPFSClient struct {
	config    config.IPFSConfig
	log       *logger.Logger
	shells    []*shell.Shell
	quorumNum int // Numerator (e.g., 2 in "2/3")
	quorumDen int // Denominator (e.g., 3 in "2/3")
}

// PinResult represents the result of a pin operation
type PinResult struct {
	Node    string
	Success bool
	Error   error
	Size    uint64
	Hash    string
}

// PinManifest holds pinning metadata for audit
type PinManifest struct {
	CID          string    `json:"cid"`
	Size         uint64    `json:"size"`
	ContentHash  string    `json:"content_hash"`
	PinnedNodes  []string  `json:"pinned_nodes"`
	Quorum       string    `json:"quorum"`
	Timestamp    time.Time `json:"timestamp"`
	SignatureHex string    `json:"signature,omitempty"`
}

// NewIPFSClient creates a new IPFS client with quorum support
func NewIPFSClient(cfg config.IPFSConfig, log *logger.Logger) (*IPFSClient, error) {
	if len(cfg.Nodes) == 0 {
		return nil, fmt.Errorf("no IPFS nodes configured")
	}

	// Parse quorum (e.g., "2/3")
	parts := strings.Split(cfg.PinQuorum, "/")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid quorum format: %s (expected format: N/M)", cfg.PinQuorum)
	}

	quorumNum, err := strconv.Atoi(parts[0])
	if err != nil {
		return nil, fmt.Errorf("invalid quorum numerator: %s", parts[0])
	}

	quorumDen, err := strconv.Atoi(parts[1])
	if err != nil {
		return nil, fmt.Errorf("invalid quorum denominator: %s", parts[1])
	}

	if quorumNum > quorumDen || quorumNum < 1 {
		return nil, fmt.Errorf("invalid quorum: %d/%d", quorumNum, quorumDen)
	}

	// Create shell connections to all nodes
	shells := make([]*shell.Shell, len(cfg.Nodes))
	for i, node := range cfg.Nodes {
		shells[i] = shell.NewShell(node)
		log.WithField("node", node).Debug("Connected to IPFS node")
	}

	client := &IPFSClient{
		config:    cfg,
		log:       log,
		shells:    shells,
		quorumNum: quorumNum,
		quorumDen: quorumDen,
	}

	return client, nil
}

// PinWithQuorum pins content to quorum of IPFS nodes
func (c *IPFSClient) PinWithQuorum(ctx context.Context, content io.Reader) (*PinManifest, error) {
	// Read content into memory (needed for multiple uploads)
	data, err := io.ReadAll(content)
	if err != nil {
		return nil, fmt.Errorf("failed to read content: %w", err)
	}

	// Compute content hash for integrity check
	contentHash := sha256.Sum256(data)

	// Pin to all nodes in parallel
	results := make(chan PinResult, len(c.shells))
	var wg sync.WaitGroup

	for i, sh := range c.shells {
		wg.Add(1)
		go func(nodeIndex int, shell *shell.Shell, nodeAddr string) {
			defer wg.Done()

			// Create context with timeout
			_, cancel := context.WithTimeout(ctx, c.config.PinTimeout)
			defer cancel()

			// Add content to IPFS
			cid, err := shell.Add(strings.NewReader(string(data)))
			if err != nil {
				results <- PinResult{
					Node:    nodeAddr,
					Success: false,
					Error:   err,
				}
				return
			}

			// Pin the CID
			err = shell.Pin(cid)
			if err != nil {
				results <- PinResult{
					Node:    nodeAddr,
					Success: false,
					Error:   err,
					Hash:    cid,
				}
				return
			}

			// Get size (stat)
			stat, err := shell.ObjectStat(cid)
			var size uint64
			if err == nil && stat != nil {
				size = uint64(stat.CumulativeSize)
			}

			results <- PinResult{
				Node:    nodeAddr,
				Success: true,
				Hash:    cid,
				Size:    size,
			}

		}(i, sh, c.config.Nodes[i])
	}

	// Wait for all pins to complete
	go func() {
		wg.Wait()
		close(results)
	}()

	// Collect results
	var successfulPins []PinResult
	var cid string
	var size uint64

	for result := range results {
		if result.Success {
			successfulPins = append(successfulPins, result)
			if cid == "" {
				cid = result.Hash
				size = result.Size
			}
			c.log.WithField("node", result.Node).WithField("cid", result.Hash).Debug("Pin successful")
		} else {
			c.log.WithError(result.Error).WithField("node", result.Node).Warn("Pin failed")
		}
	}

	// Check quorum
	if len(successfulPins) < c.quorumNum {
		return nil, fmt.Errorf("pin quorum not met: got %d/%d, required %d/%d",
			len(successfulPins), len(c.shells), c.quorumNum, c.quorumDen)
	}

	c.log.WithField("cid", cid).
		WithField("successful_pins", len(successfulPins)).
		WithField("quorum", c.config.PinQuorum).
		Info("Content pinned with quorum")

	// Build manifest
	pinnedNodes := make([]string, len(successfulPins))
	for i, pin := range successfulPins {
		pinnedNodes[i] = pin.Node
	}

	manifest := &PinManifest{
		CID:         cid,
		Size:        size,
		ContentHash: fmt.Sprintf("%x", contentHash),
		PinnedNodes: pinnedNodes,
		Quorum:      c.config.PinQuorum,
		Timestamp:   time.Now(),
	}

	return manifest, nil
}

// VerifyCID verifies CID exists and matches expected size/hash
func (c *IPFSClient) VerifyCID(ctx context.Context, cid string, expectedSize uint64, expectedHash string) error {
	// Check CID on all nodes
	successCount := 0

	for i, sh := range c.shells {
		// Get object stat
		stat, err := sh.ObjectStat(cid)
		if err != nil {
			c.log.WithError(err).
				WithField("node", c.config.Nodes[i]).
				WithField("cid", cid).
				Warn("CID stat failed")
			continue
		}

		// Verify size
		if stat == nil {
			c.log.WithField("node", c.config.Nodes[i]).
				WithField("cid", cid).
				Warn("CID stat returned nil")
			continue
		}

		actualSize := uint64(stat.CumulativeSize)
		if expectedSize > 0 && actualSize != expectedSize {
			c.log.WithField("node", c.config.Nodes[i]).
				WithField("cid", cid).
				WithField("expected_size", expectedSize).
				WithField("actual_size", actualSize).
				Warn("CID size mismatch")
			continue
		}

		// TODO: Verify content hash by downloading and hashing
		// For now, just check that CID exists

		successCount++
	}

	// Check quorum
	if successCount < c.quorumNum {
		return fmt.Errorf("CID verification quorum not met: %d/%d nodes confirmed",
			successCount, len(c.shells))
	}

	return nil
}

// Get retrieves content by CID from any available node
func (c *IPFSClient) Get(ctx context.Context, cid string) (io.ReadCloser, error) {
	// Try each node until one succeeds
	for i, sh := range c.shells {
		reader, err := sh.Cat(cid)
		if err != nil {
			c.log.WithError(err).
				WithField("node", c.config.Nodes[i]).
				WithField("cid", cid).
				Debug("Failed to get CID from node, trying next")
			continue
		}

		c.log.WithField("node", c.config.Nodes[i]).
			WithField("cid", cid).
			Debug("Retrieved CID from node")

		return reader, nil
	}

	return nil, fmt.Errorf("failed to retrieve CID from any node: %s", cid)
}

// AuditCIDs checks a list of CIDs for integrity
func (c *IPFSClient) AuditCIDs(ctx context.Context, cids []string) (missing []string, sizeMismatch []string) {
	for _, cid := range cids {
		err := c.VerifyCID(ctx, cid, 0, "")
		if err != nil {
			missing = append(missing, cid)
			c.log.WithError(err).WithField("cid", cid).Warn("CID audit failed")
		}
	}

	return missing, sizeMismatch
}

// QuorumStatus returns current quorum configuration
func (c *IPFSClient) QuorumStatus() map[string]interface{} {
	return map[string]interface{}{
		"quorum":      c.config.PinQuorum,
		"quorum_num":  c.quorumNum,
		"quorum_den":  c.quorumDen,
		"nodes":       c.config.Nodes,
		"node_count":  len(c.shells),
		"min_success": c.quorumNum,
	}
}
