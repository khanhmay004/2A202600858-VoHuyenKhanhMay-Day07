from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            self._client = chromadb.Client()
            try:
                self._collection = self._client.get_or_create_collection(name=collection_name)
            except Exception:
                self._collection = self._client.create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata) if doc.metadata else {}
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }
        return record

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        if not records:
            return []
        query_vec = self._embedding_fn(query)
        scored: list[dict[str, Any]] = []
        for rec in records:
            score = _dot(query_vec, rec["embedding"])
            scored.append(
                {
                    "id": rec["id"],
                    "content": rec["content"],
                    "metadata": rec["metadata"],
                    "score": score,
                }
            )
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            if self._use_chroma and self._collection is not None:
                try:
                    self._collection.add(
                        ids=[f"{doc.id}_{self._next_index}"],
                        documents=[doc.content],
                        embeddings=[record["embedding"]],
                        metadatas=[record["metadata"]],
                    )
                except Exception:
                    pass
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        def matches(rec: dict[str, Any]) -> bool:
            meta = rec.get("metadata") or {}
            return all(meta.get(k) == v for k, v in metadata_filter.items())

        filtered = [r for r in self._store if matches(r)]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        before = len(self._store)
        self._store = [
            r for r in self._store if (r.get("metadata") or {}).get("doc_id") != doc_id
        ]
        removed = before - len(self._store)
        if removed > 0 and self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass
        return removed > 0
