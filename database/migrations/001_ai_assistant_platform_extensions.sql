-- Migration: AI Assistant Platform Extensions
-- Version: 001
-- Date: 2025-08-19
-- Description: Adds tables and indexes to support the AI Assistant Platform functionality

BEGIN;

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
    variables JSON DEFAULT '{}',
    created_by VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    performance_metrics JSON DEFAULT '{}',
    CONSTRAINT fk_prompt_version_prompt FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE,
    CONSTRAINT fk_prompt_version_user FOREIGN KEY (created_by) REFERENCES "user"(id),
    CONSTRAINT uk_prompt_version UNIQUE(prompt_id, version_number)
);

-- Prompt categories for organization
CREATE TABLE IF NOT EXISTS prompt_category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7),
    created_at BIGINT NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    CONSTRAINT fk_prompt_category_user FOREIGN KEY (created_by) REFERENCES "user"(id)
);

-- Many-to-many relationship for prompt categorization
CREATE TABLE IF NOT EXISTS prompt_category_mapping (
    prompt_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (prompt_id, category_id),
    CONSTRAINT fk_prompt_category_mapping_prompt FOREIGN KEY (prompt_id) REFERENCES prompt(id) ON DELETE CASCADE,
    CONSTRAINT fk_prompt_category_mapping_category FOREIGN KEY (category_id) REFERENCES prompt_category(id) ON DELETE CASCADE
);

-- =============================================================================
-- AI ASSISTANT FRAMEWORK
-- =============================================================================

-- AI Assistants table
CREATE TABLE IF NOT EXISTS ai_assistant (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    model_id TEXT NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    configuration JSON DEFAULT '{}',
    capabilities JSON DEFAULT '[]',
    access_control JSON DEFAULT '{}',
    performance_stats JSON DEFAULT '{}',
    CONSTRAINT fk_ai_assistant_user FOREIGN KEY (user_id) REFERENCES "user"(id),
    CONSTRAINT fk_ai_assistant_model FOREIGN KEY (model_id) REFERENCES model(id)
);

-- Assistant capabilities/tools
CREATE TABLE IF NOT EXISTS assistant_capability (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(100) NOT NULL,
    configuration JSON DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at BIGINT NOT NULL
);

-- Many-to-many mapping of assistants to capabilities
CREATE TABLE IF NOT EXISTS assistant_capability_mapping (
    assistant_id VARCHAR(255) NOT NULL,
    capability_id INTEGER NOT NULL,
    settings JSON DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (assistant_id, capability_id),
    CONSTRAINT fk_assistant_capability_mapping_assistant FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id) ON DELETE CASCADE,
    CONSTRAINT fk_assistant_capability_mapping_capability FOREIGN KEY (capability_id) REFERENCES assistant_capability(id) ON DELETE CASCADE
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
    user_satisfaction INTEGER,
    session_metadata JSON DEFAULT '{}',
    CONSTRAINT fk_conversation_session_chat FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE,
    CONSTRAINT fk_conversation_session_assistant FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id),
    CONSTRAINT fk_conversation_session_user FOREIGN KEY (user_id) REFERENCES "user"(id)
);

-- Performance evaluation metrics
CREATE TABLE IF NOT EXISTS evaluation_metric (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    metric_type VARCHAR(100) NOT NULL,
    calculation_method TEXT,
    target_value DECIMAL(10,3),
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
    CONSTRAINT fk_performance_measurement_session FOREIGN KEY (session_id) REFERENCES conversation_session(id) ON DELETE CASCADE,
    CONSTRAINT fk_performance_measurement_message FOREIGN KEY (message_id) REFERENCES message(id) ON DELETE CASCADE,
    CONSTRAINT fk_performance_measurement_assistant FOREIGN KEY (assistant_id) REFERENCES ai_assistant(id),
    CONSTRAINT fk_performance_measurement_metric FOREIGN KEY (metric_id) REFERENCES evaluation_metric(id)
);

COMMIT;