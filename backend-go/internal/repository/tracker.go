package repository

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// RepoMetadata stores information about an uploaded repository
type RepoMetadata struct {
	RepoID      string    `json:"repo_id"`
	RepoURL     string    `json:"repo_url"`
	RepoPath    string    `json:"repo_path"`
	UploadedAt  time.Time `json:"uploaded_at"`
	Status      string    `json:"status"` // "uploaded", "analyzing", "ready"
	LastUpdated time.Time `json:"last_updated"`
	// Dashboard metrics
	Services        int      `json:"services,omitempty"`
	Dependencies    int      `json:"dependencies,omitempty"`
	FragileServices []string `json:"fragile_services,omitempty"`
	RecentIncidents int      `json:"recent_incidents,omitempty"`
}

// Tracker manages repository metadata and provides listing capabilities
type Tracker struct {
	repos      map[string]*RepoMetadata
	mu         sync.RWMutex
	storageDir string
}

// NewTracker creates a new repository tracker
func NewTracker(storageDir string) *Tracker {
	tracker := &Tracker{
		repos:      make(map[string]*RepoMetadata),
		storageDir: storageDir,
	}
	
	// Load existing repos from disk if available
	tracker.loadFromDisk()
	
	return tracker
}

// AddRepo registers a new repository
func (t *Tracker) AddRepo(repoID, repoURL, repoPath string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	metadata := &RepoMetadata{
		RepoID:      repoID,
		RepoURL:     repoURL,
		RepoPath:    repoPath,
		UploadedAt:  time.Now(),
		Status:      "uploaded",
		LastUpdated: time.Now(),
	}
	
	t.repos[repoID] = metadata
	
	// Persist to disk
	return t.saveToDisk()
}

// UpdateStatus updates the status of a repository
func (t *Tracker) UpdateStatus(repoID, status string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	if repo, exists := t.repos[repoID]; exists {
		repo.Status = status
		repo.LastUpdated = time.Now()
		return t.saveToDisk()
	}
	
	return nil
}

// UpdateMetrics updates dashboard-related metrics for a repository
func (t *Tracker) UpdateMetrics(repoID string, services, dependencies int, fragile []string, incidents int) error {
	t.mu.Lock()
	defer t.mu.Unlock()

	if repo, exists := t.repos[repoID]; exists {
		repo.Services = services
		repo.Dependencies = dependencies
		repo.FragileServices = fragile
		repo.RecentIncidents = incidents
		repo.LastUpdated = time.Now()
		return t.saveToDisk()
	}

	return nil
}

// GetRepo retrieves metadata for a specific repository
func (t *Tracker) GetRepo(repoID string) (*RepoMetadata, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()
	
	repo, exists := t.repos[repoID]
	return repo, exists
}

// ListRepos returns all registered repositories
func (t *Tracker) ListRepos() []*RepoMetadata {
	t.mu.RLock()
	defer t.mu.RUnlock()
	
	repos := make([]*RepoMetadata, 0, len(t.repos))
	for _, repo := range t.repos {
		repos = append(repos, repo)
	}
	
	return repos
}

// DeleteRepo removes a repository from tracking
func (t *Tracker) DeleteRepo(repoID string) error {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	delete(t.repos, repoID)
	return t.saveToDisk()
}

// saveToDisk persists the repository metadata to disk
func (t *Tracker) saveToDisk() error {
	if t.storageDir == "" {
		return nil // No persistence configured
	}
	
	// Ensure storage directory exists
	if err := os.MkdirAll(t.storageDir, 0755); err != nil {
		return err
	}
	
	filePath := filepath.Join(t.storageDir, "repos.json")
	
	data, err := json.MarshalIndent(t.repos, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filePath, data, 0644)
}

// loadFromDisk loads repository metadata from disk
func (t *Tracker) loadFromDisk() error {
	if t.storageDir == "" {
		return nil // No persistence configured
	}
	
	filePath := filepath.Join(t.storageDir, "repos.json")
	
	data, err := os.ReadFile(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil // File doesn't exist yet, that's okay
		}
		return err
	}
	
	return json.Unmarshal(data, &t.repos)
}

// Made with Bob