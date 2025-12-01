from __future__ import annotations

import hashlib
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterable, Optional

import psycopg2
import psycopg2.extras

from . import config


@contextmanager
def get_conn():
    conn = psycopg2.connect(config.DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def ensure_project(name: str, description: Optional[str] = None) -> str:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM projects WHERE name=%s", (name,))
            row = cur.fetchone()
            if row:
                return str(row[0])
            cur.execute(
                "INSERT INTO projects (name, description) VALUES (%s, %s) RETURNING id",
                (name, description),
            )
            pid = str(cur.fetchone()[0])
            conn.commit()
            return pid


def sha1_fingerprint(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


@dataclass
class Document:
    id: str
    project_id: str
    source_url: Optional[str]
    source_type: Optional[str]
    author: Optional[str]
    language: Optional[str]
    title: Optional[str]
    fingerprint: Optional[str]


def upsert_document(
    project_id: str,
    *,
    source_url: Optional[str],
    source_type: Optional[str],
    author: Optional[str],
    language: Optional[str],
    title: Optional[str],
    fingerprint: Optional[str],
    tags: Optional[list[str]] = None,
    blob_key: Optional[str] = None,
) -> tuple[str, bool]:
    """Insert a document. Returns (doc_id, created_bool). If fingerprint exists, returns existing id, created=False."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            if fingerprint:
                cur.execute(
                    "SELECT id FROM documents WHERE fingerprint=%s AND project_id=%s",
                    (fingerprint, project_id),
                )
                row = cur.fetchone()
                if row:
                    return (str(row[0]), False)
            cur.execute(
                """
                INSERT INTO documents (project_id, source_url, source_type, author, language, title, fingerprint, tags, blob_key)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    project_id,
                    source_url,
                    source_type,
                    author,
                    language,
                    title,
                    fingerprint,
                    tags,
                    blob_key,
                ),
            )
            doc_id = str(cur.fetchone()[0])
            conn.commit()
            return (doc_id, True)


@dataclass
class Chunk:
    id: str
    document_id: str
    idx: int
    text: str
    token_count: int
    start_offset: int
    end_offset: int
    metadata: dict[str, Any]


def insert_chunks(
    document_id: str,
    chunks: Iterable[tuple[int, str, int, int, int, dict[str, Any]]],
) -> list[str]:
    ids: list[str] = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            for idx, text, tok_count, start, end, metadata in chunks:
                cur.execute(
                    """
                    INSERT INTO chunks (document_id, idx, text, token_count, start_offset, end_offset, metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                    """,
                    (document_id, idx, text, tok_count, start, end, psycopg2.extras.Json(metadata or {})),
                )
                ids.append(str(cur.fetchone()[0]))
        conn.commit()
    return ids


def get_chunk_texts(chunk_ids: list[str]) -> list[tuple[str, str]]:
    """Return list of (chunk_id, text)."""
    if not chunk_ids:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id::text, text FROM chunks WHERE id = ANY(%s)",
                (chunk_ids,),
            )
            return [(row[0], row[1]) for row in cur.fetchall()]


def get_chunk_snippet(chunk_id: str) -> Optional[str]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT text FROM chunks WHERE id=%s", (chunk_id,))
            row = cur.fetchone()
            return row[0] if row else None


def get_chunk_meta(chunk_ids: list[str]) -> list[tuple[str, str, int]]:
    """Return list of (chunk_id, document_id, idx)."""
    if not chunk_ids:
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id::text, document_id::text, idx FROM chunks WHERE id = ANY(%s)",
                (chunk_ids,),
            )
            return [(row[0], row[1], int(row[2])) for row in cur.fetchall()]


def get_documents_source_url(doc_ids: list[str]) -> dict[str, str | None]:
    if not doc_ids:
        return {}
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id::text, source_url FROM documents WHERE id = ANY(%s)",
                (doc_ids,),
            )
            return {row[0]: row[1] for row in cur.fetchall()}
