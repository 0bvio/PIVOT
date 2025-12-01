from __future__ import annotations

import time
from typing import Any, Dict

from .celery_app import celery_app
from .. import config
from ..connectors import run_connector
from ..normalize import normalize_text
from ..chunker.token_chunker import chunk_text
from .. import db
from .. import embedding
from ..adapters import milvus_adapter


@celery_app.task(name="ingest_job", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def ingest_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Payload keys: project (name), source_type, source_ref, metadata (optional), tags (optional)"""
    t0 = time.time()
    project_name = payload.get("project") or "default"
    source_type = payload["source_type"]
    source_ref = payload["source_ref"]
    extra_meta = payload.get("metadata") or {}
    tags = payload.get("tags")

    project_id = db.ensure_project(project_name)

    raw_text, meta = run_connector(source_type, source_ref, extra_meta)
    is_html = bool(meta.get("is_html"))
    clean_text, language = normalize_text(raw_text, is_html=is_html)

    # Fingerprint for dedupe
    fp = db.sha1_fingerprint(clean_text[:10000])  # limit to speed

    doc_id, created = db.upsert_document(
        project_id=project_id,
        source_url=meta.get("source_url"),
        source_type=meta.get("source_type"),
        author=meta.get("author"),
        language=language,
        title=meta.get("title"),
        fingerprint=fp,
        tags=tags,
    )
    if not created:
        return {"project_id": project_id, "document_id": doc_id, "skipped": True}

    # Chunk
    chunks = chunk_text(clean_text, max_tokens=config.CHUNK_MAX_TOKENS, overlap=config.CHUNK_OVERLAP_TOKENS)
    chunk_rows = [(idx, text, tok, start, end, {"source_type": source_type}) for (idx, text, tok, start, end, _) in chunks]
    chunk_ids = db.insert_chunks(doc_id, chunk_rows)

    # Enqueue embedding
    embed_job.apply_async(args=[project_id, doc_id, chunk_ids], queue="embed")

    return {
        "project_id": project_id,
        "document_id": doc_id,
        "chunk_count": len(chunk_ids),
        "elapsed_ms": int((time.time() - t0) * 1000),
    }


@celery_app.task(name="embed_job", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def embed_job(self, project_id: str, document_id: str, chunk_ids: list[str]) -> Dict[str, Any]:
    t0 = time.time()
    id_texts = db.get_chunk_texts(chunk_ids)
    texts = [t for (_id, t) in id_texts]
    vecs = embedding.embed_texts(texts, normalize=False, batch_size=64)
    rows = []
    # Need doc_id and idx per chunk; fetch meta in one query
    metas = db.get_chunk_meta(chunk_ids)
    meta_map = {cid: (doc, idx) for (cid, doc, idx) in metas}
    for (cid, _t), vec in zip(id_texts, vecs):
        doc_id, idx = meta_map[cid]
        rows.append((cid, doc_id, idx, vec))
    upserted = milvus_adapter.upsert_embeddings(project_id, rows, vector_dim=len(vecs[0]) if vecs else None)
    return {"upserted": upserted, "elapsed_ms": int((time.time() - t0) * 1000)}
