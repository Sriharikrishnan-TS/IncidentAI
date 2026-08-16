package websocket

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"golang.org/x/net/websocket"
	"incidentos/backend-go/internal/queue"
)

const (
	// Time allowed to write a message to the peer
	writeWait = 10 * time.Second

	// Time allowed to read the next pong message from the peer
	pongWait = 60 * time.Second

	// Send pings to peer with this period (must be less than pongWait)
	pingPeriod = (pongWait * 9) / 10

	// Maximum message size allowed from peer
	maxMessageSize = 512
)

// Client represents a single WebSocket connection
type Client struct {
	hub    *Hub
	conn   *websocket.Conn
	send   chan []byte
	repoID string
	mu     sync.Mutex
}

// Hub maintains the set of active clients and broadcasts messages to them
type Hub struct {
	// Registered clients
	clients map[*Client]bool

	// Inbound messages from clients (not used in MVP, but kept for future)
	broadcast chan []byte

	// Register requests from clients
	register chan *Client

	// Unregister requests from clients
	unregister chan *Client

	// Room-based client mapping (repo_id -> clients)
	rooms map[string]map[*Client]bool

	// Mutex for thread-safe operations
	mu sync.RWMutex

	// Context for graceful shutdown
	ctx context.Context
}

// NewHub creates a new Hub instance
func NewHub(ctx context.Context) *Hub {
	return &Hub{
		clients:    make(map[*Client]bool),
		broadcast:  make(chan []byte, 256),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		rooms:      make(map[string]map[*Client]bool),
		ctx:        ctx,
	}
}

// Run starts the hub's main event loop
func (h *Hub) Run() {
	log.Printf("[WebSocket Hub] Starting hub event loop")
	for {
		select {
		case <-h.ctx.Done():
			log.Printf("[WebSocket Hub] Shutting down hub")
			h.closeAllConnections()
			return

		case client := <-h.register:
			h.mu.Lock()
			h.clients[client] = true
			
			// Add client to room
			if client.repoID != "" {
				if h.rooms[client.repoID] == nil {
					h.rooms[client.repoID] = make(map[*Client]bool)
				}
				h.rooms[client.repoID][client] = true
				log.Printf("[WebSocket Hub] Client registered for repo: %s (total clients: %d)", 
					client.repoID, len(h.clients))
			} else {
				log.Printf("[WebSocket Hub] Client registered without repo_id (total clients: %d)", 
					len(h.clients))
			}
			h.mu.Unlock()

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				
				// Remove from room
				if client.repoID != "" {
					if room, exists := h.rooms[client.repoID]; exists {
						delete(room, client)
						if len(room) == 0 {
							delete(h.rooms, client.repoID)
						}
					}
					log.Printf("[WebSocket Hub] Client unregistered from repo: %s (remaining clients: %d)", 
						client.repoID, len(h.clients))
				} else {
					log.Printf("[WebSocket Hub] Client unregistered (remaining clients: %d)", 
						len(h.clients))
				}
				
				close(client.send)
			}
			h.mu.Unlock()

		case message := <-h.broadcast:
			// Broadcast to all clients (not room-specific)
			h.mu.RLock()
			for client := range h.clients {
				select {
				case client.send <- message:
				default:
					// Client's send buffer is full, close the connection
					close(client.send)
					delete(h.clients, client)
				}
			}
			h.mu.RUnlock()
		}
	}
}

// BroadcastToRoom sends a message to all clients in a specific room (repo_id)
func (h *Hub) BroadcastToRoom(repoID string, message []byte) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	room, exists := h.rooms[repoID]
	if !exists {
		log.Printf("[WebSocket Hub] No clients in room: %s", repoID)
		return
	}

	log.Printf("[WebSocket Hub] Broadcasting to room %s (%d clients)", repoID, len(room))
	for client := range room {
		select {
		case client.send <- message:
		default:
			// Client's send buffer is full, skip this client
			log.Printf("[WebSocket Hub] Client send buffer full, skipping")
		}
	}
}

