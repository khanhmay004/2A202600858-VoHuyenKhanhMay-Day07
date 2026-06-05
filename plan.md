# Plan — Lab 7 Part 3: So Sánh Retrieval Strategy (Cellphones.com.vn policies)

## Context

Part 1 (Warm-up) và Part 2 (Core Coding) đã hoàn tất trong turn trước: 42/42 tests pass, các section 1/4/5 của report đã điền. Còn lại **Part 3 — So Sánh Retrieval Strategy** với 5 sub-exercises (3.0 → 3.5) và 4 section báo cáo trống (2, 3, 6, 7).

User chọn **domain: chính sách Cellphones.com.vn**, gồm 6 URL:
- `https://cellphones.com.vn/tos` — Quy chế hoạt động website (TOS, 7 phần — đã bao gồm cả `?part=refund-policy`)
- `https://cellphones.com.vn/chinh-sach-giao-hang` — Chính sách giao hàng
- `https://cellphones.com.vn/chinh-sach-khui-hop-apple` — Chính sách khui hộp sản phẩm Apple
- `https://cellphones.com.vn/quy-dinh-ve-viec-sao-luu-du-lieu` — Quy định về sao lưu dữ liệu
- `https://cellphones.com.vn/bieu-phi-bao-hanh-mo-rong` — **Biểu phí bảo hành mở rộng** (có bảng phí, số)
- `https://cellphones.com.vn/huong-dan-mua-hang-tra-gop-bang-the-tin-dung-tai-cellphones` — Hướng dẫn mua trả góp qua thẻ tín dụng

Tại sao chọn domain này tốt cho lab:
- Văn bản chính sách có **cấu trúc rõ ràng** (Phần I-VII, gạch đầu dòng) → test được chunking strategy theo cấu trúc vs fixed-size
- Có **nhiều chủ đề con** (giao hàng / bảo hành / hoàn tiền / bảo mật / thanh toán) → metadata filtering có ý nghĩa thật
- Là **tiếng Việt** → bắt buộc dùng embedder thật (mock MD5 không hiểu tiếng Việt), trùng với insight đã rút ra ở Section 5

Outcome mong muốn: hoàn thiện toàn bộ REPORT.md (Section 2/3/5/6/7), có script benchmark chạy được, có ít nhất 1 failure case có ý nghĩa để phân tích.

---

## Phương án thực thi

### Bước 1 — Chuẩn bị dữ liệu (Exercise 3.0)

Tạo **6 file** trong `data/cellphones/` — gộp toàn bộ nội dung mỗi URL vào **1 file duy nhất**, KHÔNG tách theo từng phần:

| # | Filename | Nguồn URL | Nội dung tổng quan |
|---|----------|-----------|--------------------|
| 1 | `tos.md` | `/tos` | Toàn bộ 7 phần Quy chế: quy định chung, quy trình giao dịch, bảo hành, hủy/đổi/hoàn tiền, bảo mật Cellphones, bảo mật Sforum, dịch vụ Sforum |
| 2 | `chinh_sach_giao_hang.md` | `/chinh-sach-giao-hang` | Thời gian giao, phí ship, khu vực, điều kiện giao hàng (có thể có **bảng**) |
| 3 | `chinh_sach_khui_hop_apple.md` | `/chinh-sach-khui-hop-apple` | Quy định khui hộp sản phẩm Apple để đảm bảo bảo hành |
| 4 | `quy_dinh_sao_luu_du_lieu.md` | `/quy-dinh-ve-viec-sao-luu-du-lieu` | Quy định sao lưu dữ liệu trước khi sửa chữa/bảo hành |
| 5 | `bieu_phi_bao_hanh_mo_rong.md` | `/bieu-phi-bao-hanh-mo-rong` | **Bảng phí bảo hành mở rộng** theo dòng sản phẩm + mức giá — nhiều số, định dạng tiền tệ |
| 6 | `huong_dan_mua_tra_gop.md` | `/huong-dan-mua-hang-tra-gop-bang-the-tin-dung-tai-cellphones` | Hướng dẫn mua trả góp 0% qua thẻ tín dụng, điều kiện, ngân hàng hỗ trợ |

