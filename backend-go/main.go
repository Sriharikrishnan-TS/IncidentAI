package main

import (
	"context"
	"incidentos/backend-go/internal/api"
	"incidentos/backend-go/internal/config"
	"incidentos/backend-go/internal/github"
	"incidentos/backend-go/internal/graph"
	"incidentos/backend-go/internal/investigations"
	"incidentos/backend-go/internal/queue"
	"incidentos/backend-go/internal/websocket"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	// Load .env file if it exists (system environment variables take precedence)
	if err := config.LoadEnv(".env"); err != nil {
		log.Printf("[Main] Warning: Failed to load .env file: %v", err)
	}

	// Read environment variables with defaults
	port := getEnv("PORT", "8080")
	aiEngineURL := getEnv("AI_ENGINE_URL", "http://localhost:8001")
	reposDir := getEnv("REPOS_DIR", "./repos")
	neo4jURI := getEnv("NEO4J_URI", "bolt://localhost:7687")
	neo4jUsername := getEnv("NEO4J_USERNAME", "neo4j")
	neo4jPassword := getEnv("NEO4J_PASSWORD", "password")

	// Log security configuration
	if callbackKey := os.Getenv("CALLBACK_API_KEY"); callbackKey != "" {
		log.Printf("[Main] Callback API Key: configured (%d chars)", len(callbackKey))
	} else {
		log.Printf("[Main] Warning: CALLBACK_API_KEY not set - callback endpoints not fully secured")
	}

	if aiEngineIP := os.Getenv("AI_ENGINE_IP"); aiEngineIP != "" {
		log.Printf("[Main] AI Engine IP whitelist: %s", aiEngineIP)
	}

	log.Printf("[Main] Starting IncidentOS Backend")
	log.Printf("[Main] Port: %s", port)
	log.Printf("[Main] AI Engine URL: %s", aiEngineURL)
	log.Printf("[Main] Repos Directory: %s", reposDir)
	log.Printf("[Main] Neo4j URI: %s", neo4jURI)

	// Create context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Initialize CloneService
	cloneService := github.NewCloneService(reposDir)
	log.Printf("[Main] CloneService initialized with base directory: %s", reposDir)

	// Initialize JobQueue
	jobQueue := queue.NewJobQueue(aiEngineURL, 50)
	log.Printf("[Main] JobQueue initialized with buffer size 50")

	// Start JobQueue worker
	jobQueue.Start(ctx)
	log.Printf("[Main] JobQueue worker started")

	// Initialize WebSocket Hub
	wsHub := websocket.NewHub(ctx)
	log.Printf("[Main] WebSocket Hub initialized")

	// Start WebSocket Hub
	go wsHub.Run()
	log.Printf("[Main] WebSocket Hub started")

	// Start listening to job queue events
	go wsHub.ListenToJobQueue(jobQueue)
	log.Printf("[Main] WebSocket Hub listening to job queue events")

	// Initialize Neo4j client
	neo4jClient, err := graph.NewNeo4jClient(neo4jURI, neo4jUsername, neo4jPassword)
	if err != nil {
		log.Printf("[Main] Warning: Failed to connect to Neo4j: %v", err)
		log.Printf("[Main] Continuing without Neo4j - dependency graph will use stub data")
		neo4jClient = nil
	} else {
		log.Printf("[Main] Neo4j client initialized successfully")
	}

	// Initialize Investigation Manager
	investigationMgr := investigations.NewInvestigationManager(jobQueue, wsHub)
	log.Printf("[Main] Investigation Manager initialized")

	// Initialize Gateway
	gateway := api.NewGateway(cloneService, jobQueue, investigationMgr, neo4jClient)
	log.Printf("[Main] Gateway initialized")

	// Create HTTP ServeMux and register routes
	mux := http.NewServeMux()
	gateway.RegisterRoutes(mux)
	log.Printf("[Main] Routes registered")

	// Register WebSocket endpoint
	mux.HandleFunc("/ws", wsHub.ServeWS)
	log.Printf("[Main] WebSocket endpoint registered at /ws")

	// Enable CORS
	handler := enableCORS(mux)

	// Create HTTP server
	server := &http.Server{
		Addr:         ":" + port,
		Handler:      handler,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in a goroutine
	go func() {
		log.Printf("[Main] HTTP server listening on :%s", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[Main] Server failed to start: %v", err)
		}
	}()

	// Wait for interrupt signal for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	// Block until signal received
	sig := <-sigChan
	log.Printf("[Main] Received signal: %v", sig)
	log.Printf("[Main] Initiating graceful shutdown...")

	// Cancel context to stop JobQueue worker
	cancel()

	// Close Neo4j connection if initialized
	if neo4jClient != nil {
		closeCtx, closeCancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer closeCancel()

		if err := neo4jClient.Close(closeCtx); err != nil {
			log.Printf("[Main] Neo4j close error: %v", err)
		} else {
			log.Printf("[Main] Neo4j connection closed")
		}
	}

	// Shutdown HTTP server with timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Printf("[Main] Server shutdown error: %v", err)
	} else {
		log.Printf("[Main] Server shutdown complete")
	}

	log.Printf("[Main] IncidentOS Backend stopped")
}

// getEnv retrieves an environment variable or returns a default value.
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// enableCORS enables frontend-backend communication during development
func enableCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "http://localhost:3000")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}