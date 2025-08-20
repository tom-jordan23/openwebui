-- Migration: Assistant Framework Extensions
-- Version: 002
-- Date: 2025-08-19
-- Description: Extends AI assistant tables with framework functionality

BEGIN;

-- =============================================================================
-- ASSISTANT FRAMEWORK EXTENSIONS
-- =============================================================================

-- Update ai_assistant table with framework fields
ALTER TABLE ai_assistant 
ADD COLUMN IF NOT EXISTS assistant_type VARCHAR(20) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft',
ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0.0',
ADD COLUMN IF NOT EXISTS parent_assistant_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS primary_prompt_id INTEGER,
ADD COLUMN IF NOT EXISTS prompt_version_id INTEGER,
ADD COLUMN IF NOT EXISTS fallback_prompts JSON DEFAULT '[]',
ADD COLUMN IF NOT EXISTS personality_traits JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS response_guidelines JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS context_memory_size INTEGER DEFAULT 4000,
ADD COLUMN IF NOT EXISTS temperature DECIMAL(3,2) DEFAULT 0.7,
ADD COLUMN IF NOT EXISTS max_tokens INTEGER DEFAULT 2000,
ADD COLUMN IF NOT EXISTS deployment_config JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS environment VARCHAR(20) DEFAULT 'development',
ADD COLUMN IF NOT EXISTS resource_limits JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS total_conversations INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_messages INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS avg_conversation_length DECIMAL(10,2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS avg_response_time DECIMAL(10,3) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS user_satisfaction_rating DECIMAL(3,2) DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS usage_analytics JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS performance_metrics JSON DEFAULT '{}',
ADD COLUMN IF NOT EXISTS error_logs JSON DEFAULT '[]',
ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]',
ADD COLUMN IF NOT EXISTS category_ids JSON DEFAULT '[]';

-- Add foreign key constraints
ALTER TABLE ai_assistant 
ADD CONSTRAINT fk_ai_assistant_parent 
    FOREIGN KEY (parent_assistant_id) REFERENCES ai_assistant(id),
ADD CONSTRAINT fk_ai_assistant_primary_prompt 
    FOREIGN KEY (primary_prompt_id) REFERENCES prompt(id),
ADD CONSTRAINT fk_ai_assistant_prompt_version 
    FOREIGN KEY (prompt_version_id) REFERENCES prompt_version(id);

-- Create assistant deployments table
CREATE TABLE IF NOT EXISTS assistant_deployment (
    id SERIAL PRIMARY KEY,
    assistant_id VARCHAR(255) NOT NULL,
    environment VARCHAR(20) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    deployed_at BIGINT NOT NULL,
    deployed_by VARCHAR(255) NOT NULL,
    configuration_snapshot JSON DEFAULT '{}',
    resource_allocation JSON DEFAULT '{}',
    health_check_url TEXT,
    metrics_endpoint TEXT,
    rollback_version VARCHAR(20),
    deployment_logs JSON DEFAULT '[]',
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    CONSTRAINT fk_assistant_deployment_assistant 
        FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE,
    CONSTRAINT fk_assistant_deployment_user 
        FOREIGN KEY (deployed_by) REFERENCES "user"(id)
);

-- Create conversation context table
CREATE TABLE IF NOT EXISTS conversation_context (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    assistant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    conversation_history JSON DEFAULT '[]',
    context_variables JSON DEFAULT '{}',
    active_prompt_id INTEGER,
    prompt_variables JSON DEFAULT '{}',
    max_context_length INTEGER DEFAULT 4000,
    current_context_length INTEGER DEFAULT 0,
    context_compression_enabled BOOLEAN DEFAULT TRUE,
    started_at BIGINT NOT NULL,
    last_interaction BIGINT NOT NULL,
    interaction_count INTEGER DEFAULT 0,
    avg_response_time DECIMAL(10,3) DEFAULT 0.0,
    total_tokens_used INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    CONSTRAINT fk_conversation_context_assistant 
        FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE,
    CONSTRAINT fk_conversation_context_user 
        FOREIGN KEY (user_id) REFERENCES "user"(id),
    CONSTRAINT fk_conversation_context_prompt 
        FOREIGN KEY (active_prompt_id) REFERENCES prompt(id)
);

-- Create assistant prompt mapping table for many-to-many relationship
CREATE TABLE IF NOT EXISTS assistant_prompt_mapping (
    assistant_id VARCHAR(255) NOT NULL,
    prompt_id INTEGER NOT NULL,
    prompt_version_id INTEGER,
    mapping_type VARCHAR(20) DEFAULT 'secondary', -- primary, secondary, fallback
    priority INTEGER DEFAULT 0,
    conditions JSON DEFAULT '{}', -- Conditions for when to use this prompt
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    PRIMARY KEY (assistant_id, prompt_id),
    CONSTRAINT fk_assistant_prompt_mapping_assistant 
        FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE,
    CONSTRAINT fk_assistant_prompt_mapping_prompt 
        FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE,
    CONSTRAINT fk_assistant_prompt_mapping_version 
        FOREIGN KEY (prompt_version_id) REFERENCES prompt_version(id) ON DELETE SET NULL
);

