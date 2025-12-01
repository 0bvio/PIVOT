from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List, Tuple

from transformers import AutoTokenizer

from .. import config


@lru_cache(maxsize=1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(config.EMBED_MODEL)


def chunk_text(
    text: str,
    max_tokens: int | None = None,
    overlap: int | None = None,
) -> List[Tuple[int, str, int, int, int, dict]]:
    """Return list of (idx, chunk_text, token_count, start_offset, end_offset, metadata).
    Uses tokenizer offsets to map token windows to character offsets.
    """
    if not text:
        return []
    tok = get_tokenizer()
    max_tokens = max_tokens or config.CHUNK_MAX_TOKENS
    overlap = overlap or config.CHUNK_OVERLAP_TOKENS
    step = max(1, max_tokens - overlap)

    enc = tok(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True,
        return_attention_mask=False,
        return_token_type_ids=False,
    )
    ids = enc["input_ids"]
    offsets = enc["offset_mapping"]
    chunks = []
    idx = 0
    for start in range(0, len(ids), step):
        end_tok = min(start + max_tokens, len(ids))
        if start >= end_tok:
            break
        # Character offsets
        start_char = int(offsets[start][0]) if offsets[start] else 0
        end_char = int(offsets[end_tok - 1][1]) if offsets[end_tok - 1] else start_char
        piece = text[start_char:end_char]
        if not piece.strip():
            continue
        token_count = end_tok - start
        chunks.append((idx, piece, token_count, start_char, end_char, {}))
        idx += 1
        if end_tok == len(ids):
            break
    return chunks
