-- Migration: A/B Testing and Experimentation Tables
-- Version: 003
-- Date: 2025-08-19
-- Description: Adds tables for A/B testing and experimentation framework

BEGIN;

-- =============================================================================
-- A/B TESTING & EXPERIMENTATION
-- =============================================================================

-- Experiment definitions
CREATE TABLE IF NOT EXISTS experiment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    experiment_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    start_date BIGINT,
    end_date BIGINT,
    target_metrics JSON NOT NULL,
    success_criteria JSON NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at BIGINT NOT NULL,
    CONSTRAINT fk_experiment_user FOREIGN KEY (created_by) REFERENCES "user"(id)
);

-- Experiment variants (different versions being tested)
CREATE TABLE IF NOT EXISTS experiment_variant (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL,
    variant_name VARCHAR(255) NOT NULL,
    configuration JSON NOT NULL,
    traffic_allocation DECIMAL(4,3) NOT NULL,
    is_control BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_experiment_variant_experiment FOREIGN KEY (experiment_id) REFERENCES experiment(id) ON DELETE CASCADE,
    CONSTRAINT uk_experiment_variant UNIQUE(experiment_id, variant_name)
);

-- Experiment assignments (which users see which variant)
CREATE TABLE IF NOT EXISTS experiment_assignment (
    user_id VARCHAR(255) NOT NULL,
    experiment_id INTEGER NOT NULL,
    variant_id INTEGER NOT NULL,
    assigned_at BIGINT NOT NULL,
    PRIMARY KEY (user_id, experiment_id),
    CONSTRAINT fk_experiment_assignment_user FOREIGN KEY (user_id) REFERENCES "user"(id),
    CONSTRAINT fk_experiment_assignment_experiment FOREIGN KEY (experiment_id) REFERENCES experiment(id) ON DELETE CASCADE,
    CONSTRAINT fk_experiment_assignment_variant FOREIGN KEY (variant_id) REFERENCES experiment_variant(id) ON DELETE CASCADE
);

COMMIT;