-- Create assistant analytics table for detailed performance tracking
CREATE TABLE IF NOT EXISTS assistant_analytics (
    id SERIAL PRIMARY KEY,
    assistant_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_metadata JSON DEFAULT '{}',
    time_period VARCHAR(20) DEFAULT 'daily', -- hourly, daily, weekly, monthly
    recorded_at BIGINT NOT NULL,
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    CONSTRAINT fk_assistant_analytics_assistant 
        FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE
);

-- Create assistant capabilities mapping table
CREATE TABLE IF NOT EXISTS assistant_capability_detail (
    id SERIAL PRIMARY KEY,
    assistant_id VARCHAR(255) NOT NULL,
    capability_id INTEGER NOT NULL,
    proficiency_level VARCHAR(20) DEFAULT 'intermediate', -- beginner, intermediate, advanced, expert
    enabled BOOLEAN DEFAULT TRUE,
    configuration JSON DEFAULT '{}',
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    updated_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()) * 1000,
    CONSTRAINT fk_assistant_capability_detail_assistant 
        FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE,
    CONSTRAINT fk_assistant_capability_detail_capability 
        FOREIGN KEY (capability_id) REFERENCES assistant_capability(id) ON DELETE CASCADE,
    CONSTRAINT uk_assistant_capability_detail 
        UNIQUE(assistant_id, capability_id)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Assistant framework indexes
CREATE INDEX IF NOT EXISTS idx_ai_assistant_type ON ai_assistant(assistant_type);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_status ON ai_assistant(status);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_environment ON ai_assistant(environment);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_parent ON ai_assistant(parent_assistant_id);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_primary_prompt ON ai_assistant(primary_prompt_id);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_satisfaction ON ai_assistant(user_satisfaction_rating);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_conversations ON ai_assistant(total_conversations);

-- Deployment indexes
CREATE INDEX IF NOT EXISTS idx_assistant_deployment_assistant ON assistant_deployment(assistant_id);
CREATE INDEX IF NOT EXISTS idx_assistant_deployment_environment ON assistant_deployment(environment);
CREATE INDEX IF NOT EXISTS idx_assistant_deployment_status ON assistant_deployment(status);
CREATE INDEX IF NOT EXISTS idx_assistant_deployment_deployed_at ON assistant_deployment(deployed_at);

