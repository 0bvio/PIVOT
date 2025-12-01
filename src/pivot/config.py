import os


def getenv(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


DATABASE_URL = getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pivot")
REDIS_URL = getenv("REDIS_URL", "redis://localhost:6379/0")
MILVUS_HOST = getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(getenv("MILVUS_PORT", "19530"))
EMBED_MODEL = getenv("EMBED_MODEL", "BAAI/bge-large-en")

# Tokenizer/chunker
CHUNK_MAX_TOKENS = int(getenv("CHUNK_MAX_TOKENS", "2048"))
CHUNK_OVERLAP_TOKENS = int(getenv("CHUNK_OVERLAP_TOKENS", "200"))

# Celery
CELERY_QUEUES = {
    "ingest": "ingest",
    "embed": "embed",
}
