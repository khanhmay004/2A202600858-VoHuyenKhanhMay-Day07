"""Benchmark 4 chunking strategies on Cellphones policy docs (Vietnamese).

For each strategy:
  - chunk all 6 source docs (doc-level metadata: doc_id, category, source_url, lang)
  - load chunks into an EmbeddingStore backed by LocalEmbedder (multilingual)
  - run 5 benchmark queries in two modes:
      (a) search             — no metadata filter
      (b) search_with_filter — narrows by the query's `category`
  - count hit@3 (expected doc_id appears in top-3 doc_ids of mode (a))

Output is a Markdown report appropriate for pasting into REPORT.md Section 6.

Usage:
    python scripts/run_benchmark.py            # prints to stdout
    python scripts/run_benchmark.py --out F    # also writes to file F
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    LocalEmbedder,
    RecursiveChunker,
    SentenceChunker,
    StructureAwareChunker,
    VietnamesePolicyChunker,
)
from src.custom_chunking import StructureAwareChunker as SAC
from src.custom_chunking import VietnamesePolicyChunker as VPC


# ---------------------------------------------------------------------------
# Source data definition
# ---------------------------------------------------------------------------

DATA_DIR = ROOT / "data" / "cellphones"

DOCS_META: list[dict] = [
    {
        "file": "tos.md",
        "doc_id": "tos",
        "category": "tos",
        "source_url": "https://cellphones.com.vn/tos",
    },
    {
        "file": "chinh_sach_giao_hang.md",
        "doc_id": "chinh_sach_giao_hang",
        "category": "delivery",
        "source_url": "https://cellphones.com.vn/chinh-sach-giao-hang",
    },
    {
        "file": "chinh_sach_khui_hop_apple.md",
        "doc_id": "chinh_sach_khui_hop_apple",
        "category": "unbox_apple",
        "source_url": "https://cellphones.com.vn/chinh-sach-khui-hop-apple",
    },
    {
        "file": "quy_dinh_sao_luu_du_lieu.md",
        "doc_id": "quy_dinh_sao_luu_du_lieu",
        "category": "data_backup",
        "source_url": "https://cellphones.com.vn/quy-dinh-ve-viec-sao-luu-du-lieu",
    },
    {
        "file": "bieu_phi_bao_hanh_mo_rong.md",
        "doc_id": "bieu_phi_bao_hanh_mo_rong",
        "category": "warranty_fee",
        "source_url": "https://cellphones.com.vn/bieu-phi-bao-hanh-mo-rong",
    },
    {
        "file": "huong_dan_mua_tra_gop.md",
        "doc_id": "huong_dan_mua_tra_gop",
        "category": "installment",
        "source_url": "https://cellphones.com.vn/huong-dan-mua-hang-tra-gop-bang-the-tin-dung-tai-cellphones",
    },
]


# ---------------------------------------------------------------------------
# Benchmark queries
# ---------------------------------------------------------------------------


@dataclass
class Query:
    text: str
    gold: str
    expected_doc_id: str
    category_filter: str


QUERIES: list[Query] = [
    Query(
        text="Cellphones.com.vn do công ty nào sở hữu và quy định chung là gì?",
        gold="Website do Công ty TNHH Thương mại và Dịch vụ kỹ thuật Diệu Phúc sở hữu, hàng hóa phải đáp ứng quy định nhà nước.",
        expected_doc_id="tos",
        category_filter="tos",
    ),
    Query(
        text="Phí giao hàng nội thành Hà Nội như thế nào?",
        gold="Khu vực Hà Nội nội thành giao nhanh 1-2 giờ trong bán kính 10km; ngoại thành 24-48 giờ.",
        expected_doc_id="chinh_sach_giao_hang",
        category_filter="delivery",
    ),
    Query(
        text="Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành không?",
        gold="Khách phải để nhân viên Cellphones khui hộp tại cửa hàng để đảm bảo điều kiện bảo hành.",
        expected_doc_id="chinh_sach_khui_hop_apple",
        category_filter="unbox_apple",
    ),
    Query(
        text="Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 đến 20 triệu là bao nhiêu?",
        gold="Khoảng 18.000.001 - 20.000.000: 1 đổi 1 VIP 6 tháng = 900.000đ; 12 tháng = 1.200.000đ.",
        expected_doc_id="bieu_phi_bao_hanh_mo_rong",
        category_filter="warranty_fee",
    ),
    Query(
        text="Mua trả góp qua thẻ tín dụng tại Cellphones cần điều kiện gì?",
        gold="Trả góp 0% qua thẻ tín dụng các ngân hàng hỗ trợ, đơn hàng đủ điều kiện về giá trị tối thiểu.",
        expected_doc_id="huong_dan_mua_tra_gop",
        category_filter="installment",
    ),
]


# ---------------------------------------------------------------------------
# Chunking strategies under test
# ---------------------------------------------------------------------------


def build_strategies() -> dict[str, object]:
    return {
        "fixed_size_300":     FixedSizeChunker(chunk_size=300, overlap=30),
        "by_sentences_3":     SentenceChunker(max_sentences_per_chunk=3),
        "recursive_300":      RecursiveChunker(chunk_size=300),
        "structure_aware_600": SAC(max_chunk_size=600),
        "custom_vn_policy":   VPC(max_chunk_size=600),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_source_docs() -> list[dict]:
    docs = []
    for meta in DOCS_META:
        path = DATA_DIR / meta["file"]
        if not path.exists():
            print(f"!! missing {path}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        # Strip leading HTML comments / front-matter
        text = re.sub(r"^<!--.*?-->\s*", "", text, flags=re.S)
        docs.append({**meta, "content": text})
    return docs


def chunked_documents(source_docs: list[dict], chunker) -> list[Document]:
    out: list[Document] = []
    for src in source_docs:
        text = src["content"]
        if isinstance(chunker, (VPC, SAC)):
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


def hit3(results: list[dict], expected_doc_id: str) -> bool:
    return any(r["metadata"].get("doc_id") == expected_doc_id for r in results[:3])


def summarize_chunk(text: str, n: int = 90) -> str:
    s = re.sub(r"\s+", " ", text).strip()
    return s[:n] + ("…" if len(s) > n else "")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=str, default=None, help="Optional path to write report to.")
    ap.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    model = os.getenv("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    print(f"[embedder] {model}", file=sys.stderr)
    embedder = LocalEmbedder(model_name=model)

    sources = load_source_docs()
    print(f"[data] {len(sources)} source docs loaded", file=sys.stderr)

    lines: list[str] = []
    lines.append("# Benchmark — Cellphones Policy Retrieval")
    lines.append("")
    lines.append(f"- Embedder: `{model}`")
    lines.append(f"- Docs: {len(sources)}  |  Queries: {len(QUERIES)}  |  top_k: {args.top_k}")
    lines.append("")

    summary_rows: list[tuple[str, int, int, int, float]] = []  # (strategy, n_chunks, hit_search, hit_filter, avg_len)

    for strat_name, chunker in build_strategies().items():
        t0 = time.time()
        docs = chunked_documents(sources, chunker)
        avg_len = sum(len(d.content) for d in docs) / max(1, len(docs))
        store = EmbeddingStore(collection_name=f"bench_{strat_name}", embedding_fn=embedder)
        store.add_documents(docs)
        t1 = time.time()

        lines.append(f"## Strategy `{strat_name}`")
        lines.append("")
        lines.append(f"- Total chunks: **{len(docs)}**  |  avg chunk length: **{avg_len:.0f}** chars  |  index time: {t1-t0:.1f}s")
        lines.append("")
        lines.append("| # | Query | Mode | Top-1 doc | Top-1 score | Top-3 docs | Hit@3 | Top-1 chunk |")
        lines.append("|---|-------|------|-----------|------------:|------------|:-----:|-------------|")

        hit_search = 0
        hit_filter = 0
        for i, q in enumerate(QUERIES, start=1):
            res_a = store.search(q.text, top_k=args.top_k)
            res_b = store.search_with_filter(
                q.text, top_k=args.top_k, metadata_filter={"category": q.category_filter}
            )

            def fmt(res, mode_label):
                if not res:
                    return f"| {i} | {q.text[:55]} | {mode_label} | (none) | - | - | n | - |"
                top1 = res[0]
                top1_doc = top1["metadata"].get("doc_id", "?")
                top3 = "/".join(r["metadata"].get("doc_id", "?") for r in res[:3])
                hit = "Y" if hit3(res, q.expected_doc_id) else "n"
                return f"| {i} | {q.text[:55]} | {mode_label} | `{top1_doc}` | {top1['score']:.3f} | {top3} | {hit} | {summarize_chunk(top1['content'])} |"

            lines.append(fmt(res_a, "search"))
            lines.append(fmt(res_b, "filter"))

            if hit3(res_a, q.expected_doc_id):
                hit_search += 1
            if hit3(res_b, q.expected_doc_id):
                hit_filter += 1

        lines.append("")
        lines.append(f"**Hit@3 (search)** = {hit_search}/{len(QUERIES)}    "
                     f"**Hit@3 (filter)** = {hit_filter}/{len(QUERIES)}")
        lines.append("")

        summary_rows.append((strat_name, len(docs), hit_search, hit_filter, avg_len))

    lines.append("## Summary")
    lines.append("")
    lines.append("| Strategy | # chunks | avg chunk len | Hit@3 (search) | Hit@3 (filter) |")
    lines.append("|----------|---------:|--------------:|---------------:|---------------:|")
    for name, n, hs, hf, al in summary_rows:
        lines.append(f"| `{name}` | {n} | {al:.0f} | {hs}/{len(QUERIES)} | {hf}/{len(QUERIES)} |")
    lines.append("")

    report = "\n".join(lines) + "\n"
    sys.stdout.write(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"[wrote] {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
