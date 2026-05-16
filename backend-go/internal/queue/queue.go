package queue

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
)

// Job represents a single unit of async work.
type Job struct {
	Type    string                 // e.g. "analyze_repo", "compute_fragility"
	Payload map[string]interface{} // arbitrary data for the job
}

// Event is broadcast over WebSocket to the frontend.
type Event struct {
	Event  string `json:"event"`   // e.g. "repo_analysis_started"
	RepoID string `json:"repo_id"`
}

// JobQueue is the async task dispatcher.
type JobQueue struct {
	jobs      chan Job
	aiBaseURL string // base URL of the Python AI Engine, e.g. "http://localhost:8001"
	events    chan Event
}

// NewJobQueue creates a new JobQueue with the specified AI engine base URL and buffer size.
// The jobs channel is buffered to prevent blocking the API Gateway.
// The events channel is buffered with size 100 for WebSocket broadcasting.
func NewJobQueue(aiBaseURL string, bufferSize int) *JobQueue {
	return &JobQueue{
		jobs:      make(chan Job, bufferSize),
		aiBaseURL: aiBaseURL,
		events:    make(chan Event, 100),
	}
}

// Start begins the background worker goroutine that processes jobs from the queue.
// It runs until the context is cancelled.
func (q *JobQueue) Start(ctx context.Context) {
	go func() {
		log.Printf("[JobQueue] Worker started, listening for jobs...")
		for {
			select {
			case <-ctx.Done():
				log.Printf("[JobQueue] Worker shutting down...")
				return
			case job := <-q.jobs:
				q.dispatch(ctx, job)
			}
		}
	}()
}

// Enqueue adds a new job to the queue.
// It returns an error if the queue is full (non-blocking send).
func (q *JobQueue) Enqueue(jobType string, payload map[string]interface{}) error {
	job := Job{
		Type:    jobType,
		Payload: payload,
	}

	// Non-blocking send - return error if queue is full
	select {
	case q.jobs <- job:
		log.Printf("[JobQueue] Enqueued job: type=%s", jobType)
		return nil
	default:
		return fmt.Errorf("job queue is full, try again later")
	}
}

// dispatch sends a job to the appropriate AI Engine endpoint.
// It maps job types to endpoints and POSTs the payload as JSON.
func (q *JobQueue) dispatch(ctx context.Context, job Job) {
	// Map job type to AI Engine endpoint
	endpoint := q.getEndpoint(job.Type)
	if endpoint == "" {
		log.Printf("[JobQueue] Unknown job type: %s", job.Type)
		return
	}

	// Build full URL
	url := q.aiBaseURL + endpoint

	// Marshal payload to JSON
	jsonData, err := json.Marshal(job.Payload)
	if err != nil {
		log.Printf("[JobQueue] Failed to marshal payload for job %s: %v", job.Type, err)
		return
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("[JobQueue] Failed to create request for job %s: %v", job.Type, err)
		return
	}
	req.Header.Set("Content-Type", "application/json")

	// Send request
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("[JobQueue] Failed to dispatch job %s to %s: %v", job.Type, url, err)
		return
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		log.Printf("[JobQueue] Successfully dispatched job %s to %s (status: %d)", job.Type, url, resp.StatusCode)
		
		// Emit event on success (non-blocking)
		q.emitEvent(job)
	} else {
		log.Printf("[JobQueue] Job %s dispatch failed with status %d", job.Type, resp.StatusCode)
	}
}

// getEndpoint maps job types to AI Engine endpoints.
func (q *JobQueue) getEndpoint(jobType string) string {
	endpoints := map[string]string{
		"analyze_repo":       "/analyze-repo",
		"compute_fragility":  "/compute-fragility",
		"start_investigation": "/start-investigation",
		"mentor_query":       "/mentor-query",
	}
	return endpoints[jobType]
}

// emitEvent sends an event to the events channel (non-blocking).
func (q *JobQueue) emitEvent(job Job) {
	// Extract repo_id from payload
	repoID := ""
	if id, ok := job.Payload["repo_id"].(string); ok {
		repoID = id
	}

	event := Event{
		Event:  job.Type + "_dispatched",
		RepoID: repoID,
	}

	// Non-blocking send
	select {
	case q.events <- event:
		log.Printf("[JobQueue] Emitted event: %s for repo %s", event.Event, event.RepoID)
	default:
		log.Printf("[JobQueue] Events channel full, dropping event: %s", event.Event)
	}
}

// Events returns the read-only events channel for WebSocket broadcasting.
func (q *JobQueue) Events() <-chan Event {
	return q.events
}

// Made with Bob
