CREATE DATABASE IF NOT EXISTS engram;
USE engram;

-- Application migrations own table creation. This production-only index assumes
-- LIVE_EMBEDDING_DIMENSION=1024 for Amazon Titan Text Embeddings V2; keep
-- application configuration and existing stored vectors aligned.
SET CLUSTER SETTING feature.vector_index.enabled = true;

CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx
ON memories (organization_id, project_id, embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS memories_project_status_type_idx
ON memories (project_id, status, memory_type, updated_at DESC);

CREATE INDEX IF NOT EXISTS retrieval_runs_project_created_idx
ON retrieval_runs (project_id, created_at DESC);

-- Create a separate read-only SQL user for MCP and grant only the schemas/views
-- required for inspection. Do not reuse the application service account.
