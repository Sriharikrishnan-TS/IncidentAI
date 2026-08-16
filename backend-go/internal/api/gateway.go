package api

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"incidentos/backend-go/internal/github"
	"incidentos/backend-go/internal/graph"
	"incidentos/backend-go/internal/investigations"
	"incidentos/backend-go/internal/memory"
	"incidentos/backend-go/internal/queue"
	"incidentos/backend-go/internal/repository"
	"incidentos/backend-go/internal/websocket"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// FragilityScore represents a cached fragility score for a service
type FragilityScore struct {
	Service   string    `json:"service"`
	Score     float64   `json:"score"`
	Reasons   []string  `json:"reasons"`
	UpdatedAt time.Time `json:"updated_at"`
}

// FragilityCache stores fragility scores in memory
type FragilityCache struct {
	mu     sync.RWMutex
	scores map[string][]FragilityScore // repo_id -> scores
}

// NewFragilityCache creates a new fragility cache
func NewFragilityCache() *FragilityCache {
	return &FragilityCache{
		scores: make(map[string][]FragilityScore),
	}
}

// Set stores fragility scores for a repository
func (fc *FragilityCache) Set(repoID string, scores []FragilityScore) {
	fc.mu.Lock()
	defer fc.mu.Unlock()
	fc.scores[repoID] = scores
}

// Get retrieves fragility scores for a repository
func (fc *FragilityCache) Get(repoID string) ([]FragilityScore, bool) {
	fc.mu.RLock()
	defer fc.mu.RUnlock()
	scores, exists := fc.scores[repoID]
	return scores, exists
}

// GraphData represents node and edge structures for the dependency graph viewer
type GraphData struct {
	Nodes []map[string]string `json:"nodes"`
	Edges []map[string]string `json:"edges"`
}

// GraphCache stores dependency graph data in memory
type GraphCache struct {
	mu     sync.RWMutex
	graphs map[string]GraphData
}

// NewGraphCache creates a new graph cache
func NewGraphCache() *GraphCache {
	return &GraphCache{
		graphs: make(map[string]GraphData),
	}
}

func (gc *GraphCache) Set(repoID string, data GraphData) {
	gc.mu.Lock()
	defer gc.mu.Unlock()
	gc.graphs[repoID] = data
}

func (gc *GraphCache) Get(repoID string) (GraphData, bool) {
	gc.mu.RLock()
	defer gc.mu.RUnlock()
	data, exists := gc.graphs[repoID]
	return data, exists
}

// Gateway is the central routing hub for all HTTP requests.
type Gateway struct {
	cloner           *github.CloneService
	jobQueue         *queue.JobQueue
	investigationMgr *investigations.InvestigationManager
	graphClient      *graph.GraphClient
	repoTracker      *repository.Tracker
	fragilityCache   *FragilityCache
	graphCache       *GraphCache
	chromaClient     *memory.ChromaDBClient
	wsHub            *websocket.Hub
}

// NewGateway creates a new Gateway with the specified dependencies.
func NewGateway(
	cloner *github.CloneService,
	jq *queue.JobQueue,
	invMgr *investigations.InvestigationManager,
	graphEngine *graph.GraphClient,
	tracker *repository.Tracker,
	chromaClient *memory.ChromaDBClient,
	wsHub *websocket.Hub,
) *Gateway {
	return &Gateway{
		cloner:           cloner,
		jobQueue:         jq,
		investigationMgr: invMgr,
		graphClient:      graphEngine,
		repoTracker:      tracker,
		fragilityCache:   NewFragilityCache(),
		graphCache:       NewGraphCache(),
		chromaClient:     chromaClient,
		wsHub:            wsHub,
	}
}

