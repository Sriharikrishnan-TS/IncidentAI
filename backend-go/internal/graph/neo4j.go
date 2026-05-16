package graph

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
)

// Neo4jClient manages connections to Neo4j database
type Neo4jClient struct {
	driver neo4j.DriverWithContext
	uri    string
}

// GraphNode represents a node in the dependency graph
type GraphNode struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"` // "service", "module", "api", "repository"
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// GraphEdge represents a relationship between nodes
type GraphEdge struct {
	Source string                 `json:"source"`
	Target string                 `json:"target"`
	Type   string                 `json:"type"` // "DEPENDS_ON", "CALLS", "IMPORTS"
	Properties map[string]interface{} `json:"properties,omitempty"`
}

// DependencyGraphResult represents the complete graph structure
type DependencyGraphResult struct {
	Nodes []GraphNode `json:"nodes"`
	Edges []GraphEdge `json:"edges"`
}

// NewNeo4jClient creates a new Neo4j client with connection pooling
func NewNeo4jClient(uri, username, password string) (*Neo4jClient, error) {
	// Configure driver with connection pooling
	driver, err := neo4j.NewDriverWithContext(
		uri,
		neo4j.BasicAuth(username, password, ""),
		func(config *neo4j.Config) {
			config.MaxConnectionPoolSize = 50
			config.MaxConnectionLifetime = 1 * time.Hour
			config.ConnectionAcquisitionTimeout = 2 * time.Minute
		},
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create Neo4j driver: %w", err)
	}

	client := &Neo4jClient{
		driver: driver,
		uri:    uri,
	}

	// Verify connectivity
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := driver.VerifyConnectivity(ctx); err != nil {
		driver.Close(ctx)
		return nil, fmt.Errorf("failed to verify Neo4j connectivity: %w", err)
	}

	log.Printf("[Neo4j] Connected to Neo4j at %s", uri)
	return client, nil
}

// Close closes the Neo4j driver and releases all connections
func (c *Neo4jClient) Close(ctx context.Context) error {
	if c.driver != nil {
		log.Printf("[Neo4j] Closing Neo4j connection")
		return c.driver.Close(ctx)
	}
	return nil
}

// StoreNode stores a node in Neo4j with retry logic
func (c *Neo4jClient) StoreNode(ctx context.Context, repoID string, node GraphNode) error {
	return c.executeWithRetry(ctx, func(ctx context.Context) error {
		session := c.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
		defer session.Close(ctx)

		// Create node with properties
		query := `
			MERGE (n {id: $id, repo_id: $repo_id})
			SET n.type = $type
			SET n += $properties
			RETURN n
		`

		params := map[string]interface{}{
			"id":         node.ID,
			"repo_id":    repoID,
			"type":       node.Type,
			"properties": node.Properties,
		}

		_, err := session.Run(ctx, query, params)
		if err != nil {
			return fmt.Errorf("failed to store node %s: %w", node.ID, err)
		}

		log.Printf("[Neo4j] Stored node: %s (type: %s) for repo: %s", node.ID, node.Type, repoID)
		return nil
	})
}

// StoreEdge stores a relationship between two nodes with retry logic
func (c *Neo4jClient) StoreEdge(ctx context.Context, repoID string, edge GraphEdge) error {
	return c.executeWithRetry(ctx, func(ctx context.Context) error {
		session := c.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
		defer session.Close(ctx)

		// Create relationship with properties
		query := fmt.Sprintf(`
			MATCH (source {id: $source, repo_id: $repo_id})
			MATCH (target {id: $target, repo_id: $repo_id})
			MERGE (source)-[r:%s]->(target)
			SET r += $properties
			RETURN r
		`, edge.Type)

		params := map[string]interface{}{
			"source":     edge.Source,
			"target":     edge.Target,
			"repo_id":    repoID,
			"properties": edge.Properties,
		}

		_, err := session.Run(ctx, query, params)
		if err != nil {
			return fmt.Errorf("failed to store edge %s->%s: %w", edge.Source, edge.Target, err)
		}

		log.Printf("[Neo4j] Stored edge: %s -[%s]-> %s for repo: %s", edge.Source, edge.Type, edge.Target, repoID)
		return nil
	})
}

