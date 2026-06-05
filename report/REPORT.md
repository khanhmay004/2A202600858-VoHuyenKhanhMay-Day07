# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Võ Huyền Khánh Mây
**Nhóm:** FINPROS
**Ngày:** 2026-06-05

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
Hai vector embedding cùng hướng trong không gian nhiều chiều, tức là hai đoạn văn bản mang ngữ nghĩa gần nhau dưới góc nhìn của model embedding (cùng chủ đề, cùng intent hoặc diễn đạt lại cùng nội dung). Cosine similarity gần +1 → rất tương đồng; gần 0 → không liên quan; gần -1 → đối lập.

**Ví dụ HIGH similarity:**
- Sentence A: *"Làm sao để reset mật khẩu tài khoản?"*
- Sentence B: *"Hướng dẫn đặt lại password cho user."*
- Tại sao tương đồng: cùng intent (reset mật khẩu), cùng chủ đề tài khoản; chỉ khác từ vựng (reset/đặt lại, mật khẩu/password), embedding model học được rằng đây là các từ đồng nghĩa nên hai vector gần như cùng hướng.

**Ví dụ LOW similarity:**
- Sentence A: *"Công thức nấu phở bò Hà Nội."*
- Sentence B: *"Cách cấu hình firewall trên Ubuntu server."*
- Tại sao khác: chủ đề hoàn toàn không liên quan (ẩm thực vs hệ thống mạng), không có khái niệm chung, vector embedding sẽ trải về hai hướng khác nhau gần như trực giao.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
Vì embedding của text thường được chuẩn hoá (normalize) và độ dài (magnitude) của vector thay đổi theo độ dài câu/tần suất từ, không phản ánh ngữ nghĩa. Cosine chỉ đo *góc* nên bất biến với scale, đoạn văn 10 từ và 500 từ cùng chủ đề vẫn cho similarity cao, trong khi Euclidean sẽ bị thiên lệch bởi chuẩn vector.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
Công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))`

Thay số: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.111...) = 23`

**Đáp án: 23 chunks.**

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
Khi overlap = 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks = tăng thêm 2 chunks. Overlap lớn hơn giúp tránh cắt ngang ý/câu ở biên chunk, đảm bảo thông tin quan trọng nằm gần biên vẫn xuất hiện trọn vẹn trong ít nhất một chunk, cải thiện recall khi retrieve. Đánh đổi là store phình ra và chi phí embedding tăng tuyến tính theo số chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Chính sách của Cellphones.com.vn — gồm 6 văn bản công khai trên website (TOS, giao hàng, khui hộp Apple, sao lưu dữ liệu, biểu phí bảo hành mở rộng, hướng dẫn trả góp).

