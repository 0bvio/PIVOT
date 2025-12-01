from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

import hashlib
import math

# Try to import sentence_transformers and numpy; fall back to lightweight implementation if missing
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except Exception:
    np = None  # type: ignore
    SentenceTransformer = None  # type: ignore
    _HAS_ST = False

from . import config


@lru_cache(maxsize=1)
def get_embed_model() -> "SentenceTransformer | None":
    if _HAS_ST:
        return SentenceTransformer(config.EMBED_MODEL)
    return None


def _hash_embed(text: str, dim: int = 128) -> List[float]:
    # Deterministic but cheap embedding: use sha256 blocks to create numbers in [-1,1]
    h = hashlib.sha256(text.encode("utf-8")).digest()
    vec = []
    # expand to dim using iterative hashing
    cur = h
    i = 0
    while len(vec) < dim:
        cur = hashlib.sha256(cur + i.to_bytes(2, "big")).digest()
        for j in range(0, len(cur), 4):
            if len(vec) >= dim:
                break
            v = int.from_bytes(cur[j : j + 4], "big", signed=False)
            # map to [-1,1]
            vec.append(((v / 2 ** 32) * 2.0) - 1.0)
        i += 1
    # normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def embed_texts(texts: Iterable[str], *, normalize: bool = False, batch_size: int = 64) -> List[List[float]]:
    texts = list(texts)
    model = get_embed_model()
    if model is not None:
        vecs = model.encode(texts, normalize_embeddings=normalize, batch_size=batch_size)
        if isinstance(vecs, (list, tuple)):
            # convert numpy arrays if necessary
            try:
                return (vecs.astype(float).tolist() if hasattr(vecs, 'astype') else [[float(x) for x in v] for v in vecs])
            except Exception:
                return [[float(x) for x in v] for v in vecs]
        elif np is not None and isinstance(vecs, np.ndarray):
            return vecs.astype(float).tolist()
        else:
            return [[float(x) for x in v] for v in vecs]
    # fallback
    return [_hash_embed(t) for t in texts]


def embed_query(text: str, *, normalize: bool = False) -> List[float]:
    return embed_texts([text], normalize=normalize)[0]
