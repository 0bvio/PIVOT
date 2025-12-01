import sys
sys.path.insert(0, 'src')

from pivot.api import main as api_main
from pivot.api.main import QueryReq
from pivot import adapters, db


def test_query_pipeline_monkeypatch(monkeypatch):
    # Patch milvus_adapter.search to return two hits
    def fake_search(project_id, query_vector, top_k=25):
        # return list of (chunk_id, score, doc_id, idx)
        return [
            ("c1", 0.8, "d1", 0),
            ("c2", 0.75, "d2", 0),
        ]

    monkeypatch.setattr(adapters.milvus_adapter, 'search', fake_search)

    # Patch db.get_documents_source_url and get_chunk_snippet
    monkeypatch.setattr(db, 'get_documents_source_url', lambda ids: {"d1": "http://a", "d2": "http://b"})
    monkeypatch.setattr(db, 'get_chunk_snippet', lambda cid: "PIVOT is a RAG system." if cid == 'c1' else "Other content.")

    req = QueryReq(project='default', query='What is PIVOT?', top_k=2)
    resp = api_main.query(req)

    assert 'results' in resp
    assert len(resp['results']) == 2
    # ensure rerank_score exists
    assert 'rerank_score' in resp['results'][0]
    # ensure answer included
    assert 'answer' in resp


if __name__ == '__main__':
    # Run test manually
    import pytest
    pytest.main([__file__])

