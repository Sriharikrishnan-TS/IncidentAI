package database

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"time"

	_ "github.com/lib/pq"
)

// SupabaseClient manages connection and queries to Supabase Cloud Postgres
type SupabaseClient struct {
	db *sql.DB
}

// NewSupabaseClient creates connection pool to Supabase Postgres database
func NewSupabaseClient(databaseURL string) (*SupabaseClient, error) {
	if databaseURL == "" {
		return nil, fmt.Errorf("DATABASE_URL is empty")
	}

	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open postgres database: %w", err)
	}

	// Configure connection pooling
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(15 * time.Minute)

	// Verify connectivity
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to ping Supabase Postgres database: %w", err)
	}

	log.Printf("[Supabase] Connected to Supabase Cloud PostgreSQL database successfully")

	client := &SupabaseClient{db: db}

	// Auto-migrate tables
	if err := client.AutoMigrate(ctx); err != nil {
		log.Printf("[Supabase] Warning: Auto-migration failed: %v", err)
	}

	return client, nil
}

// Close closes database connection pool
func (c *SupabaseClient) Close() error {
	if c.db != nil {
		log.Printf("[Supabase] Closing Supabase Postgres database pool")
		return c.db.Close()
	}
	return nil
}

// AutoMigrate creates required IncidentOS schema tables in Supabase Postgres
func (c *SupabaseClient) AutoMigrate(ctx context.Context) error {
	schema := `
	CREATE EXTENSION IF NOT EXISTS vector;

	CREATE TABLE IF NOT EXISTS repositories (
		id VARCHAR(255) PRIMARY KEY,
		name VARCHAR(255) NOT NULL,
		repo_path TEXT NOT NULL,
		status VARCHAR(50) DEFAULT 'uploaded',
		created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS incidents (
		id VARCHAR(255) PRIMARY KEY,
		repo_id VARCHAR(255) NOT NULL,
		type VARCHAR(100) NOT NULL,
		severity VARCHAR(50) NOT NULL,
		component TEXT NOT NULL,
		title TEXT NOT NULL,
		description TEXT NOT NULL,
		recommendations JSONB DEFAULT '[]',
		metrics JSONB DEFAULT '{}',
		created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS dependency_graphs (
		repo_id VARCHAR(255) PRIMARY KEY,
		nodes JSONB DEFAULT '[]',
		edges JSONB DEFAULT '[]',
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS fragility_scores (
		repo_id VARCHAR(255) PRIMARY KEY,
		scores JSONB DEFAULT '{}',
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS mentor_contexts (
		repo_id VARCHAR(255) PRIMARY KEY,
		context_data JSONB DEFAULT '{}',
		updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
	);

	CREATE TABLE IF NOT EXISTS code_embeddings (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		repo_id VARCHAR(255) NOT NULL,
		filepath TEXT NOT NULL,
		content TEXT NOT NULL,
		embedding VECTOR(384),
		created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
	);
	`

	_, err := c.db.ExecContext(ctx, schema)
	if err != nil {
		return fmt.Errorf("failed to execute schema migration: %w", err)
	}

	log.Printf("[Supabase] Schema tables (repositories, incidents, dependency_graphs, fragility_scores, mentor_contexts) ready")
	return nil
}

// SaveDependencyGraph persists node and edge JSON in Supabase
func (c *SupabaseClient) SaveDependencyGraph(ctx context.Context, repoID string, nodesJSON, edgesJSON string) error {
	query := `
		INSERT INTO dependency_graphs (repo_id, nodes, edges, updated_at)
		VALUES ($1, $2::jsonb, $3::jsonb, CURRENT_TIMESTAMP)
		ON CONFLICT (repo_id) DO UPDATE
		SET nodes = EXCLUDED.nodes, edges = EXCLUDED.edges, updated_at = CURRENT_TIMESTAMP;
	`
	_, err := c.db.ExecContext(ctx, query, repoID, nodesJSON, edgesJSON)
	return err
}

// SaveIncidents persists incident records in Supabase
func (c *SupabaseClient) SaveIncident(ctx context.Context, repoID, incidentID, incType, severity, component, title, description, recsJSON, metricsJSON string) error {
	query := `
		INSERT INTO incidents (id, repo_id, type, severity, component, title, description, recommendations, metrics, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, CURRENT_TIMESTAMP)
		ON CONFLICT (id) DO UPDATE
		SET type = EXCLUDED.type, severity = EXCLUDED.severity, component = EXCLUDED.component,
		    title = EXCLUDED.title, description = EXCLUDED.description, recommendations = EXCLUDED.recommendations,
			metrics = EXCLUDED.metrics;
	`
	_, err := c.db.ExecContext(ctx, query, incidentID, repoID, incType, severity, component, title, description, recsJSON, metricsJSON)
	return err
}
