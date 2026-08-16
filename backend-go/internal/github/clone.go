package github

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// CloneResult represents the result of a successful repository clone operation.
type CloneResult struct {
	RepoID   string `json:"repo_id"`
	RepoPath string `json:"repo_path"`
	Status   string `json:"status"` // always "cloned" on success
}

// CloneService handles cloning GitHub repositories to local disk.
type CloneService struct {
	BaseDir string // e.g. "./repos" — root directory for all cloned repos
}

// NewCloneService creates a new CloneService with the specified base directory.
// It creates the base directory if it doesn't exist.
func NewCloneService(baseDir string) *CloneService {
	// Create base directory if it doesn't exist
	if err := os.MkdirAll(baseDir, 0755); err != nil {
		// Log error but don't fail - let Clone() handle directory creation errors
		fmt.Printf("[CloneService] Warning: failed to create base directory %s: %v\n", baseDir, err)
	}
	return &CloneService{
		BaseDir: baseDir,
	}
}

// IsValidGitHubURL validates that a URL is a valid GitHub repository URL.
// Rules:
// - Must start with "https://github.com/"
// - Must have at least one "/" after the domain (owner)
// - Must have at least one more segment after the owner (repo name)
func IsValidGitHubURL(url string) bool {
	// Must start with https://github.com/
	if !strings.HasPrefix(url, "https://github.com/") {
		return false
	}

	// Remove the prefix to get the path
	path := strings.TrimPrefix(url, "https://github.com/")
	
	// Split by "/" to get segments
	segments := strings.Split(path, "/")
	
	// Must have at least 2 segments: owner and repo
	if len(segments) < 2 {
		return false
	}
	
	// Both owner and repo must be non-empty
	if segments[0] == "" || segments[1] == "" {
		return false
	}
	
	return true
}

// Clone clones a GitHub repository to local disk.
// It generates a unique repo_id, creates a local directory, runs git clone,
// and returns the CloneResult on success.
func (s *CloneService) Clone(ctx context.Context, repoURL string) (*CloneResult, error) {
	// Generate unique repo_id using short hash of the URL
	repoID := fmt.Sprintf("repo_%s", shortHash(repoURL))
	
	// Build local path
	localPath := filepath.Join(s.BaseDir, repoID)
	
	// Remove localPath if it already exists from a previous attempt
	_ = os.RemoveAll(localPath)
	
	// Create parent directory for baseDir
	if err := os.MkdirAll(s.BaseDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create base directory %s: %w", s.BaseDir, err)
	}
	
	// Run git clone command
	cmd := exec.CommandContext(ctx, "git", "clone", repoURL, localPath)
	
	// Capture stderr for error reporting
	stderr, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("git clone failed: %w\nOutput: %s", err, string(stderr))
	}
	
	// Return successful result
	return &CloneResult{
		RepoID:   repoID,
		RepoPath: localPath,
		Status:   "cloned",
	}, nil
}

// shortHash generates a short hash (first 8 hex characters) from the input string.
// This makes repo_id deterministic per URL (same URL = same ID).
func shortHash(input string) string {
	hash := sha256.Sum256([]byte(input))
	return hex.EncodeToString(hash[:])[:8]
}

// Made with Bob
