-- Migration: Indexes and Views for Performance
-- Version: 004
-- Date: 2025-08-19
-- Description: Adds indexes and views for optimal query performance

BEGIN;

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Indexes for prompt management
CREATE INDEX IF NOT EXISTS idx_prompt_version_prompt_id ON prompt_version(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_version_active ON prompt_version(prompt_id, is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_version_created_by ON prompt_version(created_by);
CREATE INDEX IF NOT EXISTS idx_prompt_category_mapping_prompt ON prompt_category_mapping(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_category_mapping_category ON prompt_category_mapping(category_id);

-- Indexes for assistants
CREATE INDEX IF NOT EXISTS idx_ai_assistant_user ON ai_assistant(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_model ON ai_assistant(model_id);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_active ON ai_assistant(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_created_at ON ai_assistant(created_at);

-- Indexes for performance tracking
CREATE INDEX IF NOT EXISTS idx_conversation_session_chat ON conversation_session(chat_id);
CREATE INDEX IF NOT EXISTS idx_conversation_session_assistant ON conversation_session(assistant_id);
CREATE INDEX IF NOT EXISTS idx_conversation_session_user ON conversation_session(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_session_started ON conversation_session(started_at);
CREATE INDEX IF NOT EXISTS idx_performance_measurement_session ON performance_measurement(session_id);
CREATE INDEX IF NOT EXISTS idx_performance_measurement_metric ON performance_measurement(metric_id);
CREATE INDEX IF NOT EXISTS idx_performance_measurement_measured_at ON performance_measurement(measured_at);

-- Indexes for knowledge management
CREATE INDEX IF NOT EXISTS idx_knowledge_source_user ON knowledge_source(user_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_status ON knowledge_source(processing_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_source_type ON knowledge_source(source_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_type ON knowledge_entity(entity_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_source ON knowledge_entity(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_entity_name ON knowledge_entity(name);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_from ON knowledge_relationship(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_to ON knowledge_relationship(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationship_type ON knowledge_relationship(relationship_type);

-- Indexes for experiments
CREATE INDEX IF NOT EXISTS idx_experiment_status ON experiment(status);
CREATE INDEX IF NOT EXISTS idx_experiment_dates ON experiment(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_experiment_created_by ON experiment(created_by);
CREATE INDEX IF NOT EXISTS idx_experiment_assignment_user ON experiment_assignment(user_id);
CREATE INDEX IF NOT EXISTS idx_experiment_assignment_experiment ON experiment_assignment(experiment_id);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active assistants with their latest performance stats
CREATE OR REPLACE VIEW active_assistants AS
SELECT 
    a.id,
    a.name,
    a.description,
    a.system_prompt,
    a.model_id,
    a.user_id,
    a.created_at,
    a.updated_at,
    a.configuration,
    a.capabilities,
    u.name as creator_name,
    m.name as model_name,
    COALESCE(COUNT(cs.id), 0) as total_conversations,
    COALESCE(AVG(cs.user_satisfaction), 0) as avg_satisfaction,
    COALESCE(AVG(cs.avg_response_time), 0) as avg_response_time
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
    p.user_id as prompt_owner,
    pv.id as version_id,
    pv.version_number,
    pv.title as version_title,
    pv.content,
    pv.variables,
    pv.created_at as version_created_at,
    pv.performance_metrics,
    u.name as created_by_name
FROM prompt p
JOIN prompt_version pv ON p.id = pv.prompt_id
JOIN "user" u ON pv.created_by = u.id
WHERE pv.is_active = TRUE
ORDER BY p.id, pv.version_number DESC;

-- Knowledge entity summary with relationship counts
CREATE OR REPLACE VIEW knowledge_entity_summary AS
SELECT 
    ke.id,
    ke.name,
    ke.entity_type,
    ke.description,
    ke.confidence_score,
    ke.created_at,
    ks.name as source_name,
    ks.source_type,
    COALESCE(from_rels.outgoing_count, 0) as outgoing_relationships,
    COALESCE(to_rels.incoming_count, 0) as incoming_relationships
FROM knowledge_entity ke
LEFT JOIN knowledge_source ks ON ke.source_id = ks.id
LEFT JOIN (
    SELECT from_entity_id, COUNT(*) as outgoing_count 
    FROM knowledge_relationship 
    GROUP BY from_entity_id
) from_rels ON ke.id = from_rels.from_entity_id
LEFT JOIN (
    SELECT to_entity_id, COUNT(*) as incoming_count 
    FROM knowledge_relationship 
    GROUP BY to_entity_id
) to_rels ON ke.id = to_rels.to_entity_id;

-- Performance metrics summary
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    em.name as metric_name,
    em.metric_type,
    em.target_value,
    COUNT(pm.id) as measurement_count,
    AVG(pm.measured_value) as avg_value,
    MIN(pm.measured_value) as min_value,
    MAX(pm.measured_value) as max_value,
    STDDEV(pm.measured_value) as stddev_value
FROM evaluation_metric em
LEFT JOIN performance_measurement pm ON em.id = pm.metric_id
WHERE em.is_active = TRUE
GROUP BY em.id, em.name, em.metric_type, em.target_value;

COMMIT;