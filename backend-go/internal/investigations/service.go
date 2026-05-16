package investigations

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"incidentos/backend-go/internal/queue"
	"incidentos/backend-go/internal/websocket"
)

// Investigation represents an ongoing or completed investigation
type Investigation struct {
	ID               string    `json:"id"`
	RepoID           string    `json:"repo_id"`
	Incident         string    `json:"incident"`
	Status           string    `json:"status"` // "started", "analyzing", "complete", "failed"
	Progress         []Step    `json:"progress"`
	RootCause        string    `json:"root_cause,omitempty"`
	AffectedServices []string  `json:"affected_services,omitempty"`
	FragilityScore   float64   `json:"fragility_score,omitempty"`
	HistoricalCorr   string    `json:"historical_correlation,omitempty"`
	RecommendedActions []string `json:"recommended_actions,omitempty"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
}

// Step represents a single step in the investigation workflow
type Step struct {
	Name      string    `json:"name"`
	Status    string    `json:"status"` // "pending", "in_progress", "complete", "failed"
	Timestamp time.Time `json:"timestamp"`
}

// RCAResult represents the final result from AI Engine investigation
type RCAResult struct {
	RootCause          string   `json:"root_cause"`
	AffectedServices   []string `json:"affected_services"`
	FragilityScore     float64  `json:"fragility_score"`
	HistoricalCorr     string   `json:"historical_correlation"`
	RecommendedActions []string `json:"recommended_actions"`
}

// InvestigationManager orchestrates investigation workflows
type InvestigationManager struct {
	investigations map[string]*Investigation
	jobQueue       *queue.JobQueue
	wsHub          *websocket.Hub
	mu             sync.RWMutex
}

// NewInvestigationManager creates a new InvestigationManager
func NewInvestigationManager(jq *queue.JobQueue, hub *websocket.Hub) *InvestigationManager {
	return &InvestigationManager{
		investigations: make(map[string]*Investigation),
		jobQueue:       jq,
		wsHub:          hub,
	}
}

// StartInvestigation creates a new investigation and enqueues it for processing
func (im *InvestigationManager) StartInvestigation(repoID, incident string) (string, error) {
	if repoID == "" {
		return "", fmt.Errorf("repo_id is required")
	}
	if incident == "" {
		return "", fmt.Errorf("incident description is required")
	}

	// Generate investigation ID
	investigationID := fmt.Sprintf("inv_%s_%d", repoID, time.Now().Unix())

	// Create investigation record
	now := time.Now()
	investigation := &Investigation{
		ID:        investigationID,
		RepoID:    repoID,
		Incident:  incident,
		Status:    "started",
		Progress:  []Step{},
		CreatedAt: now,
		UpdatedAt: now,
	}

	// Store investigation
	im.mu.Lock()
	im.investigations[investigationID] = investigation
	im.mu.Unlock()

	// Add initial step
	im.UpdateProgress(investigationID, "Investigation initialized", "complete")

	// Enqueue job for AI Engine
	payload := map[string]interface{}{
		"investigation_id": investigationID,
		"repo_id":          repoID,
		"incident":         incident,
	}

	if err := im.jobQueue.Enqueue("start_investigation", payload); err != nil {
		// Mark investigation as failed
		im.mu.Lock()
		investigation.Status = "failed"
		investigation.UpdatedAt = time.Now()
		im.mu.Unlock()
		return "", fmt.Errorf("failed to enqueue investigation job: %w", err)
	}

	// Emit WebSocket event (investigation_started will be emitted by queue)
	// The queue will emit the event when it processes the job

	return investigationID, nil
}

// GetInvestigation retrieves an investigation by ID
func (im *InvestigationManager) GetInvestigation(investigationID string) (*Investigation, error) {
	im.mu.RLock()
	defer im.mu.RUnlock()

	investigation, exists := im.investigations[investigationID]
	if !exists {
		return nil, fmt.Errorf("investigation not found: %s", investigationID)
	}

	// Return a copy to prevent external modification
	investigationCopy := *investigation
	investigationCopy.Progress = make([]Step, len(investigation.Progress))
	copy(investigationCopy.Progress, investigation.Progress)
	if investigation.AffectedServices != nil {
		investigationCopy.AffectedServices = make([]string, len(investigation.AffectedServices))
		copy(investigationCopy.AffectedServices, investigation.AffectedServices)
	}
	if investigation.RecommendedActions != nil {
		investigationCopy.RecommendedActions = make([]string, len(investigation.RecommendedActions))
		copy(investigationCopy.RecommendedActions, investigation.RecommendedActions)
	}

	return &investigationCopy, nil
}

// UpdateProgress adds a progress step to an investigation
func (im *InvestigationManager) UpdateProgress(investigationID, stepName, status string) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	investigation, exists := im.investigations[investigationID]
	if !exists {
		return fmt.Errorf("investigation not found: %s", investigationID)
	}

	// Add new step
	step := Step{
		Name:      stepName,
		Status:    status,
		Timestamp: time.Now(),
	}
	investigation.Progress = append(investigation.Progress, step)
	investigation.UpdatedAt = time.Now()

	// Update investigation status based on step
	if status == "in_progress" && investigation.Status == "started" {
		investigation.Status = "analyzing"
	}

	return nil
}

// CompleteInvestigation marks an investigation as complete with final results
func (im *InvestigationManager) CompleteInvestigation(investigationID string, result RCAResult) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	investigation, exists := im.investigations[investigationID]
	if !exists {
		return fmt.Errorf("investigation not found: %s", investigationID)
	}

	// Update investigation with results
	investigation.Status = "complete"
	investigation.RootCause = result.RootCause
	investigation.AffectedServices = result.AffectedServices
	investigation.FragilityScore = result.FragilityScore
	investigation.HistoricalCorr = result.HistoricalCorr
	investigation.RecommendedActions = result.RecommendedActions
	investigation.UpdatedAt = time.Now()

	// Add completion step
	step := Step{
		Name:      "Investigation complete",
		Status:    "complete",
		Timestamp: time.Now(),
	}
	investigation.Progress = append(investigation.Progress, step)

	// Emit WebSocket event for completion
	if im.wsHub != nil {
		eventData := map[string]interface{}{
			"event":            "investigation_complete",
			"investigation_id": investigationID,
			"repo_id":          investigation.RepoID,
		}
		eventJSON, err := json.Marshal(eventData)
		if err == nil {
			im.wsHub.BroadcastToRoom(investigation.RepoID, eventJSON)
		}
	}

	return nil
}

// FailInvestigation marks an investigation as failed
func (im *InvestigationManager) FailInvestigation(investigationID string, reason string) error {
	im.mu.Lock()
	defer im.mu.Unlock()

	investigation, exists := im.investigations[investigationID]
	if !exists {
		return fmt.Errorf("investigation not found: %s", investigationID)
	}

	investigation.Status = "failed"
	investigation.UpdatedAt = time.Now()

	// Add failure step
	step := Step{
		Name:      fmt.Sprintf("Investigation failed: %s", reason),
		Status:    "failed",
		Timestamp: time.Now(),
	}
	investigation.Progress = append(investigation.Progress, step)

	return nil
}

// ListInvestigations returns all investigations for a given repo_id
func (im *InvestigationManager) ListInvestigations(repoID string) ([]*Investigation, error) {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var investigations []*Investigation
	for _, inv := range im.investigations {
		if inv.RepoID == repoID {
			// Create a copy
			invCopy := *inv
			invCopy.Progress = make([]Step, len(inv.Progress))
			copy(invCopy.Progress, inv.Progress)
			if inv.AffectedServices != nil {
				invCopy.AffectedServices = make([]string, len(inv.AffectedServices))
				copy(invCopy.AffectedServices, inv.AffectedServices)
			}
			if inv.RecommendedActions != nil {
				invCopy.RecommendedActions = make([]string, len(inv.RecommendedActions))
				copy(invCopy.RecommendedActions, inv.RecommendedActions)
			}
			investigations = append(investigations, &invCopy)
		}
	}

	return investigations, nil
}

// GetAllInvestigations returns all investigations (for admin/debugging)
func (im *InvestigationManager) GetAllInvestigations() []*Investigation {
	im.mu.RLock()
	defer im.mu.RUnlock()

	var investigations []*Investigation
	for _, inv := range im.investigations {
		invCopy := *inv
		invCopy.Progress = make([]Step, len(inv.Progress))
		copy(invCopy.Progress, inv.Progress)
		if inv.AffectedServices != nil {
			invCopy.AffectedServices = make([]string, len(inv.AffectedServices))
			copy(invCopy.AffectedServices, inv.AffectedServices)
		}
		if inv.RecommendedActions != nil {
			invCopy.RecommendedActions = make([]string, len(inv.RecommendedActions))
			copy(invCopy.RecommendedActions, inv.RecommendedActions)
		}
		investigations = append(investigations, &invCopy)
	}

	return investigations
}

// Made with Bob
