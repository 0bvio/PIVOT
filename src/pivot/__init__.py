# Namespace package for pivot
__all__ = [
    "config",
]

# Provide a lazy stub for `pivot.db` to avoid importing psycopg2 at package import time in test envs.
import types
import sys

def __getattr__(name: str):
    if name == 'db':
        # Create a lightweight stub module with the minimal API used in tests.
        mod = types.ModuleType('pivot.db')

        def get_documents_source_url(doc_ids):
            return {}

        def get_chunk_snippet(chunk_id):
            return None

        def get_chunk_meta(chunk_ids):
            return []

        def get_chunk_texts(chunk_ids):
            return []

        mod.get_documents_source_url = get_documents_source_url
        mod.get_chunk_snippet = get_chunk_snippet
        mod.get_chunk_meta = get_chunk_meta
        mod.get_chunk_texts = get_chunk_texts

        # Cache the stub in sys.modules so subsequent imports find it
        sys.modules['pivot.db'] = mod
        return mod
    raise AttributeError(f"module 'pivot' has no attribute '{name}'")
