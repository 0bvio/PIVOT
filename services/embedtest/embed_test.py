import json
import math
import os
import sys

def main():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print("[ERROR] Failed to import sentence-transformers:", e, file=sys.stderr)
        sys.exit(2)

    model_name = os.environ.get("EMBED_MODEL", "BAAI/bge-large-en")
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    text = "Sprint 0 embedding sanity check for PIVOT."
    vec = model.encode([text], normalize_embeddings=False)[0]

    dim = len(vec)
    norm = math.sqrt(float((vec ** 2).sum())) if hasattr(vec, "__array__") else math.sqrt(sum(float(x) * float(x) for x in vec))

    result = {
        "model": model_name,
        "input": text,
        "dim": dim,
        "l2_norm": round(norm, 6),
        "ok": True,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
