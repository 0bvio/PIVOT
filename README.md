# PIVOT — Retrieval-Augmented Generation Platform (RAG)

A modular, production-oriented RAG stack for ingesting multi-source content, producing tokenizer-aligned chunks and embeddings, storing vectors + metadata, and serving a fast retrieval + reranking API with a local LLM runtime and a lightweight UI.

This repository contains:
- `docker-compose.yml` — development Docker Compose to bring up Postgres, Redis, Milvus/Qdrant, API, workers, and optional LLM runtimes (Ollama, vLLM, llama.cpp).
- `services/` — service Dockerfiles and support code
- `src/pivot/` — Python backend: FastAPI endpoints, workers (Celery), connectors, chunker, embedding, adapters, and session manager
- `ui/` — minimal React + Vite + Tailwind UI (chat, source browser, admin/upload)
- `docs/SPRINT0.md`, `docs/SPRINT1.md` — sprint notes and usage

This README consolidates the docs and provides step-by-step run instructions: Docker (recommended) and native/local development.

----

Table of contents
- Goals & Architecture
- Quick Prerequisites
- Recommended: Docker Compose (full stack)
  - Start core services
  - Start Ollama & install QWEN2.5:32B (optional LLM profile)
  - Start UI
- Local/native development
  - Python backend (uvicorn) and Celery workers
  - Node UI (Vite)
- API endpoints (quick reference)
- UI usage (chat, sessions, upload)
- Troubleshooting & common issues
- Resources & notes

----

Goals & Architecture
====================
PIVOT is an end-to-end pipeline and runtime for RAG applications:
- Ingestion: connectors (local files, HTTP, Reddit, Discord, Google Drive, PDF/HTML) → normalization → deduplication → tokenizer-aware chunking (2048 tokens, 200 overlap) → store chunks
- Embedding: GPU-enabled batch embedding (configurable model; default: BAAI/bge-large-en)
- Vector store: Milvus (preferred) / Qdrant as an alternative; metadata persisted to Postgres
- Retrieval: Query embedding → TopK vector search (25) → reranking (bge-reranker-v2-m3 if available) → provide provenance
- LLM runtime: Integrates with local runtimes (vLLM, Ollama, llama.cpp) for final response generation and streaming
- UI: Lightweight React chat, session manager, source snippet browser, admin/upload

The system is designed to be modular so you can swap backends (vector DB, reranker, LLM runtime) as you scale.

Quick Prerequisites
===================
Minimum for development and testing:
- Docker Engine + Docker Compose v2 (recommended)
- Node.js + npm (for the UI)
- Python 3.10+ (for running backend natively)

Optional (for full performance / production):
- NVIDIA GPU + NVIDIA Container Toolkit (to run GPU-enabled embeddings / LLMs)
- Enough disk space & memory for large LLMs (QWEN2.5:32B requires substantial resources)

Recommended ports (defaults in docker-compose.yml):
- API: 9000 (container) → 9000 (host)
- UI (Vite dev): 5173
- Postgres: 5432
- Redis: 6379
- Milvus gRPC: 19530
- Ollama (if using Docker service): 11434

Docker Compose (recommended)
============================
The repository includes a `docker-compose.yml` that defines core infra and optional LLM runtime containers.

1) Start the core stack (Postgres, Redis, Milvus, API, Workers):

```sh
# From repo root
docker compose up -d postgres redis milvus api workers
```

This will:
- Start Postgres and initialize DB schema from `docker/postgres/initdb.d/`.
- Start Redis (Celery broker/backend).
- Start Milvus for vector storage.
- Build & run the `api` and `workers` containers (see `services/` Dockerfiles).

Check container health and logs:

```sh
docker compose ps
docker compose logs -f api
docker compose logs -f workers
```

2) Start optional LLM runtimes (profile: `llm`)

This repo contains optional LLM services in the compose file. To start Ollama (recommended for local model hosting):

```sh
# Start only the ollama service via the llm profile
docker compose --profile llm up -d ollama
```

Pull the QWEN2.5:32B model into Ollama

Note: model slugs differ per provider/registry. Replace `<OLLAMA_MODEL_NAME>` with the correct Ollama model identifier for QWEN2.5:32B. Typical example (illustrative only): `qwen/qwen-2.5-32b` — verify with the Ollama Hub or docs.

If you have `ollama` CLI locally (host):

```sh
# Pull the model via ollama CLI on host
ollama pull <OLLAMA_MODEL_NAME>
```

If you started Ollama inside Docker and don't have the CLI locally, run inside the container:

