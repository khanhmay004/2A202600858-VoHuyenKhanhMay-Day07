from src import StructureAwareChunker, VietnamesePolicyChunker


def test_splits_by_phan_and_dieu():
    text = (
        "PHẦN I. QUY ĐỊNH CHUNG\n"
        "1. Nguyên tắc chung. Website hoạt động theo pháp luật Việt Nam.\n"
        "2. Định nghĩa. Người bán là Công ty X. Người mua là khách hàng.\n"
        "PHẦN II. QUY TRÌNH GIAO DỊCH\n"
        "1. Đặt hàng qua website. 2. Xác nhận đơn hàng qua điện thoại.\n"
    )
    chunker = VietnamesePolicyChunker(max_chunk_size=600)
    chunks = chunker.chunk_with_metadata(text)

    mucs = {c[1]["muc"] for c in chunks}
    assert mucs == {"I", "II"}

    # Inside Phần I we should see điều 1 and 2 (header line may also produce a dieu=None chunk)
    p1_dieus = {c[1]["dieu"] for c in chunks if c[1]["muc"] == "I"}
    assert {"1", "2"}.issubset(p1_dieus)


def test_chunk_indices_are_unique_and_monotonic():
    text = (
        "PHẦN I. QUY ĐỊNH CHUNG\n"
        "1. A.\n"
        "2. B.\n"
        "PHẦN II. QUY TRÌNH\n"
        "1. C.\n"
    )
    chunks = VietnamesePolicyChunker().chunk_with_metadata(text)
    indices = [m["chunk_index"] for _, m in chunks]
    assert indices == list(range(len(chunks)))


def test_table_is_kept_intact():
    text = (
        "PHẦN III. BIỂU PHÍ\n"
        "1. Bảng giá.\n"
        "| Khoảng giá | Phí |\n"
        "| --- | --- |\n"
        "| 1-2 triệu | 100.000 |\n"
        "| 2-5 triệu | 200.000 |\n"
        "| 5-10 triệu | 300.000 |\n"
    )
    chunks = VietnamesePolicyChunker(max_chunk_size=50).chunk(text)
    # Some chunk must contain all 3 price rows (table never split)
    has_full_table = any(
        "1-2 triệu" in c and "2-5 triệu" in c and "5-10 triệu" in c for c in chunks
    )
    assert has_full_table


def test_chunk_returns_strings_only():
    text = "PHẦN I. ABC\n1. câu mở đầu. câu thứ hai.\n"
    chunks = VietnamesePolicyChunker().chunk(text)
    assert all(isinstance(c, str) for c in chunks)
    assert len(chunks) >= 1


def test_empty_text_returns_empty_list():
    assert VietnamesePolicyChunker().chunk("") == []
    assert VietnamesePolicyChunker().chunk("   \n  ") == []


# --- StructureAwareChunker -------------------------------------------------


def test_structure_keeps_markdown_table_intact():
    text = (
        "# Pricing\n\n"
        "Some intro paragraph that explains the table below.\n\n"
        "| Plan | Price |\n"
        "| --- | --- |\n"
        "| Free | 0 |\n"
        "| Pro | 10 |\n"
        "| Enterprise | 100 |\n\n"
        "Closing remark after the table.\n"
    )
    chunks = StructureAwareChunker(max_chunk_size=80).chunk(text)
    # Some chunk must contain the entire table (3 rows + header)
    assert any(
        "Free | 0" in c and "Pro | 10" in c and "Enterprise | 100" in c for c in chunks
    )


def test_structure_keeps_code_block_intact():
    code = "```python\nfor i in range(100):\n    print(i)\n    do_something(i)\n```"
    text = f"Intro line.\n\n{code}\n\nFollow-up paragraph."
    chunks = StructureAwareChunker(max_chunk_size=40).chunk(text)
    assert any("```python" in c and "```" in c.rstrip()[-4:] for c in chunks)


def test_structure_keeps_list_together_when_it_fits():
    text = (
        "Header paragraph.\n\n"
        "- item one\n"
        "- item two\n"
        "- item three\n"
        "- item four\n\n"
        "Next paragraph.\n"
    )
    chunks = StructureAwareChunker(max_chunk_size=200).chunk_with_metadata(text)
    # Exactly one chunk should carry the list block; that chunk's text contains all 4 items.
    list_chunks = [c for c, m in chunks if "list" in m["block_types"]]
    assert list_chunks
    assert all(
        all(it in c for it in ["item one", "item two", "item three", "item four"])
        for c in list_chunks
    )


def test_structure_metadata_records_block_types_and_index():
    text = (
        "# Title\n\n"
        "First paragraph.\n\n"
        "| a | b |\n| --- | --- |\n| 1 | 2 |\n"
    )
    chunks = StructureAwareChunker(max_chunk_size=10_000).chunk_with_metadata(text)
    # With a very large max_chunk_size everything packs into one chunk.
    assert len(chunks) == 1
    _, meta = chunks[0]
    assert meta["chunk_index"] == 0
    assert set(meta["block_types"]) >= {"heading", "paragraph", "table"}


def test_structure_oversized_protected_block_kept_whole():
    big_table = "| col |\n| --- |\n" + "\n".join(f"| row-{i} |" for i in range(50))
    chunks = StructureAwareChunker(max_chunk_size=100).chunk_with_metadata(big_table)
    # Even though the table is far longer than max_chunk_size, it must remain one chunk.
    assert len(chunks) == 1
    body, meta = chunks[0]
    assert meta.get("oversized") is True
    assert body.count("row-") == 50
