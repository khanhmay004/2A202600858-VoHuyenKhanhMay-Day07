from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)

        if not results:
            context_block = "(no relevant context found)"
        else:
            lines = []
            for idx, r in enumerate(results, start=1):
                source = (r.get("metadata") or {}).get("doc_id", r.get("id", "unknown"))
                lines.append(f"[{idx}] (source={source}) {r['content']}")
            context_block = "\n".join(lines)

        prompt = (
            "Answer the question using ONLY the context below. "
            "If the answer is not in the context, say you don't know.\n\n"
            f"Context:\n{context_block}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
