from pivot.services import reranker_service


def test_reranker_basic():
    q = "What is PIVOT?"
    cands = [
        {"chunk_id": "1", "snippet": "PIVOT is a scalable RAG system for ingestion and retrieval."},
        {"chunk_id": "2", "snippet": "This text talks about something else unrelated."},
    ]
    out = reranker_service.rerank(q, cands)
    # Expect chunk 1 to be ranked higher
    assert out[0]["chunk_id"] == "1"


if __name__ == '__main__':
    test_reranker_basic()
    print('test_reranker_basic passed')