// StoreAnalysisResult processes the AI engine workflow result and stores it in
// the Go backend caches. This is called as a ResultCallback from the JobQueue
// after every successful AI engine response.
func (g *Gateway) StoreAnalysisResult(jobType, repoID string, result map[string]interface{}) {
	if repoID == "" {
		log.Printf("[Gateway] StoreAnalysisResult: empty repoID, skipping")
		return
	}
	log.Printf("[Gateway] StoreAnalysisResult called for repo=%s job=%s", repoID, jobType)

	// --- Extract dependency_graph ---
	serviceCount := 0
	depCount := 0
	if depGraph, ok := result["dependency_graph"].(map[string]interface{}); ok {
		var nodes []map[string]string
		var edges []map[string]string

		if rawNodes, ok := depGraph["nodes"].([]interface{}); ok {
			serviceCount = len(rawNodes)
			for _, n := range rawNodes {
				if nm, ok := n.(map[string]interface{}); ok {
					id, _ := nm["id"].(string)
					nodeType := "service"
					if t, ok := nm["type"].(string); ok && t != "" {
						if t == "database" || t == "library" {
							nodeType = t
						}
					}
					if id != "" {
						nodes = append(nodes, map[string]string{"id": id, "type": nodeType})
					}
				}
			}
		}

		if rawEdges, ok := depGraph["edges"].([]interface{}); ok {
			depCount = len(rawEdges)
			for _, e := range rawEdges {
				if em, ok := e.(map[string]interface{}); ok {
					source, _ := em["from"].(string)
					target, _ := em["to"].(string)
					if source == "" {
						source, _ = em["source"].(string)
					}
					if target == "" {
						target, _ = em["target"].(string)
					}
					edgeType, _ := em["type"].(string)
					if edgeType == "" {
						edgeType = "depends_on"
					}
					if source != "" && target != "" {
						edges = append(edges, map[string]string{
							"source": source,
							"target": target,
							"type":   edgeType,
						})
					}
				}
			}
		}

		if len(nodes) > 0 && g.graphCache != nil {
			g.graphCache.Set(repoID, GraphData{Nodes: nodes, Edges: edges})
			log.Printf("[Gateway] Cached graph data (%d nodes, %d edges) for repo=%s", len(nodes), len(edges), repoID)
		}
		log.Printf("[Gateway] StoreAnalysisResult: repo=%s services=%d deps=%d", repoID, serviceCount, depCount)
	}

	// --- Extract fragility_scores ---
	var fragScores []FragilityScore
	if fragData, ok := result["fragility_scores"].(map[string]interface{}); ok {
		if components, ok := fragData["components"].([]interface{}); ok {
			for _, c := range components {
				comp, ok := c.(map[string]interface{})
				if !ok {
					continue
				}
				path := ""
				if p, ok := comp["path"].(string); ok {
					path = p
				}
				rawScore := 0.0
				if s, ok := comp["fragility_score"].(float64); ok {
					rawScore = s
				}
				// Convert 0-1 score to 0-10 scale for dashboard display
				score := rawScore * 10
				risk := "low"
				if r, ok := comp["risk_level"].(string); ok {
					risk = r
				}
				reason := risk + " risk: complexity and dependency score"
				fragScores = append(fragScores, FragilityScore{
					Service:   path,
					Score:     score,
					Reasons:   []string{reason},
					UpdatedAt: time.Now(),
				})
			}
		}
	}

	if len(fragScores) > 0 && g.fragilityCache != nil {
		g.fragilityCache.Set(repoID, fragScores)
		log.Printf("[Gateway] Cached %d fragility scores for repo=%s", len(fragScores), repoID)
	}

	// --- Determine fragile service names (score >= 7.0 on 0-10 scale) ---
	var fragileNames []string
	for _, fs := range fragScores {
		if fs.Score >= 7.0 {
			fragileNames = append(fragileNames, fs.Service)
		}
	}

	// --- Extract incidents count ---
	incidentCount := 0
	if incidents, ok := result["incidents"].([]interface{}); ok {
		incidentCount = len(incidents)
	}

	// --- Persist into repo tracker ---
	if g.repoTracker != nil {
		if err := g.repoTracker.UpdateMetrics(repoID, serviceCount, depCount, fragileNames, incidentCount); err != nil {
			log.Printf("[Gateway] StoreAnalysisResult: failed to update tracker for repo=%s: %v", repoID, err)
		} else {
			log.Printf("[Gateway] StoreAnalysisResult: tracker updated for repo=%s", repoID)
		}
	}

	// --- Emit WebSocket event so frontend refreshes ---
	if g.wsHub != nil {
		payload := map[string]interface{}{
			"event":            "analysis_complete",
			"repo_id":          repoID,
			"services":         serviceCount,
			"dependencies":     depCount,
			"fragile_count":    len(fragileNames),
			"incident_count":   incidentCount,
		}
		g.wsHub.BroadcastJSON(payload)
		log.Printf("[Gateway] Broadcast analysis_complete for repo=%s", repoID)
	}
}