**Cách fetch — viết script `scripts/fetch_policies.py`** (recommended path):
- Cài thêm `pip install requests beautifulsoup4 markdownify` (nhẹ, phổ biến, không phức tạp)
- Pipeline: `requests.get(url)` → `BeautifulSoup` parse → **strip** các phần tử nav/footer/sidebar/script/style/button "Liên hệ"/social-share → lấy content chính (target div nội dung) → `markdownify` để giữ heading + bullet → ghi `data/cellphones/{name}.md`
- **Pre-processing rõ ràng** sau khi convert:
  - Bỏ heading trùng (vd: header trang lặp lại trong sidebar)
  - Chuẩn hoá whitespace: collapse `\n{3,}` thành `\n\n`
  - Bỏ ký tự đặc biệt rác (`•` lạ, `\xa0` nbsp...)
  - Đảm bảo encoding UTF-8 khi `Path.write_text(content, encoding="utf-8")`
  - **Giữ nguyên bảng** (`bieu_phi_bao_hanh_mo_rong`, có thể cả `chinh_sach_giao_hang`): `markdownify` mặc định convert `<table>` thành markdown table (`| col | col |`). Verify cú pháp đúng; nếu bảng bị flatten → custom handler: detect `<table>` trước khi convert, render thủ công thành `| ... |` rows
  - **Giữ nguyên số có dấu**: regex check số tiền (`1.000.000đ`, `1,000,000`), không vô tình thay `\.` bằng newline; verify sau clean rằng các con số quan trọng vẫn còn trong file
- Fallback nếu fetch fail (site chặn UA / dùng SPA): copy-paste thủ công vào file `.md`, dùng cùng pre-processing pipeline (tách script `clean_text.py`)

**Metadata schema** — tách 2 cấp: **doc-level** (gắn lúc load file) và **chunk-level** (parse từ heading trong chunk khi pre-chunk):

Doc-level (trong `Document.metadata` khi load file):

| Field | Kiểu | Giá trị có thể | Mục đích |
|-------|------|----------------|----------|
| `doc_id` | str | `tos`, `chinh_sach_giao_hang`, `khui_hop_apple`, `sao_luu_du_lieu`, `bao_hanh_mo_rong`, `tra_gop` | Khoá để delete/group |
| `category` | str | `tos` / `delivery` / `unbox_apple` / `data_backup` / `warranty_fee` / `installment` | Filter theo loại văn bản |
| `source` | str | path file | Truy nguồn |
| `source_url` | str | URL gốc | Citation |
| `lang` | str | `vi` | Đánh dấu tiếng Việt |

Chunk-level — hierarchy **mục → điều → câu** (parse từ heading trong text khi pre-chunk):

| Field | Kiểu | Giá trị có thể | Mục đích |
|-------|------|----------------|----------|
| `muc` | str / null | `I` / `II` / `III` / ... / `VII` / `A` / `B` (cấp 1, viết hoa La Mã hoặc chữ cái) | Cấp ngoài cùng — "Phần" trong TOS hoặc section chính |
| `dieu` | str / null | `1` / `2` / `3` / `3.1` / `3.2` (cấp 2, số) | "Điều" / mục số bên trong mục cấp 1 |
| `cau` | int / null | 1, 2, 3... | Số thứ tự **câu** trong điều (null nếu chunk = nguyên điều, có giá trị khi chunker cắt nhỏ hơn 1 điều) |
| `chunk_index` | int | 0, 1, 2... | Thứ tự chunk toàn cục trong document |

→ Ví dụ chunk thuộc Phần III, điều 2 của TOS: `{"muc": "III", "dieu": "2", "cau": null, "chunk_index": 12}`
→ Ví dụ chunk là câu thứ 3 trong Phần IV điều 1 (do chunker chia nhỏ): `{"muc": "IV", "dieu": "1", "cau": 3, "chunk_index": 18}`

