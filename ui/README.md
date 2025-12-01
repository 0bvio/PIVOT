# PIVOT UI (lightweight)

This is a minimal React + Vite UI for the PIVOT project. It provides a Chat interface, a Source Browser, and a small Admin panel for uploading files to be ingested.

Quick start (dev):

1. cd ui
2. npm install
3. npm run dev

The Vite dev server proxies `/api` to `http://localhost:8000` by default. Make sure the PIVOT backend is running (uvicorn pivot.api.main:app --reload) and listening on port 8000.

Notes:
- The UI is dark-themed and very lightweight — intended as a starter. Expand components and add state persistence as needed.
- File uploads hit `/api/upload` which saves files under `/data/uploads` and triggers the ingest flow.