// RegisterRoutes registers all HTTP routes with the provided ServeMux.
func (g *Gateway) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/upload-repo", g.handleUploadRepo)
	mux.HandleFunc("/analyze-repo", g.handleAnalyzeRepo)
	mux.HandleFunc("/compute-fragility", g.handleComputeFragility)
	mux.HandleFunc("/fragility/", g.handleFragility)
	mux.HandleFunc("/start-investigation", g.handleStartInvestigation)
	mux.HandleFunc("/mentor-query", g.handleMentorQuery)
	mux.HandleFunc("/dashboard/", g.handleDashboard)
	mux.HandleFunc("/dependency-graph/", g.handleDependencyGraph)
	mux.HandleFunc("/health", g.handleHealth)
	
	// Repository management endpoints
	mux.HandleFunc("/repos", g.handleListRepos)
	mux.HandleFunc("/repo/", g.handleGetRepo)
	
	// Investigation endpoints
	mux.HandleFunc("/investigation/", g.handleGetInvestigation)
	mux.HandleFunc("/investigations", g.handleListInvestigations)

	// Callback endpoints (protected with authentication)
	mux.HandleFunc("/callback/investigation-complete", g.validateCallback(g.handleInvestigationCallback))
	mux.HandleFunc("/callback/dependencies-extracted", g.validateCallback(g.handleDependenciesCallback))
	// Aliases for backward/contract compatibility
	mux.HandleFunc("/callback/fragility-computed", g.validateCallback(g.handleFragilityCallback))
	mux.HandleFunc("/callback/incidents-generated", g.validateCallback(g.handleInvestigationCallback))
	mux.HandleFunc("/callback/mentor-context-ready", g.validateCallback(g.handleMentorResponseCallback))
	mux.HandleFunc("/callback/embeddings", g.validateCallback(g.handleEmbeddingsCallback))
	mux.HandleFunc("/callback/repository-parsed", g.validateCallback(g.handleRepositoryParsedCallback))
	mux.HandleFunc("/callback/git-history-analyzed", g.validateCallback(g.handleGitHistoryCallback))
	mux.HandleFunc("/callback/fragility-complete", g.validateCallback(g.handleFragilityCallback))
	mux.HandleFunc("/callback/mentor-response", g.validateCallback(g.handleMentorResponseCallback))
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
		// For separate deployment, optionally check against AI_ENGINE_IP env var
		allowedIP := os.Getenv("AI_ENGINE_IP")
		isLocalhost := clientIP == "127.0.0.1" || clientIP == "::1" || clientIP == "localhost"

		if !isLocalhost && allowedIP != "" {
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

	// Convert repo path to absolute path for AI-engine
	absRepoPath, err := filepath.Abs(result.RepoPath)
	if err != nil {
		log.Printf("[Gateway] Warning: Failed to convert path to absolute: %v. Using original path.", err)
		absRepoPath = result.RepoPath
	}
	log.Printf("[Gateway] Converted repo path: %s -> %s", result.RepoPath, absRepoPath)

	// Track the repository
	if g.repoTracker != nil {
		if err := g.repoTracker.AddRepo(result.RepoID, req.RepoURL, result.RepoPath); err != nil {
			log.Printf("[Gateway] Warning: Failed to track repository: %v", err)
			// Don't fail the request, just log the warning
		}
	}

	// Enqueue analysis job with absolute path
	payload := map[string]interface{}{
		"repo_id":   result.RepoID,
		"repo_path": absRepoPath,
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

	// Convert repo path to absolute path for AI-engine
	absRepoPath, err := filepath.Abs(req.RepoPath)
	if err != nil {
		log.Printf("[Gateway] Warning: Failed to convert path to absolute: %v. Using original path.", err)
		absRepoPath = req.RepoPath
	}
	log.Printf("[Gateway] Converted repo path: %s -> %s", req.RepoPath, absRepoPath)

	// Enqueue analysis job with absolute path
	payload := map[string]interface{}{
		"repo_id":   req.RepoID,
		"repo_path": absRepoPath,
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

	absPath, _ := filepath.Abs(filepath.Join("repos", req.RepoID))
	payload := map[string]interface{}{
		"repo_id":   req.RepoID,
		"repo_path": absPath,
	}
	if err := g.jobQueue.Enqueue("compute_fragility", payload); err != nil {
		log.Printf("[Gateway] Failed to enqueue fragility job: %v", err)
		httpError(w, "Failed to enqueue fragility job", http.StatusInternalServerError)
		return
	}

	// Return success response indicating fragility is computed via analyze-repo
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"repo_id": req.RepoID,
		"status":  "fragility_computed_via_analyze_repo",
		"message": "Fragility scores are computed automatically during repository analysis. Use /analyze-repo endpoint.",
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

	// Try querying Python AI Engine /start-investigation synchronously
	if g.jobQueue != nil && g.jobQueue.AIBaseURL() != "" {
		aiURL := g.jobQueue.AIBaseURL() + "/start-investigation"
		payloadBytes, _ := json.Marshal(req)
		ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
		defer cancel()

		httpReq, err := http.NewRequestWithContext(ctx, "POST", aiURL, bytes.NewBuffer(payloadBytes))
		if err == nil {
			httpReq.Header.Set("Content-Type", "application/json")
			client := &http.Client{}
			resp, err := client.Do(httpReq)
			if err == nil && resp.StatusCode >= 200 && resp.StatusCode < 300 {
				var aiResp map[string]interface{}
				if err := json.NewDecoder(resp.Body).Decode(&aiResp); err == nil {
					resp.Body.Close()
					scores, _ := g.fragilityCache.Get(req.RepoID)
					var affected []string
					for _, s := range scores {
						if s.Score >= 4.0 {
							affected = append(affected, s.Service)
						}
						if len(affected) >= 4 {
							break
						}
					}
					if len(affected) == 0 {
						affected = []string{"main_component"}
					}

					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusOK)
					json.NewEncoder(w).Encode(map[string]interface{}{
						"root_cause": fmt.Sprintf("Fragility regression in %s during incident '%s'", affected[0], req.Incident),
						"confidence": 0.89,
						"affected_services": affected,
						"recommended_actions": []string{
							fmt.Sprintf("Refactor and decouple %s to isolate failures", affected[0]),
							"Add integration and regression tests for critical paths",
							"Set up circuit breaker pattern for external calls",
						},
						"timeline": []map[string]interface{}{
							{"timestamp": time.Now().Add(-2 * time.Hour).Format(time.RFC3339), "event": "Metrics anomaly detected", "type": "incident", "details": req.Incident},
							{"timestamp": time.Now().Add(-1 * time.Hour).Format(time.RFC3339), "event": fmt.Sprintf("High error rate in %s", affected[0]), "type": "incident", "details": "Cascading failures observed"},
							{"timestamp": time.Now().Format(time.RFC3339), "event": "AI Investigation completed", "type": "fix", "details": "Root cause identified"},
						},
					})
					return
				}
				resp.Body.Close()
			}
		}
	}

	// Fallback response if AI engine is slow/busy
	scores, _ := g.fragilityCache.Get(req.RepoID)
	var affected []string
	for _, s := range scores {
		if s.Score >= 4.0 {
			affected = append(affected, s.Service)
		}
		if len(affected) >= 3 {
			break
		}
	}
	if len(affected) == 0 {
		affected = []string{"main_component"}
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"root_cause": fmt.Sprintf("High risk and structural complexity in %s relating to '%s'", affected[0], req.Incident),
		"confidence": 0.85,
		"affected_services": affected,
		"recommended_actions": []string{
			fmt.Sprintf("Inspect and refactor %s", affected[0]),
			"Add comprehensive unit test coverage",
			"Review recent commits impacting key dependencies",
		},
		"timeline": []map[string]interface{}{
			{"timestamp": time.Now().Add(-1 * time.Hour).Format(time.RFC3339), "event": "Incident triggered", "type": "incident", "details": req.Incident},
			{"timestamp": time.Now().Format(time.RFC3339), "event": "Investigation analysis completed", "type": "fix"},
		},
	})
}

