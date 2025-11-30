-- Enable UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE job_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE job_type AS ENUM (
    'intent_classification',
    'planning',
    'search',
    'valuation',
    'legal_check',
    'verification',
    'summarization'
);

-- Main table
CREATE TABLE IF NOT EXISTS jobs (
    job_id VARCHAR(36) PRIMARY KEY,  -- Store UUID as string to match app usage
    type job_type NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    request_payload JSONB NOT NULL,
    response_payload JSONB,
    error_message TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- app must update this on UPDATE
    completed_at TIMESTAMPTZ,
    parent_job_id VARCHAR(36),  -- Store UUID as string to match app usage
    CONSTRAINT fk_parent_job
        FOREIGN KEY (parent_job_id)
        REFERENCES jobs(job_id)
        ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_parent_job_id ON jobs(parent_job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created_at ON jobs(status, created_at DESC);
