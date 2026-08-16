package queue

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
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
	Data   map[string]interface{} `json:"data,omitempty"`
}

// ResultCallback is called when a job produces a response body.
// jobType and repoID identify what was processed; result is the decoded JSON map.
type ResultCallback func(jobType, repoID string, result map[string]interface{})

// JobQueue is the async task dispatcher.
type JobQueue struct {
	jobs           chan Job
	aiBaseURL      string // base URL of the Python AI Engine, e.g. "http://localhost:8001"
	events         chan Event
	resultCallback ResultCallback // called synchronously after a successful job response
}

// NewJobQueue creates a new JobQueue with the specified AI engine base URL and buffer size.
func NewJobQueue(aiBaseURL string, bufferSize int) *JobQueue {
	return &JobQueue{
		jobs:      make(chan Job, bufferSize),
		aiBaseURL: aiBaseURL,
		events:    make(chan Event, 100),
	}
}

// SetResultCallback registers a callback to receive job results from the AI engine.
func (q *JobQueue) SetResultCallback(cb ResultCallback) {
	q.resultCallback = cb
}

// AIBaseURL returns the configured base URL of the AI engine.
func (q *JobQueue) AIBaseURL() string {
	return q.aiBaseURL
}

// Start begins the background worker goroutine that processes jobs from the queue.
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
func (q *JobQueue) Enqueue(jobType string, payload map[string]interface{}) error {
	job := Job{
		Type:    jobType,
		Payload: payload,
	}

	select {
	case q.jobs <- job:
		log.Printf("[JobQueue] Enqueued job: type=%s", jobType)
		return nil
	default:
		return fmt.Errorf("job queue is full, try again later")
	}
}

// dispatch sends a job to the appropriate AI Engine endpoint and reads the response.
func (q *JobQueue) dispatch(ctx context.Context, job Job) {
	endpoint := q.getEndpoint(job.Type)
	if endpoint == "" {
		log.Printf("[JobQueue] Unknown job type: %s", job.Type)
		return
	}

	url := q.aiBaseURL + endpoint

	jsonData, err := json.Marshal(job.Payload)
	if err != nil {
		log.Printf("[JobQueue] Failed to marshal payload for job %s: %v", job.Type, err)
		return
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("[JobQueue] Failed to create request for job %s: %v", job.Type, err)
		return
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("[JobQueue] Failed to dispatch job %s to %s: %v", job.Type, url, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		log.Printf("[JobQueue] Successfully dispatched job %s to %s (status: %d)", job.Type, url, resp.StatusCode)

		// Read and decode the response body
		body, readErr := io.ReadAll(resp.Body)
		if readErr == nil && len(body) > 0 && q.resultCallback != nil {
			var result map[string]interface{}
			if jsonErr := json.Unmarshal(body, &result); jsonErr == nil {
				repoID := ""
				if id, ok := job.Payload["repo_id"].(string); ok {
					repoID = id
				}
				log.Printf("[JobQueue] Calling result callback for job %s repo %s", job.Type, repoID)
				q.resultCallback(job.Type, repoID, result)
			} else {
				log.Printf("[JobQueue] Failed to decode response JSON for job %s: %v", job.Type, jsonErr)
			}
		}

		q.emitEvent(job)
	} else {
		log.Printf("[JobQueue] Job %s dispatch failed with status %d", job.Type, resp.StatusCode)
	}
}

// getEndpoint maps job types to AI Engine endpoints.
func (q *JobQueue) getEndpoint(jobType string) string {
	endpoints := map[string]string{
		"analyze_repo":        "/analyze-repo",
		"compute_fragility":   "/compute-fragility",
		"start_investigation": "/start-investigation",
		"mentor_query":        "/mentor-query",
	}
	return endpoints[jobType]
}

// emitEvent sends an event to the events channel (non-blocking).
func (q *JobQueue) emitEvent(job Job) {
	repoID := ""
	if id, ok := job.Payload["repo_id"].(string); ok {
		repoID = id
	}

	event := Event{
		Event:  job.Type + "_dispatched",
		RepoID: repoID,
	}

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