// BroadcastEvent broadcasts a queue.Event to the appropriate room
func (h *Hub) BroadcastEvent(event queue.Event) {
	// Marshal event to JSON
	data, err := json.Marshal(event)
	if err != nil {
		log.Printf("[WebSocket Hub] Failed to marshal event: %v", err)
		return
	}

	// Broadcast to room if repo_id is present
	if event.RepoID != "" {
		h.BroadcastToRoom(event.RepoID, data)
	} else {
		// Broadcast to all clients if no repo_id
		select {
		case h.broadcast <- data:
		default:
			log.Printf("[WebSocket Hub] Broadcast channel full, dropping event")
		}
	}
}

// BroadcastJSON marshals the given value to JSON and broadcasts it to all clients.
func (h *Hub) BroadcastJSON(v interface{}) {
	data, err := json.Marshal(v)
	if err != nil {
		log.Printf("[WebSocket Hub] BroadcastJSON marshal error: %v", err)
		return
	}
	select {
	case h.broadcast <- data:
	default:
		log.Printf("[WebSocket Hub] BroadcastJSON: broadcast channel full, dropping message")
	}
}

// ListenToJobQueue listens to the job queue events and broadcasts them
func (h *Hub) ListenToJobQueue(jobQueue *queue.JobQueue) {
	log.Printf("[WebSocket Hub] Starting job queue event listener")
	events := jobQueue.Events()
	
	for {
		select {
		case <-h.ctx.Done():
			log.Printf("[WebSocket Hub] Stopping job queue event listener")
			return
		case event := <-events:
			h.BroadcastEvent(event)
		}
	}
}

// closeAllConnections closes all active client connections
func (h *Hub) closeAllConnections() {
	h.mu.Lock()
	defer h.mu.Unlock()

	log.Printf("[WebSocket Hub] Closing %d client connections", len(h.clients))
	for client := range h.clients {
		close(client.send)
		client.conn.Close()
	}
	h.clients = make(map[*Client]bool)
	h.rooms = make(map[string]map[*Client]bool)
}

// readPump pumps messages from the websocket connection to the hub
func (c *Client) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	// Set read deadline
	c.conn.SetReadDeadline(time.Now().Add(pongWait))
	
	for {
		var msg map[string]interface{}
		err := websocket.JSON.Receive(c.conn, &msg)
		if err != nil {
			if err.Error() != "EOF" {
				log.Printf("[WebSocket Client] Read error: %v", err)
			}
			break
		}
		
		// Reset read deadline on successful read
		c.conn.SetReadDeadline(time.Now().Add(pongWait))
		
		// Handle ping/pong or other client messages if needed
		if msgType, ok := msg["type"].(string); ok && msgType == "ping" {
			// Respond with pong
			pong := map[string]string{"type": "pong"}
			websocket.JSON.Send(c.conn, pong)
		}
	}
}

// writePump pumps messages from the hub to the websocket connection
func (c *Client) writePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				// Hub closed the channel
				return
			}

			// Send the message
			if _, err := c.conn.Write(message); err != nil {
				log.Printf("[WebSocket Client] Write error: %v", err)
				return
			}

		case <-ticker.C:
			// Send ping
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			ping := map[string]string{"type": "ping"}
			if err := websocket.JSON.Send(c.conn, ping); err != nil {
				return
			}
		}
	}
}

// ServeWS handles websocket requests from clients
func (h *Hub) ServeWS(w http.ResponseWriter, r *http.Request) {
	// Extract repo_id from query parameters
	repoID := r.URL.Query().Get("repo_id")
	
	// Upgrade connection to WebSocket
	ws := websocket.Server{
		Handler: func(conn *websocket.Conn) {
			// Create new client
			client := &Client{
				hub:    h,
				conn:   conn,
				send:   make(chan []byte, 256),
				repoID: repoID,
			}

			// Register client
			h.register <- client

			// Send welcome message
			welcome := map[string]interface{}{
				"type":    "connected",
				"repo_id": repoID,
				"message": "WebSocket connection established",
			}
			websocket.JSON.Send(conn, welcome)

			// Start client goroutines
			go client.writePump()
			client.readPump() // This blocks until connection closes
		},
	}

	ws.ServeHTTP(w, r)
}

// Made with Bob