```sh
# Exec into the ollama container and pull model
docker exec -it pivot-ollama ollama pull <OLLAMA_MODEL_NAME>
```

Important notes about QWEN2.5:32B
- This model is very large. Ensure you have appropriate GPU resources (multi-GPU or server-grade GPUs) and tens to hundreds of GB of disk.
- If you don't have sufficient hardware, choose a smaller model for local testing.

3) Verify Ollama and the model

If Ollama is running on the host, you can list models with:

```sh
ollama ls
```

If using the container:

```sh
docker exec -it pivot-ollama ollama ls
```

## Fixes applied to `docker-compose.yml`

While preparing this repo, two practical issues were encountered that can stop `docker compose` from successfully starting the stack:

1. The top-level `version:` key in `docker-compose.yml` is obsolete when using Compose v2 and emits a warning. It is harmless but noisy; it has been removed from the file.

2. The Milvus image tag `milvusdb/milvus:2.4.9` caused a manifest-not-found error on some registries. The compose file has been updated to use `milvusdb/milvus:latest` to avoid that error. If you prefer to pin a specific Milvus version, replace the image with a known-good tag (for example, a tag available on Docker Hub or your registry).

If you previously saw an error like:

```
Error response from daemon: manifest for milvusdb/milvus:2.4.9 not found: manifest unknown: manifest unknown
```

then updating the image tag (as above) resolves that error.

## Helper script: `scripts/pull-ollama-model.sh`

I've added a convenience script to automate pulling an Ollama model either with the host `ollama` CLI (preferred) or by exec-ing into the `pivot-ollama` container and running the pull there.

Location: `scripts/pull-ollama-model.sh` (executable)

Usage examples:

```bash
# Pull model using local ollama CLI (preferred if you have it on host):
./scripts/pull-ollama-model.sh <OLLAMA_MODEL_SLUG>

# Example (replace with the correct Ollama model slug for QWEN2.5:32B):
./scripts/pull-ollama-model.sh qwen/qwen-2.5-32b
```

What the script does:
- If `ollama` CLI is available on the host, it runs `ollama pull <model>` locally.
- Otherwise it checks whether a container named `pivot-ollama` is running and runs `docker exec pivot-ollama ollama pull <model>`.
- If the container isn't running it will start the `pivot-ollama` service using Compose (`docker compose --profile llm up -d pivot-ollama`) and then try the pull inside the container.

> Note: model slugs vary by provider / Ollama Hub; confirm the canonical slug before pulling.

## How to recover and resume (copy/paste)

If you hit the milvus manifest error or an interrupted compose run, run these commands in order:

1) Ensure `docker-compose.yml` was updated (we already updated it in the repo). Optionally back up and re-check the file:

```bash
cp docker-compose.yml docker-compose.yml.bak
# (optional) inspect the milvus line:
grep -n "milvus" -n docker-compose.yml || true
```

2) Pull fresh images and recreate services:

```bash
# Pull images (may re-download large images like ollama)
docker compose pull

# Start the core infra and API/workers
docker compose up -d postgres redis qdrant milvus api workers

# If you want optional LLMs (Ollama) as well:
docker compose --profile llm up -d ollama
```

3) Check container health and logs:

```bash
docker compose ps
docker compose logs -f pivot-milvus
docker compose logs -f pivot-ollama
docker compose logs -f pivot-api
```

4) Pull the QWEN model into Ollama (run the helper script):

```bash
# Example using the helper script (replace with actual Ollama model slug):
./scripts/pull-ollama-model.sh qwen/qwen-2.5-32b
```

If the containerized Ollama doesn't include a working `ollama` CLI, the script will try to use the host `ollama` CLI; if neither works you'll see a helpful error in the script's output.

## If `ollama` CLI is not found inside the container

The message `ollama: command not found` in the container logs suggests the container image may not expose the CLI in that runtime or the path differs. Options:

- Install `ollama` on the host and run the `ollama pull` locally. The `~/.ollama` folder can be mounted into the container via the `ollama_data` volume so the container has the model files.
- Inspect the container logs to verify whether the image completed setup. Run:

```bash
docker compose logs -f pivot-ollama
```

- Exec into the container to inspect paths and binaries:

```bash
docker exec -it pivot-ollama /bin/sh
# inside container, try: which ollama || ls -la /usr/local/bin /usr/bin /bin
```

If `ollama` truly isn't available inside the image, prefer installing `ollama` locally on the host and using the host CLI to pull models.

----

If you'd like, I can now create an automation script to pull the Ollama model into the `pivot-ollama` container and verify it, or modify `llm_runtime.py` to call the Ollama HTTP API. Which would you prefer?