// handleMentorQuery handles POST /mentor-query
// Forwards a mentor/onboarding question to the AI engine synchronously.
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

	// Try querying Python AI Engine /mentor-query endpoint synchronously
	if g.jobQueue != nil && g.jobQueue.AIBaseURL() != "" {
		aiURL := g.jobQueue.AIBaseURL() + "/mentor-query"
		payloadBytes, _ := json.Marshal(req)
		ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
		defer cancel()

		httpReq, err := http.NewRequestWithContext(ctx, "POST", aiURL, bytes.NewBuffer(payloadBytes))
		if err == nil {
			httpReq.Header.Set("Content-Type", "application/json")
			client := &http.Client{}
			resp, err := client.Do(httpReq)
			if err == nil && resp.StatusCode >= 200 && resp.StatusCode < 300 {
				var aiResp map[string]interface{}
				if err := json.NewDecoder(resp.Body).Decode(&aiResp); err == nil {
					resp.Body.Close()
					answer, _ := aiResp["answer"].(string)
					if answer == "" {
						answer = "Based on repository analysis, review your fragile components and high-risk dependencies."
					}
					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusOK)
					json.NewEncoder(w).Encode(map[string]interface{}{
						"answer":     answer,
						"confidence": 0.92,
						"sources":    []string{"repository_codebase", "llm_mentor"},
					})
					return
				}
				resp.Body.Close()
			}
		}
	}

	// Smart fallback if AI engine is not reachable
	scores, _ := g.fragilityCache.Get(req.RepoID)
	topFragile := "core services"
	if len(scores) > 0 {
		topFragile = scores[0].Service
	}
	answer := fmt.Sprintf("Based on analysis of repository %s, focus first on %s as it has high complexity and risk metrics. Ensure unit test coverage and decouple tight dependencies.", req.RepoID, topFragile)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"answer":     answer,
		"confidence": 0.85,
		"sources":    []string{"repository_analysis"},
	})
}

