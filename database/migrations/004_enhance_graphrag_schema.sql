-- Migration: Enhance existing knowledge schema for full GraphRAG support
-- Version: 004
-- Date: 2025-08-19
-- Description: Adds missing columns and tables for complete GraphRAG functionality

BEGIN;

-- =============================================================================
-- ENHANCE EXISTING TABLES
-- =============================================================================

-- Add missing columns to knowledge_source table
ALTER TABLE knowledge_source 
    ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255),
    ADD COLUMN IF NOT EXISTS file_size BIGINT,
    ADD COLUMN IF NOT EXISTS processing_error TEXT,
    ADD COLUMN IF NOT EXISTS processing_metadata JSON DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS content_preview TEXT,
    ADD COLUMN IF NOT EXISTS extracted_text TEXT,
    ADD COLUMN IF NOT EXISTS language VARCHAR(10),
    ADD COLUMN IF NOT EXISTS content_length INTEGER,
    ADD COLUMN IF NOT EXISTS entities_extracted INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS relationships_extracted INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS chunks_created INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS embeddings_generated INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS collection_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS custom_metadata JSON DEFAULT '{}';

-- Update knowledge_entity to match GraphRAG schema
-- First check if the table needs restructuring
DO $$
BEGIN
    -- Add missing columns to knowledge_entity
    ALTER TABLE knowledge_entity 
        ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50) DEFAULT 'concept',
        ADD COLUMN IF NOT EXISTS canonical_name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS description TEXT,
        ADD COLUMN IF NOT EXISTS aliases JSON DEFAULT '[]',
        ADD COLUMN IF NOT EXISTS properties JSON DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS source_documents JSON DEFAULT '[]',
        ADD COLUMN IF NOT EXISTS mention_count INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS first_mentioned_at BIGINT,
        ADD COLUMN IF NOT EXISTS last_mentioned_at BIGINT,
        ADD COLUMN IF NOT EXISTS degree_centrality DECIMAL(10,8),
        ADD COLUMN IF NOT EXISTS betweenness_centrality DECIMAL(10,8),
        ADD COLUMN IF NOT EXISTS pagerank_score DECIMAL(10,8),
        ADD COLUMN IF NOT EXISTS embedding_vector JSON,
        ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(255),
        ADD COLUMN IF NOT EXISTS extraction_confidence DECIMAL(5,4) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS type_confidence DECIMAL(5,4) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000;
        
    -- Update canonical_name for existing entities
    UPDATE knowledge_entity 
    SET canonical_name = LOWER(TRIM(name))
    WHERE canonical_name IS NULL;
EXCEPTION
    WHEN duplicate_column THEN
        -- Column already exists, continue
        NULL;
END$$;

-- Update knowledge_relationship to match GraphRAG schema
DO $$
BEGIN
    ALTER TABLE knowledge_relationship 
        ADD COLUMN IF NOT EXISTS relationship_type VARCHAR(50) DEFAULT 'related_to',
        ADD COLUMN IF NOT EXISTS description TEXT,
        ADD COLUMN IF NOT EXISTS weight DECIMAL(5,4) DEFAULT 1.0,
        ADD COLUMN IF NOT EXISTS confidence DECIMAL(5,4) DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS properties JSON DEFAULT '{}',
        ADD COLUMN IF NOT EXISTS source_documents JSON DEFAULT '[]',
        ADD COLUMN IF NOT EXISTS source_chunks JSON DEFAULT '[]',
        ADD COLUMN IF NOT EXISTS evidence_text JSON DEFAULT '[]',
        ADD COLUMN IF NOT EXISTS temporal_context VARCHAR(255),
        ADD COLUMN IF NOT EXISTS start_date VARCHAR(20),
        ADD COLUMN IF NOT EXISTS end_date VARCHAR(20),
        ADD COLUMN IF NOT EXISTS updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000;
EXCEPTION
    WHEN duplicate_column THEN
        NULL;
END$$;

-- =============================================================================
-- CREATE NEW TABLES
-- =============================================================================

