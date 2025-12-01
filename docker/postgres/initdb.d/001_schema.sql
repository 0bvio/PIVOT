-- Sprint 0: Metadata schema for PIVOT
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid()

-- Projects/collections
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  source_url TEXT,
  source_type TEXT,
  author TEXT,
  language TEXT,
  title TEXT,
  created_at TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ DEFAULT now(),
  fingerprint TEXT UNIQUE,
  tags TEXT[],
  blob_key TEXT
);

-- Chunks aligned with embeddings
CREATE TABLE IF NOT EXISTS chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  idx INT,
  text TEXT NOT NULL,
  token_count INT,
  start_offset INT,
  end_offset INT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN (metadata);