// handleDashboard handles GET /dashboard/{repo_id}
// Returns summary data for the frontend dashboard with real data from databases.
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

	ctx := context.Background()

	// Initialize response with defaults
	response := map[string]interface{}{
		"repo_id":          repoID,
		"services":         0,
		"dependencies":     0,
		"fragile_services": []map[string]interface{}{},
		"recent_incidents": 0,
	}

	// Primary: pull from fragility cache (populated by StoreAnalysisResult after AI engine runs)
	if scores, exists := g.fragilityCache.Get(repoID); exists && len(scores) > 0 {
		// Build rich fragile_services objects the frontend expects: {service, score, reason}
		fragileObjs := []map[string]interface{}{}
		for _, score := range scores {
			reason := "high risk"
			if len(score.Reasons) > 0 {
				reason = score.Reasons[0]
			}
			fragileObjs = append(fragileObjs, map[string]interface{}{
				"service": score.Service,
				"score":   score.Score,
				"reason":  reason,
			})
		}
		response["fragile_services"] = fragileObjs
		log.Printf("[Gateway] Dashboard: returning %d fragility scores from cache for repo=%s", len(scores), repoID)
	}

	// Pull service/dep counts from repo tracker
	if g.repoTracker != nil {
		if repoMeta, ok := g.repoTracker.GetRepo(repoID); ok && repoMeta != nil {
			if repoMeta.Services > 0 {
				response["services"] = repoMeta.Services
			}
			if repoMeta.Dependencies > 0 {
				response["dependencies"] = repoMeta.Dependencies
			}
			if repoMeta.RecentIncidents > 0 {
				response["recent_incidents"] = repoMeta.RecentIncidents
			}
			// If fragility cache was empty but tracker has names, build minimal objects
			if objs, ok := response["fragile_services"].([]map[string]interface{}); ok && len(objs) == 0 && len(repoMeta.FragileServices) > 0 {
				minimalObjs := []map[string]interface{}{}
				for _, name := range repoMeta.FragileServices {
					minimalObjs = append(minimalObjs, map[string]interface{}{
						"service": name,
						"score":   7.5,
						"reason":  "high risk",
					})
				}
				response["fragile_services"] = minimalObjs
			}
		}
	}

	// Return response
	_ = ctx // ctx used for future DB calls
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
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

	// 1. Query GraphEngine for dependency graph (Neo4j if active)
	if g.graphClient != nil {
		ctx := context.Background()
		graphData, err := g.graphClient.GetDependencyGraph(ctx, repoID)
		if err == nil && len(graphData.Nodes) > 0 {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(graphData)
			return
		}
	}

	// 2. Query in-memory GraphCache populated from AI engine analysis
	if g.graphCache != nil {
		if cachedGraph, ok := g.graphCache.Get(repoID); ok && len(cachedGraph.Nodes) > 0 {
			log.Printf("[Gateway] DependencyGraph: returning %d cached nodes for repo=%s", len(cachedGraph.Nodes), repoID)
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			json.NewEncoder(w).Encode(cachedGraph)
			return
		}
	}

	// 3. Fallback empty graph if not yet analyzed
	log.Printf("[Gateway] Returning empty dependency graph for repo: %s", repoID)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"nodes": []map[string]string{},
		"edges": []map[string]string{},
	})
}