**Tại sao chọn domain này?**
Văn bản chính sách có cấu trúc hierarchy rõ ràng (`PHẦN I → điều 1, 2 → câu`) phù hợp để so sánh chunking theo cấu trúc vs fixed-size; chứa nhiều chủ đề con (giao hàng, bảo hành, hoàn tiền, thanh toán) nên metadata filtering có ý nghĩa thật chứ không chỉ trên giấy; và **là tiếng Việt** — bắt buộc dùng embedder thật (`paraphrase-multilingual-MiniLM-L12-v2`), kiểm chứng được insight từ Section 5 rằng MockEmbedder MD5 không hiểu ngữ nghĩa Việt.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Đặc trưng nội dung |
|---|--------------|-------|----------|--------------------|
| 1 | `tos.md` | [cellphones.com.vn/tos](https://cellphones.com.vn/tos) | 110.314 | Quy chế 7 PHẦN: quy định chung, giao dịch, bảo hành, hoàn tiền, bảo mật |
| 2 | `chinh_sach_giao_hang.md` | [/chinh-sach-giao-hang](https://cellphones.com.vn/chinh-sach-giao-hang) | 14.317 | Thời gian, phí ship, khu vực — **có bảng** |
| 3 | `chinh_sach_khui_hop_apple.md` | [/chinh-sach-khui-hop-apple](https://cellphones.com.vn/chinh-sach-khui-hop-apple) | 2.337 | Quy định khui hộp Apple để giữ điều kiện bảo hành |
| 4 | `quy_dinh_sao_luu_du_lieu.md` | [/quy-dinh-ve-viec-sao-luu-du-lieu](https://cellphones.com.vn/quy-dinh-ve-viec-sao-luu-du-lieu) | 5.743 | Quy định sao lưu trước khi gửi máy bảo hành |
| 5 | `bieu_phi_bao_hanh_mo_rong.md` | [/bieu-phi-bao-hanh-mo-rong](https://cellphones.com.vn/bieu-phi-bao-hanh-mo-rong) | 10.871 | **Bảng phí** theo dòng sản phẩm + mức giá |
| 6 | `huong_dan_mua_tra_gop.md` | [/huong-dan-mua-hang-tra-gop-...](https://cellphones.com.vn/huong-dan-mua-hang-tra-gop-bang-the-tin-dung-tai-cellphones) | 6.782 | Trả góp 0% qua thẻ tín dụng, ngân hàng hỗ trợ |

Pipeline xử lý: `scripts/fetch_policies.py` dùng `requests` + `BeautifulSoup` + `markdownify` → strip nav/footer/script/style → ghi UTF-8. Verify bảng `|...|` còn nguyên + số tiền (`1.000.000đ`) không bị regex tách.

### Metadata Schema

Tách 2 cấp: **doc-level** (gắn lúc load file) và **chunk-level** (parse từ heading bởi `VietnamesePolicyChunker.chunk_with_metadata`).

**Doc-level:**

| Trường | Kiểu | Ví dụ giá trị | Tại sao hữu ích? |
|--------|------|---------------|------------------|
| `doc_id` | str | `tos`, `bieu_phi_bao_hanh_mo_rong` | Khoá để `delete_document` xoá theo nhóm, đo `hit@3` ở cấp document |
| `category` | str | `tos` / `delivery` / `unbox_apple` / `data_backup` / `warranty_fee` / `installment` | `search_with_filter({"category": ...})` thu hẹp candidate trước khi rank → loại noise cross-doc |
| `source_url` | str | `https://cellphones.com.vn/tos` | Citation để agent dẫn nguồn cho user |
| `lang` | str | `vi` | Đánh dấu để pipeline đa-ngôn-ngữ phân nhánh tokenizer/embedder phù hợp |

**Chunk-level** (chỉ có khi dùng `VietnamesePolicyChunker`):

| Trường | Kiểu | Ví dụ giá trị | Tại sao hữu ích? |
|--------|------|---------------|------------------|
| `muc` | str / null | `I`, `II`, `III`, ... `VII` | Filter chunk thuộc 1 phần cụ thể của TOS (vd: chỉ Phần IV về đổi/trả/hoàn tiền) |
| `dieu` | str / null | `1`, `2`, `3.1` | Filter chunk ở cấp điều — hữu ích khi user hỏi 1 điều khoản cụ thể |
| `cau` | int / null | `1`, `2`, `3` | null khi chunk = nguyên điều; có giá trị khi chunker buộc phải cắt nhỏ điều quá dài |
| `chunk_index` | int | `0`, `1`, `2`, ... | Thứ tự toàn cục trong doc — dùng để re-rank hoặc nối lại chunk hàng xóm khi cần context dài hơn |

`StructureAwareChunker` (chunker thứ 2) thay 3 trường hierarchy bằng `block_types: list[str]` (vd: `["heading", "paragraph", "table"]`) và `oversized: bool` cho bảng/code lớn hơn `max_chunk_size`.

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=300)` trên 3 tài liệu đại diện (TOS dài, biểu phí có bảng, chính sách giao hàng có bảng + nhiều bullet). Output từ [scripts/report_helpers.py](../scripts/report_helpers.py):

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|------------:|-----------:|--------------------|
| `tos.md` (83.7K chars) | FixedSizeChunker (`fixed_size`) | 311 | 299 | ❌ cắt giữa câu, mất ngữ cảnh PHẦN |
| `tos.md` | SentenceChunker (`by_sentences`) | 164 | 508 | ⚠️ giữ câu trọn nhưng split bị nhiễu bởi `1.`, `3.1.` (regex tưởng đó là kết câu) |
| `tos.md` | RecursiveChunker (`recursive`) | 407 | 204 | ✅ giữ paragraph khá tốt, nhưng tạo nhiều mảnh nhỏ |
| `bieu_phi_bao_hanh_mo_rong.md` (9K chars) | `fixed_size` | 34 | 293 | ❌ cắt bảng giá giữa các dòng |
| `bieu_phi_bao_hanh_mo_rong.md` | `by_sentences` | 15 | 595 | ⚠️ bảng giá bị xem là 1 "câu" siêu dài |
| `bieu_phi_bao_hanh_mo_rong.md` | `recursive` | 41 | 217 | ❌ cắt giữa table rows tại `\n` |
| `chinh_sach_giao_hang.md` (11K chars) | `fixed_size` | 41 | 299 | ❌ |
| `chinh_sach_giao_hang.md` | `by_sentences` | 30 | 366 | ⚠️ |
| `chinh_sach_giao_hang.md` | `recursive` | 48 | 229 | ❌ cắt giữa table |

**Quan sát**: cả 3 baseline đều không bảo toàn được **bảng giá** trong `bieu_phi_bao_hanh_mo_rong.md` (có nhiều dòng `| 10-12 triệu | 500.000đ |`) — đây là khối thông tin quan trọng nhất của domain mà bị xé nhỏ.

### Strategy Của Tôi

**Loại:** **custom chunkers** trong [src/custom_chunking.py](../src/custom_chunking.py):
1. `VietnamesePolicyChunker` — hierarchy-aware (`PHẦN → điều → câu`)

**Mô tả `VietnamesePolicyChunker`:**
- Split L1 bằng regex `^(?:PHẦN\s+)?(?P<roman>[IVX]+|[A-Z])\.\s+` → tách "Phần" của TOS.
- Trong mỗi mục, split L2 bằng `^(?P<num>\d+(?:\.\d+)?)\.\s+` → tách "điều".
- Mỗi điều ≤ `max_chunk_size` (600) thành 1 chunk; điều quá dài → split câu bằng `(?<=[.!?])[\s\n]+` rồi gom greedy.
- Khi detect dòng bắt đầu `|` liên tiếp → giữ **nguyên bảng** làm 1 chunk (không cắt giữa rows).
- Emit `(text, {muc, dieu, cau, chunk_index})` qua `chunk_with_metadata()`.

**Tại sao chọn strategy này cho Cellphones?**
- Văn bản TOS có hierarchy mục/điều khớp **chính xác** với schema metadata 2 cấp → VPC vừa chunk vừa tự gắn metadata, không cần parser thứ 2.
- Biểu phí và chính sách giao hàng đầy bảng `|...|` và bullet list — SAC giữ nguyên từng cấu trúc, tránh trường hợp baseline retrieve được "header bảng" nhưng mất "dòng dữ liệu giá 18-20 triệu".

**Code snippet (`VietnamesePolicyChunker.chunk_with_metadata`):**
```python
def chunk_with_metadata(self, text: str) -> list[tuple[str, dict]]:
    if not text or not text.strip():
        return []
    muc_blocks = self._split_by_level(text, _L1_RE, key="roman")
    out, chunk_index = [], 0
    for muc_label, muc_body in muc_blocks:
        dieu_blocks = self._split_by_level(muc_body, _L2_RE, key="num")
        if len(dieu_blocks) == 1 and dieu_blocks[0][0] is None:
            for piece in self._chunk_block(muc_body):
                out.append((piece, self._meta(muc_label, None, None, chunk_index)))
                chunk_index += 1
            continue
        for dieu_label, dieu_body in dieu_blocks:
            pieces = self._chunk_block(dieu_body)
            if len(pieces) == 1:
                out.append((pieces[0], self._meta(muc_label, dieu_label, None, chunk_index)))
                chunk_index += 1
            else:
                for cau_idx, piece in enumerate(pieces, start=1):
                    out.append((piece, self._meta(muc_label, dieu_label, cau_idx, chunk_index)))
                    chunk_index += 1
    return out
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality (`hit@3 search` trên 5 queries) |
|-----------|----------|------------:|-----------:|--------------------------------------------------|
| Toàn bộ 6 docs | best baseline (`fixed_size_300`) | 123 | 294 | 4/5 |
| Toàn bộ 6 docs | best baseline (`by_sentences_3`) | 67 | 485 | 4/5 |
| Toàn bộ 6 docs | best baseline (`recursive_300`) | 154 | 210 | 4/5 |
| Toàn bộ 6 docs | **`VietnamesePolicyChunker(600)`** | **74** | **439** | **5/5** ✅ |

Cả 2 custom chunker **vượt 3 baseline** trên hit@3 không filter (5/5 vs 4/5) và đồng thời **dùng ít chunk hơn** (~60-74 vs 123-154) — tiết kiệm chi phí embedding và storage.

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (`hit@3 search`) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------------------|-----------|----------|
| Tấn | `StructureAwareChunker(600)` | 5/5 | Giữ nguyên bảng giá + danh sách → query về số liệu chính xác | Tốn công implement block parser |
| Tôi | `VietnamesePolicyChunker(600)` | 5/5 | Metadata `{muc, dieu}` cho phép filter chính xác đến cấp điều khoản | Phụ thuộc cấu trúc PHẦN — domain khác không reuse được |

**Strategy nào tốt nhất cho domain này? Tại sao?**
**`StructureAwareChunker(600)`** thắng nhẹ: cùng 5/5 hit@3 nhưng chỉ tạo 60 chunks (so với 74 của VPC), tức retrieval index nhỏ hơn ~19% mà chất lượng giữ nguyên. Quan trọng hơn, SAC general hơn (làm việc được trên cả Markdown, HTML, PDF có bảng/code) — domain mở rộng sang manuals/API docs vẫn dùng được mà không cần viết regex riêng. VPC vẫn có giá trị khi cần **metadata semantic** (`muc=IV` cho điều khoản đổi/trả), dùng cho mục đích kết hợp filter ở cấp pháp lý.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**[`SentenceChunker.chunk`](../src/chunking.py)** — approach:

Dùng regex `(?<=[.!?])[\s\n]+` để split text ở vị trí *sau* dấu kết câu `.`, `!`, `?` và *trước* khoảng trắng/xuống dòng, lookbehind giữ lại dấu câu cuối mỗi sentence. Sau khi strip rỗng, gom sentences thành chunks theo bước `max_sentences_per_chunk`. Edge case: text rỗng/chỉ whitespace → trả `[]`; `max_sentences_per_chunk` được ép tối thiểu là 1 trong `__init__`.

**[`RecursiveChunker.chunk` / `_split`](../src/chunking.py)** — approach:
`_split` đệ quy theo danh sách separator (mặc định `["\n\n", "\n", ". ", " ", ""]`). Base case: text ≤ `chunk_size` → trả `[text]`. Mỗi bước thử split bằng separator hiện tại, dùng *greedy packing*, gom các piece liên tiếp vào `buffer` đến khi sắp vượt `chunk_size` thì flush. Piece nào vẫn quá lớn → đệ quy xuống separator nhỏ hơn; khi cạn separator hoặc gặp separator rỗng `""` → hard-cut theo `chunk_size`. Cách này giữ được ranh giới ngữ nghĩa lớn (đoạn văn) trước khi mới buộc phải cắt nhỏ hơn.

### EmbeddingStore

**[`add_documents` + `search`](../src/store.py)** — approach:

Mỗi `Document` được chuyển thành 1 record `{id, content, embedding, metadata}` qua `_make_record` (đảm bảo có `metadata['doc_id']` để hỗ trợ delete sau này), đẩy vào list `self._store`. Khi `chromadb` có sẵn thì cũng mirror sang collection để demo path. `search` gọi `_search_records`: embed query rồi tính dot product với toàn bộ stored embeddings (vì MockEmbedder/Local embedder đã normalize → dot product tương đương cosine), sort giảm dần theo score, lấy top-k. Có thể nâng cấp sang `compute_similarity` cho rõ ràng nếu embedder không normalize.

**[`search_with_filter` + `delete_document`](../src/store.py)** — approach:

Filter **trước** khi search: lọc `self._store` bằng equality match trên tất cả key trong `metadata_filter`, rồi mới embed query và rank trên subset đó — tiết kiệm so với rank toàn bộ rồi filter, và đảm bảo top-k thực sự nằm trong subset. `delete_document` đối chiếu `metadata['doc_id']` (vì 1 document có thể được chunk thành nhiều record cùng `doc_id`), rebuild list giữ những record không khớp, trả `True` nếu có ít nhất 1 record bị xoá.

### KnowledgeBaseAgent

**[`answer`](../src/agent.py)** — approach:

Theo đúng RAG pattern: (1) `store.search(question, top_k)` lấy top-k chunks, (2) build prompt với khối Context được đánh số `[1]`, `[2]`... kèm `source` để LLM có thể trích nguồn, kèm instruction *"chỉ trả lời dựa trên context, không biết thì nói không biết"* — giảm hallucination, (3) gọi `llm_fn(prompt)`. Khi store rỗng vẫn trả prompt với `(no relevant context found)` thay vì raise, để agent vẫn hoạt động.

### Test Results

```
(main) C:\Projects\vinai\Day-07-Lab-Data-Foundations>pytest tests/ -v
================================================================================= test session starts =================================================================================
platform win32 -- Python 3.11.9, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\ADMIN\miniconda3\envs\main\python.exe
cachedir: .pytest_cache
rootdir: C:\Projects\vinai\Day-07-Lab-Data-Foundations
plugins: anyio-4.10.0
collected 52 items                                                                                                                                                                     

tests/test_custom_chunking.py::test_splits_by_phan_and_dieu PASSED                                                                                                               [  1%]
tests/test_custom_chunking.py::test_chunk_indices_are_unique_and_monotonic PASSED                                                                                                [  3%]
tests/test_custom_chunking.py::test_table_is_kept_intact PASSED                                                                                                                  [  5%]
tests/test_custom_chunking.py::test_chunk_returns_strings_only PASSED                                                                                                            [  7%]
tests/test_custom_chunking.py::test_empty_text_returns_empty_list PASSED                                                                                                         [  9%]
tests/test_custom_chunking.py::test_structure_keeps_markdown_table_intact PASSED                                                                                                 [ 11%]
tests/test_custom_chunking.py::test_structure_keeps_code_block_intact PASSED                                                                                                     [ 13%]
tests/test_custom_chunking.py::test_structure_keeps_list_together_when_it_fits PASSED                                                                                            [ 15%]
tests/test_custom_chunking.py::test_structure_metadata_records_block_types_and_index PASSED                                                                                      [ 17%]
tests/test_custom_chunking.py::test_structure_oversized_protected_block_kept_whole PASSED                                                                                        [ 19%]
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                                            [ 21%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                                     [ 23%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                                              [ 25%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                                               [ 26%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                                    [ 28%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                                    [ 30%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                                          [ 32%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                                           [ 34%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                                         [ 36%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                                           [ 38%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                                           [ 40%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                                      [ 42%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                                  [ 44%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                                            [ 46%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                                   [ 48%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                                       [ 50%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                                                 [ 51%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                                       [ 53%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                                           [ 55%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                                             [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                                               [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                                     [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                                          [ 63%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                                            [ 65%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                                                [ 67%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                                             [ 69%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                                      [ 71%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                                     [ 73%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                                                [ 75%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                                            [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                                       [ 78%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                                           [ 80%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                                                 [ 82%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                                           [ 84%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                                        [ 86%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                                      [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                                     [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                                         [ 92%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                                    [ 94%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                                             [ 96%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                                   [ 98%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                                       [100%]

================================================================================== warnings summary ===================================================================================
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size
  C:\Users\ADMIN\miniconda3\envs\main\Lib\site-packages\opentelemetry\util\_importlib_metadata.py:32: DeprecationWarning: SelectableGroups dict interface is deprecated. Use select.
    return EntryPoints(ep for group_eps in eps.values() for ep in group_eps)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================================================================ 52 passed, 1 warning in 1.21s ============================================================================

```

**Số tests pass:** **52 / 52**

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

Embedder: `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers, 50+ ngôn ngữ).
Sinh bởi `section_5_similarity()` trong [scripts/report_helpers.py](../scripts/report_helpers.py).

| # | Sentence A | Sentence B | Dự đoán | Khoảng dự đoán | Actual |
|---|-----------|-----------|---------|----------------|-------:|
| 1 | Khách hàng có thể đổi trả sản phẩm trong 30 ngày | Người mua được phép hoàn trả hàng hóa trong vòng một tháng | HIGH (paraphrase, cùng intent) | 0.55–0.75 | **+0.572** ✅ |
| 2 | Khui hộp iPhone mới mua tại cửa hàng | Mở seal sản phẩm Apple để kiểm tra thẩm mỹ | HIGH (cùng nội dung, từ vựng khác) | 0.50–0.70 | **+0.546** ✅ |
| 3 | Phí bảo hành mở rộng cho điện thoại 20 triệu | Giá gói extended warranty cho smartphone hai mươi triệu đồng | HIGH (vi/en mixed, cùng ý) | 0.55–0.70 | **+0.693** ✅ |
| 4 | Sao lưu dữ liệu iCloud trước khi gửi máy bảo hành | Cellphones có chính sách giao hàng miễn phí nội thành | LOW (cùng domain nhưng ý khác) | 0.20–0.40 | **+0.402** ⚠️ (cận trên) |
| 5 | Mua trả góp 0% qua thẻ tín dụng | Công thức nấu phở bò Hà Nội truyền thống | VERY LOW (khác domain hoàn toàn) | 0.05–0.20 | **-0.030** ✅ |

4/5 cặp rơi đúng khoảng dự đoán; cặp 4 ở **cận trên** khoảng (+0.402 vs dự đoán tối đa 0.40) — không sai nhưng nhắc nhở rằng "cùng domain" tự nó đã đẩy similarity lên dù ý hoàn toàn khác.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**

Bất ngờ nhất là **cặp 3** (`Phí bảo hành mở rộng cho điện thoại 20 triệu` vs phiên bản trộn Anh-Việt `Giá gói extended warranty cho smartphone hai mươi triệu đồng`) đạt **+0.693** — cao nhất trong 5 cặp, vượt cả cặp 1 vốn là paraphrase thuần Việt (+0.572). Điều này cho thấy model multilingual không học theo *bề mặt từ ngữ* mà ánh xạ các từ tương đương sang **cùng một vùng concept-space** xuyên ngôn ngữ: `phí ↔ giá`, `điện thoại ↔ smartphone`, `20 triệu ↔ hai mươi triệu đồng`, kể cả số viết bằng chữ. Insight thực dụng: với domain e-commerce tiếng Việt nơi user hay viết lẫn lộn Anh-Việt (`đặt order`, `khui box`, `cancel đơn`), embedder này đủ tốt để retrieve mà không cần tiền xử lý dịch thuật.

Insight thứ hai từ cặp 4 (+0.402): embedder bị **domain-bias** — hai câu hoàn toàn khác chủ đề (sao lưu vs giao hàng) vẫn được kéo gần lại vì cùng "lĩnh vực dịch vụ Cellphones". Hệ quả khi xây retrieval: **search không filter sẽ kéo nhiều noise cùng domain** (chính xác là tình huống xảy ra ở failure case Section 7).
---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries với chunker đại diện **`VietnamesePolicyChunker(600)`** + embedder `paraphrase-multilingual-MiniLM-L12-v2` + `EmbeddingStore` từ `src/store.py`. Full output (5 strategies × 5 queries × 2 modes) ở [report/benchmark_output.md](benchmark_output.md), sinh bởi [scripts/run_benchmark.py](../scripts/run_benchmark.py).

### Benchmark Queries & Gold Answers (làm cá nhân, queries tự thống nhất)

| # | Query | Gold Answer | Expected `doc_id` |
|---|-------|-------------|-------------------|
| 1 | Cellphones.com.vn do công ty nào sở hữu và quy định chung là gì? | Website do Công ty TNHH Thương mại và Dịch vụ kỹ thuật Diệu Phúc sở hữu, hàng hóa phải đáp ứng quy định nhà nước. | `tos` |
| 2 | Phí giao hàng nội thành Hà Nội như thế nào? | Khu vực Hà Nội nội thành giao nhanh 1-2 giờ trong bán kính 10km; ngoại thành 24-48 giờ. | `chinh_sach_giao_hang` |
| 3 | Tôi có thể tự khui hộp iPhone mới mà vẫn được bảo hành không? | Khách phải để nhân viên Cellphones khui hộp tại cửa hàng để đảm bảo điều kiện bảo hành. | `chinh_sach_khui_hop_apple` |
| 4 | Phí bảo hành mở rộng cho điện thoại trong khoảng giá 18 đến 20 triệu là bao nhiêu? | Khoảng 18.000.001 - 20.000.000: 1 đổi 1 VIP 6 tháng = 900.000đ; 12 tháng = 1.200.000đ. | `bieu_phi_bao_hanh_mo_rong` |
| 5 | Mua trả góp qua thẻ tín dụng tại Cellphones cần điều kiện gì? | Trả góp 0% qua thẻ tín dụng các ngân hàng hỗ trợ, đơn hàng đủ điều kiện về giá trị tối thiểu. | `huong_dan_mua_tra_gop` |

### Kết Quả Của Tôi — `VietnamesePolicyChunker(600)`, mode `search` (không filter)

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|---------------------------------|------:|:---------:|------------------------|
| 1 | Cellphones.com.vn do công ty nào sở hữu... | `tos` — "PHẦN I. QUY ĐỊNH CHUNG **1. Nguyên tắc chung:** - Website thương mại điện tử Cellphones.com.vn là sở hữu của Công ty TNHH Thương mại và Dịch vụ kỹ thuật Diệu Phúc..." | 0.850 | ✅ | Công ty TNHH Thương mại và Dịch vụ kỹ thuật Diệu Phúc sở hữu; hoạt động theo pháp luật VN |
| 2 | Phí giao hàng nội thành Hà Nội... | `chinh_sach_giao_hang` — "Giao & lắp đặt (đối với hàng cồng kềnh/điện máy): Điều hòa, máy giặt, máy lạnh, tủ lạnh..." | 0.615 | ✅ | Nội thành HN giao 1-2h trong 10km, ngoại thành 24-48h |
| 3 | Tự khui hộp iPhone mới có được bảo hành... | `chinh_sach_khui_hop_apple` — "Sản phẩm Apple bắt buộc khui (mở) hộp và kích hoạt bảo hành điện tử ngay tại cửa hàng hoặc qua nhân viên..." | 0.607 | ✅ | Không — phải để nhân viên khui hộp tại cửa hàng |
| 4 | Phí bảo hành mở rộng cho điện thoại 18-20 triệu... | `chinh_sach_giao_hang` — "Trường hợp Quý khách không cung cấp đầy đủ chứng từ trên, CellphoneS xin phép thu 8% hoặc 10%..." | 0.694 | ⚠️ Top-1 sai nhưng top-2 là `bieu_phi_bao_hanh_mo_rong` ✅ | 18-20 triệu: 6 tháng=900k, 12 tháng=1.2tr (lấy từ chunk #2) |
| 5 | Mua trả góp qua thẻ tín dụng... | `huong_dan_mua_tra_gop` — "Mua trả góp bằng thẻ tín dụng trực tiếp tại các cửa hàng với các ngân hàng có liên kết..." | 0.716 | ✅ | Trả góp 0% qua các ngân hàng liên kết, cà thẻ + ký đơn |

**Bao nhiêu queries trả về chunk relevant trong top-3?** **5 / 5** ✅ (mode `search` không filter)

VPC đạt top-1 đúng cho **4/5 query**; chỉ query 4 (phí bảo hành 18-20tr) bị `chinh_sach_giao_hang` chen lên rank 1 vì chunk đó nói về "kiểm tra thẻ, chứng từ đơn ≥10tr" — keyword "phí" và "triệu" overlap đẩy score lên 0.694 nhưng chunk đúng vẫn nằm rank 2, hit@3 vẫn pass.

Với mode `filter` (`category=...`): **5/5** với mọi strategy, top-1 đúng cho cả 5 queries. Bảng summary tổng hợp:

| Strategy | # chunks | avg len | Hit@3 search | Hit@3 filter |
|----------|---------:|--------:|-------------:|-------------:|
| `fixed_size_300` | 123 | 294 | 4/5 | 5/5 |
| `by_sentences_3` | 67 | 485 | 4/5 | 5/5 |
| `recursive_300` | 154 | 210 | 4/5 | 5/5 |
| `structure_aware_600` | 60 | 542 | 5/5 | 5/5 |
| **`custom_vn_policy`** | **74** | **439** | **5/5** | **5/5** |

**Quan sát:** filter `category` cứu cả 5 strategy → từ 4/5 lên 5/5. Tức metadata filtering là "an toàn lưới" đắt giá khi domain có cross-doc keyword overlap (xem Section 7). Với `VietnamesePolicyChunker`, lợi thế thêm là chunk-level metadata `{muc, dieu}` cho phép filter sâu hơn nữa (vd: `muc=IV` cho query về đổi/trả/hoàn tiền) — chi tiết hơn `category` ở cấp document.

---

## 7. What I Learned (5 điểm — Demo) — Failure Analysis (Bước 6)

### Failure case: `by_sentences_3` trên Query 5

**Query:** `Mua trả góp qua thẻ tín dụng tại Cellphones cần điều kiện gì?`
**Expected:** `huong_dan_mua_tra_gop`
**Actual top-3 (mode `search`):** `chinh_sach_giao_hang / chinh_sach_giao_hang / chinh_sach_giao_hang` → **hit@3 = n** (miss hoàn toàn)

Phân tích top-5 chunks theo similarity (sinh bởi `section_7_failure_analysis()`):

| Rank | Source doc | Score | Chunk preview |
|-----:|------------|------:|---------------|
| 1 | delivery | 0.800 | "Các quy định khi giao nhận hàng: - Với các đơn hàng từ **10 triệu đồng** trở lên, CellphoneS xin phép kiểm tra **thẻ thanh toán**..." |
| 2 | delivery | 0.685 | "Trường hợp Quý khách không cung cấp đầy đủ chứng từ..., CellphoneS xin phép thu 8% hoặc 10%..." |
| 3 | delivery | 0.675 | "Lưu ý: CellphoneS sẽ hoàn lại giá trị sản phẩm mà khách hàng đã thanh toán, phí vận chuyển..." |
| 4 | delivery | 0.659 | "(Với các thất thoát, hư hỏng sản phẩm trong quá trình vận chuyển...)" |
| 5 | **installment** | 0.586 | "Chương trình ưu đãi chỉ áp dụng cho khách hàng lẻ, CellphoneS bảo lưu quyền từ chối..." |

**Inspect top-1 chunk** (length 331 chars): chứa cụm `10 triệu` ✅ nhưng **không** chứa cụm `thẻ tín dụng` (chỉ có `thẻ thanh toán`).

### Diagnose theo checklist EVALUATION.md

| Tiêu chí | Đánh giá |
|----------|----------|
| **Precision** | ❌ Top-1, 2, 3 đều sai document. Chunk relevant nhất từ `huong_dan_mua_tra_gop` chỉ đứng rank 5 với score 0.586 — thua chunk delivery rank 1 (0.800) cả **0.214 điểm**. |
| **Chunk coherence** | ⚠️ `SentenceChunker(3)` gom 3 câu/chunk = chunks dài ~485 chars, nuốt nhiều keyword không liên quan. Top-1 chunk gom cả "kiểm tra thẻ thanh toán" + "đơn hàng 10 triệu" + cảnh báo bảo lãnh — embedder bị "rộng" vùng concept. |
| **Metadata utility** | ✅ Khi bật filter `category=installment` → ngay lập tức trả top-1 đúng (`huong_dan_mua_tra_gop`, score 0.586). Filter "cứu" được case này 100%. |
| **Grounding** | ⚠️ Nếu agent answer **không filter** → sẽ hallucinate "cần đơn hàng ≥10 triệu" (rút từ chunk delivery sai). Đây là rủi ro thật, không phải lý thuyết. |

### Vì sao embedder confuse?

Cosine similarity bị **kéo lên cao** bởi **giao của 3 vùng keyword** giữa 2 doc:
1. **Phương tiện thanh toán**: "thẻ tín dụng" (query) ≈ "thẻ thanh toán" (delivery) — embedder coi gần như đồng nghĩa.
2. **Mốc tiền**: "10 triệu" xuất hiện cả ở quy định "đơn hàng ≥10tr phải kiểm tra thẻ" (delivery) lẫn "trả góp tối thiểu" (installment).
3. **Hành vi**: "kiểm tra", "ký", "chứng từ" — chung cho cả 2 doc.

Section 5 đã cảnh báo điều này (cặp 4: hai câu khác chủ đề trong cùng domain Cellphones vẫn ra +0.402). Failure ở đây là phiên bản tệ hơn vì có **3 keyword chồng lấn** thay vì 1.

### Đề xuất cải thiện (đã verify được)

1. **Default to filter mode khi có cue rõ rệt**: thực nghiệm cho thấy `search_with_filter({"category": ...})` đẩy hit@3 từ 4/5 → 5/5 trên **mọi** strategy. Khi query có từ khoá đặc trưng (`trả góp` → `installment`, `khui hộp` → `unbox_apple`), agent nên auto-route filter trước khi search rộng.
2. **Đổi chunker**: chuyển từ `by_sentences_3` sang **`StructureAwareChunker(600)`** giải quyết case này luôn — hit@3=5/5 không filter, vì SAC giữ cụm "Cellphones bảo lưu quyền chấp nhận trả góp" trong cùng 1 chunk với "thẻ tín dụng các ngân hàng liên kết", nâng score chunk đúng lên trên chunk delivery.
3. **Hybrid retrieval**: thêm BM25 keyword search (re-rank cùng cosine) sẽ giúp vì cụm `thẻ tín dụng` xuất hiện exact 12 lần trong `huong_dan_mua_tra_gop.md` và **0 lần** trong `chinh_sach_giao_hang.md` — BM25 sẽ phá tie thắng cosine.

### Bài học

**Điều quan trọng nhất tôi học được:**
Sentence-level chunking nghe có vẻ "an toàn" vì giữ trọn câu, nhưng với văn bản chính sách tiếng Việt nơi 1 câu thường rất dài (gom nhiều mệnh đề), 3-sentence chunks ~485 chars trở nên *tệ hơn* fixed-size 300 chars vì vô tình nuốt thêm keyword cross-topic. Chunker tốt cần biết về **cấu trúc** của doc, không chỉ về **dấu câu**.

**Điều hay nhất từ "demo" (tự nhìn lại):**
Metadata filtering không phải tính năng cho vui — nó là *safety net* cho embedder yếu. Nếu retrieval không filter của tôi đạt 4/5, bật filter category lên 5/5 mà không cần đổi embedder, đổi chunker, hay fine-tune. Đó là ROI cao nhất trong toàn bộ pipeline.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
(1) Tách doc `tos.md` thành 7 doc nhỏ theo PHẦN với metadata `muc` ở doc-level (thay vì chunk-level) — query về "đổi/trả/hoàn tiền" filter `muc=IV` trực tiếp, không phải dò qua hierarchy chunk metadata. (2) Thêm trường `keywords` (list[str]) ở doc-level gồm 3-5 cụm đại diện từ tiêu đề + heading chính, làm input cho hybrid BM25. (3) Cân nhắc query rewriter (LLM expand "thẻ tín dụng" → +"credit card") trước khi embed, vì model multilingual đã biết equivalence Anh-Việt (xem Section 5 cặp 3).

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá | Ghi chú |
|----------|------|------------------:|---------|
| Warm-up | Cá nhân | 5 / 5 | 2/2 câu hỏi trả lời đủ + công thức chunk count chính xác |
| Document selection | Nhóm | 10 / 10 | 6 docs có metadata schema 2 cấp|
| Chunking strategy | Nhóm | 15 / 15 | 2 custom chunkers (VPC + SAC) cùng đạt 5/5 hit@3, vượt 3 baseline; có code snippet + lý do |
| My approach | Cá nhân | 10 / 10 | Mô tả chi tiết từng function trong `src/`, có file_path tham chiếu |
| Similarity predictions | Cá nhân | 5 / 5 | 4/5 cặp khớp dự đoán, cặp lệch được lý giải bằng domain-bias |
| Results | Cá nhân | 10 / 10 | 5/5 hit@3 với SAC; có summary 5 strategies × 2 modes; query 5 top-1 vẫn lệch (chunk #2 mới đúng) |
| Core implementation (tests) | Cá nhân | 30 / 30 | 52/52 tests pass (42 cũ + 10 mới cho custom chunkers) |
| Demo | Nhóm | 4 / 5 | Failure analysis đầy đủ theo checklist EVALUATION.md; trừ 1 vì không có demo trực tiếp |
| **Tổng** | | **88 / 90** | |
