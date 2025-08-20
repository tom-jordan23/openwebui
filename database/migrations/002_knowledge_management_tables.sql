-- Migration: Knowledge Management Tables
-- Version: 002
-- Date: 2025-08-19
-- Description: Adds tables for GraphRAG and knowledge management

BEGIN;

-- =============================================================================
-- KNOWLEDGE MANAGEMENT (GraphRAG Integration)
-- =============================================================================

-- Knowledge sources/documents
CREATE TABLE IF NOT EXISTS knowledge_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    source_path TEXT NOT NULL,
    content_hash VARCHAR(255),
    last_processed_at BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    user_id VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    metadata JSON DEFAULT '{}',
    CONSTRAINT fk_knowledge_source_user FOREIGN KEY (user_id) REFERENCES "user"(id)
);

-- Knowledge graph entities (for GraphRAG)
-- Note: Using TEXT for embedding_vector until pgvector is available
CREATE TABLE IF NOT EXISTS knowledge_entity (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    description TEXT,
    properties JSON DEFAULT '{}',
    embedding_vector TEXT, -- Serialized vector, will upgrade to VECTOR(384) when pgvector available
    source_id INTEGER,
    created_at BIGINT NOT NULL,
    confidence_score DECIMAL(4,3) DEFAULT 1.0,
    CONSTRAINT fk_knowledge_entity_source FOREIGN KEY (source_id) REFERENCES knowledge_source(id) ON DELETE CASCADE
);

-- Knowledge relationships (for GraphRAG)
CREATE TABLE IF NOT EXISTS knowledge_relationship (
    id SERIAL PRIMARY KEY,
    from_entity_id INTEGER NOT NULL,
    to_entity_id INTEGER NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    strength DECIMAL(4,3) DEFAULT 1.0,
    properties JSON DEFAULT '{}',
    source_id INTEGER,
    created_at BIGINT NOT NULL,
    CONSTRAINT fk_knowledge_relationship_from FOREIGN KEY (from_entity_id) REFERENCES knowledge_entity(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_relationship_to FOREIGN KEY (to_entity_id) REFERENCES knowledge_entity(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_relationship_source FOREIGN KEY (source_id) REFERENCES knowledge_source(id) ON DELETE SET NULL
);

COMMIT;