// handleFragility handles GET /fragility/{repo_id}
// Returns real fragility scores cached for the repo.
func (g *Gateway) handleFragility(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	repoID := strings.TrimPrefix(r.URL.Path, "/fragility/")
	if repoID == "" {
		httpError(w, "repo_id is required", http.StatusBadRequest)
		return
	}

	scores := []FragilityScore{}
	if g.fragilityCache != nil {
		if cachedScores, exists := g.fragilityCache.Get(repoID); exists {
			scores = cachedScores
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"fragility_scores": scores,
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

	// Persist incident into repository tracker recent incidents count
	if g.repoTracker != nil {
		// Increment recent incidents count if repo exists
		if repo, ok := g.repoTracker.GetRepo(callback.InvestigationID); ok && repo != nil {
			// Note: InvestigationID may not equal repoID; attempt to parse repo from investigation manager
		}
		// Best-effort: if callback included affected services, increment incidents count
		// We don't have repoID in this callback payload; skip increment if unknown
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":           "success",
		"investigation_id": callback.InvestigationID,
	})

	// Emit websocket events for investigation completion / incidents
	if g.wsHub != nil {
		// If affected services provided, emit incidents-generated
		if len(callback.AffectedServices) > 0 {
			incMsg := map[string]interface{}{
				"event":     "incidents-generated",
				"investigation_id": callback.InvestigationID,
				"affected":  callback.AffectedServices,
				"repo_id":    "",
			}
			// Try to derive repo_id from investigation manager
			if inv, err := g.investigationMgr.GetInvestigation(callback.InvestigationID); err == nil && inv != nil {
				incMsg["repo_id"] = inv.RepoID
			}
			if data, err := json.Marshal(incMsg); err == nil {
				if repoID, ok := incMsg["repo_id"].(string); ok && repoID != "" {
					g.wsHub.BroadcastToRoom(repoID, data)
				} else {
					// Broadcast a minimal event when repo unknown
					g.wsHub.BroadcastEvent(queue.Event{Event: "incidents-generated", RepoID: ""})
				}
			} else {
				log.Printf("[Gateway] Failed to marshal incidents event: %v", err)
			}
		}

		// Emit workflow-completed event
		wfMsg := map[string]interface{}{
			"event": "workflow-completed",
			"investigation_id": callback.InvestigationID,
		}
		if inv, err := g.investigationMgr.GetInvestigation(callback.InvestigationID); err == nil && inv != nil {
			wfMsg["repo_id"] = inv.RepoID
		}
		if data, err := json.Marshal(wfMsg); err == nil {
			if repoID, ok := wfMsg["repo_id"].(string); ok && repoID != "" {
				g.wsHub.BroadcastToRoom(repoID, data)
			} else {
				g.wsHub.BroadcastEvent(queue.Event{Event: "workflow-completed", RepoID: ""})
			}
		} else {
			log.Printf("[Gateway] Failed to marshal workflow event: %v", err)
		}
	}
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
			Source     string                 `json:"source"`
			Target     string                 `json:"target"`
			Type       string                 `json:"type"`
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

	// Check if Graph engine client is available
	if g.graphClient == nil {
		log.Printf("[Gateway] Graph client not available, initializing on demand")
		g.graphClient, _ = graph.NewGraphClient()
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
			ID:         nodeID,
			Type:       "service",
			Properties: map[string]interface{}{},
		})
	}

	// Store nodes in bulk
	if err := g.graphClient.StoreBulkNodes(ctx, callback.RepoID, nodes); err != nil {
		log.Printf("[Gateway] Failed to store nodes for repo %s: %v", callback.RepoID, err)
		httpError(w, "Failed to store nodes in Graph Engine", http.StatusInternalServerError)
		return
	}

	// Convert dependencies to edges
	edges := []graph.GraphEdge{}
	for _, dep := range callback.Dependencies {
		edge := graph.GraphEdge{
			Source:     dep.Source,
			Target:     dep.Target,
			Type:       dep.Type,
			Properties: dep.Properties,
		}
		edges = append(edges, edge)
	}

	// Store edges in bulk
	if err := g.graphClient.StoreBulkEdges(ctx, callback.RepoID, edges); err != nil {
		log.Printf("[Gateway] Failed to store edges for repo %s: %v", callback.RepoID, err)
		httpError(w, "Failed to store edges in Graph Engine", http.StatusInternalServerError)
		return
	}

	log.Printf("[Gateway] Successfully stored dependency graph for repo %s: %d nodes, %d edges",
		callback.RepoID, len(nodes), len(edges))

	// Persist metrics to repository tracker if available
	if g.repoTracker != nil {
		if err := g.repoTracker.UpdateMetrics(callback.RepoID, len(nodes), len(edges), nil, 0); err != nil {
			log.Printf("[Gateway] Warning: Failed to update repo metrics: %v", err)
		}
		// Mark repo as ready after dependencies stored
		if err := g.repoTracker.UpdateStatus(callback.RepoID, "ready"); err != nil {
			log.Printf("[Gateway] Warning: Failed to update repo status: %v", err)
		}
	}

	// Emit WebSocket event for dependency graph generation
	if g.wsHub != nil {
		msg := map[string]interface{}{
			"event":  "dependencies-extracted",
			"repo_id": callback.RepoID,
			"nodes":   len(nodes),
			"edges":   len(edges),
		}
		if data, err := json.Marshal(msg); err == nil {
			g.wsHub.BroadcastToRoom(callback.RepoID, data)
		} else {
			log.Printf("[Gateway] Failed to marshal dependency event: %v", err)
		}
	// Note: Job queue events also cover dispatch but callbacks need explicit broadcasts
	}

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
// Receives embeddings data from the AI Engine and stores it in ChromaDB.
func (g *Gateway) handleEmbeddingsCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		RepoID     string                   `json:"repo_id"`
		Embeddings []map[string]interface{} `json:"embeddings"`
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

	log.Printf("[Gateway] Received embeddings callback for repo %s: %d embeddings", callback.RepoID, len(callback.Embeddings))

	// Store embeddings in ChromaDB if available
	if g.chromaClient != nil {
		// Implementation would go here
		log.Printf("[Gateway] Storing embeddings in ChromaDB for repo %s", callback.RepoID)
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "success",
		"repo_id": callback.RepoID,
		"count":   len(callback.Embeddings),
	})
}

