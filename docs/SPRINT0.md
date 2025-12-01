Sprint 0: Planning & Infrastructure Setup
=======================================

Objective

Provision a development environment with all necessary services (Postgres, Redis, Vector DB) and validate embeddings. This document describes how to bring up the stack and run the embedding sanity test.

Prerequisites

- Docker + Docker Compose v2
- (Optional) NVIDIA GPU + NVIDIA Container Toolkit for GPU runtimes

Services

- Postgres 16 (metadata) — auto-initialized with schema
- Redis 7 (queue/cache)
- Qdrant (vector DB) on ports 6333/6334
- Optional LLM runtimes (profile: llm): Ollama, vLLM, llama.cpp

Usage

1) Start core services

    make up

2) Verify containers

    make ps

3) Run embedding sanity test (BGE Large EN)

    make embed-test

Expected output (example):

    {
      "model": "BAAI/bge-large-en",
      "input": "Sprint 0 embedding sanity check for PIVOT.",
      "dim": 1024,
      "l2_norm": 19.876543,
      "ok": true
    }

4) Start optional LLM runtimes

- Ollama:

    make llm-ollama

- vLLM (ensure GPU if using large models):

    make llm-vllm

- llama.cpp server (CPU by default):

    make llm-llamacpp

Database Schema

See docker/postgres/initdb.d/001_schema.sql for tables:
- projects
- documents
- chunks

Cleanup

    make down         # stop services
    make clean        # remove volumes (data loss!)
