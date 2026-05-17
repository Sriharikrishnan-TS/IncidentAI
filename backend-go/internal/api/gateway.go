package api

import (
	"context"
	"encoding/json"
	"incidentos/backend-go/internal/github"
	"incidentos/backend-go/internal/graph"
	"incidentos/backend-go/internal/investigations"
	"incidentos/backend-go/internal/memory"
	"incidentos/backend-go/internal/queue"
	"log"
	"net/http"
	"os"
	"strings"
)

// Gateway is the central routing hub for all HTTP requests.
type Gateway struct {
	cloner              *github.CloneService
	jobQueue            *queue.JobQueue
	investigationMgr    *investigations.InvestigationManager
	neo4jClient         *graph.Neo4jClient
	chromaClient        *memory.ChromaDBClient
}

// NewGateway creates a new Gateway with the specified dependencies.
func NewGateway(cloner *github.CloneService, jq *queue.JobQueue, invMgr *investigations.InvestigationManager, neo4j *graph.Neo4jClient, chroma *memory.ChromaDBClient) *Gateway {
	return &Gateway{
		cloner:           cloner,
		jobQueue:         jq,
		investigationMgr: invMgr,
		neo4jClient:      neo4j,
		chromaClient:     chroma,
	}
}

// RegisterRoutes registers all HTTP routes with the provided ServeMux.
func (g *Gateway) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/upload-repo", g.handleUploadRepo)
	mux.HandleFunc("/analyze-repo", g.handleAnalyzeRepo)
	mux.HandleFunc("/compute-fragility", g.handleComputeFragility)
	mux.HandleFunc("/start-investigation", g.handleStartInvestigation)
	mux.HandleFunc("/mentor-query", g.handleMentorQuery)
	mux.HandleFunc("/dashboard/", g.handleDashboard)
	mux.HandleFunc("/dependency-graph/", g.handleDependencyGraph)
	mux.HandleFunc("/health", g.handleHealth)
	
	// Investigation endpoints
	mux.HandleFunc("/investigation/", g.handleGetInvestigation)
	mux.HandleFunc("/investigations", g.handleListInvestigations)
	
	// Callback endpoints (protected with authentication)
	mux.HandleFunc("/callback/investigation-complete", g.validateCallback(g.handleInvestigationCallback))
	mux.HandleFunc("/callback/dependencies-extracted", g.validateCallback(g.handleDependenciesCallback))
	mux.HandleFunc("/callback/embeddings", g.validateCallback(g.handleEmbeddingsCallback))
}

// validateCallback is a middleware that validates callback requests from AI Engine
// It checks both IP address and API key for security
func (g *Gateway) validateCallback(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Extract client IP from RemoteAddr (format: "IP:port")
		clientIP := r.RemoteAddr
		if idx := strings.LastIndex(clientIP, ":"); idx != -1 {
			clientIP = clientIP[:idx]
		}
		// Remove IPv6 brackets if present
		clientIP = strings.Trim(clientIP, "[]")

		// 1. IP Whitelisting Check
		// For localhost deployment, allow 127.0.0.1 and ::1
		// For separate deployment, check against AI_ENGINE_IP env var
		allowedIP := os.Getenv("AI_ENGINE_IP")
		isLocalhost := clientIP == "127.0.0.1" || clientIP == "::1" || clientIP == "localhost"
		
		if !isLocalhost {
			if allowedIP == "" {
				log.Printf("[Security] AI_ENGINE_IP not configured, rejecting non-localhost callback from: %s", clientIP)
				httpError(w, "Forbidden", http.StatusForbidden)
				return
			}
			if clientIP != allowedIP {
				log.Printf("[Security] Rejected callback from unauthorized IP: %s (expected: %s)", clientIP, allowedIP)
				httpError(w, "Forbidden", http.StatusForbidden)
				return
			}
		}

		// 2. API Key Authentication Check
		apiKey := r.Header.Get("X-API-Key")
		expectedKey := os.Getenv("CALLBACK_API_KEY")
		
		// If CALLBACK_API_KEY is set, validate it
		if expectedKey != "" {
			if apiKey == "" {
				log.Printf("[Security] Rejected callback without API key from IP: %s", clientIP)
				httpError(w, "Unauthorized: Missing API key", http.StatusUnauthorized)
				return
			}
			if apiKey != expectedKey {
				log.Printf("[Security] Rejected callback with invalid API key from IP: %s", clientIP)
				httpError(w, "Unauthorized: Invalid API key", http.StatusUnauthorized)
				return
			}
		} else {
			// Warn if API key is not configured (security risk)
			log.Printf("[Security Warning] CALLBACK_API_KEY not configured - callback endpoints are not fully secured")
		}

		// Log successful authentication
		log.Printf("[Security] Authenticated callback from IP: %s", clientIP)
		
		// Call the actual handler
		next(w, r)
	}
}