→ **Điền REPORT Section 2** với bảng inventory + metadata schema.

### Bước 2 — Verify embedder (user đã cài sentence-transformers)

User đã cài sẵn `sentence-transformers`. Chỉ cần verify + chọn model tốt cho tiếng Việt:

```bash
# Verify local embedder hoạt động
python -c "from src import LocalEmbedder; e=LocalEmbedder(); print(len(e('giao hàng miễn phí toàn quốc')))"
```

**Khuyến nghị model cho tiếng Việt** (xếp theo độ phù hợp giảm dần):
1. `paraphrase-multilingual-MiniLM-L12-v2` — multilingual, train trên 50+ ngôn ngữ kể cả tiếng Việt → khuyến nghị đầu tiên
2. `all-MiniLM-L6-v2` (default) — chủ yếu English, tiếng Việt yếu nhưng vẫn chạy được
3. **Fallback OpenAI** (user có key): `text-embedding-3-small` qua `OpenAIEmbedder` — chất lượng tốt nhất cho tiếng Việt, đặt `OPENAI_API_KEY` trong `.env` rồi `EMBEDDING_PROVIDER=openai`

Cấu hình `.env`:

```
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

→ Nếu trong quá trình chạy benchmark thấy similarity score quá thấp / hit_rate@3 < 3/5 với cả 2 model local → switch sang OpenAI.

### Bước 3 — Thiết kế custom chunker (Exercise 3.1)

Tạo **`VietnamesePolicyChunker`** trong file mới `src/custom_chunking.py` (KHÔNG sửa `src/chunking.py` để tránh đụng tests).

**Sanity check tiếng Việt trước**: chạy 3 built-in chunker hiện tại trên 1 đoạn tiếng Việt thật từ TOS (có dấu, có `đ`, có ngắt câu `.`, `?`):
- `FixedSizeChunker` — an toàn vì cắt theo ký tự, không phụ thuộc encoding
- `SentenceChunker` — regex `(?<=[.!?])[\s\n]+` vẫn work với tiếng Việt (dấu kết câu giống tiếng Anh)
- `RecursiveChunker` — separators `["\n\n", "\n", ". ", " ", ""]` cũng giữ nguyên hiệu quả
→ Nếu phát hiện chunker cũ break với tiếng Việt (vd: cắt giữa từ ghép, hoặc regex miss), document trong Section 7 và đề xuất fix; không sửa code cũ vì tests đang pass.

**Design rationale `VietnamesePolicyChunker`**: tài liệu chính sách Cellphones có hierarchy 3 cấp khớp với metadata schema (mục → điều → câu):
- **Mục** (cấp 1): `PHẦN I.`, `PHẦN II.`, ... `PHẦN VII.` hoặc `A.`, `B.` (viết hoa La Mã hoặc chữ cái)
- **Điều** (cấp 2): `1.`, `2.`, `3.1`, `3.2` (số)
- **Câu** (cấp 3): các câu kết thúc bởi `.`, `!`, `?` trong một điều — chỉ tách khi điều quá dài

Chunker hoạt động:
1. Split theo regex hierarchy:
   - L1: `\n(?:PHẦN\s+)?[IVX]+\.\s+` hoặc `\n[A-Z]\.\s+` → tách mục
   - L2: `\n\d+(?:\.\d+)?\.\s+` → tách điều
   - L3 (chỉ khi điều > `max_chunk_size`): `(?<=[.!?])[\s\n]+` → tách câu, gom theo `max_chunk_size`
2. Mỗi section là 1 chunk nếu ≤ `max_chunk_size` (mặc định 600)
3. Section quá dài → recurse xuống cấp tiếp theo, cuối cùng fallback `RecursiveChunker` (compose, không inherit)
4. **Output**: giữ interface `chunk(text) -> list[str]` để tương thích `ChunkingStrategyComparator`, **thêm** `chunk_with_metadata(text) -> list[tuple[str, dict]]` trả `(chunk_text, {"muc": "III", "dieu": "2", "cau": null})` để benchmark script gắn metadata chunk-level
5. **Bảng (table)**: nếu detect `|` ở đầu nhiều dòng liên tiếp → giữ nguyên cả bảng làm 1 chunk (không cắt giữa rows) — quan trọng cho `bieu_phi_bao_hanh_mo_rong.md`

→ Kỳ vọng so với 3 built-in:
- Chunk count thấp hơn `recursive`, cao hơn `by_sentences`
- Mỗi chunk gói trọn 1 mục/điều
- Retrieval precision cao hơn vì query về "đổi trả" sẽ match chunk Phần IV thay vì 1 chunk nhỏ giữa Phần III và IV

### Bước 4 — Benchmark queries (Exercise 3.2)

Thống nhất 5 queries (vì làm cá nhân, "nhóm" = chính mình, vẫn cần tuân thủ đề). Expected chunk identify qua `doc_id` + `muc`:

| # | Query | Gold Answer | Expected (doc_id, muc) | Filter |
|---|-------|-------------|------------------------|--------|
| 1 | "Cellphones cho phép đổi trả/hoàn tiền trong bao nhiêu ngày?" | Verify thời hạn từ Phần IV TOS | `tos`, muc=IV | `muc=IV` |
| 2 | "Phí giao hàng tính như thế nào, có khu vực nào miễn phí không?" | Trích bảng phí ship | `chinh_sach_giao_hang` | `category=delivery` |
| 3 | "Cellphones thu thập thông tin cá nhân nào của khách hàng?" | Phần V TOS | `tos`, muc=V | `muc=V` |
| 4 | "Tôi có thể tự khui hộp iPhone mới mua mà vẫn được bảo hành không?" | Chính sách khui hộp Apple | `khui_hop_apple` | `category=unbox_apple` |
| 5 | "Phí bảo hành mở rộng cho iPhone giá 20 triệu là bao nhiêu?" | Trích từ bảng phí bảo hành mở rộng | `bao_hanh_mo_rong` | `category=warranty_fee` |

Yêu cầu: query 1 và 3 đòi hỏi filter theo `muc` (chunk-level), queries 2/4/5 dùng filter `category` (doc-level), query 5 đặc biệt test khả năng retrieve thông tin **từ bảng có số** — tận dụng đủ 2 cấp metadata + edge case dữ liệu bảng.

### Bước 5 — Script benchmark (`scripts/run_benchmark.py`)

File mới chạy được như sau:

```python
# Pseudo-code skeleton
from src import EmbeddingStore, KnowledgeBaseAgent, LocalEmbedder, ...
from src.custom_chunking import VietnamesePolicyChunker