-- Conversation context indexes
CREATE INDEX IF NOT EXISTS idx_conversation_context_assistant ON conversation_context(assistant_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context_user ON conversation_context(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context_last_interaction ON conversation_context(last_interaction);
CREATE INDEX IF NOT EXISTS idx_conversation_context_session ON conversation_context(session_id);

-- Prompt mapping indexes
CREATE INDEX IF NOT EXISTS idx_assistant_prompt_mapping_assistant ON assistant_prompt_mapping(assistant_id);
CREATE INDEX IF NOT EXISTS idx_assistant_prompt_mapping_prompt ON assistant_prompt_mapping(prompt_id);
CREATE INDEX IF NOT EXISTS idx_assistant_prompt_mapping_type ON assistant_prompt_mapping(mapping_type);
CREATE INDEX IF NOT EXISTS idx_assistant_prompt_mapping_priority ON assistant_prompt_mapping(priority);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_assistant_analytics_assistant ON assistant_analytics(assistant_id);
CREATE INDEX IF NOT EXISTS idx_assistant_analytics_metric ON assistant_analytics(metric_name);
CREATE INDEX IF NOT EXISTS idx_assistant_analytics_time ON assistant_analytics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_assistant_analytics_period ON assistant_analytics(time_period);

-- Capability detail indexes
CREATE INDEX IF NOT EXISTS idx_assistant_capability_detail_assistant ON assistant_capability_detail(assistant_id);
CREATE INDEX IF NOT EXISTS idx_assistant_capability_detail_capability ON assistant_capability_detail(capability_id);
CREATE INDEX IF NOT EXISTS idx_assistant_capability_detail_enabled ON assistant_capability_detail(enabled);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active assistants with deployment info
CREATE OR REPLACE VIEW assistant_deployment_status AS
SELECT 
    a.id,
    a.name,
    a.assistant_type,
    a.status,
    a.version,
    a.environment,
    a.is_active,
    a.total_conversations,
    a.user_satisfaction_rating,
    a.avg_response_time,
    u.name as creator_name,
    d.deployed_at,
    d.deployed_by,
    d.status as deployment_status
FROM ai_assistant a
JOIN "user" u ON a.user_id = u.id
LEFT JOIN assistant_deployment d ON a.id = d.assistant_id 
    AND d.environment = a.environment
    AND d.status = 'active'
WHERE a.is_active = TRUE;

-- Assistant performance summary
CREATE OR REPLACE VIEW assistant_performance_summary AS
SELECT 
    a.id,
    a.name,
    a.assistant_type,
    a.total_conversations,
    a.total_messages,
    a.avg_conversation_length,
    a.avg_response_time,
    a.user_satisfaction_rating,
    COUNT(DISTINCT cc.session_id) as active_sessions,
    AVG(cc.avg_response_time) as current_avg_response_time,
    SUM(cc.total_tokens_used) as total_tokens_consumed
FROM ai_assistant a
LEFT JOIN conversation_context cc ON a.id = cc.assistant_id
WHERE a.is_active = TRUE
GROUP BY a.id, a.name, a.assistant_type, a.total_conversations, a.total_messages,
         a.avg_conversation_length, a.avg_response_time, a.user_satisfaction_rating;

-- Assistant prompt relationships
CREATE OR REPLACE VIEW assistant_prompt_overview AS
SELECT 
    a.id as assistant_id,
    a.name as assistant_name,
    a.primary_prompt_id,
    p.title as primary_prompt_title,
    pv.version_number as primary_version,
    pv.title as primary_version_title,
    COUNT(apm.prompt_id) as additional_prompts
FROM ai_assistant a
LEFT JOIN prompt p ON a.primary_prompt_id = p.id
LEFT JOIN prompt_version pv ON a.prompt_version_id = pv.id
LEFT JOIN assistant_prompt_mapping apm ON a.id = apm.assistant_id 
    AND apm.mapping_type != 'primary'
WHERE a.is_active = TRUE
GROUP BY a.id, a.name, a.primary_prompt_id, p.title, pv.version_number, pv.title;

-- Assistant capability overview
CREATE OR REPLACE VIEW assistant_capability_overview AS
SELECT 
    a.id as assistant_id,
    a.name as assistant_name,
    a.assistant_type,
    ac.name as capability_name,
    ac.description as capability_description,
    acd.proficiency_level,
    acd.enabled,
    acd.updated_at as capability_updated_at
FROM ai_assistant a
JOIN assistant_capability_detail acd ON a.id = acd.assistant_id
JOIN assistant_capability ac ON acd.capability_id = ac.id
WHERE a.is_active = TRUE AND acd.enabled = TRUE
ORDER BY a.name, ac.name;

-- =============================================================================
-- FUNCTIONS FOR COMMON OPERATIONS
-- =============================================================================

-- Function to update assistant usage statistics
CREATE OR REPLACE FUNCTION update_assistant_usage_stats(
    p_assistant_id VARCHAR(255),
    p_message_count INTEGER,
    p_response_time DECIMAL(10,3),
    p_user_rating INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE ai_assistant SET
        total_conversations = total_conversations + 1,
        total_messages = total_messages + p_message_count,
        avg_conversation_length = (
            (avg_conversation_length * total_conversations + p_message_count) 
            / (total_conversations + 1)
        ),
        avg_response_time = (
            (avg_response_time * total_conversations + p_response_time)
            / (total_conversations + 1)
        ),
        user_satisfaction_rating = CASE 
            WHEN p_user_rating IS NOT NULL THEN
                CASE WHEN user_satisfaction_rating = 0 THEN p_user_rating
                ELSE user_satisfaction_rating * 0.8 + p_user_rating * 0.2
                END
            ELSE user_satisfaction_rating
        END,
        updated_at = EXTRACT(EPOCH FROM NOW()) * 1000
    WHERE id = p_assistant_id;
END;
$$ LANGUAGE plpgsql;

-- Function to record assistant analytics
CREATE OR REPLACE FUNCTION record_assistant_metric(
    p_assistant_id VARCHAR(255),
    p_metric_name VARCHAR(100),
    p_metric_value DECIMAL(15,4),
    p_time_period VARCHAR(20) DEFAULT 'daily',
    p_metadata JSON DEFAULT '{}'
) RETURNS VOID AS $$
BEGIN
    INSERT INTO assistant_analytics (
        assistant_id, 
        metric_name, 
        metric_value, 
        time_period,
        metric_metadata,
        recorded_at
    ) VALUES (
        p_assistant_id,
        p_metric_name,
        p_metric_value,
        p_time_period,
        p_metadata,
        EXTRACT(EPOCH FROM NOW()) * 1000
    );
END;
$$ LANGUAGE plpgsql;

COMMIT;