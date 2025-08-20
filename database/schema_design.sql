-- AI Assistant Platform Database Schema Extensions
-- Extends the existing OpenWebUI schema with specialized tables for:
-- - Enhanced prompt management and versioning
-- - AI Assistant framework
-- - Performance analytics and evaluation
-- - Knowledge management integration

-- =============================================================================
-- PROMPT MANAGEMENT EXTENSIONS
-- =============================================================================

-- Prompt versions table for A/B testing and version control
CREATE TABLE IF NOT EXISTS prompt_version (
    id SERIAL PRIMARY KEY,
    prompt_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    variables JSON DEFAULT '{}', -- Template variables definition
    created_by VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    performance_metrics JSON DEFAULT '{}', -- A/B testing results
    FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES "user"(id),
    UNIQUE(prompt_id, version_number)
);

-- Prompt categories for organization
CREATE TABLE IF NOT EXISTS prompt_category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    created_at BIGINT NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    FOREIGN KEY (created_by) REFERENCES "user"(id)
);

-- Many-to-many relationship for prompt categorization
CREATE TABLE IF NOT EXISTS prompt_category_mapping (
    prompt_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (prompt_id, category_id),
    FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES prompt_category(id) ON DELETE CASCADE
);

-- =============================================================================
-- AI ASSISTANT FRAMEWORK
-- =============================================================================

-- AI Assistants table - extends model concept with specialized behavior
CREATE TABLE IF NOT EXISTS ai_assistant (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL, -- Base system prompt
    model_id TEXT NOT NULL, -- Which model to use
    user_id VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    configuration JSON DEFAULT '{}', -- Model parameters, temperature, etc.
    capabilities JSON DEFAULT '[]', -- List of capabilities/tools
    access_control JSON DEFAULT '{}',
    performance_stats JSON DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES "user"(id),
    FOREIGN KEY (model_id) REFERENCES model(id)
);

-- Assistant capabilities/tools
CREATE TABLE IF NOT EXISTS assistant_capability (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(100) NOT NULL, -- 'tool', 'function', 'integration'
    configuration JSON DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at BIGINT NOT NULL
);

-- Many-to-many mapping of assistants to capabilities
CREATE TABLE IF NOT EXISTS assistant_capability_mapping (
    assistant_id VARCHAR(255) NOT NULL,
    capability_id INTEGER NOT NULL,
    settings JSON DEFAULT '{}', -- Capability-specific settings
    is_enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (assistant_id, capability_id),
    FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE,
    FOREIGN KEY (capability_id) REFERENCES assistant_capability(id) ON DELETE CASCADE
);

-- =============================================================================
-- CONVERSATION ANALYTICS & EVALUATION
-- =============================================================================

-- Enhanced conversation tracking with performance metrics
CREATE TABLE IF NOT EXISTS conversation_session (
    id VARCHAR(255) PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    assistant_id VARCHAR(255),
    user_id VARCHAR(255) NOT NULL,
    model_used VARCHAR(255) NOT NULL,
    started_at BIGINT NOT NULL,
    ended_at BIGINT,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    avg_response_time DECIMAL(10,3) DEFAULT 0,
    user_satisfaction INTEGER, -- 1-5 rating
    session_metadata JSON DEFAULT '{}',
    FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE,
    FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id),
    FOREIGN KEY (user_id) REFERENCES "user"(id)
);

-- Performance evaluation metrics
CREATE TABLE IF NOT EXISTS evaluation_metric (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    metric_type VARCHAR(100) NOT NULL, -- 'response_time', 'accuracy', 'satisfaction'
    calculation_method TEXT, -- How the metric is calculated
    target_value DECIMAL(10,3), -- Target/goal value
    is_active BOOLEAN DEFAULT TRUE
);

-- Performance measurements
CREATE TABLE IF NOT EXISTS performance_measurement (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255),
    message_id TEXT,
    assistant_id VARCHAR(255),
    metric_id INTEGER NOT NULL,
    measured_value DECIMAL(10,3) NOT NULL,
    measured_at BIGINT NOT NULL,
    context JSON DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES conversation_session(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE,
    FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id),
    FOREIGN KEY (metric_id) REFERENCES evaluation_metric(id)
);

-- =============================================================================
-- KNOWLEDGE MANAGEMENT (GraphRAG Integration)
-- =============================================================================

-- Knowledge sources/documents
CREATE TABLE IF NOT EXISTS knowledge_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL, -- 'document', 'url', 'api', 'database'
    source_path TEXT NOT NULL, -- File path, URL, connection string
    content_hash VARCHAR(255), -- For change detection
    last_processed_at BIGINT,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    user_id VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    metadata JSON DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES "user"(id)
);

-- Knowledge graph entities (for GraphRAG)
CREATE TABLE IF NOT EXISTS knowledge_entity (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL, -- 'concept', 'person', 'organization', etc.
    description TEXT,
    properties JSON DEFAULT '{}',
    embedding_vector VECTOR(384), -- For vector similarity (requires pgvector)
    source_id INTEGER,
    created_at BIGINT NOT NULL,
    confidence_score DECIMAL(4,3) DEFAULT 1.0,
    FOREIGN KEY (source_id) REFERENCES knowledge_source(id) ON DELETE CASCADE
);