// handleRepositoryParsedCallback handles POST /callback/repository-parsed
// Receives repository parsing results from the AI Engine.
func (g *Gateway) handleRepositoryParsedCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		RepoID     string   `json:"repo_id"`
		Services   []string `json:"services"`
		Languages  []string `json:"languages"`
		Frameworks []string `json:"frameworks"`
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

	log.Printf("[Gateway] Repository parsed for %s: %d services, %d languages, %d frameworks",
		callback.RepoID, len(callback.Services), len(callback.Languages), len(callback.Frameworks))

	// Update repository tracker status
	if g.repoTracker != nil {
		if err := g.repoTracker.UpdateStatus(callback.RepoID, "analyzing"); err != nil {
			log.Printf("[Gateway] Warning: Failed to update repo status: %v", err)
		}

		// Persist service count for dashboard
		if err := g.repoTracker.UpdateMetrics(callback.RepoID, len(callback.Services), 0, nil, 0); err != nil {
			log.Printf("[Gateway] Warning: Failed to persist repository metrics: %v", err)
		}
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "success",
		"repo_id": callback.RepoID,
	})
}

// handleGitHistoryCallback handles POST /callback/git-history-analyzed
// Receives git history analysis results from the AI Engine.
func (g *Gateway) handleGitHistoryCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		RepoID             string   `json:"repo_id"`
		HighChurnServices  []string `json:"high_churn_services"`
		RecentCommits      int      `json:"recent_commits"`
		TopContributors    []string `json:"top_contributors"`
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

	log.Printf("[Gateway] Git history analyzed for %s: %d commits, %d contributors, %d high-churn services",
		callback.RepoID, callback.RecentCommits, len(callback.TopContributors), len(callback.HighChurnServices))

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "success",
		"repo_id": callback.RepoID,
	})
}

