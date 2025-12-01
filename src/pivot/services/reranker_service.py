from __future__ import annotations

from typing import List, Dict, Any
import logging

from .. import config

logger = logging.getLogger(__name__)

# Try to import CrossEncoder from sentence_transformers (optional, best-effort)
try:
    from sentence_transformers.cross_encoder import CrossEncoder
    _HAS_CROSS = True
except Exception:
    CrossEncoder = None  # type: ignore
    _HAS_CROSS = False


class Reranker:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or config.getenv("RERANKER_MODEL") or "BAAI/bge-reranker-v2-m3"
        self._cross = None
        if _HAS_CROSS:
            try:
                self._cross = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning("Failed to load CrossEncoder %s: %s", self.model_name, e)
                self._cross = None

    def _embed_rescore(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Fallback: try to compute embeddings for snippets if embedding module available
        try:
            from ..embedding import embed_query as _embed_query, embed_texts as _embed_texts
            qvec = _embed_query(query)
            snippets = [c.get("snippet", "") for c in candidates]
            vecs = _embed_texts(snippets)
            # cosine similarity
            import math

            def cosine(a, b):
                ad = sum(x * y for x, y in zip(a, b))
                an = math.sqrt(sum(x * x for x in a))
                bn = math.sqrt(sum(x * x for x in b))
                if an == 0 or bn == 0:
                    return 0.0
                return ad / (an * bn)

            for c, v in zip(candidates, vecs):
                c["rerank_score"] = float(cosine(qvec, v))
            return sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        except Exception as e:
            logger.info("Embedding-based rescoring not available (%s), falling back to simple scorer", e)
            # Simple fallback: score by overlap of words / length heuristic
            qtokens = set(query.lower().split())
            for c in candidates:
                txt = (c.get("snippet", "") or "").lower()
                score = sum(1 for t in txt.split() if t in qtokens)
                # normalize by length
                denom = max(1, len(txt.split()))
                c["rerank_score"] = float(score) / denom
            return sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)

    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return candidates reordered with an added `rerank_score` field (higher is better)."""
        if not candidates:
            return []
        # Prefer cross-encoder scoring when available
        if self._cross is not None:
            try:
                # cross encoder expects list of pairs (query, text)
                pairs = [(query, c.get("snippet", "")) for c in candidates]
                scores = self._cross.predict(pairs)
                for c, s in zip(candidates, scores):
                    c["rerank_score"] = float(s)
                # Higher is better in CrossEncoder
                return sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            except Exception as e:
                logger.warning("CrossEncoder scoring failed: %s", e)
                # fallback to embed rescore
        # Fallback
        return self._embed_rescore(query, candidates)


# module-level default
_default_reranker = Reranker()


def rerank(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _default_reranker.rerank(query, candidates)
