-- Migration: GraphRAG Knowledge Management System
-- Version: 003
-- Date: 2025-08-19
-- Description: Creates comprehensive knowledge management schema for GraphRAG integration

BEGIN;

-- =============================================================================
-- KNOWLEDGE COLLECTIONS
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

-- Enhanced knowledge sources with GraphRAG capabilities
CREATE TABLE IF NOT EXISTS knowledge_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(20) NOT NULL DEFAULT 'text',
    source_path TEXT NOT NULL,
    original_filename VARCHAR(255),
    file_size BIGINT,
    content_hash VARCHAR(64),
    
    -- Processing information
    processing_status VARCHAR(20) DEFAULT 'pending',
    last_processed_at BIGINT,
    processing_error TEXT,
    processing_metadata JSON DEFAULT '{}',
    
    -- Content analysis
    content_preview TEXT,
    extracted_text TEXT,
    language VARCHAR(10),
    content_length INTEGER,
    
    -- Graph extraction results
    entities_extracted INTEGER DEFAULT 0,
    relationships_extracted INTEGER DEFAULT 0,
    chunks_created INTEGER DEFAULT 0,
    embeddings_generated INTEGER DEFAULT 0,
    
    -- Relationships
    user_id VARCHAR(255) NOT NULL,
    collection_id VARCHAR(255),
    
    -- Metadata
    tags JSON DEFAULT '[]',
    custom_metadata JSON DEFAULT '{}',
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    
    CONSTRAINT fk_knowledge_source_user 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_source_collection 
        FOREIGN KEY (collection_id) REFERENCES knowledge_collection(id) ON DELETE SET NULL
);

-- Document chunks for vector embeddings
CREATE TABLE IF NOT EXISTS document_chunk (
    id VARCHAR(255) PRIMARY KEY,
    source_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    
    -- Chunking metadata
    start_position INTEGER DEFAULT 0,
    end_position INTEGER DEFAULT 0,
    token_count INTEGER,
    character_count INTEGER NOT NULL,
    
    -- Vector embedding
    embedding_model VARCHAR(255),
    embedding_vector JSON, -- Store as JSON array for PostgreSQL
    embedding_dimension INTEGER,
    
    -- Context information
    parent_chunk_id VARCHAR(255),
    child_chunk_ids JSON DEFAULT '[]',
    section_title VARCHAR(255),
    page_number INTEGER,
    
    -- Graph relationships
    entities_mentioned JSON DEFAULT '[]',
    concepts_identified JSON DEFAULT '[]',
    
    -- Quality metrics
    relevance_score DECIMAL(5,4),
    coherence_score DECIMAL(5,4),
    completeness_score DECIMAL(5,4),
    
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    
    CONSTRAINT fk_document_chunk_source 
        FOREIGN KEY (source_id) REFERENCES knowledge_source(id) ON DELETE CASCADE,
    CONSTRAINT fk_document_chunk_parent 
        FOREIGN KEY (parent_chunk_id) REFERENCES document_chunk(id) ON DELETE SET NULL
);

-- =============================================================================
-- KNOWLEDGE GRAPH ENTITIES AND RELATIONSHIPS
-- =============================================================================

-- Knowledge entities extracted from documents
CREATE TABLE IF NOT EXISTS knowledge_entity (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL DEFAULT 'concept',
    canonical_name VARCHAR(255) NOT NULL,
    
    -- Entity properties
    description TEXT,
    aliases JSON DEFAULT '[]',
    properties JSON DEFAULT '{}',
    
    -- Source tracking
    source_documents JSON DEFAULT '[]',
    mention_count INTEGER DEFAULT 0,
    first_mentioned_at BIGINT,
    last_mentioned_at BIGINT,
    
    -- Graph metrics
    degree_centrality DECIMAL(10,8),
    betweenness_centrality DECIMAL(10,8),
    pagerank_score DECIMAL(10,8),
    
    -- Vector representation
    embedding_vector JSON,
    embedding_model VARCHAR(255),
    
    -- Confidence scores
    extraction_confidence DECIMAL(5,4) DEFAULT 0.0,
    type_confidence DECIMAL(5,4) DEFAULT 0.0,
    
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000
);

