#!/usr/bin/env python3
"""Database setup script"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

SQL = """
-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    whatsapp_id     VARCHAR(20) UNIQUE NOT NULL,
    name            VARCHAR(100),
    role            VARCHAR(20) DEFAULT 'user',
    preferences     JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_active_at  TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT TRUE
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                  UUID REFERENCES users(id) ON DELETE CASCADE,
    original_name            VARCHAR(255) NOT NULL,
    file_type                VARCHAR(20) NOT NULL,
    mime_type                VARCHAR(100),
    file_size                BIGINT NOT NULL,
    file_hash                VARCHAR(64),
    fuzzy_hash               VARCHAR(200),
    r2_key                   VARCHAR(500),
    r2_url                   TEXT,
    status                   VARCHAR(20) DEFAULT 'pending',
    processing_time          FLOAT,
    error_message            TEXT,
    page_count               INTEGER,
    word_count               INTEGER,
    language                 VARCHAR(10),
    was_password_protected   BOOLEAN DEFAULT FALSE,
    password_protection_type VARCHAR(30),
    decryption_method        VARCHAR(30),
    created_at               TIMESTAMPTZ DEFAULT NOW(),
    processed_at             TIMESTAMPTZ,
    updated_at               TIMESTAMPTZ DEFAULT NOW()
);

-- Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    content_hash    VARCHAR(64),
    embedding       vector(1024),
    chunk_index     INTEGER NOT NULL,
    page_number     INTEGER,
    start_char      INTEGER,
    end_char        INTEGER,
    token_count     INTEGER,
    chunk_type      VARCHAR(20),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, content_hash)
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id      VARCHAR(100),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    message_count   INTEGER DEFAULT 0,
    metadata        JSONB DEFAULT '{}'
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role                VARCHAR(10) NOT NULL,
    content             TEXT NOT NULL,
    query_embedding     vector(1024),
    detected_language   VARCHAR(10),
    rewritten_query     TEXT,
    complexity          VARCHAR(20),
    chunks_used         UUID[],
    model_used          VARCHAR(50),
    tokens_input        INTEGER,
    tokens_output       INTEGER,
    latency_ms          INTEGER,
    faithfulness_score  FLOAT,
    relevance_score     FLOAT,
    user_feedback       INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Query Cache
CREATE TABLE IF NOT EXISTS query_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash      VARCHAR(64) UNIQUE NOT NULL,
    original_query  TEXT NOT NULL,
    cached_response JSONB NOT NULL,
    hit_count       INTEGER DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    last_hit_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Support Tickets
CREATE TABLE IF NOT EXISTS support_tickets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_number   VARCHAR(20) UNIQUE NOT NULL,
    user_id         UUID REFERENCES users(id),
    original_query  TEXT NOT NULL,
    system_attempts JSONB,
    status          VARCHAR(20) DEFAULT 'open',
    assigned_to     VARCHAR(100),
    resolution      TEXT,
    priority        VARCHAR(10) DEFAULT 'normal',
    ticket_type     VARCHAR(30) DEFAULT 'general',
    sla_deadline    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- Analytics
CREATE TABLE IF NOT EXISTS analytics_daily (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date                    DATE UNIQUE NOT NULL DEFAULT CURRENT_DATE,
    total_queries           INTEGER DEFAULT 0,
    cache_hits              INTEGER DEFAULT 0,
    avg_latency_ms          FLOAT,
    avg_faithfulness        FLOAT,
    hallucinations_blocked  INTEGER DEFAULT 0,
    escalations             INTEGER DEFAULT 0,
    documents_uploaded      INTEGER DEFAULT 0,
    chunks_created          INTEGER DEFAULT 0,
    tokens_used             BIGINT DEFAULT 0,
    llamaparse_pages        INTEGER DEFAULT 0,
    textract_pages          INTEGER DEFAULT 0,
    vision_pages            INTEGER DEFAULT 0,
    estimated_cost          DECIMAL(10,4)
);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id              UUID PRIMARY KEY,
    task_type       VARCHAR(50) NOT NULL,
    document_id     UUID REFERENCES documents(id),
    status          VARCHAR(20) DEFAULT 'pending',
    progress        INTEGER DEFAULT 0,
    current_step    VARCHAR(100),
    result          JSONB,
    error           TEXT,
    retry_count     INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);
CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm ON chunks USING gin (content gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_chunks_fts ON chunks USING gin (to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents (user_id, status);
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents (file_hash);
CREATE INDEX IF NOT EXISTS idx_tasks_document ON tasks (document_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_query_cache_hash ON query_cache (query_hash);
"""

async def setup():
    db_url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {db_url}")
    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute(SQL)
        print("All tables and indexes created!")
        
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )
        print(f"Tables: {[t['tablename'] for t in tables]}")
        
        extensions = await conn.fetch("SELECT extname FROM pg_extension")
        print(f"Extensions: {[e['extname'] for e in extensions]}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup())