// GetDependencyGraph retrieves the complete dependency graph for a repository
func (c *Neo4jClient) GetDependencyGraph(ctx context.Context, repoID string) (*DependencyGraphResult, error) {
	var result *DependencyGraphResult
	
	err := c.executeWithRetry(ctx, func(ctx context.Context) error {
		session := c.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeRead})
		defer session.Close(ctx)

		// Query all nodes for the repository
		nodesQuery := `
			MATCH (n {repo_id: $repo_id})
			RETURN n.id as id, n.type as type, properties(n) as properties
		`

		nodesResult, err := session.Run(ctx, nodesQuery, map[string]interface{}{"repo_id": repoID})
		if err != nil {
			return fmt.Errorf("failed to query nodes: %w", err)
		}

		nodes := []GraphNode{}
		for nodesResult.Next(ctx) {
			record := nodesResult.Record()
			
			id, _ := record.Get("id")
			nodeType, _ := record.Get("type")
			props, _ := record.Get("properties")
			
			properties := make(map[string]interface{})
			if propsMap, ok := props.(map[string]interface{}); ok {
				// Filter out internal properties
				for k, v := range propsMap {
					if k != "id" && k != "repo_id" && k != "type" {
						properties[k] = v
					}
				}
			}

			node := GraphNode{
				ID:         fmt.Sprintf("%v", id),
				Type:       fmt.Sprintf("%v", nodeType),
				Properties: properties,
			}
			nodes = append(nodes, node)
		}

		if err := nodesResult.Err(); err != nil {
			return fmt.Errorf("error iterating nodes: %w", err)
		}

		// Query all relationships for the repository
		edgesQuery := `
			MATCH (source {repo_id: $repo_id})-[r]->(target {repo_id: $repo_id})
			RETURN source.id as source, target.id as target, type(r) as type, properties(r) as properties
		`

		edgesResult, err := session.Run(ctx, edgesQuery, map[string]interface{}{"repo_id": repoID})
		if err != nil {
			return fmt.Errorf("failed to query edges: %w", err)
		}

		edges := []GraphEdge{}
		for edgesResult.Next(ctx) {
			record := edgesResult.Record()
			
			source, _ := record.Get("source")
			target, _ := record.Get("target")
			edgeType, _ := record.Get("type")
			props, _ := record.Get("properties")
			
			properties := make(map[string]interface{})
			if propsMap, ok := props.(map[string]interface{}); ok {
				properties = propsMap
			}

			edge := GraphEdge{
				Source:     fmt.Sprintf("%v", source),
				Target:     fmt.Sprintf("%v", target),
				Type:       fmt.Sprintf("%v", edgeType),
				Properties: properties,
			}
			edges = append(edges, edge)
		}

		if err := edgesResult.Err(); err != nil {
			return fmt.Errorf("error iterating edges: %w", err)
		}

		result = &DependencyGraphResult{
			Nodes: nodes,
			Edges: edges,
		}

		log.Printf("[Neo4j] Retrieved dependency graph for repo %s: %d nodes, %d edges", repoID, len(nodes), len(edges))
		return nil
	})

	if err != nil {
		return nil, err
	}

	return result, nil
}

// QueryServiceDependencies retrieves all services that depend on a specific service
func (c *Neo4jClient) QueryServiceDependencies(ctx context.Context, repoID, serviceID string) ([]string, error) {
	var dependencies []string
	
	err := c.executeWithRetry(ctx, func(ctx context.Context) error {
		session := c.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeRead})
		defer session.Close(ctx)

		query := `
			MATCH (service {id: $service_id, repo_id: $repo_id, type: 'service'})<-[:DEPENDS_ON]-(dependent)
			RETURN dependent.id as id
		`

		params := map[string]interface{}{
			"service_id": serviceID,
			"repo_id":    repoID,
		}

		result, err := session.Run(ctx, query, params)
		if err != nil {
			return fmt.Errorf("failed to query service dependencies: %w", err)
		}

		dependencies = []string{}
		for result.Next(ctx) {
			record := result.Record()
			if id, ok := record.Get("id"); ok {
				dependencies = append(dependencies, fmt.Sprintf("%v", id))
			}
		}

		if err := result.Err(); err != nil {
			return fmt.Errorf("error iterating dependencies: %w", err)
		}

		log.Printf("[Neo4j] Found %d dependencies for service %s in repo %s", len(dependencies), serviceID, repoID)
		return nil
	})

	if err != nil {
		return nil, err
	}

	return dependencies, nil
}

