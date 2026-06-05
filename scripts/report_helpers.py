"""Generate data needed to fill REPORT sections 3, 5, 7."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from src import (
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    LocalEmbedder,
    RecursiveChunker,
    SentenceChunker,
    StructureAwareChunker,
    VietnamesePolicyChunker,
    compute_similarity,
)


def section_3_baseline(file_path: str):
    text = Path(file_path).read_text(encoding="utf-8")
    text = re.sub(r"^<!--.*?-->\s*", "", text, flags=re.S)
    print(f"\n### Baseline ChunkingStrategyComparator on {file_path}  ({len(text)} chars)\n")
    result = ChunkingStrategyComparator().compare(text, chunk_size=300)
    for name, info in result.items():
        print(f"  {name:14s} -> count={info['count']:4d}  avg_length={info['avg_length']:.0f}")

    # Also custom strategies
    for name, chunker in [
        ("VietnamesePolicyChunker(600)", VietnamesePolicyChunker(max_chunk_size=600)),
        ("StructureAwareChunker(600)", StructureAwareChunker(max_chunk_size=600)),
    ]:
        chunks = chunker.chunk(text)
        avg = sum(len(c) for c in chunks) / max(1, len(chunks))
        print(f"  {name:30s} -> count={len(chunks):4d}  avg_length={avg:.0f}")


def section_5_similarity():
    model = os.getenv("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    emb = LocalEmbedder(model_name=model)
    print(f"\n### Section 5 — similarity pairs (model={model})\n")
    pairs = [
        # (sentence_A, sentence_B, prediction_label, predicted_score_range)
        ("Khách hàng có thể đổi trả sản phẩm trong 30 ngày",
         "Người mua được phép hoàn trả hàng hóa trong vòng một tháng",
         "HIGH (paraphrase, cùng intent)", "0.55–0.75"),
        ("Khui hộp iPhone mới mua tại cửa hàng",
         "Mở seal sản phẩm Apple để kiểm tra thẩm mỹ",
         "HIGH (cùng nội dung, từ vựng khác)", "0.50–0.70"),
        ("Phí bảo hành mở rộng cho điện thoại 20 triệu",
         "Giá gói extended warranty cho smartphone hai mươi triệu đồng",
         "HIGH (vi/en mixed, cùng ý)", "0.55–0.70"),
        ("Sao lưu dữ liệu iCloud trước khi gửi máy bảo hành",
         "Cellphones có chính sách giao hàng miễn phí nội thành",
         "LOW (cùng domain nhưng ý khác)", "0.20–0.40"),
        ("Mua trả góp 0% qua thẻ tín dụng",
         "Công thức nấu phở bò Hà Nội truyền thống",
         "VERY LOW (khác domain hoàn toàn)", "0.05–0.20"),
    ]
    print("| # | Sentence A | Sentence B | Dự đoán | Khoảng dự đoán | Actual |")
    print("|---|-----------|-----------|---------|----------------|-------:|")
    for i, (a, b, pred, rng) in enumerate(pairs, 1):
        s = compute_similarity(emb(a), emb(b))
        print(f"| {i} | {a} | {b} | {pred} | {rng} | **{s:+.3f}** |")


def section_7_failure_analysis():
    """Examine `by_sentences_3` failure on query 5 (trả góp vs giao hàng)."""
    print("\n### Section 7 — Failure: SentenceChunker on query 5\n")
    model = os.getenv("LOCAL_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    emb = LocalEmbedder(model_name=model)

    delivery = Path("data/cellphones/chinh_sach_giao_hang.md").read_text(encoding="utf-8")
    delivery = re.sub(r"^<!--.*?-->\s*", "", delivery, flags=re.S)
    install = Path("data/cellphones/huong_dan_mua_tra_gop.md").read_text(encoding="utf-8")
    install = re.sub(r"^<!--.*?-->\s*", "", install, flags=re.S)

    sc = SentenceChunker(max_sentences_per_chunk=3)
    delivery_chunks = sc.chunk(delivery)
    install_chunks = sc.chunk(install)

    q = "Mua trả góp qua thẻ tín dụng tại Cellphones cần điều kiện gì?"
    qv = emb(q)

    # Score every chunk
    scored = []
    for c in delivery_chunks:
        scored.append(("delivery", c, compute_similarity(qv, emb(c))))
    for c in install_chunks:
        scored.append(("installment", c, compute_similarity(qv, emb(c))))
    scored.sort(key=lambda r: -r[2])

    print("Top-5 chunks by similarity to query `'Mua trả góp qua thẻ tín dụng...'`:\n")
    print("| Rank | Source | Score | Chunk preview |")
    print("|-----:|--------|------:|---------------|")
    for i, (src, c, s) in enumerate(scored[:5], 1):
        preview = re.sub(r"\s+", " ", c)[:120]
        print(f"| {i} | {src} | {s:.3f} | {preview}… |")

    # Top-1 chunk length & analysis
    top1 = scored[0]
    print(f"\nTop-1 chunk length: {len(top1[1])} chars")
    print(f"Contains 'thẻ tín dụng'? {'thẻ tín dụng' in top1[1]}")
    print(f"Contains '10 triệu'? {'10 triệu' in top1[1]}")


if __name__ == "__main__":
    section_3_baseline("data/cellphones/tos.md")
    section_3_baseline("data/cellphones/bieu_phi_bao_hanh_mo_rong.md")
    section_3_baseline("data/cellphones/chinh_sach_giao_hang.md")
    section_5_similarity()
    section_7_failure_analysis()
