package main

import (
	"context"
	"incidentos/backend-go/internal/api"
	"incidentos/backend-go/internal/github"
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
	// Read environment variables with defaults
	port := getEnv("PORT", "8080")
	aiEngineURL := getEnv("AI_ENGINE_URL", "http://localhost:8001")
	reposDir := getEnv("REPOS_DIR", "./repos")

	log.Printf("[Main] Starting IncidentOS Backend")
	log.Printf("[Main] Port: %s", port)
	log.Printf("[Main] AI Engine URL: %s", aiEngineURL)
	log.Printf("[Main] Repos Directory: %s", reposDir)

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

	// Initialize Gateway
	gateway := api.NewGateway(cloneService, jobQueue)
	log.Printf("[Main] Gateway initialized")

	// Create HTTP ServeMux and register routes
	mux := http.NewServeMux()
	gateway.RegisterRoutes(mux)
	log.Printf("[Main] Routes registered")

	// Register WebSocket endpoint
	mux.HandleFunc("/ws", wsHub.ServeWS)
	log.Printf("[Main] WebSocket endpoint registered at /ws")

	// Create HTTP server
	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
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

// Made with Bob
