package api

import (
	"context"
	"encoding/json"
	"incidentos/backend-go/internal/github"
	"incidentos/backend-go/internal/queue"
	"log"
	"net/http"
	"strings"
)

// Gateway is the central routing hub for all HTTP requests.
type Gateway struct {
	cloner   *github.CloneService
	jobQueue *queue.JobQueue
}

// NewGateway creates a new Gateway with the specified dependencies.
func NewGateway(cloner *github.CloneService, jq *queue.JobQueue) *Gateway {
	return &Gateway{
		cloner:   cloner,
		jobQueue: jq,
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

	// Enqueue investigation job
	payload := map[string]interface{}{
		"repo_id":  req.RepoID,
		"incident": req.Incident,
	}
	if err := g.jobQueue.Enqueue("start_investigation", payload); err != nil {
		log.Printf("[Gateway] Failed to enqueue investigation job: %v", err)
		httpError(w, "Failed to enqueue investigation job", http.StatusInternalServerError)
		return
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"repo_id": req.RepoID,
		"status":  "investigation_started",
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

	// Return stubbed response (real data will come from Neo4j later)
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