-- Knowledge relationships (for GraphRAG)
CREATE TABLE IF NOT EXISTS knowledge_relationship (
    id SERIAL PRIMARY KEY,
    from_entity_id INTEGER NOT NULL,
    to_entity_id INTEGER NOT NULL,
    relationship_type VARCHAR(100) NOT NULL, -- 'related_to', 'part_of', 'causes', etc.
    strength DECIMAL(4,3) DEFAULT 1.0, -- Relationship strength 0.0-1.0
    properties JSON DEFAULT '{}',
    source_id INTEGER,
    created_at BIGINT NOT NULL,
    FOREIGN KEY (from_entity_id) REFERENCES knowledge_entity(id) ON DELETE CASCADE,
    FOREIGN KEY (to_entity_id) REFERENCES knowledge_entity(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES knowledge_source(id) ON DELETE SET NULL
);

-- =============================================================================
-- A/B TESTING & EXPERIMENTATION
-- =============================================================================

-- Experiment definitions
CREATE TABLE IF NOT EXISTS experiment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    experiment_type VARCHAR(100) NOT NULL, -- 'prompt_ab', 'model_comparison', 'assistant_comparison'
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, paused, completed
    start_date BIGINT,
    end_date BIGINT,
    target_metrics JSON NOT NULL, -- Which metrics to track
    success_criteria JSON NOT NULL, -- What defines success
    created_by VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    FOREIGN KEY (created_by) REFERENCES "user"(id)
);

-- Experiment variants (different versions being tested)
CREATE TABLE IF NOT EXISTS experiment_variant (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL,
    variant_name VARCHAR(255) NOT NULL,
    configuration JSON NOT NULL, -- Variant-specific settings
    traffic_allocation DECIMAL(4,3) NOT NULL, -- 0.0-1.0 percentage of traffic
    is_control BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (experiment_id) REFERENCES experiment(id) ON DELETE CASCADE,
    UNIQUE(experiment_id, variant_name)
);

-- Experiment assignments (which users see which variant)
CREATE TABLE IF NOT EXISTS experiment_assignment (
    user_id VARCHAR(255) NOT NULL,
    experiment_id INTEGER NOT NULL,
    variant_id INTEGER NOT NULL,
    assigned_at BIGINT NOT NULL,
    PRIMARY KEY (user_id, experiment_id),
    FOREIGN KEY (user_id) REFERENCES "user"(id),
    FOREIGN KEY (experiment_id) REFERENCES experiment(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES experiment_variant(id) ON DELETE CASCADE
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Indexes for prompt management
CREATE INDEX IF NOT EXISTS idx_prompt_version_prompt_id ON prompt_version(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_version_active ON prompt_version(prompt_id, is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_category_mapping_prompt ON prompt_category_mapping(prompt_id);

-- Indexes for assistants
CREATE INDEX IF NOT EXISTS idx_ai_assistant_user ON ai_assistant(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_model ON ai_assistant(model_id);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_active ON ai_assistant(is_active);

-- Indexes for performance tracking
CREATE INDEX IF NOT EXISTS idx_conversation_session_chat ON conversation_session(chat_id);
CREATE INDEX IF NOT EXISTS idx_conversation_session_assistant ON conversation_session(assistant_id);
CREATE INDEX IF NOT EXISTS idx_conversation_session_started ON conversation_session(started_at);
CREATE INDEX IF NOT EXISTS idx_performance_measurement_session ON performance_measurement(session_id);
CREATE INDEX IF NOT EXISTS idx_performance_measurement_metric ON performance_measurement(metric_id);

-- Indexes for knowledge management
CREATE INDEX IF NOT EXISTS idx_knowledge_source_user ON knowledge_source(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_status ON knowledge_source(processing_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_type ON knowledge_entity(entity_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_source ON knowledge_entity(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_from ON knowledge_relationship(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_to ON knowledge_relationship(to_entity_id);

-- Indexes for experiments
CREATE INDEX IF NOT EXISTS idx_experiment_status ON experiment(status);
CREATE INDEX IF NOT EXISTS idx_experiment_dates ON experiment(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_experiment_assignment_user ON experiment_assignment(user_id);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active assistants with their latest performance stats
CREATE OR REPLACE VIEW active_assistants AS
SELECT 
    a.*,
    u.name as creator_name,
    m.name as model_name,
    COUNT(cs.id) as total_conversations,
    AVG(cs.user_satisfaction) as avg_satisfaction,
    AVG(cs.avg_response_time) as avg_response_time
FROM ai_assistant a
JOIN "user" u ON a.user_id = u.id
JOIN model m ON a.model_id = m.id
LEFT JOIN conversation_session cs ON a.id = cs.assistant_id
WHERE a.is_active = TRUE
GROUP BY a.id, u.name, m.name;

-- Latest prompt versions
CREATE OR REPLACE VIEW latest_prompt_versions AS
SELECT DISTINCT ON (p.id)
    p.id as prompt_id,
    p.command,
    p.title as prompt_title,
    pv.version_number,
    pv.title as version_title,
    pv.content,
    pv.variables,
    pv.created_at as version_created_at,
    u.name as created_by_name
FROM prompt p
JOIN prompt_version pv ON p.id = pv.prompt_id
JOIN "user" u ON pv.created_by = u.id
WHERE pv.is_active = TRUE
ORDER BY p.id, pv.version_number DESC;