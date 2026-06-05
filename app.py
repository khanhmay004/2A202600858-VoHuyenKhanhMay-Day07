"""Streamlit demo for the Cellphones RAG knowledge base.

Run:
    streamlit run app.py

Features
--------
- Pick an embedder (Mock=fast, Local=multilingual sentence-transformers).
- Pick one or more chunking strategies; each gets its own EmbeddingStore.
- Enter a question -> see top-k chunks per strategy, side by side, with citations
  back to the real source documents.
- Optional category filter to narrow the search.
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from src import (  # noqa: E402
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    LocalEmbedder,
    MockEmbedder,
    RecursiveChunker,
    SentenceChunker,
    StructureAwareChunker,
    VietnamesePolicyChunker,
)

DATA_DIR = ROOT / "data" / "cellphones"

DOCS_META = [
    {"file": "tos.md", "doc_id": "tos", "category": "tos",
     "source_url": "https://cellphones.com.vn/tos"},
    {"file": "chinh_sach_giao_hang.md", "doc_id": "chinh_sach_giao_hang", "category": "delivery",
     "source_url": "https://cellphones.com.vn/chinh-sach-giao-hang"},
    {"file": "chinh_sach_khui_hop_apple.md", "doc_id": "chinh_sach_khui_hop_apple", "category": "unbox_apple",
     "source_url": "https://cellphones.com.vn/chinh-sach-khui-hop-apple"},
    {"file": "quy_dinh_sao_luu_du_lieu.md", "doc_id": "quy_dinh_sao_luu_du_lieu", "category": "data_backup",
     "source_url": "https://cellphones.com.vn/quy-dinh-ve-viec-sao-luu-du-lieu"},
    {"file": "bieu_phi_bao_hanh_mo_rong.md", "doc_id": "bieu_phi_bao_hanh_mo_rong", "category": "warranty_fee",
     "source_url": "https://cellphones.com.vn/bieu-phi-bao-hanh-mo-rong"},
    {"file": "huong_dan_mua_tra_gop.md", "doc_id": "huong_dan_mua_tra_gop", "category": "installment",
     "source_url": "https://cellphones.com.vn/huong-dan-mua-hang-tra-gop-bang-the-tin-dung-tai-cellphones"},
]

STRATEGIES = {
    "fixed_size_300": lambda: FixedSizeChunker(chunk_size=300, overlap=30),
    "by_sentences_3": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive_300": lambda: RecursiveChunker(chunk_size=300),
    "structure_aware_600": lambda: StructureAwareChunker(max_chunk_size=600),
    "custom_vn_policy": lambda: VietnamesePolicyChunker(max_chunk_size=600),
}


# ---------- data loading & chunking ----------------------------------------


@st.cache_data(show_spinner=False)
def load_sources() -> list[dict]:
    docs = []
    for meta in DOCS_META:
        path = DATA_DIR / meta["file"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"^<!--.*?-->\s*", "", text, flags=re.S)
        docs.append({**meta, "content": text})
    return docs


def chunk_documents(sources: list[dict], chunker) -> list[Document]:
    out: list[Document] = []
    for src in sources:
        text = src["content"]
        if isinstance(chunker, (VietnamesePolicyChunker, StructureAwareChunker)):
            pieces = chunker.chunk_with_metadata(text)
        else:
            pieces = [(p, {}) for p in chunker.chunk(text)]
        for i, (piece, extra) in enumerate(pieces):
            md = {
                "doc_id": src["doc_id"],
                "category": src["category"],
                "source_url": src["source_url"],
                "lang": "vi",
                **extra,
            }
            out.append(Document(id=f"{src['doc_id']}#{i}", content=piece, metadata=md))
    return out


# ---------- embedder + store builders --------------------------------------


@st.cache_resource(show_spinner="Loading embedder…")
def get_embedder(kind: str):
    if kind == "Local (multilingual, ~120MB)":
        model = os.getenv("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        return LocalEmbedder(model_name=model)
    return MockEmbedder()


@st.cache_resource(show_spinner=False)
def build_store(strategy_name: str, embedder_kind: str) -> tuple[EmbeddingStore, int, float]:
    """Return (store, n_chunks, build_seconds). Cached per (strategy, embedder)."""
    embedder = get_embedder(embedder_kind)
    chunker = STRATEGIES[strategy_name]()
    sources = load_sources()
    t0 = time.time()
    docs = chunk_documents(sources, chunker)
    store = EmbeddingStore(
        collection_name=f"ui_{strategy_name}_{embedder_kind}",
        embedding_fn=embedder,
    )
    store.add_documents(docs)
    return store, len(docs), time.time() - t0


# ---------- formatting helpers ---------------------------------------------


def format_citation(meta: dict) -> str:
    doc_id = meta.get("doc_id", "?")
    muc = meta.get("muc")
    dieu = meta.get("dieu")
    parts = [doc_id]
    if muc:
        parts.append(f"PHẦN {muc}")
    if dieu:
        parts.append(f"Điều {dieu}")
    label = " · ".join(parts)
    url = meta.get("source_url", "#")
    return f"[{label}]({url})"


def snippet(text: str, n: int = 280) -> str:
    s = re.sub(r"\s+", " ", text).strip()
    return s if len(s) <= n else s[:n] + "…"


# ---------- UI -------------------------------------------------------------


st.set_page_config(page_title="Cellphones RAG Demo", layout="wide")
st.title("📱 Cellphones RAG Demo")
st.caption(
    "Truy vấn knowledge base (6 tài liệu chính sách Cellphones tiếng Việt). "
    "So sánh top-k kết quả từ nhiều chunking strategies, kèm citation về nguồn gốc."
)

with st.sidebar:
    st.header("⚙️ Cấu hình")

    embedder_kind = st.radio(
        "Embedder",
        options=["Mock (fast, demo only)", "Local (multilingual, ~120MB)"],
        index=0,
        help="Mock dùng hash MD5 — chạy ngay. Local tải sentence-transformers lần đầu (~30s).",
    )

    strategies_selected = st.multiselect(
        "Chunking strategies",
        options=list(STRATEGIES.keys()),
        default=["recursive_300", "structure_aware_600", "custom_vn_policy"],
        help="Mỗi strategy build 1 vector store riêng. Chọn tối đa 3–4 để layout dễ nhìn.",
    )

    top_k = st.slider("Top-K", min_value=1, max_value=10, value=3)

    categories = ["(không lọc)"] + sorted({m["category"] for m in DOCS_META})
    category = st.selectbox("Lọc theo category", categories, index=0)

    st.divider()
    st.markdown("**📚 Knowledge base**")
    for m in DOCS_META:
        st.markdown(f"- `{m['doc_id']}` ({m['category']})")

query = st.text_input(
    "Câu hỏi",
    placeholder="VD: Phí giao hàng nội thành Hà Nội như thế nào?",
)

col_btn, col_examples = st.columns([1, 4])
with col_btn:
    run = st.button("🔎 Tìm kiếm", type="primary", use_container_width=True)
with col_examples:
    examples = [
        "Phí giao hàng nội thành Hà Nội như thế nào?",
        "Tôi có thể tự khui hộp iPhone mà vẫn được bảo hành không?",
        "Mua trả góp qua thẻ tín dụng cần điều kiện gì?",
        "Phí bảo hành mở rộng cho điện thoại 18-20 triệu?",
    ]
    chosen = st.selectbox("Hoặc thử câu hỏi mẫu", [""] + examples, index=0, label_visibility="collapsed")
    if chosen and not query:
        query = chosen

if run or (query and chosen):
    if not query.strip():
        st.warning("Hãy nhập câu hỏi trước.")
    elif not strategies_selected:
        st.warning("Chọn ít nhất 1 chunking strategy ở sidebar.")
    else:
        meta_filter = None if category == "(không lọc)" else {"category": category}

        # Build/get stores (cached after first call)
        stores: dict[str, tuple[EmbeddingStore, int, float]] = {}
        with st.spinner(f"Indexing {len(strategies_selected)} strateg(y/ies)…"):
            for name in strategies_selected:
                stores[name] = build_store(name, embedder_kind)

        st.markdown(f"### Kết quả cho: _{query}_")
        if meta_filter:
            st.caption(f"🔖 Lọc category = `{category}`")

        cols = st.columns(len(strategies_selected))
        for col, name in zip(cols, strategies_selected):
            store, n_chunks, build_sec = stores[name]
            with col:
                st.subheader(f"`{name}`")
                st.caption(f"{n_chunks} chunks · index {build_sec:.1f}s")

                t0 = time.time()
                if meta_filter:
                    results = store.search_with_filter(query, top_k=top_k, metadata_filter=meta_filter)
                else:
                    results = store.search(query, top_k=top_k)
                query_ms = (time.time() - t0) * 1000

                st.caption(f"⏱ query {query_ms:.0f} ms · {len(results)} hits")

                if not results:
                    st.info("Không có kết quả.")
                    continue

                for rank, r in enumerate(results, start=1):
                    score = r["score"]
                    meta = r["metadata"]
                    with st.container(border=True):
                        st.markdown(f"**#{rank}** · score `{score:.3f}` · {format_citation(meta)}")
                        st.markdown(snippet(r["content"]))
                        with st.expander("Full chunk + metadata"):
                            st.code(r["content"], language="markdown")
                            st.json(meta)
else:
    st.info("Nhập câu hỏi và bấm **Tìm kiếm** để bắt đầu.")
