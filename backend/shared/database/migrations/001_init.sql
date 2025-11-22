-- Initialize the real_estate_agents database
-- Run this SQL file to create the initial schema

-- Create database (if running manually)
-- CREATE DATABASE real_estate_agents;

-- Connect to the database
-- \c real_estate_agents;

-- Enable UUID extension for generating job IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
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

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    type job_type NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    request_payload JSONB NOT NULL,
    response_payload JSONB,
    error_message TEXT,
    retry_count VARCHAR(10) DEFAULT '0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    parent_job_id VARCHAR(255),
    
    -- Indexes for common queries
    CONSTRAINT fk_parent_job FOREIGN KEY (parent_job_id) REFERENCES jobs(job_id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_parent_job_id ON jobs(parent_job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created_at ON jobs(status, created_at DESC);

-- Add comments to table and columns
COMMENT ON TABLE jobs IS 'Tracks all agent task executions across the system';
COMMENT ON COLUMN jobs.job_id IS 'Unique job identifier (UUID or SQS message ID)';
COMMENT ON COLUMN jobs.type IS 'Type of agent job';
COMMENT ON COLUMN jobs.status IS 'Current job status';
COMMENT ON COLUMN jobs.request_payload IS 'Input data for the job (query, parameters, context)';
COMMENT ON COLUMN jobs.response_payload IS 'Output data from the job (results, errors, metadata)';
COMMENT ON COLUMN jobs.error_message IS 'Error message if job failed';
COMMENT ON COLUMN jobs.retry_count IS 'Number of retry attempts';
COMMENT ON COLUMN jobs.created_at IS 'When the job was created';
COMMENT ON COLUMN jobs.updated_at IS 'When the job was last updated';
COMMENT ON COLUMN jobs.completed_at IS 'When the job completed or failed';
COMMENT ON COLUMN jobs.parent_job_id IS 'Parent job ID for multi-step workflows';

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to call the function before updates
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
