// WebSocket support for real-time updates
package api

import (
	"encoding/json"
	"net/http"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

// WebSocket upgrader
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins (configure properly in production)
	},
}

// WSClient represents a WebSocket client
type WSClient struct {
	conn       *websocket.Conn
	send       chan []byte
	hub        *WSHub
	subscribed map[string]bool // Subscription topics
	mu         sync.RWMutex
}

// WSHub manages WebSocket connections and broadcasts
type WSHub struct {
	clients    map[*WSClient]bool
	broadcast  chan *WSMessage
	register   chan *WSClient
	unregister chan *WSClient
	mu         sync.RWMutex
	log        *logger.Logger
}

// WSMessage represents a WebSocket message
type WSMessage struct {
	Type    string      `json:"type"`    // "transaction", "block", "escrow", "status"
	Topic   string      `json:"topic"`   // Subscription topic
	Payload interface{} `json:"payload"` // Message data
}

// NewWSHub creates a new WebSocket hub
func NewWSHub(log *logger.Logger) *WSHub {
	return &WSHub{
		clients:    make(map[*WSClient]bool),
		broadcast:  make(chan *WSMessage, 256),
		register:   make(chan *WSClient),
		unregister: make(chan *WSClient),
		log:        log,
	}
}

// Run starts the WebSocket hub
func (h *WSHub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client] = true
			h.mu.Unlock()
			h.log.WithField("client_count", len(h.clients)).Debug("WebSocket client registered")

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.send)
			}
			h.mu.Unlock()
			h.log.WithField("client_count", len(h.clients)).Debug("WebSocket client unregistered")

		case message := <-h.broadcast:
			h.mu.RLock()
			for client := range h.clients {
				// Check if client is subscribed to this topic
				client.mu.RLock()
				subscribed := client.subscribed[message.Topic] || client.subscribed["all"]
				client.mu.RUnlock()

				if subscribed {
					select {
					case client.send <- mustMarshal(message):
					default:
						// Client send buffer full, disconnect
						h.mu.RUnlock()
						h.unregister <- client
						h.mu.RLock()
					}
				}
			}
			h.mu.RUnlock()
		}
	}
}

// Broadcast sends a message to all subscribed clients
func (h *WSHub) Broadcast(msgType, topic string, payload interface{}) {
	msg := &WSMessage{
		Type:    msgType,
		Topic:   topic,
		Payload: payload,
	}

	select {
	case h.broadcast <- msg:
	default:
		h.log.Warn("WebSocket broadcast channel full, dropping message")
	}
}

// ClientCount returns the number of connected clients
func (h *WSHub) ClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// handleWebSocket handles WebSocket connections
func (s *Server) handleWebSocket(c *gin.Context) {
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		s.log.WithError(err).Error("Failed to upgrade WebSocket connection")
		return
	}

	client := &WSClient{
		conn:       conn,
		send:       make(chan []byte, 256),
		hub:        s.wsHub,
		subscribed: make(map[string]bool),
	}

	// Default subscription to "all"
	client.subscribed["all"] = true

	s.wsHub.register <- client

	// Start client goroutines
	go client.writePump()
	go client.readPump()
}

// readPump reads messages from the client (for subscriptions)
func (c *WSClient) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				c.hub.log.WithError(err).Error("WebSocket read error")
			}
			break
		}

		// Handle subscription messages
		var sub struct {
			Action string `json:"action"` // "subscribe" or "unsubscribe"
			Topic  string `json:"topic"`  // "transactions", "blocks", "escrows", "all"
		}

		if err := json.Unmarshal(message, &sub); err == nil {
			c.mu.Lock()
			if sub.Action == "subscribe" {
				c.subscribed[sub.Topic] = true
			} else if sub.Action == "unsubscribe" {
				delete(c.subscribed, sub.Topic)
			}
			c.mu.Unlock()
		}
	}
}

// writePump writes messages to the client
func (c *WSClient) writePump() {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				// Hub closed the channel
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			// Add queued messages to current websocket message
			n := len(c.send)
			for i := 0; i < n; i++ {
				w.Write([]byte{'\n'})
				w.Write(<-c.send)
			}

			if err := w.Close(); err != nil {
				return
			}

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// Helper: marshal to JSON (panic on error, for internal use)
func mustMarshal(v interface{}) []byte {
	data, err := json.Marshal(v)
	if err != nil {
		panic(err)
	}
	return data
}

// BroadcastTransaction broadcasts a transaction to WebSocket clients
func (s *Server) BroadcastTransaction(txHash [32]byte, from, to [32]byte, amount, fee uint64) {
	if s.wsHub != nil {
		s.wsHub.Broadcast("transaction", "transactions", gin.H{
			"tx_hash": mustHex(txHash[:]),
			"from":    mustHex(from[:]),
			"to":      mustHex(to[:]),
			"amount":  amount,
			"fee":     fee,
			"time":    time.Now().Unix(),
		})
	}
}

// BroadcastBlock broadcasts a block to WebSocket clients
func (s *Server) BroadcastBlock(blockNumber uint64, blockHash [32]byte, txCount int) {
	if s.wsHub != nil {
		s.wsHub.Broadcast("block", "blocks", gin.H{
			"block_number": blockNumber,
			"block_hash":   mustHex(blockHash[:]),
			"tx_count":     txCount,
			"time":         time.Now().Unix(),
		})
	}
}

// BroadcastEscrow broadcasts an escrow event to WebSocket clients
func (s *Server) BroadcastEscrow(escrowID [32]byte, event string, data interface{}) {
	if s.wsHub != nil {
		s.wsHub.Broadcast("escrow", "escrows", gin.H{
			"escrow_id": mustHex(escrowID[:]),
			"event":     event,
			"data":      data,
			"time":      time.Now().Unix(),
		})
	}
}

// Helper: convert bytes to hex string
func mustHex(b []byte) string {
	return "0x" + hexEncode(b)
}

func hexEncode(b []byte) string {
	const hexDigits = "0123456789abcdef"
	result := make([]byte, len(b)*2)
	for i, v := range b {
		result[i*2] = hexDigits[v>>4]
		result[i*2+1] = hexDigits[v&0x0f]
	}
	return string(result)
}
