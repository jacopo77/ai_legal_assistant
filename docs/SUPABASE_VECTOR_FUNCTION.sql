-- ============================================================
-- Run this ONCE in Supabase → SQL Editor → New Query → Run
-- This creates the match_chunks function used by the backend
-- for vector similarity search via the REST API.
-- ============================================================

-- Ensure pgvector is enabled (safe to run again if already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop and recreate to pick up any signature changes
DROP FUNCTION IF EXISTS match_chunks(vector, int, text);

CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding  vector(1536),
    match_count      int     DEFAULT 6,
    filter_country   text    DEFAULT NULL
)
RETURNS TABLE (
    text    text,
    score   float,
    source  text,
    url     text,
    title   text
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        c.text,
        (1 - (c.embedding <=> query_embedding))::float AS score,
        d.source,
        d.url,
        d.title
    FROM   chunks   c
    JOIN   documents d ON d.id = c.document_id
    WHERE  filter_country IS NULL
        OR d.country = filter_country
    ORDER  BY c.embedding <=> query_embedding
    LIMIT  match_count;
$$;

-- Grant access so the REST API (anon + service_role) can call it
GRANT EXECUTE ON FUNCTION match_chunks(vector, int, text) TO anon, authenticated, service_role;
