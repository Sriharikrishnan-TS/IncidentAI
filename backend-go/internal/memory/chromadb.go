package memory

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"
)

// ChromaDBClient manages connections to ChromaDB vector database
type ChromaDBClient struct {
	baseURL    string
	httpClient *http.Client
}

// Document represents a document with embeddings in ChromaDB
type Document struct {
	ID        string                 `json:"id"`
	Content   string                 `json:"content"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
	Embedding []float64              `json:"embedding"`
}

// QueryResult represents the result of a semantic search query
type QueryResult struct {
	IDs       [][]string               `json:"ids"`
	Documents [][]string               `json:"documents"`
	Metadatas [][]map[string]interface{} `json:"metadatas"`
	Distances [][]float64              `json:"distances"`
}

// CollectionInfo represents metadata about a collection
type CollectionInfo struct {
	Name     string                 `json:"name"`
	ID       string                 `json:"id"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// NewChromaDBClient creates a new ChromaDB client
func NewChromaDBClient(baseURL string) *ChromaDBClient {
	return &ChromaDBClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// CreateCollection creates a new collection in ChromaDB
func (c *ChromaDBClient) CreateCollection(ctx context.Context, name string) error {
	return c.executeWithRetry(ctx, func(ctx context.Context) error {
		payload := map[string]interface{}{
			"name": name,
			"metadata": map[string]interface{}{
				"created_at": time.Now().UTC().Format(time.RFC3339),
			},
		}

		body, err := json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("failed to marshal request: %w", err)
		}

		req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/v1/collections", bytes.NewReader(body))
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/json")

		resp, err := c.httpClient.Do(req)
		if err != nil {
			return fmt.Errorf("failed to execute request: %w", err)
		}
		defer resp.Body.Close()

		// ChromaDB returns 200 for success, 409 if collection already exists
		if resp.StatusCode == http.StatusConflict {
			log.Printf("[ChromaDB] Collection '%s' already exists", name)
			return nil // Not an error - collection exists
		}

		if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
			bodyBytes, _ := io.ReadAll(resp.Body)
			return fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(bodyBytes))
		}

		log.Printf("[ChromaDB] Created collection: %s", name)
		return nil
	})
}

// AddDocument adds a single document to a collection
func (c *ChromaDBClient) AddDocument(ctx context.Context, collection string, doc Document) error {
	return c.AddDocuments(ctx, collection, []Document{doc})
}

// AddDocuments adds multiple documents to a collection (batch operation)
func (c *ChromaDBClient) AddDocuments(ctx context.Context, collection string, docs []Document) error {
	if len(docs) == 0 {
		return nil
	}

	return c.executeWithRetry(ctx, func(ctx context.Context) error {
		// Prepare batch data
		ids := make([]string, len(docs))
		documents := make([]string, len(docs))
		embeddings := make([][]float64, len(docs))
		metadatas := make([]map[string]interface{}, len(docs))

		for i, doc := range docs {
			ids[i] = doc.ID
			documents[i] = doc.Content
			embeddings[i] = doc.Embedding
			if doc.Metadata != nil {
				metadatas[i] = doc.Metadata
			} else {
				metadatas[i] = make(map[string]interface{})
			}
		}

		payload := map[string]interface{}{
			"ids":        ids,
			"documents":  documents,
			"embeddings": embeddings,
			"metadatas":  metadatas,
		}

		body, err := json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("failed to marshal request: %w", err)
		}

		url := fmt.Sprintf("%s/api/v1/collections/%s/add", c.baseURL, collection)
		req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/json")

		resp, err := c.httpClient.Do(req)
		if err != nil {
			return fmt.Errorf("failed to execute request: %w", err)
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
			bodyBytes, _ := io.ReadAll(resp.Body)
			return fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(bodyBytes))
		}

		log.Printf("[ChromaDB] Added %d documents to collection: %s", len(docs), collection)
		return nil
	})
}

// Query performs semantic search on a collection
func (c *ChromaDBClient) Query(ctx context.Context, collection string, queryEmbedding []float64, limit int) ([]Document, error) {
	var result []Document

	err := c.executeWithRetry(ctx, func(ctx context.Context) error {
		payload := map[string]interface{}{
			"query_embeddings": [][]float64{queryEmbedding},
			"n_results":        limit,
			"include":          []string{"documents", "metadatas", "distances"},
		}

		body, err := json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("failed to marshal request: %w", err)
		}

		url := fmt.Sprintf("%s/api/v1/collections/%s/query", c.baseURL, collection)
		req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/json")

		resp, err := c.httpClient.Do(req)
		if err != nil {
			return fmt.Errorf("failed to execute request: %w", err)
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			bodyBytes, _ := io.ReadAll(resp.Body)
			return fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(bodyBytes))
		}

		var queryResult QueryResult
		if err := json.NewDecoder(resp.Body).Decode(&queryResult); err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}

		// Convert ChromaDB response to Document slice
		if len(queryResult.IDs) > 0 && len(queryResult.IDs[0]) > 0 {
			result = make([]Document, len(queryResult.IDs[0]))
			for i := range queryResult.IDs[0] {
				doc := Document{
					ID:      queryResult.IDs[0][i],
					Content: queryResult.Documents[0][i],
				}
				if len(queryResult.Metadatas) > 0 && len(queryResult.Metadatas[0]) > i {
					doc.Metadata = queryResult.Metadatas[0][i]
				}
				result[i] = doc
			}
		}

		log.Printf("[ChromaDB] Query returned %d results from collection: %s", len(result), collection)
		return nil
	})

	return result, err
}