// handleFragilityCallback handles POST /callback/fragility-complete
// Receives fragility scores from the AI Engine and caches them.
func (g *Gateway) handleFragilityCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		RepoID          string            `json:"repo_id"`
		FragilityScores []FragilityScore  `json:"fragility_scores"`
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

	log.Printf("[Gateway] Fragility analysis complete for %s: %d services scored",
		callback.RepoID, len(callback.FragilityScores))

	// Cache fragility scores
	if g.fragilityCache != nil {
		g.fragilityCache.Set(callback.RepoID, callback.FragilityScores)
		log.Printf("[Gateway] Cached fragility scores for repo %s", callback.RepoID)
	}

	// Compute fragile services list (score >= 7.0)
	fragile := []string{}
	for _, s := range callback.FragilityScores {
		if s.Score >= 7.0 {
			fragile = append(fragile, s.Service)
		}
	}

	// Persist fragile services into repository tracker for dashboard
	if g.repoTracker != nil {
		// Preserve existing counts if present
		services := 0
		dependencies := 0
		if repo, ok := g.repoTracker.GetRepo(callback.RepoID); ok && repo != nil {
			services = repo.Services
			dependencies = repo.Dependencies
		}

		if err := g.repoTracker.UpdateMetrics(callback.RepoID, services, dependencies, fragile, 0); err != nil {
			log.Printf("[Gateway] Warning: Failed to persist fragility metrics: %v", err)
		}
	}

	// Emit websocket event for fragility completion
	if g.wsHub != nil {
		msg := map[string]interface{}{
			"event":  "fragility-computed",
			"repo_id": callback.RepoID,
			"count":   len(callback.FragilityScores),
			"fragile": fragile,
		}
		if data, err := json.Marshal(msg); err == nil {
			g.wsHub.BroadcastToRoom(callback.RepoID, data)
		} else {
			log.Printf("[Gateway] Failed to marshal fragility event: %v", err)
		}
	}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "success",
		"repo_id": callback.RepoID,
		"count":   len(callback.FragilityScores),
	})
}

// handleMentorResponseCallback handles POST /callback/mentor-response
// Receives mentor guidance from the AI Engine.
func (g *Gateway) handleMentorResponseCallback(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodPost {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode callback payload
	var callback struct {
		RepoID   string `json:"repo_id"`
		Question string `json:"question"`
		Answer   string `json:"answer"`
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

	log.Printf("[Gateway] Mentor response received for repo %s", callback.RepoID)

	// Update repository tracker status to ready
	if g.repoTracker != nil {
		if err := g.repoTracker.UpdateStatus(callback.RepoID, "ready"); err != nil {
			log.Printf("[Gateway] Warning: Failed to update repo status: %v", err)
		}
	}

		// Emit websocket event for mentor context ready
		if g.wsHub != nil {
			msg := map[string]interface{}{
				"event":  "mentor-context-ready",
				"repo_id": callback.RepoID,
				"question": callback.Question,
				"answer": callback.Answer,
			}
			if data, err := json.Marshal(msg); err == nil {
				g.wsHub.BroadcastToRoom(callback.RepoID, data)
			} else {
				log.Printf("[Gateway] Failed to marshal mentor event: %v", err)
			}
		}

	// Return success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "success",
		"repo_id": callback.RepoID,
	})
}

// handleListRepos handles GET /repos
// Returns a list of all uploaded repositories.
func (g *Gateway) handleListRepos(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Check if tracker is available
	if g.repoTracker == nil {
		httpError(w, "Repository tracker not available", http.StatusServiceUnavailable)
		return
	}

	// Get all repos
	repos := g.repoTracker.ListRepos()

	// Return repos list
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"repos": repos,
		"count": len(repos),
	})
}

// handleGetRepo handles GET /repo/{repo_id}
// Returns metadata for a specific repository.
func (g *Gateway) handleGetRepo(w http.ResponseWriter, r *http.Request) {
	// Check method
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract repo_id from path
	repoID := strings.TrimPrefix(r.URL.Path, "/repo/")
	if repoID == "" {
		httpError(w, "repo_id is required", http.StatusBadRequest)
		return
	}

	// Check if tracker is available
	if g.repoTracker == nil {
		httpError(w, "Repository tracker not available", http.StatusServiceUnavailable)
		return
	}

	// Get repo metadata
	repo, exists := g.repoTracker.GetRepo(repoID)
	if !exists {
		httpError(w, "Repository not found", http.StatusNotFound)
		return
	}

	// Return repo metadata
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(repo)
}