-- Relationships between entities
CREATE TABLE IF NOT EXISTS knowledge_relationship (
    id VARCHAR(255) PRIMARY KEY,
    source_entity_id VARCHAR(255) NOT NULL,
    target_entity_id VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL DEFAULT 'related_to',
    
    -- Relationship properties
    description TEXT,
    weight DECIMAL(5,4) DEFAULT 1.0,
    confidence DECIMAL(5,4) DEFAULT 0.0,
    properties JSON DEFAULT '{}',
    
    -- Source tracking
    source_documents JSON DEFAULT '[]',
    source_chunks JSON DEFAULT '[]',
    evidence_text JSON DEFAULT '[]',
    
    -- Temporal information
    temporal_context VARCHAR(255),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    
    CONSTRAINT fk_knowledge_relationship_source 
        FOREIGN KEY (source_entity_id) REFERENCES knowledge_entity(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_relationship_target 
        FOREIGN KEY (target_entity_id) REFERENCES knowledge_entity(id) ON DELETE CASCADE,
    CONSTRAINT uk_knowledge_relationship 
        UNIQUE(source_entity_id, target_entity_id, relationship_type)
);

-- =============================================================================
-- RETRIEVAL AND QUERY TRACKING
-- =============================================================================

-- Knowledge retrieval queries
CREATE TABLE IF NOT EXISTS knowledge_query (
    id VARCHAR(255) PRIMARY KEY,
    query_text TEXT NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    assistant_id VARCHAR(255),
    
    -- Query configuration
    max_results INTEGER DEFAULT 10,
    similarity_threshold DECIMAL(5,4) DEFAULT 0.7,
    use_graph_expansion BOOLEAN DEFAULT TRUE,
    graph_depth INTEGER DEFAULT 2,
    include_entities BOOLEAN DEFAULT TRUE,
    include_relationships BOOLEAN DEFAULT TRUE,
    
    -- Filtering
    source_types JSON DEFAULT '[]',
    entity_types JSON DEFAULT '[]',
    collection_ids JSON DEFAULT '[]',
    date_range JSON,
    
    -- Results
    results_found INTEGER DEFAULT 0,
    processing_time_ms DECIMAL(10,3),
    retrieval_strategy VARCHAR(100),
    
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    
    CONSTRAINT fk_knowledge_query_user 
        FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_query_assistant 
        FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE SET NULL
);

-- Knowledge retrieval results
CREATE TABLE IF NOT EXISTS knowledge_retrieval_result (
    id VARCHAR(255) PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL,
    
    -- Source information
    source_type VARCHAR(20) NOT NULL, -- chunk, entity, relationship
    source_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    
    -- Scoring
    similarity_score DECIMAL(5,4) DEFAULT 0.0,
    relevance_score DECIMAL(5,4) DEFAULT 0.0,
    graph_score DECIMAL(5,4),
    combined_score DECIMAL(5,4) DEFAULT 0.0,
    
    -- Context
    source_document_id INTEGER,
    source_document_name VARCHAR(255),
    chunk_position INTEGER,
    
    -- Related entities
    related_entities JSON DEFAULT '[]',
    related_relationships JSON DEFAULT '[]',
    
    -- Metadata
    metadata JSON DEFAULT '{}',
    
    CONSTRAINT fk_knowledge_retrieval_result_query 
        FOREIGN KEY (query_id) REFERENCES knowledge_query(id) ON DELETE CASCADE,
    CONSTRAINT fk_knowledge_retrieval_result_document 
        FOREIGN KEY (source_document_id) REFERENCES knowledge_source(id) ON DELETE SET NULL
);

-- =============================================================================
-- ASSISTANT KNOWLEDGE INTEGRATION
-- =============================================================================

-- Link assistants to knowledge collections
CREATE TABLE IF NOT EXISTS assistant_knowledge_link (
    assistant_id VARCHAR(255) NOT NULL,
    collection_id VARCHAR(255) NOT NULL,
    link_type VARCHAR(20) DEFAULT 'primary', -- primary, secondary, reference
    priority INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    
    -- Configuration for this link
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
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Knowledge collection indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_collection_user ON knowledge_collection(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_collection_public ON knowledge_collection(is_public);
CREATE INDEX IF NOT EXISTS idx_knowledge_collection_status ON knowledge_collection(processing_status);

-- Knowledge source indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_source_user ON knowledge_source(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_collection ON knowledge_source(collection_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_type ON knowledge_source(source_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_status ON knowledge_source(processing_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_hash ON knowledge_source(content_hash);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_created ON knowledge_source(created_at);

-- Document chunk indexes
CREATE INDEX IF NOT EXISTS idx_document_chunk_source ON document_chunk(source_id);
CREATE INDEX IF NOT EXISTS idx_document_chunk_parent ON document_chunk(parent_chunk_id);
CREATE INDEX IF NOT EXISTS idx_document_chunk_model ON document_chunk(embedding_model);
CREATE INDEX IF NOT EXISTS idx_document_chunk_dimension ON document_chunk(embedding_dimension);
CREATE INDEX IF NOT EXISTS idx_document_chunk_relevance ON document_chunk(relevance_score);

-- Knowledge entity indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_name ON knowledge_entity(name);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_canonical ON knowledge_entity(canonical_name);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_type ON knowledge_entity(entity_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_mention_count ON knowledge_entity(mention_count);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_pagerank ON knowledge_entity(pagerank_score);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_centrality ON knowledge_entity(degree_centrality);

-- Knowledge relationship indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_source ON knowledge_relationship(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_target ON knowledge_relationship(target_entity_id);
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
-- VIEWS FOR COMMON QUERIES
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

-- Entity relationship summary
CREATE OR REPLACE VIEW entity_relationship_summary AS
SELECT 
    ke.id,
    ke.name,
    ke.entity_type,
    ke.mention_count,
    ke.pagerank_score,
    ke.degree_centrality,
    COUNT(DISTINCT kr1.id) as outgoing_relationships,
    COUNT(DISTINCT kr2.id) as incoming_relationships,
    COUNT(DISTINCT kr1.id) + COUNT(DISTINCT kr2.id) as total_relationships
FROM knowledge_entity ke
LEFT JOIN knowledge_relationship kr1 ON ke.id = kr1.source_entity_id
LEFT JOIN knowledge_relationship kr2 ON ke.id = kr2.target_entity_id
GROUP BY ke.id, ke.name, ke.entity_type, ke.mention_count, ke.pagerank_score, ke.degree_centrality;

-- Assistant knowledge integration status
CREATE OR REPLACE VIEW assistant_knowledge_status AS
SELECT 
    a.id as assistant_id,
    a.name as assistant_name,
    a.assistant_type,
    COUNT(DISTINCT akl.collection_id) as linked_collections,
    COUNT(DISTINCT ks.id) as total_sources,
    SUM(ks.entities_extracted) as total_entities,
    SUM(ks.relationships_extracted) as total_relationships,
    SUM(ks.chunks_created) as total_chunks,
    MAX(ks.last_processed_at) as last_knowledge_update
FROM ai_assistant a
LEFT JOIN assistant_knowledge_link akl ON a.id = akl.assistant_id AND akl.enabled = TRUE
LEFT JOIN knowledge_source ks ON akl.collection_id = ks.collection_id
WHERE a.is_active = TRUE
GROUP BY a.id, a.name, a.assistant_type;

-- =============================================================================
-- FUNCTIONS FOR KNOWLEDGE MANAGEMENT
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
        total_entities = (
            SELECT COUNT(DISTINCT ke.id)
            FROM knowledge_entity ke
            JOIN knowledge_source ks ON ks.collection_id = p_collection_id
            WHERE ke.source_documents::jsonb ? ks.id::text
        ),
        total_relationships = (
            SELECT COUNT(DISTINCT kr.id)
            FROM knowledge_relationship kr
            JOIN knowledge_source ks ON ks.collection_id = p_collection_id
            WHERE kr.source_documents::jsonb ? ks.id::text
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