// GetDocument retrieves a specific document by ID
func (c *ChromaDBClient) GetDocument(ctx context.Context, collection, docID string) (*Document, error) {
	var result *Document

	err := c.executeWithRetry(ctx, func(ctx context.Context) error {
		payload := map[string]interface{}{
			"ids":     []string{docID},
			"include": []string{"documents", "metadatas", "embeddings"},
		}

		body, err := json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("failed to marshal request: %w", err)
		}

		url := fmt.Sprintf("%s/api/v1/collections/%s/get", c.baseURL, collection)
		req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/json")

		resp, err := c.httpClient.Do(req)
		if err != nil {
			return fmt.Errorf("failed to execute request: %w", err)
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			bodyBytes, _ := io.ReadAll(resp.Body)
			return fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(bodyBytes))
		}

		var getResult struct {
			IDs        []string                 `json:"ids"`
			Documents  []string                 `json:"documents"`
			Metadatas  []map[string]interface{} `json:"metadatas"`
			Embeddings [][]float64              `json:"embeddings"`
		}

		if err := json.NewDecoder(resp.Body).Decode(&getResult); err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}

		if len(getResult.IDs) == 0 {
			return fmt.Errorf("document not found: %s", docID)
		}

		result = &Document{
			ID:      getResult.IDs[0],
			Content: getResult.Documents[0],
		}

		if len(getResult.Metadatas) > 0 {
			result.Metadata = getResult.Metadatas[0]
		}

		if len(getResult.Embeddings) > 0 {
			result.Embedding = getResult.Embeddings[0]
		}

		return nil
	})

	return result, err
}

// DeleteCollection deletes a collection from ChromaDB
func (c *ChromaDBClient) DeleteCollection(ctx context.Context, name string) error {
	return c.executeWithRetry(ctx, func(ctx context.Context) error {
		url := fmt.Sprintf("%s/api/v1/collections/%s", c.baseURL, name)
		req, err := http.NewRequestWithContext(ctx, "DELETE", url, nil)
		if err != nil {
			return fmt.Errorf("failed to create request: %w", err)
		}

		resp, err := c.httpClient.Do(req)
		if err != nil {
			return fmt.Errorf("failed to execute request: %w", err)
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusNoContent {
			bodyBytes, _ := io.ReadAll(resp.Body)
			return fmt.Errorf("unexpected status code %d: %s", resp.StatusCode, string(bodyBytes))
		}

		log.Printf("[ChromaDB] Deleted collection: %s", name)
		return nil
	})
}

// QueryIncidentHistory retrieves similar historical incidents for correlation
func (c *ChromaDBClient) QueryIncidentHistory(ctx context.Context, repoID string, incidentEmbedding []float64, limit int) ([]Document, error) {
	collection := fmt.Sprintf("incidents_%s", repoID)
	return c.Query(ctx, collection, incidentEmbedding, limit)
}

// GetCollectionName returns the standardized collection name for a repo and type
func GetCollectionName(repoID, collectionType string) string {
	return fmt.Sprintf("%s_%s", collectionType, repoID)
}

// executeWithRetry executes a function with exponential backoff retry logic
func (c *ChromaDBClient) executeWithRetry(ctx context.Context, fn func(context.Context) error) error {
	maxRetries := 3
	baseDelay := 100 * time.Millisecond

	var lastErr error
	for attempt := 0; attempt < maxRetries; attempt++ {
		if attempt > 0 {
			delay := baseDelay * time.Duration(1<<uint(attempt-1))
			log.Printf("[ChromaDB] Retry attempt %d after %v", attempt+1, delay)
			
			select {
			case <-time.After(delay):
			case <-ctx.Done():
				return ctx.Err()
			}
		}

		lastErr = fn(ctx)
		if lastErr == nil {
			return nil
		}

		// Don't retry on context cancellation
		if ctx.Err() != nil {
			return ctx.Err()
		}

		log.Printf("[ChromaDB] Attempt %d failed: %v", attempt+1, lastErr)
	}

	return fmt.Errorf("failed after %d attempts: %w", maxRetries, lastErr)
}

// HealthCheck verifies ChromaDB connectivity
func (c *ChromaDBClient) HealthCheck(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, "GET", c.baseURL+"/api/v1/heartbeat", nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	log.Printf("[ChromaDB] Health check passed")
	return nil
}

// Made with Bob