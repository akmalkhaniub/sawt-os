-- SawtOS PostgreSQL 17 + pgvector 0.8+ Database Initialization

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. In-Call Clinical & Enterprise Knowledge Base (pgvector HNSW)
CREATE TABLE IF NOT EXISTS clinical_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,         -- e.g., 'triage_protocol', 'insurance_policy', 'formulary'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),                 -- OpenAI / Cohere / Gemini vector
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fast HNSW cosine similarity index for sub-4ms in-call query retrieval
CREATE INDEX IF NOT EXISTS idx_clinical_knowledge_hnsw 
ON clinical_knowledge USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 2. Call Record Telemetry & Transcripts
CREATE TABLE IF NOT EXISTS call_records (
    call_sid VARCHAR(64) PRIMARY KEY,
    room_name VARCHAR(128) NOT NULL,
    from_number VARCHAR(32) NOT NULL,
    to_number VARCHAR(32) NOT NULL,
    region VARCHAR(32) NOT NULL,            -- 'gulf' or 'us'
    language VARCHAR(16) NOT NULL,
    duration_seconds NUMERIC(10, 2) DEFAULT 0.0,
    billable_minutes INTEGER DEFAULT 0,
    disconnect_reason VARCHAR(128),
    transcript_full TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Post-Call LLM-as-a-Judge Quality & Compliance Evaluations
CREATE TABLE IF NOT EXISTS call_qa_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_sid VARCHAR(64) REFERENCES call_records(call_sid) ON DELETE CASCADE,
    script_adherence_score NUMERIC(5, 2),   -- 0.00 to 100.00%
    compliance_passed BOOLEAN NOT NULL DEFAULT TRUE,
    forbidden_phrases_detected TEXT[],
    sentiment_opening VARCHAR(32),          -- 'positive', 'neutral', 'negative'
    sentiment_closing VARCHAR(32),
    sentiment_trajectory VARCHAR(64),       -- e.g., 'frustrated_to_satisfied'
    csat_score INTEGER CHECK (csat_score BETWEEN 1 AND 5),
    csat_reasoning TEXT,
    coaching_feedback TEXT,
    langfuse_trace_id VARCHAR(128),
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. HIPAA Immutable Audit Vault (Append-Only)
CREATE TABLE IF NOT EXISTS hipaa_audit_log (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id VARCHAR(64) NOT NULL,          -- User ID or Agent Worker ID
    action_type VARCHAR(64) NOT NULL,       -- 'READ_PHI', 'UPDATE_PHI', 'DISCLOSE_PHI', 'DEIDENTIFY'
    patient_id VARCHAR(64) NOT NULL,
    resource_accessed VARCHAR(128) NOT NULL,
    client_ip VARCHAR(45),
    tamper_proof_hash VARCHAR(64) NOT NULL, -- SHA-256 HMAC of log payload
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hipaa_patient ON hipaa_audit_log(patient_id);