// StoreBulkNodes stores multiple nodes in a single transaction for efficiency
func (c *Neo4jClient) StoreBulkNodes(ctx context.Context, repoID string, nodes []GraphNode) error {
	return c.executeWithRetry(ctx, func(ctx context.Context) error {
		session := c.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
		defer session.Close(ctx)

		_, err := session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (interface{}, error) {
			for _, node := range nodes {
				query := `
					MERGE (n {id: $id, repo_id: $repo_id})
					SET n.type = $type
					SET n += $properties
				`

				params := map[string]interface{}{
					"id":         node.ID,
					"repo_id":    repoID,
					"type":       node.Type,
					"properties": node.Properties,
				}

				if _, err := tx.Run(ctx, query, params); err != nil {
					return nil, fmt.Errorf("failed to store node %s: %w", node.ID, err)
				}
			}
			return nil, nil
		})

		if err != nil {
			return err
		}

		log.Printf("[Neo4j] Stored %d nodes in bulk for repo: %s", len(nodes), repoID)
		return nil
	})
}

// StoreBulkEdges stores multiple edges in a single transaction for efficiency
func (c *Neo4jClient) StoreBulkEdges(ctx context.Context, repoID string, edges []GraphEdge) error {
	return c.executeWithRetry(ctx, func(ctx context.Context) error {
		session := c.driver.NewSession(ctx, neo4j.SessionConfig{AccessMode: neo4j.AccessModeWrite})
		defer session.Close(ctx)

		_, err := session.ExecuteWrite(ctx, func(tx neo4j.ManagedTransaction) (interface{}, error) {
			for _, edge := range edges {
				query := fmt.Sprintf(`
					MATCH (source {id: $source, repo_id: $repo_id})
					MATCH (target {id: $target, repo_id: $repo_id})
					MERGE (source)-[r:%s]->(target)
					SET r += $properties
				`, edge.Type)

				params := map[string]interface{}{
					"source":     edge.Source,
					"target":     edge.Target,
					"repo_id":    repoID,
					"properties": edge.Properties,
				}

				if _, err := tx.Run(ctx, query, params); err != nil {
					return nil, fmt.Errorf("failed to store edge %s->%s: %w", edge.Source, edge.Target, err)
				}
			}
			return nil, nil
		})

		if err != nil {
			return err
		}

		log.Printf("[Neo4j] Stored %d edges in bulk for repo: %s", len(edges), repoID)
		return nil
	})
}

// executeWithRetry executes a function with exponential backoff retry logic
func (c *Neo4jClient) executeWithRetry(ctx context.Context, fn func(context.Context) error) error {
	maxRetries := 3
	baseDelay := 100 * time.Millisecond

	for attempt := 0; attempt < maxRetries; attempt++ {
		err := fn(ctx)
		if err == nil {
			return nil
		}

		// Check if error is retryable (transient errors)
		if !isRetryableError(err) {
			return err
		}

		if attempt < maxRetries-1 {
			delay := baseDelay * time.Duration(1<<uint(attempt)) // Exponential backoff
			log.Printf("[Neo4j] Retrying after error (attempt %d/%d): %v", attempt+1, maxRetries, err)
			
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(delay):
				// Continue to next retry
			}
		} else {
			return fmt.Errorf("max retries exceeded: %w", err)
		}
	}

	return fmt.Errorf("unexpected retry loop exit")
}

// isRetryableError determines if an error is transient and should be retried
func isRetryableError(err error) bool {
	if err == nil {
		return false
	}

	// Check for Neo4j transient errors
	if neo4j.IsNeo4jError(err) {
		neo4jErr := err.(*neo4j.Neo4jError)
		// Retry on transient errors (connection issues, deadlocks, etc.)
		return neo4jErr.Code == "Neo.TransientError.Transaction.DeadlockDetected" ||
			neo4jErr.Code == "Neo.TransientError.Network.CommunicationError" ||
			neo4jErr.Code == "Neo.TransientError.General.DatabaseUnavailable"
	}

	return false
}

// Made with Bob