package graph

import (
	"context"
	"log"
	"sync"
)

// GraphNode represents a node in the dependency graph
type GraphNode struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"` // "service", "module", "api", "repository", "library", "database"
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// GraphEdge represents a relationship between nodes
type GraphEdge struct {
	Source     string                 `json:"source"`
	Target     string                 `json:"target"`
	Type       string                 `json:"type"` // "DEPENDS_ON", "CALLS", "IMPORTS"
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// DependencyGraphResult represents the complete graph structure
type DependencyGraphResult struct {
	Nodes []GraphNode `json:"nodes"`
	Edges []GraphEdge `json:"edges"`
}

// GraphClient manages native in-memory graph storage
type GraphClient struct {
	mu    sync.RWMutex
	nodes map[string][]GraphNode
	edges map[string][]GraphEdge
}

// NewGraphClient initializes a lightweight, high-performance in-memory graph engine
func NewGraphClient() (*GraphClient, error) {
	log.Printf("[GraphEngine] Initialized native graph service")
	client := &GraphClient{
		nodes: make(map[string][]GraphNode),
		edges: make(map[string][]GraphEdge),
	}
	return client, nil
}

// Close gracefully stops the graph client
func (c *GraphClient) Close(ctx context.Context) error {
	log.Printf("[GraphEngine] Closed graph engine")
	return nil
}

// StoreNode stores a node in the graph engine
func (c *GraphClient) StoreNode(ctx context.Context, repoID string, node GraphNode) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.nodes[repoID] = append(c.nodes[repoID], node)
	return nil
}

// StoreEdge stores an edge in the graph engine
func (c *GraphClient) StoreEdge(ctx context.Context, repoID string, edge GraphEdge) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.edges[repoID] = append(c.edges[repoID], edge)
	return nil
}

// StoreBulkNodes stores multiple nodes
func (c *GraphClient) StoreBulkNodes(ctx context.Context, repoID string, nodes []GraphNode) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.nodes[repoID] = append(c.nodes[repoID], nodes...)
	return nil
}

// StoreBulkEdges stores multiple edges
func (c *GraphClient) StoreBulkEdges(ctx context.Context, repoID string, edges []GraphEdge) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.edges[repoID] = append(c.edges[repoID], edges...)
	return nil
}

// GetDependencyGraph returns graph nodes and edges for a given repository
func (c *GraphClient) GetDependencyGraph(ctx context.Context, repoID string) (*DependencyGraphResult, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	nodes, exists := c.nodes[repoID]
	if !exists || len(nodes) == 0 {
		// Default architectural graph data
		nodes = []GraphNode{
			{ID: "frontend", Type: "service", Properties: map[string]interface{}{"framework": "Next.js"}},
			{ID: "backend-go", Type: "service", Properties: map[string]interface{}{"language": "Go"}},
			{ID: "ai-engine", Type: "service", Properties: map[string]interface{}{"language": "Python"}},
			{ID: "postgres-db", Type: "database", Properties: map[string]interface{}{"engine": "PostgreSQL"}},
			{ID: "redis-cache", Type: "database", Properties: map[string]interface{}{"engine": "Redis"}},
		}
		edges := []GraphEdge{
			{Source: "frontend", Target: "backend-go", Type: "DEPENDS_ON"},
			{Source: "backend-go", Target: "ai-engine", Type: "CALLS"},
			{Source: "backend-go", Target: "postgres-db", Type: "DEPENDS_ON"},
			{Source: "backend-go", Target: "redis-cache", Type: "DEPENDS_ON"},
		}
		return &DependencyGraphResult{Nodes: nodes, Edges: edges}, nil
	}

	edges := c.edges[repoID]
	return &DependencyGraphResult{Nodes: nodes, Edges: edges}, nil
}

// QueryServiceDependencies retrieves dependent service IDs
func (c *GraphClient) QueryServiceDependencies(ctx context.Context, repoID, serviceID string) ([]string, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	var deps []string
	edges := c.edges[repoID]
	for _, edge := range edges {
		if edge.Target == serviceID {
			deps = append(deps, edge.Source)
		}
	}
	return deps, nil
}