-- Knowledge collections for organizing related documents
CREATE TABLE IF NOT EXISTS knowledge_collection (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id VARCHAR(255) NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    source_count INTEGER DEFAULT 0,
    total_entities INTEGER DEFAULT 0,
    total_relationships INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    processing_status VARCHAR(20) DEFAULT 'pending',
    last_updated BIGINT,
    chunking_strategy VARCHAR(50) DEFAULT 'semantic',
    embedding_model VARCHAR(255) DEFAULT 'sentence-transformers/all-mpnet-base-v2',
    chunk_size INTEGER DEFAULT 512,
    chunk_overlap INTEGER DEFAULT 50,
    tags JSON DEFAULT '[]',
    custom_settings JSON DEFAULT '{}',
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    CONSTRAINT fk_knowledge_collection_user 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- Document chunks for vector embeddings
CREATE TABLE IF NOT EXISTS document_chunk (
    id VARCHAR(255) PRIMARY KEY,
    source_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    start_position INTEGER DEFAULT 0,
    end_position INTEGER DEFAULT 0,
    token_count INTEGER,
    character_count INTEGER NOT NULL,
    embedding_model VARCHAR(255),
    embedding_vector JSON,
    embedding_dimension INTEGER,
    parent_chunk_id VARCHAR(255),
    child_chunk_ids JSON DEFAULT '[]',
    section_title VARCHAR(255),
    page_number INTEGER,
    entities_mentioned JSON DEFAULT '[]',
    concepts_identified JSON DEFAULT '[]',
    relevance_score DECIMAL(5,4),
    coherence_score DECIMAL(5,4),
    completeness_score DECIMAL(5,4),
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    CONSTRAINT fk_document_chunk_source 
        FOREIGN KEY (source_id) REFERENCES knowledge_source(id) ON DELETE CASCADE,
    CONSTRAINT fk_document_chunk_parent 
        FOREIGN KEY (parent_chunk_id) REFERENCES document_chunk(id) ON DELETE SET NULL
);

-- Knowledge retrieval queries
CREATE TABLE IF NOT EXISTS knowledge_query (
    id VARCHAR(255) PRIMARY KEY,
    query_text TEXT NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    assistant_id VARCHAR(255),
    max_results INTEGER DEFAULT 10,
    similarity_threshold DECIMAL(5,4) DEFAULT 0.7,
    use_graph_expansion BOOLEAN DEFAULT TRUE,
    graph_depth INTEGER DEFAULT 2,
    include_entities BOOLEAN DEFAULT TRUE,
    include_relationships BOOLEAN DEFAULT TRUE,
    source_types JSON DEFAULT '[]',
    entity_types JSON DEFAULT '[]',
    collection_ids JSON DEFAULT '[]',
    date_range JSON,
    results_found INTEGER DEFAULT 0,
    processing_time_ms DECIMAL(10,3),
    retrieval_strategy VARCHAR(100),
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    CONSTRAINT fk_knowledge_query_user 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

-- Knowledge retrieval results
CREATE TABLE IF NOT EXISTS knowledge_retrieval_result (
    id VARCHAR(255) PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    similarity_score DECIMAL(5,4) DEFAULT 0.0,
    relevance_score DECIMAL(5,4) DEFAULT 0.0,
    graph_score DECIMAL(5,4),
    combined_score DECIMAL(5,4) DEFAULT 0.0,
    source_document_id INTEGER,
    source_document_name VARCHAR(255),
    chunk_position INTEGER,
    related_entities JSON DEFAULT '[]',
    related_relationships JSON DEFAULT '[]',
    metadata JSON DEFAULT '{}',
    CONSTRAINT fk_knowledge_retrieval_result_query 
        FOREIGN KEY (query_id) REFERENCES knowledge_query(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_retrieval_result_document 
        FOREIGN KEY (source_document_id) REFERENCES knowledge_source(id) ON DELETE SET NULL
);

-- Link assistants to knowledge collections
CREATE TABLE IF NOT EXISTS assistant_knowledge_link (
    assistant_id VARCHAR(255) NOT NULL,
    collection_id VARCHAR(255) NOT NULL,
    link_type VARCHAR(20) DEFAULT 'primary',
    priority INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    retrieval_config JSON DEFAULT '{}',
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    PRIMARY KEY (assistant_id, collection_id),
    CONSTRAINT fk_assistant_knowledge_link_assistant 
        FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE,
    CONSTRAINT fk_assistant_knowledge_link_collection 
        FOREIGN KEY (collection_id) REFERENCES knowledge_collection(id) ON DELETE CASCADE
);

-- =============================================================================
-- ADD FOREIGN KEY CONSTRAINTS FOR ENHANCED TABLES
-- =============================================================================

-- Add foreign key for collection_id in knowledge_source
DO $$
BEGIN
    ALTER TABLE knowledge_source 
    ADD CONSTRAINT fk_knowledge_source_collection 
        FOREIGN KEY (collection_id) REFERENCES knowledge_collection(id) ON DELETE SET NULL;
EXCEPTION
    WHEN duplicate_object THEN
        NULL;
END$$;

-- =============================================================================
-- CREATE ADDITIONAL INDEXES
-- =============================================================================

-- Knowledge collection indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_collection_user ON knowledge_collection(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_collection_public ON knowledge_collection(is_public);
CREATE INDEX IF NOT EXISTS idx_knowledge_collection_status ON knowledge_collection(processing_status);

-- Enhanced knowledge source indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_source_collection ON knowledge_source(collection_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_hash ON knowledge_source(content_hash);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_created ON knowledge_source(created_at);

-- Document chunk indexes
CREATE INDEX IF NOT EXISTS idx_document_chunk_source ON document_chunk(source_id);
CREATE INDEX IF NOT EXISTS idx_document_chunk_parent ON document_chunk(parent_chunk_id);
CREATE INDEX IF NOT EXISTS idx_document_chunk_model ON document_chunk(embedding_model);
CREATE INDEX IF NOT EXISTS idx_document_chunk_dimension ON document_chunk(embedding_dimension);
CREATE INDEX IF NOT EXISTS idx_document_chunk_relevance ON document_chunk(relevance_score);

-- Enhanced entity indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_canonical ON knowledge_entity(canonical_name);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_type ON knowledge_entity(entity_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_mention_count ON knowledge_entity(mention_count);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_pagerank ON knowledge_entity(pagerank_score);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_centrality ON knowledge_entity(degree_centrality);

-- Enhanced relationship indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_type ON knowledge_relationship(relationship_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_weight ON knowledge_relationship(weight);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_confidence ON knowledge_relationship(confidence);

-- Query tracking indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_query_user ON knowledge_query(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_query_assistant ON knowledge_query(assistant_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_query_created ON knowledge_query(created_at);

-- Retrieval result indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_result_query ON knowledge_retrieval_result(query_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_result_source ON knowledge_retrieval_result(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_result_score ON knowledge_retrieval_result(combined_score);

-- Assistant knowledge link indexes
CREATE INDEX IF NOT EXISTS idx_assistant_knowledge_link_assistant ON assistant_knowledge_link(assistant_id);
CREATE INDEX IF NOT EXISTS idx_assistant_knowledge_link_collection ON assistant_knowledge_link(collection_id);
CREATE INDEX IF NOT EXISTS idx_assistant_knowledge_link_enabled ON assistant_knowledge_link(enabled);

-- =============================================================================
-- CREATE VIEWS
-- =============================================================================

-- Knowledge collection overview
CREATE OR REPLACE VIEW knowledge_collection_overview AS
SELECT 
    kc.id,
    kc.name,
    kc.description,
    kc.user_id,
    u.name as owner_name,
    kc.is_public,
    kc.processing_status,
    kc.source_count,
    kc.total_entities,
    kc.total_relationships,
    kc.total_chunks,
    kc.embedding_model,
    kc.created_at,
    kc.updated_at,
    COUNT(DISTINCT akl.assistant_id) as linked_assistants
FROM knowledge_collection kc
JOIN "user" u ON kc.user_id = u.id
LEFT JOIN assistant_knowledge_link akl ON kc.id = akl.collection_id AND akl.enabled = TRUE
GROUP BY kc.id, kc.name, kc.description, kc.user_id, u.name, kc.is_public, 
         kc.processing_status, kc.source_count, kc.total_entities, kc.total_relationships,
         kc.total_chunks, kc.embedding_model, kc.created_at, kc.updated_at;

-- Document processing status
CREATE OR REPLACE VIEW document_processing_status AS
SELECT 
    ks.id,
    ks.name,
    ks.source_type,
    ks.processing_status,
    ks.content_length,
    ks.entities_extracted,
    ks.relationships_extracted,
    ks.chunks_created,
    ks.embeddings_generated,
    ks.last_processed_at,
    ks.processing_error,
    kc.name as collection_name,
    u.name as owner_name
FROM knowledge_source ks
JOIN "user" u ON ks.user_id = u.id
LEFT JOIN knowledge_collection kc ON ks.collection_id = kc.id;

-- =============================================================================
-- CREATE FUNCTIONS
-- =============================================================================

-- Function to update collection statistics
CREATE OR REPLACE FUNCTION update_knowledge_collection_stats(
    p_collection_id VARCHAR(255)
) RETURNS VOID AS $$
BEGIN
    UPDATE knowledge_collection SET
        source_count = (
            SELECT COUNT(*) FROM knowledge_source 
            WHERE collection_id = p_collection_id
        ),
        total_chunks = (
            SELECT COUNT(*)
            FROM document_chunk dc
            JOIN knowledge_source ks ON dc.source_id = ks.id
            WHERE ks.collection_id = p_collection_id
        ),
        last_updated = EXTRACT(EPOCH FROM NOW()) * 1000,
        updated_at = EXTRACT(EPOCH FROM NOW()) * 1000
    WHERE id = p_collection_id;
END;
$$ LANGUAGE plpgsql;

-- Function to record knowledge query
CREATE OR REPLACE FUNCTION record_knowledge_query(
    p_query_text TEXT,
    p_user_id VARCHAR(255),
    p_assistant_id VARCHAR(255) DEFAULT NULL,
    p_results_found INTEGER DEFAULT 0,
    p_processing_time_ms DECIMAL(10,3) DEFAULT NULL
) RETURNS VARCHAR(255) AS $$
DECLARE
    v_query_id VARCHAR(255);
BEGIN
    v_query_id := encode(gen_random_bytes(16), 'hex');
    
    INSERT INTO knowledge_query (
        id, query_text, user_id, assistant_id, 
        results_found, processing_time_ms
    ) VALUES (
        v_query_id, p_query_text, p_user_id, p_assistant_id,
        p_results_found, p_processing_time_ms
    );
    
    RETURN v_query_id;
END;
$$ LANGUAGE plpgsql;

COMMIT;