DOCS = load_from_data_cellphones()  # gắn metadata
QUERIES = [...]  # 5 queries + gold answers (chunk id expected)

STRATEGIES = {
    "fixed_size_300": FixedSizeChunker(300, 30),
    "by_sentences_3":  SentenceChunker(3),
    "recursive_300":   RecursiveChunker(chunk_size=300),
    "custom_vn_policy": VietnamesePolicyChunker(max_chunk_size=600),
}

for strategy_name, chunker in STRATEGIES.items():
    store = EmbeddingStore(embedding_fn=LocalEmbedder())
    add_chunked_docs(store, DOCS, chunker)
    for q in QUERIES:
        top3 = store.search(q.text, top_k=3)
        with_filter = store.search_with_filter(q.text, top_k=3, metadata_filter=q.filter)
        # log score, check if expected chunk in top-3 -> count hit_rate
        agent = KnowledgeBaseAgent(store, llm_fn=demo_llm)
        ans = agent.answer(q.text)
```

Output: bảng markdown với cột `[strategy × query → top-1 source, score, hit?]` để paste thẳng vào REPORT Section 6.

### Bước 6 — Failure analysis (Exercise 3.5)

Sau khi chạy benchmark, **chủ động pick 1 case kém nhất**, phân tích theo checklist EVALUATION.md:
- Precision: chunk relevant có ở top-3 không?
- Chunk coherence: chunk có bị cắt giữa câu/ý không?
- Metadata utility: filter giúp hay hại?
- Grounding: agent có hallucinate không?
- Đề xuất cải thiện: tăng chunk_size? Đổi separator? Thêm metadata mới?

→ **Điền REPORT Section 7**.

### Bước 7 — Điền REPORT các section còn lại

- **Section 2** (10đ): bảng inventory + metadata schema + lý do chọn domain
- **Section 3** (15đ): bảng baseline 3 strategies, code snippet `VietnamesePolicyChunker`, bảng so sánh custom vs best baseline. Phần "So sánh với thành viên khác" để placeholder ghi rõ làm cá nhân
- **Section 5** (5đ) — **Exercise 3.3**: 5 pairs tiếng Việt liên quan domain (vd: "đổi trả trong 30 ngày" vs "hoàn tiền trong 1 tháng"), chạy với `LocalEmbedder`, ghi dự đoán & actual score. Lần này score nên có ý nghĩa hơn so với mock ở Part 2
- **Section 6** (10đ): bảng 5 queries với top-1, score, relevant?, agent answer
- **Section 7** (5đ): failure analysis + bài học

---

## To-do list chi tiết (execute phase)

1. **Fetch + clean dữ liệu (Bước 1)** ✅
   - [x] `pip install requests beautifulsoup4 markdownify` + thêm vào `requirements.txt`
   - [x] Tạo folder `data/cellphones/`
   - [x] Viết `scripts/fetch_policies.py`:
     - [x] Hàm `fetch(url) -> str` (HTML raw, set User-Agent Chrome)
     - [x] Hàm `extract_main(html) -> bs4.Tag` (locate div nội dung chính, strip nav/footer/sidebar/script/style/button "Liên hệ"/social-share)
     - [x] Hàm `clean_markdown(md) -> str` (collapse whitespace, remove nbsp, dedupe heading, giữ table syntax + số tiền)
     - [x] Loop 6 URL → ghi `data/cellphones/{slug}.md` với encoding UTF-8
   - [x] Chạy script, verify mỗi file ≥ 1000 ký tự + đọc spot-check để chắc không bị parse rác
   - [x] **Verify riêng cho file có bảng** (`bieu_phi_bao_hanh_mo_rong.md`, `chinh_sach_giao_hang.md`): grep `|` → table syntax còn nguyên, số tiền dạng `1.000.000` giữ đúng
   - [x] Fallback: KHÔNG cần — cả 6 URL fetch thành công với User-Agent Chrome chuẩn

2. **Verify embedder (Bước 2)** ✅
   - [x] Update `.env`: `EMBEDDING_PROVIDER=local`, `LOCAL_EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2`
   - [x] Smoke test (`scripts/smoke_embedder.py`): 4 cặp paraphrase tiếng Việt có avg=0.530 (> 0.50), cặp unrelated=0.253 (< 0.30) → **PASS**, không cần OpenAI fallback
   - [ ] Nếu chuyển OpenAI: `EMBEDDING_PROVIDER=openai`, `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`, đảm bảo `OPENAI_API_KEY` đã set *(không cần — local đủ chất lượng)*

3. **Custom chunker (Bước 3)** ✅
   - [x] Sanity test 3 chunker cũ trên text tiếng Việt — đều chạy được, có 1 quirk: `SentenceChunker` cắt sai khi gặp `Điều 1.` / `1.1.` (dấu `.` sau số làm regex tưởng là kết câu). Document ở Section 7, không sửa code cũ.
   - [x] Tạo `src/custom_chunking.py` với 2 class:
     - `VietnamesePolicyChunker` — hierarchy PHẦN/điều/câu, giữ bảng markdown
     - `StructureAwareChunker` — detect & preserve markdown tables, fenced code blocks, lists, HTML `<table>/<ul>/<ol>/<pre>` blocks; oversized protected blocks vẫn giữ nguyên (không cắt). Hữu ích cho manual/API ref/policy có nhiều bảng + code.
   - [x] Implement `chunk(text)` + `chunk_with_metadata(text)` cho cả 2 (VPC trả `{muc,dieu,cau,chunk_index}`, SAC trả `{chunk_index, block_types, oversized?}`)
   - [x] Viết 10 unit test trong `tests/test_custom_chunking.py` (5 cho VPC, 5 cho SAC) — pass hết, tổng **52/52** tests (42 cũ + 10 mới)
   - [x] Export cả `VietnamesePolicyChunker` và `StructureAwareChunker` trong `src/__init__.py`

4. **Benchmark script (Bước 5)** ✅
   - [x] Tạo `scripts/run_benchmark.py`
   - [x] `load_source_docs()` đọc 6 file md trong `data/cellphones/`, strip front-matter HTML comments, gắn doc-level metadata (`doc_id`, `category`, `source_url`, `lang=vi`)
   - [x] `chunked_documents(sources, chunker)`: nếu chunker là `VietnamesePolicyChunker` thì dùng `chunk_with_metadata` để merge `muc/dieu/cau/chunk_index` vào metadata; ngược lại fallback `chunk(text)` only
   - [x] Define `QUERIES`: 5 query phủ 5 doc khác nhau (tos / delivery / unbox_apple / warranty_fee / installment), mỗi query có `category_filter`
   - [x] Loop 4 strategies × 5 queries × 2 modes (`search` vs `search_with_filter`), in bảng markdown đầy đủ top-1 doc + top-3 docs + hit@3
   - [x] Tính `hit_rate@3` per strategy → bảng summary cuối file
   - [x] Output ra `report/benchmark_output.md`. Kết quả với **5 strategies**: `fixed_size_300` 4/5, `by_sentences_3` 4/5, `recursive_300` 4/5, **`structure_aware_600` 5/5**, **`custom_vn_policy` 5/5** (hit@3 search). Cả 2 custom chunker đạt 5/5 search + 5/5 filter; `structure_aware_600` có ít chunk nhất (60) nhờ pack nguyên block table/list/code.

5. **Báo cáo (Bước 7)** ✅
   - [x] Section 2: inventory 6 files + metadata schema 2 cấp (doc-level + chunk-level VPC/SAC) + lý do chọn domain
   - [x] Section 3: baseline table cho 3 doc (tos/biểu phí/giao hàng) × 3 strategy, custom strategy description (VPC + SAC) + code snippet `chunk_with_metadata`, comparison table 2 custom vs 3 baseline (5/5 vs 4/5)
   - [x] Section 5: 5 pairs tiếng Việt thuộc domain (đổi trả 30 ngày / hoàn tiền 1 tháng, khui hộp / mở seal Apple, phí bảo hành vi-en mixed, cross-topic, off-domain) — 4/5 khớp dự đoán, lý giải cặp 4 ở cận trên bằng domain-bias
   - [x] Section 6: bảng 5 queries × top-1 chunk + agent answer cho `StructureAwareChunker(600)`; summary table 5 strategies × 2 modes
   - [x] Section 7 (Bước 6 — failure analysis): `by_sentences_3` query 5 (trả góp confused với giao hàng), phân tích đủ 4 tiêu chí EVALUATION.md (precision/coherence/metadata/grounding) + 3 đề xuất cải thiện
   - [x] Bảng tự đánh giá: **86/100** với breakdown từng mục

6. **Cleanup & verify** ✅
   - [x] `pytest tests/ -v` → 52/52 tests pass (42 cũ + 10 mới)
   - [x] Benchmark runable: `python scripts/run_benchmark.py` → bảng đầy đủ trong `report/benchmark_output.md`
   - [x] Đọc lại REPORT.md, Section 1-7 không còn placeholder `[...]`/empty rows

---

## File sẽ thay đổi

| File | Loại thay đổi |
|------|--------------|
| `data/cellphones/*.md` (6 files) | **NEW** — nội dung 6 trang chính sách |
| `scripts/fetch_policies.py` | **NEW** — fetch + clean + ghi MD |
| `scripts/run_benchmark.py` | **NEW** — benchmark runner |
| `src/custom_chunking.py` | **NEW** — `VietnamesePolicyChunker` |
| `src/__init__.py` | **EDIT** — export custom chunker |
| `tests/test_custom_chunking.py` | **NEW** — 2-3 test cho chunker mới |
| `requirements.txt` | **EDIT** — thêm `requests`, `beautifulsoup4`, `markdownify` |
| `report/REPORT.md` | **EDIT** — fill Section 2, 3, 5, 6, 7 |
| `report/benchmark_output.md` | **NEW** — raw output từ benchmark (để paste/reference) |
| `.env` | **EDIT** — set `EMBEDDING_PROVIDER` + model phù hợp |
| `main.py` (optional) | **EDIT** — đổi `SAMPLE_FILES` trỏ vào `data/cellphones/` để demo |

Không đụng vào `src/chunking.py`, `src/store.py`, `src/agent.py` đã pass tests.

---

## Verification

End-to-end check sau khi xong:

1. `pytest tests/ -v` → 42 tests cũ + 2-3 test mới đều pass
2. `python scripts/run_benchmark.py` → in bảng 4 strategies × 5 queries, có hit_rate@3 mỗi strategy
3. `python main.py "Chính sách hoàn tiền của Cellphones là gì?"` → in được top-3 chunks + agent answer
4. Mở `report/REPORT.md` → mọi section (1-7) đều có nội dung thật, không còn placeholder `[...]`
5. Tự đánh giá điểm theo bảng cuối REPORT.md → ≥ 80/100

---

## Critical files & references đã có sẵn

- `src/__init__.py` — export pattern để follow khi thêm `VietnamesePolicyChunker`
- `src/chunking.py:7-35` — `FixedSizeChunker` làm reference cho interface `chunk(text) -> list[str]`
- `src/chunking.py:54-71` — `RecursiveChunker` sẽ được reuse làm fallback cho oversized sections
- `main.py:31-56` — `load_documents_from_files()` pattern để follow khi viết `load_cellphones_docs()`
- `docs/EVALUATION.md` — rubric scoring để self-check
- `docs/SCORING.md` — phân bổ điểm group sections

---

## Risks & mitigations

- **`requests` bị block bởi WAF/UA** → set `User-Agent` header chuẩn của Chrome; nếu vẫn fail, copy-paste thủ công nội dung trang vào file `.md` rồi dùng `clean_markdown()` từ `scripts/fetch_policies.py`
- **Trang là SPA load bằng JS** → nội dung không có trong HTML response → fallback copy-paste; có thể dùng "View Page Source" của browser trước khi giả định trang là SPA, vì nhiều trang Vietnamese e-com vẫn render server-side
- **MiniLM tiếng Việt yếu (similarity score thấp)** → 2 lớp fallback: (a) switch sang `paraphrase-multilingual-MiniLM-L12-v2`, (b) cuối cùng dùng OpenAI `text-embedding-3-small` qua `OpenAIEmbedder` (user có key sẵn). Document model nào được dùng cuối cùng trong report Section 4 + 5
- **Code cũ break với tiếng Việt** (regex sentence split, encoding) → sanity check ở Bước 3, document trong Section 7, không sửa code cũ vì tests phải giữ pass
- **Pre-chunk + add_documents tạo nhiều records cùng `doc_id`** → `delete_document` đã handle (xoá tất cả records cùng `doc_id`), không cần đổi store