// handleUploadRepo handles POST /upload-repo
// Accepts a GitHub URL, clones the repo, and enqueues analysis.
func (g *Gateway) handleUploadRepo(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode request body
	var req struct {
		RepoURL string `json:"repo_url"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate repo_url is present
	if req.RepoURL == "" {
		httpError(w, "repo_url is required", http.StatusBadRequest)
		return
	}

	// Validate GitHub URL
	if !github.IsValidGitHubURL(req.RepoURL) {
		httpError(w, "Invalid GitHub URL", http.StatusBadRequest)
		return
	}

	// Clone the repository
	result, err := g.cloner.Clone(context.Background(), req.RepoURL)
	if err != nil {
		log.Printf("[Gateway] Clone failed: %v", err)
		httpError(w, "Failed to clone repository", http.StatusInternalServerError)
		return
	}

	// Enqueue analysis job
	payload := map[string]interface{}{
		"repo_id":   result.RepoID,
		"repo_path": result.RepoPath,
	}
	if err := g.jobQueue.Enqueue("analyze_repo", payload); err != nil {
		log.Printf("[Gateway] Failed to enqueue analysis job: %v", err)
		httpError(w, "Failed to enqueue analysis job", http.StatusInternalServerError)
		return
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"repo_id": result.RepoID,
		"status":  "uploaded",
	})
}

// handleAnalyzeRepo handles POST /analyze-repo
// Directly triggers AI analysis for an already-cloned repo.
func (g *Gateway) handleAnalyzeRepo(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode request body
	var req struct {
		RepoID   string `json:"repo_id"`
		RepoPath string `json:"repo_path"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if req.RepoID == "" || req.RepoPath == "" {
		httpError(w, "repo_id and repo_path are required", http.StatusBadRequest)
		return
	}

	// Enqueue analysis job
	payload := map[string]interface{}{
		"repo_id":   req.RepoID,
		"repo_path": req.RepoPath,
	}
	if err := g.jobQueue.Enqueue("analyze_repo", payload); err != nil {
		log.Printf("[Gateway] Failed to enqueue analysis job: %v", err)
		httpError(w, "Failed to enqueue analysis job", http.StatusInternalServerError)
		return
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"repo_id": req.RepoID,
		"status":  "analysis_started",
	})
}

// handleComputeFragility handles POST /compute-fragility
// Requests fragility score computation for a given repo.
func (g *Gateway) handleComputeFragility(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode request body
	var req struct {
		RepoID string `json:"repo_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required field
	if req.RepoID == "" {
		httpError(w, "repo_id is required", http.StatusBadRequest)
		return
	}

	// Enqueue fragility job
	payload := map[string]interface{}{
		"repo_id": req.RepoID,
	}
	if err := g.jobQueue.Enqueue("compute_fragility", payload); err != nil {
		log.Printf("[Gateway] Failed to enqueue fragility job: %v", err)
		httpError(w, "Failed to enqueue fragility job", http.StatusInternalServerError)
		return
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"repo_id": req.RepoID,
		"status":  "fragility_job_queued",
	})
}

// handleStartInvestigation handles POST /start-investigation
// Kicks off an incident investigation workflow.
func (g *Gateway) handleStartInvestigation(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode request body
	var req struct {
		RepoID   string `json:"repo_id"`
		Incident string `json:"incident"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if req.RepoID == "" || req.Incident == "" {
		httpError(w, "repo_id and incident are required", http.StatusBadRequest)
		return
	}

	// Start investigation using Investigation Manager
	investigationID, err := g.investigationMgr.StartInvestigation(req.RepoID, req.Incident)
	if err != nil {
		log.Printf("[Gateway] Failed to start investigation: %v", err)
		httpError(w, "Failed to start investigation", http.StatusInternalServerError)
		return
	}

	// Return success response with investigation_id
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"investigation_id": investigationID,
		"repo_id":          req.RepoID,
		"status":           "investigation_started",
	})
}

