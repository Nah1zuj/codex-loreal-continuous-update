from typing import Protocol

class Reranker(Protocol):
    def rerank(self, query: str, results: list[dict]) -> list[dict]: ...

class MockReranker:
    def rerank(self, query, results):
        return sorted(results,key=lambda x:x['score'], reverse=True)

class RemoteRerankerAdapter:
    """Extension interface: inject a callable returning ranked result dictionaries."""
    def __init__(self, transport=None):
        self.transport = transport
    def rerank(self, query, results):
        if self.transport is None:
            raise RuntimeError('Remote reranker transport is not configured; use RERANKER_PROVIDER=mock')
        return self.transport(query, results)
