Sprint 1: Ingestion & Vector Store
=================================

Objective

Implement core ingestion pipeline (connectors → normalize → chunk → embed) and store vectors in Milvus with a basic retrieval API.

What’s included

- FastAPI service (port 9000): /ingest, /query, /health
- Celery workers (Redis broker) for async ingestion and embedding
- Milvus (2.4.x) as the vector DB; Postgres for metadata; Redis for queue
- Tokenizer‑aware chunker (2048 tokens, 200 overlap) with offsets
- Connectors: local_file, http_url, reddit (public JSON)
- Normalization: HTML stripping (BeautifulSoup), emoji removal, language detect
- Embeddings: BAAI/bge-large-en via sentence-transformers (CPU by default)

Start services

    make up

This builds and starts: postgres, redis, milvus, qdrant (unused), api, workers.

Health checks

- API: http://localhost:9000/health → {"ok": true}

Quick ingest examples

1) Local file (mount ./data → /data):

    curl -X POST http://localhost:9000/ingest \
      -H 'Content-Type: application/json' \
      -d '{
            "project": "demo",
            "source_type": "local_file",
            "source_ref": "sample.txt",
            "tags": ["test"]
          }'

Place your file at ./data/sample.txt before calling. The job ID is returned.

2) HTTP URL (HTML will be cleaned):

    curl -X POST http://localhost:9000/ingest \
      -H 'Content-Type: application/json' \
      -d '{
            "project": "demo",
            "source_type": "http_url",
            "source_ref": "https://example.com"
          }'

3) Reddit thread (public):

    curl -X POST http://localhost:9000/ingest \
      -H 'Content-Type: application/json' \
      -d '{
            "project": "demo",
            "source_type": "reddit",
            "source_ref": "https://www.reddit.com/r/MachineLearning/comments/xxxxx/some_thread/"
          }'

Wait for workers to process (check logs):

    make logs

Query

    curl -X POST http://localhost:9000/query \
      -H 'Content-Type: application/json' \
      -d '{
            "project": "demo",
            "query": "What does the sample say?",
            "top_k": 10
          }'

Expected: JSON with results, scores, snippets, and source_url values. This indicates vectors are in Milvus and retrieval works.

Notes

- Embeddings download the BGE model on first use; this can take time.
- For GPU embeddings, swap the base images and install CUDA PyTorch, or run the workers on a GPU host.
- Qdrant service is present for flexibility but unused in Sprint 1.
- Fingerprinting (SHA1 of normalized text head) prevents duplicate document rows per project.

Troubleshooting

- If Milvus isn’t ready, workers may log errors; they auto‑retry. Ensure port 19530 is open.
- If import errors occur, rebuild services: `docker compose build api workers`.
