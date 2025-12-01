from __future__ import annotations

from typing import Dict, Tuple
from pathlib import Path

from pypdf import PdfReader


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(texts)


def load_local_file(source_ref: str) -> Tuple[str, Dict]:
    """Read a local file from the mounted /data directory or an absolute path.
    Returns (text, metadata).
    """
    p = Path(source_ref)
    if not p.is_absolute():
        # Allow relative path under /data for containers
        p = Path("/data") / source_ref
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    text = ""
    if p.suffix.lower() in {".txt", ".md", ".log"}:
        text = p.read_text(encoding="utf-8", errors="ignore")
    elif p.suffix.lower() == ".pdf":
        text = _read_pdf(p)
    else:
        # Fallback try text
        text = p.read_text(encoding="utf-8", errors="ignore")

    meta = {
        "title": p.name,
        "source_url": str(p),
        "source_type": "local_file",
    }
    return text, meta