// handleMentorQuery handles POST /mentor-query
// Forwards a mentor/onboarding question to the AI engine asynchronously.
func (g *Gateway) handleMentorQuery(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode request body
	var req struct {
		RepoID   string `json:"repo_id"`
		Question string `json:"question"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if req.RepoID == "" || req.Question == "" {
		httpError(w, "repo_id and question are required", http.StatusBadRequest)
		return
	}

	// Enqueue mentor query job
	payload := map[string]interface{}{
		"repo_id":  req.RepoID,
		"question": req.Question,
	}
	if err := g.jobQueue.Enqueue("mentor_query", payload); err != nil {
		log.Printf("[Gateway] Failed to enqueue mentor query job: %v", err)
		httpError(w, "Failed to enqueue mentor query job", http.StatusInternalServerError)
		return
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"repo_id": req.RepoID,
		"status":  "mentor_query_queued",
	})
}

// handleDashboard handles GET /dashboard/{repo_id}
// Returns summary data for the frontend dashboard.
func (g *Gateway) handleDashboard(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract repo_id from path
	repoID := strings.TrimPrefix(r.URL.Path, "/dashboard/")
	if repoID == "" {
		httpError(w, "repo_id is required", http.StatusBadRequest)
		return
	}

	// Return stubbed response (real data will come from Neo4j/ChromaDB later)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"repo_id":           repoID,
		"services":          12,
		"dependencies":      38,
		"fragile_services":  []string{"auth-service", "checkout-service"},
		"recent_incidents":  4,
	})
}

// handleDependencyGraph handles GET /dependency-graph/{repo_id}
// Returns graph nodes and edges for the dependency graph viewer.
func (g *Gateway) handleDependencyGraph(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract repo_id from path
	repoID := strings.TrimPrefix(r.URL.Path, "/dependency-graph/")
	if repoID == "" {
		httpError(w, "repo_id is required", http.StatusBadRequest)
		return
	}

	// Query Neo4j for dependency graph (with fallback to stub data)
	if g.neo4jClient != nil {
		ctx := context.Background()
		graphData, err := g.neo4jClient.GetDependencyGraph(ctx, repoID)
		if err != nil {
			log.Printf("[Gateway] Failed to fetch dependency graph from Neo4j for repo %s: %v", repoID, err)
			// Fall through to return stub data
		} else {
			// Return real data from Neo4j
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(graphData)
			return
		}
	}

	// Return stubbed response if Neo4j is not available or query failed
	log.Printf("[Gateway] Returning stub data for dependency graph (repo: %s)", repoID)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"nodes": []map[string]string{
			{"id": "auth-service", "type": "service"},
			{"id": "checkout-service", "type": "service"},
		},
		"edges": []map[string]string{
			{"source": "checkout-service", "target": "auth-service"},
		},
	})
}

// handleHealth handles GET /health
// Health check endpoint.
func (g *Gateway) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status": "ok",
	})
}

// httpError writes a JSON error response with the specified message and status code.
func httpError(w http.ResponseWriter, message string, code int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(map[string]string{
		"error": message,
	})
}

// Made with Bob


// handleGetInvestigation handles GET /investigation/{investigation_id}
// Returns the status and details of a specific investigation.
func (g *Gateway) handleGetInvestigation(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract investigation_id from path
	investigationID := strings.TrimPrefix(r.URL.Path, "/investigation/")
	if investigationID == "" {
		httpError(w, "investigation_id is required", http.StatusBadRequest)
		return
	}

	// Get investigation from manager
	investigation, err := g.investigationMgr.GetInvestigation(investigationID)
	if err != nil {
		log.Printf("[Gateway] Failed to get investigation %s: %v", investigationID, err)
		httpError(w, "Investigation not found", http.StatusNotFound)
		return
	}

	// Return investigation data
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(investigation)
}

// handleListInvestigations handles GET /investigations?repo_id={repo_id}
// Returns all investigations for a given repository.
func (g *Gateway) handleListInvestigations(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get repo_id from query parameters
	repoID := r.URL.Query().Get("repo_id")
	if repoID == "" {
		httpError(w, "repo_id query parameter is required", http.StatusBadRequest)
		return
	}

	// Get investigations from manager
	investigations, err := g.investigationMgr.ListInvestigations(repoID)
	if err != nil {
		log.Printf("[Gateway] Failed to list investigations for repo %s: %v", repoID, err)
		httpError(w, "Failed to retrieve investigations", http.StatusInternalServerError)
		return
	}

	// Return investigations list
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"repo_id":        repoID,
		"investigations": investigations,
	})
}

// handleInvestigationCallback handles POST /callback/investigation-complete
// Receives the final RCA report from the AI Engine when investigation completes.
func (g *Gateway) handleInvestigationCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		InvestigationID    string   `json:"investigation_id"`
		Incident           string   `json:"incident"`
		RootCause          string   `json:"root_cause"`
		AffectedServices   []string `json:"affected_services"`
		FragilityScore     float64  `json:"fragility_score"`
		HistoricalCorr     string   `json:"historical_correlation"`
		RecommendedActions []string `json:"recommended_actions"`
	}
	if err := json.NewDecoder(r.Body).Decode(&callback); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if callback.InvestigationID == "" {
		httpError(w, "investigation_id is required", http.StatusBadRequest)
		return
	}

	// Create RCA result
	result := investigations.RCAResult{
		RootCause:          callback.RootCause,
		AffectedServices:   callback.AffectedServices,
		FragilityScore:     callback.FragilityScore,
		HistoricalCorr:     callback.HistoricalCorr,
		RecommendedActions: callback.RecommendedActions,
	}

	// Complete investigation
	if err := g.investigationMgr.CompleteInvestigation(callback.InvestigationID, result); err != nil {
		log.Printf("[Gateway] Failed to complete investigation %s: %v", callback.InvestigationID, err)
		httpError(w, "Failed to complete investigation", http.StatusInternalServerError)
		return
	}

	log.Printf("[Gateway] Investigation %s completed successfully", callback.InvestigationID)

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":           "success",
		"investigation_id": callback.InvestigationID,
	})
}

// handleDependenciesCallback handles POST /callback/dependencies-extracted
// Receives dependency graph data from the AI Engine and stores it in Neo4j.
func (g *Gateway) handleDependenciesCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		RepoID       string `json:"repo_id"`
		Dependencies []struct {
			Source string                 `json:"source"`
			Target string                 `json:"target"`
			Type   string                 `json:"type"`
			Properties map[string]interface{} `json:"properties,omitempty"`
		} `json:"dependencies"`
	}
	if err := json.NewDecoder(r.Body).Decode(&callback); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if callback.RepoID == "" {
		httpError(w, "repo_id is required", http.StatusBadRequest)
		return
	}

	if len(callback.Dependencies) == 0 {
		log.Printf("[Gateway] No dependencies provided for repo %s", callback.RepoID)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{
			"status":  "success",
			"message": "No dependencies to store",
		})
		return
	}

	// Check if Neo4j client is available
	if g.neo4jClient == nil {
		log.Printf("[Gateway] Neo4j client not available, cannot store dependencies for repo %s", callback.RepoID)
		httpError(w, "Neo4j client not available", http.StatusServiceUnavailable)
		return
	}

	ctx := context.Background()

	// Extract unique nodes from dependencies
	nodeMap := make(map[string]bool)
	for _, dep := range callback.Dependencies {
		nodeMap[dep.Source] = true
		nodeMap[dep.Target] = true
	}

	// Create nodes (assuming they are services)
	nodes := []graph.GraphNode{}
	for nodeID := range nodeMap {
		nodes = append(nodes, graph.GraphNode{
			ID:   nodeID,
			Type: "service",
			Properties: map[string]interface{}{},
		})
	}

	// Store nodes in bulk
	if err := g.neo4jClient.StoreBulkNodes(ctx, callback.RepoID, nodes); err != nil {
		log.Printf("[Gateway] Failed to store nodes for repo %s: %v", callback.RepoID, err)
		httpError(w, "Failed to store nodes in Neo4j", http.StatusInternalServerError)
		return
	}

	// Convert dependencies to edges
	edges := []graph.GraphEdge{}
	for _, dep := range callback.Dependencies {
		edge := graph.GraphEdge{
			Source: dep.Source,
			Target: dep.Target,
			Type:   dep.Type,
			Properties: dep.Properties,
		}
		edges = append(edges, edge)
	}

	// Store edges in bulk
	if err := g.neo4jClient.StoreBulkEdges(ctx, callback.RepoID, edges); err != nil {
		log.Printf("[Gateway] Failed to store edges for repo %s: %v", callback.RepoID, err)
		httpError(w, "Failed to store edges in Neo4j", http.StatusInternalServerError)
		return
	}

	log.Printf("[Gateway] Successfully stored dependency graph for repo %s: %d nodes, %d edges",
		callback.RepoID, len(nodes), len(edges))

	// Emit WebSocket event for dependency graph generation
	// Note: This would be handled by the job queue event system if needed

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "success",
		"repo_id": callback.RepoID,
		"nodes":   len(nodes),
		"edges":   len(edges),
	})
}

// handleEmbeddingsCallback handles POST /callback/embeddings
// Receives pre-computed embeddings from the AI Engine and stores them in ChromaDB.
func (g *Gateway) handleEmbeddingsCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		RepoID         string `json:"repo_id"`
		CollectionType string `json:"collection_type"` // "mentor", "incidents", "rca", "architecture"
		Documents      []struct {
			ID        string                 `json:"id"`
			Content   string                 `json:"content"`
			Metadata  map[string]interface{} `json:"metadata"`
			Embedding []float64              `json:"embedding"`
		} `json:"documents"`
	}
	if err := json.NewDecoder(r.Body).Decode(&callback); err != nil {
		httpError(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate required fields
	if callback.RepoID == "" {
		httpError(w, "repo_id is required", http.StatusBadRequest)
		return
	}

	if callback.CollectionType == "" {
		httpError(w, "collection_type is required", http.StatusBadRequest)
		return
	}

	// Validate collection type
	validTypes := map[string]bool{
		"mentor":       true,
		"incidents":    true,
		"rca":          true,
		"architecture": true,
	}
	if !validTypes[callback.CollectionType] {
		httpError(w, "Invalid collection_type. Must be one of: mentor, incidents, rca, architecture", http.StatusBadRequest)
		return
	}

	if len(callback.Documents) == 0 {
		log.Printf("[Gateway] No documents provided for repo %s, collection %s", callback.RepoID, callback.CollectionType)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]string{
			"status":  "success",
			"message": "No documents to store",
		})
		return
	}

	// Check if ChromaDB client is available
	if g.chromaClient == nil {
		log.Printf("[Gateway] ChromaDB client not available, cannot store embeddings for repo %s", callback.RepoID)
		httpError(w, "ChromaDB client not available", http.StatusServiceUnavailable)
		return
	}

	ctx := context.Background()

	// Get collection name
	collectionName := memory.GetCollectionName(callback.CollectionType, callback.RepoID)

	// Create collection if it doesn't exist
	if err := g.chromaClient.CreateCollection(ctx, collectionName); err != nil {
		log.Printf("[Gateway] Failed to create collection %s: %v", collectionName, err)
		httpError(w, "Failed to create collection", http.StatusInternalServerError)
		return
	}

	// Convert callback documents to ChromaDB documents
	docs := make([]memory.Document, len(callback.Documents))
	for i, doc := range callback.Documents {
		docs[i] = memory.Document{
			ID:        doc.ID,
			Content:   doc.Content,
			Metadata:  doc.Metadata,
			Embedding: doc.Embedding,
		}
	}

	// Store documents in ChromaDB
	if err := g.chromaClient.AddDocuments(ctx, collectionName, docs); err != nil {
		log.Printf("[Gateway] Failed to store documents in collection %s: %v", collectionName, err)
		httpError(w, "Failed to store documents in ChromaDB", http.StatusInternalServerError)
		return
	}

	log.Printf("[Gateway] Successfully stored %d documents in collection %s for repo %s",
		len(docs), collectionName, callback.RepoID)

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":     "success",
		"repo_id":    callback.RepoID,
		"collection": collectionName,
		"documents":  len(docs),
	})
}
