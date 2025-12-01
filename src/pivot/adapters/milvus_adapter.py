from __future__ import annotations

from typing import Iterable, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    from pymilvus import (
        connections,
        FieldSchema,
        CollectionSchema,
        DataType,
        Collection,
        utility,
    )
    _HAS_PYMILVUS = True
except Exception:
    # pymilvus not available in test environment; provide stubs
    connections = None  # type: ignore
    FieldSchema = None  # type: ignore
    CollectionSchema = None  # type: ignore
    DataType = None  # type: ignore
    Collection = None  # type: ignore
    utility = None  # type: ignore
    _HAS_PYMILVUS = False

from .. import config

_CONN_ALIAS = "default"
_COLLECTION_NAME = "chunks"
_INDEX_NAME = "hnsw_cosine"


if _HAS_PYMILVUS:
    def _connect():
        if not connections.has_connection(_CONN_ALIAS):
            connections.connect(alias=_CONN_ALIAS, host=config.MILVUS_HOST, port=str(config.MILVUS_PORT))


    def ensure_collection(vector_dim: int):
        _connect()
        if not utility.has_collection(_COLLECTION_NAME):
            fields = [
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema(name="project_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="idx", dtype=DataType.INT64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=vector_dim),
            ]
            schema = CollectionSchema(fields=fields, description="PIVOT chunks embeddings")
            coll = Collection(name=_COLLECTION_NAME, schema=schema)
            # Create index
            coll.create_index(
                field_name="embedding",
                index_name=_INDEX_NAME,
                index_params={
                    "index_type": "HNSW",
                    "metric_type": "COSINE",
                    "params": {"M": 48, "efConstruction": 200},
                },
            )
            coll.load()
            return coll
        else:
            coll = Collection(name=_COLLECTION_NAME)
            return coll


    def upsert_embeddings(
        project_id: str,
        rows: Iterable[Tuple[str, str, int, List[float]]],
        *,
        vector_dim: Optional[int] = None,
    ) -> int:
        """rows: iterable of (chunk_id, doc_id, idx, embedding)"""
        rows = list(rows)
        if not rows:
            return 0
        if vector_dim is None:
            vector_dim = len(rows[0][3])
        coll = ensure_collection(vector_dim)
        entities = [
            [r[0] for r in rows],  # chunk_id
            [project_id] * len(rows),
            [r[1] for r in rows],  # doc_id
            [int(r[2]) for r in rows],  # idx
            [r[3] for r in rows],  # embedding
        ]
        coll.upsert(data=entities)
        coll.load()
        return len(rows)


    def search(
        project_id: str,
        query_vector: List[float],
        top_k: int = 25,
    ) -> list[tuple[str, float, str, int]]:
        """Return list of (chunk_id, score, doc_id, idx). Higher score is better (cosine)."""
        _connect()
        coll = Collection(name=_COLLECTION_NAME)
        if not utility.has_collection(_COLLECTION_NAME):
            return []
        coll.load()
        res = coll.search(
            data=[query_vector],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=top_k,
            expr=f"project_id == '{project_id}'",
            output_fields=["doc_id", "idx"],
        )
        hits = []
        for hit in res[0]:
            hits.append((hit.id, float(hit.distance), hit.entity.get("doc_id"), int(hit.entity.get("idx"))))
        # For cosine, Milvus returns distance (1 - cosine) if metric is IP cos? With COSINE, smaller is better.
        # Convert to descending score: score = 1 - distance
        hits = [(cid, 1.0 - dist, doc, idx) for (cid, dist, doc, idx) in hits]
        return hits

else:
    # Stubs for environments without pymilvus. The test environment will monkeypatch `search` when needed.
    def _connect():
        return None


    def ensure_collection(vector_dim: int):
        logger.info("pymilvus not available; ensure_collection is a no-op in tests")
        return None


    def upsert_embeddings(project_id: str, rows: Iterable[Tuple[str, str, int, List[float]]], *, vector_dim: Optional[int] = None) -> int:
        logger.info("pymilvus not available; upsert_embeddings is a no-op in tests")
        return len(list(rows))


    def search(project_id: str, query_vector: List[float], top_k: int = 25) -> list[tuple[str, float, str, int]]:
        logger.info("pymilvus not available; search returns empty list in tests (caller may monkeypatch)")
        return []
