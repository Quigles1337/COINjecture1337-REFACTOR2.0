// REST API server for COINjecture
package api

import (
	"context"
	"fmt"
	"net/http"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/config"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/ipfs"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/limiter"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/p2p"
	"github.com/gin-gonic/gin"
)

// Server is the REST API server
type Server struct {
	config      config.APIConfig
	log         *logger.Logger
	limiter     *limiter.RateLimiter
	ipfsClient  *ipfs.IPFSClient
	p2pManager  *p2p.Manager
	router      *gin.Engine
	httpServer  *http.Server
}

// NewServer creates a new API server
func NewServer(
	cfg config.APIConfig,
	rateLimiter *limiter.RateLimiter,
	ipfsClient *ipfs.IPFSClient,
	p2pManager *p2p.Manager,
	log *logger.Logger,
) *Server {
	// Set Gin mode
	gin.SetMode(gin.ReleaseMode)

	router := gin.New()
	router.Use(gin.Recovery())

	s := &Server{
		config:     cfg,
		log:        log,
		limiter:    rateLimiter,
		ipfsClient: ipfsClient,
		p2pManager: p2pManager,
		router:     router,
	}

	s.setupRoutes()
	return s
}

// setupRoutes configures API routes
func (s *Server) setupRoutes() {
	// Middleware
	s.router.Use(s.rateLimitMiddleware())
	s.router.Use(s.loggingMiddleware())

	if s.config.EnableCORS {
		s.router.Use(corsMiddleware())
	}

	// Health check
	s.router.GET("/health", s.handleHealth)

	// API v1
	v1 := s.router.Group("/v1")
	{
		v1.POST("/submit_proof", s.handleSubmitProof)
		v1.GET("/block/:hash", s.handleGetBlock)
		v1.GET("/block/latest", s.handleGetLatestBlock)
		v1.GET("/ipfs/:cid", s.handleGetIPFS)
		v1.GET("/status", s.handleStatus)
	}
}

// Start starts the API server
func (s *Server) Start() error {
	addr := fmt.Sprintf("%s:%d", s.config.Host, s.config.Port)

	s.httpServer = &http.Server{
		Addr:         addr,
		Handler:      s.router,
		ReadTimeout:  s.config.ReadTimeout,
		WriteTimeout: s.config.WriteTimeout,
	}

	s.log.WithField("address", addr).Info("API server starting")
	return s.httpServer.ListenAndServe()
}

// Shutdown gracefully shuts down the server
func (s *Server) Shutdown(ctx context.Context) error {
	if s.httpServer != nil {
		return s.httpServer.Shutdown(ctx)
	}
	return nil
}

// Middleware

func (s *Server) rateLimitMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		allowed, err := s.limiter.CheckRequest(c.Request.RemoteAddr)
		if !allowed {
			s.log.WithError(err).WithField("ip", c.ClientIP()).Warn("Rate limit exceeded")
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error": "rate limit exceeded",
			})
			c.Abort()
			return
		}
		c.Next()
	}
}

func (s *Server) loggingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		s.log.WithFields(logger.Fields{
			"method": c.Request.Method,
			"path":   c.Request.URL.Path,
			"status": c.Writer.Status(),
			"ip":     c.ClientIP(),
		}).Info("API request")
	}
}

func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}

// Handlers

func (s *Server) handleHealth(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"version": "4.0.0",
	})
}

func (s *Server) handleSubmitProof(c *gin.Context) {
	// TODO: Implement proof submission with:
	// 1. Early syntactic checks
	// 2. Commitment verification
	// 3. Subset sum verification with budget
	// 4. IPFS pinning with quorum
	// 5. Broadcast to P2P network

	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "not implemented yet",
	})
}

func (s *Server) handleGetBlock(c *gin.Context) {
	hash := c.Param("hash")

	// TODO: Retrieve block from storage

	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "not implemented yet",
		"hash":  hash,
	})
}

func (s *Server) handleGetLatestBlock(c *gin.Context) {
	c.JSON(http.StatusNotImplemented, gin.H{
		"error": "not implemented yet",
	})
}

func (s *Server) handleGetIPFS(c *gin.Context) {
	cid := c.Param("cid")

	// Get content from IPFS
	reader, err := s.ipfsClient.Get(c.Request.Context(), cid)
	if err != nil {
		s.log.WithError(err).WithField("cid", cid).Error("Failed to get IPFS content")
		c.JSON(http.StatusNotFound, gin.H{
			"error": "CID not found",
		})
		return
	}
	defer reader.Close()

	// Stream content
	c.DataFromReader(http.StatusOK, -1, "application/octet-stream", reader, nil)
}

func (s *Server) handleStatus(c *gin.Context) {
	status := map[string]interface{}{
		"api_version":  "4.0.0",
		"rate_limiter": s.limiter.Stats(),
		"ipfs_quorum":  s.ipfsClient.QuorumStatus(),
		"p2p_peers":    s.p2pManager.PeerCount(),
	}

	c.JSON(http.StatusOK, status)
}
