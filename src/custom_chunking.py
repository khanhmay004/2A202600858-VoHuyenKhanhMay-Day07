"""Vietnamese policy document chunker.

Splits text into chunks aligned with the natural hierarchy of Cellphones policy
documents: PHẦN (mục) → điều → câu. Tables (Markdown pipe rows) are kept
together as a single chunk so price/fee data is never split mid-row.
"""
from __future__ import annotations

import re

from .chunking import RecursiveChunker

# L1 (mục): "PHẦN I.", "PHẦN II.", ... or top-level "A.", "B."
_L1_RE = re.compile(
    r"^(?:(?:PHẦN|Phần)\s+)?(?P<roman>[IVX]+|[A-Z])\.\s+",
    re.MULTILINE,
)
# L2 (điều): "1.", "2.", "3.1", "3.2.", "10."
_L2_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)?)\.\s+", re.MULTILINE)
# Sentence terminator (used only when an "điều" still exceeds max_chunk_size)
_SENT_SPLIT = re.compile(r"(?<=[.!?])[\s\n]+")

_ROMAN = "IVX"


def _is_roman(token: str) -> bool:
    return bool(token) and all(ch in _ROMAN for ch in token)


def _table_lines(text: str) -> list[tuple[int, int]]:
    """Return [(start_line, end_line)] index ranges (1-based) of contiguous table blocks."""
    lines = text.split("\n")
    blocks: list[tuple[int, int]] = []
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            j = i
            while j < len(lines) and (lines[j].lstrip().startswith("|") or lines[j].strip() == ""):
                if lines[j].strip() == "" and (j + 1 >= len(lines) or not lines[j + 1].lstrip().startswith("|")):
                    break
                j += 1
            blocks.append((i, j))
            i = j
        i += 1
    return blocks


class VietnamesePolicyChunker:
    """Hierarchy-aware chunker for Vietnamese policy documents.

    Output of `chunk_with_metadata` is a list of ``(chunk_text, {muc, dieu, cau,
    chunk_index})`` tuples. Use `chunk` for a strings-only view that satisfies
    the common ``chunk(text) -> list[str]`` interface used by
    `ChunkingStrategyComparator`.
    """

    def __init__(self, max_chunk_size: int = 600) -> None:
        self.max_chunk_size = max(100, max_chunk_size)
        self._fallback = RecursiveChunker(chunk_size=self.max_chunk_size)

    # ---- public API -------------------------------------------------------

    def chunk(self, text: str) -> list[str]:
        return [c for c, _ in self.chunk_with_metadata(text)]

    def chunk_with_metadata(self, text: str) -> list[tuple[str, dict]]:
        if not text or not text.strip():
            return []

        muc_blocks = self._split_by_level(text, _L1_RE, key="roman")
        out: list[tuple[str, dict]] = []
        chunk_index = 0
        for muc_label, muc_body in muc_blocks:
            dieu_blocks = self._split_by_level(muc_body, _L2_RE, key="num")
            if len(dieu_blocks) == 1 and dieu_blocks[0][0] is None:
                # No "điều" markers — treat whole mục as one block
                pieces = self._chunk_block(muc_body)
                for piece in pieces:
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

    # ---- internal ---------------------------------------------------------

    @staticmethod
    def _meta(muc, dieu, cau, idx) -> dict:
        return {"muc": muc, "dieu": dieu, "cau": cau, "chunk_index": idx}

    @staticmethod
    def _split_by_level(text: str, pattern: re.Pattern, key: str) -> list[tuple[str | None, str]]:
        """Split text by header markers; returns [(label_or_None, body), ...].

        If no marker is found, returns ``[(None, text)]``. The first chunk before
        the first marker (preamble) is attached under label ``None`` only when
        non-empty; otherwise it is dropped.
        """
        markers = list(pattern.finditer(text))
        if not markers:
            return [(None, text.strip())] if text.strip() else []

        blocks: list[tuple[str | None, str]] = []
        # Preamble before first marker
        preamble = text[: markers[0].start()].strip()
        if preamble:
            blocks.append((None, preamble))
        for i, m in enumerate(markers):
            label = m.group(key)
            start = m.start()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            body = text[start:end].strip()
            blocks.append((label, body))
        return blocks

    def _chunk_block(self, block: str) -> list[str]:
        """Chunk a single điều/mục body, preserving tables intact."""
        block = block.strip()
        if not block:
            return []

        segments = self._split_off_tables(block)

        pieces: list[str] = []
        for seg, is_table in segments:
            seg = seg.strip()
            if not seg:
                continue
            if is_table:
                # Always keep table as one chunk regardless of size
                pieces.append(seg)
                continue
            if len(seg) <= self.max_chunk_size:
                pieces.append(seg)
                continue
            # Try sentence-pack first
            packed = self._pack_sentences(seg)
            if all(len(p) <= self.max_chunk_size for p in packed):
                pieces.extend(packed)
            else:
                # Final fallback: recursive chunker
                pieces.extend(self._fallback.chunk(seg))
        return pieces

    @staticmethod
    def _split_off_tables(text: str) -> list[tuple[str, bool]]:
        """Yield alternating (text_segment, is_table) regions."""
        lines = text.split("\n")
        segments: list[tuple[str, bool]] = []
        cur_buf: list[str] = []
        cur_is_table = False
        for line in lines:
            line_is_table = line.lstrip().startswith("|")
            if line_is_table != cur_is_table:
                if cur_buf:
                    segments.append(("\n".join(cur_buf), cur_is_table))
                cur_buf = [line]
                cur_is_table = line_is_table
            else:
                cur_buf.append(line)
        if cur_buf:
            segments.append(("\n".join(cur_buf), cur_is_table))
        return segments

    def _pack_sentences(self, text: str) -> list[str]:
        """Pack sentences greedily up to max_chunk_size; emit chunks at boundaries."""
        sentences = [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]
        if not sentences:
            return [text.strip()] if text.strip() else []
        out: list[str] = []
        buf = ""
        for s in sentences:
            candidate = (buf + " " + s).strip() if buf else s
            if len(candidate) <= self.max_chunk_size:
                buf = candidate
            else:
                if buf:
                    out.append(buf)
                buf = s
        if buf:
            out.append(buf)
        return out


# ---------------------------------------------------------------------------
# Structure-aware chunker (Markdown / HTML-derived text)
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
_FENCE_RE = re.compile(r"^\s*```")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S")
_HTML_TAG_BLOCK_RE = re.compile(r"^\s*<(table|ul|ol|pre|code)[\s>]", re.IGNORECASE)
_HTML_TAG_BLOCK_END_RE = re.compile(r"</(table|ul|ol|pre|code)\s*>", re.IGNORECASE)


class StructureAwareChunker:
    """Structure-aware chunker for Markdown/HTML-derived documents.

    The text is first parsed into atomic blocks that must never be split mid-
    structure:

    * Markdown tables (consecutive ``|`` rows)
    * Fenced code blocks (between ``` fences)
    * Lists (consecutive ``- ``, ``* ``, ``+ ``, or ``N. `` lines, including
      indented continuations)
    * HTML ``<table>`` / ``<ul>`` / ``<ol>`` / ``<pre>`` blocks (kept whole)
    * Headings (kept as their own marker block so they stay with the following
      content)
    * Regular paragraphs (text separated by blank lines)

    Blocks are then packed greedily into chunks up to ``max_chunk_size``. A
    block larger than ``max_chunk_size`` is emitted as its own chunk **without**
    being split — preserving structure is the explicit contract of this
    strategy, even if the chunk exceeds the soft limit.

    Designed for manuals, API references, and policy/spec pages where splitting
    a table or code block would destroy the meaning of the surrounding text.
    """

    BLOCK_TABLE = "table"
    BLOCK_CODE = "code"
    BLOCK_LIST = "list"
    BLOCK_HEADING = "heading"
    BLOCK_HTML_BLOCK = "html_block"
    BLOCK_PARAGRAPH = "paragraph"

    PROTECTED = {BLOCK_TABLE, BLOCK_CODE, BLOCK_LIST, BLOCK_HTML_BLOCK}

    def __init__(self, max_chunk_size: int = 600) -> None:
        self.max_chunk_size = max(100, max_chunk_size)

    # ---- public API -------------------------------------------------------

    def chunk(self, text: str) -> list[str]:
        return [c for c, _ in self.chunk_with_metadata(text)]

    def chunk_with_metadata(self, text: str) -> list[tuple[str, dict]]:
        if not text or not text.strip():
            return []
        blocks = self._parse_blocks(text)
        return self._pack_blocks(blocks)

    # ---- block parsing ----------------------------------------------------

    def _parse_blocks(self, text: str) -> list[tuple[str, str]]:
        """Return [(block_type, block_text), ...] in document order."""
        lines = text.split("\n")
        blocks: list[tuple[str, str]] = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Blank line: skip
            if not stripped:
                i += 1
                continue

            # Fenced code block
            if _FENCE_RE.match(line):
                start = i
                i += 1
                while i < n and not _FENCE_RE.match(lines[i]):
                    i += 1
                if i < n:
                    i += 1  # include closing fence
                blocks.append((self.BLOCK_CODE, "\n".join(lines[start:i])))
                continue

            # HTML block (table/ul/ol/pre)
            if _HTML_TAG_BLOCK_RE.match(line):
                tag_match = _HTML_TAG_BLOCK_RE.match(line)
                start = i
                # Walk until the matching closing tag is seen on a line
                while i < n:
                    if _HTML_TAG_BLOCK_END_RE.search(lines[i]):
                        i += 1
                        break
                    i += 1
                blocks.append((self.BLOCK_HTML_BLOCK, "\n".join(lines[start:i])))
                continue

            # Heading
            if _HEADING_RE.match(line):
                blocks.append((self.BLOCK_HEADING, line.rstrip()))
                i += 1
                continue

            # Markdown table: a contiguous run of lines starting with '|'
            if stripped.startswith("|"):
                start = i
                while i < n and lines[i].lstrip().startswith("|"):
                    i += 1
                blocks.append((self.BLOCK_TABLE, "\n".join(lines[start:i])))
                continue

            # List: contiguous run of list items, allowing indented continuation lines
            if _LIST_ITEM_RE.match(line):
                start = i
                while i < n:
                    cur = lines[i]
                    if not cur.strip():
                        # blank line ends list unless next non-blank is still a list item
                        j = i + 1
                        while j < n and not lines[j].strip():
                            j += 1
                        if j < n and (_LIST_ITEM_RE.match(lines[j]) or lines[j].startswith((" ", "\t"))):
                            i = j
                            continue
                        break
                    if _LIST_ITEM_RE.match(cur) or cur.startswith((" ", "\t")):
                        i += 1
                        continue
                    break
                blocks.append((self.BLOCK_LIST, "\n".join(l for l in lines[start:i] if l.strip() or True).rstrip()))
                continue

            # Paragraph: collect lines until blank line or structural marker
            start = i
            while i < n:
                cur = lines[i]
                if not cur.strip():
                    break
                if _FENCE_RE.match(cur) or _HEADING_RE.match(cur) or _HTML_TAG_BLOCK_RE.match(cur):
                    break
                if cur.lstrip().startswith("|"):
                    break
                if _LIST_ITEM_RE.match(cur):
                    break
                i += 1
            blocks.append((self.BLOCK_PARAGRAPH, "\n".join(lines[start:i]).rstrip()))

        return [(t, b) for t, b in blocks if b.strip()]

    # ---- packing ----------------------------------------------------------

    def _pack_blocks(self, blocks: list[tuple[str, str]]) -> list[tuple[str, dict]]:
        out: list[tuple[str, dict]] = []
        buf_text = ""
        buf_types: list[str] = []
        chunk_index = 0

        def flush():
            nonlocal buf_text, buf_types, chunk_index
            if buf_text.strip():
                meta = {
                    "chunk_index": chunk_index,
                    "block_types": sorted(set(buf_types)),
                }
                out.append((buf_text.strip(), meta))
                chunk_index += 1
            buf_text = ""
            buf_types = []

        for block_type, body in blocks:
            body = body.strip("\n")
            block_len = len(body)

            # A protected block larger than max_chunk_size becomes its own chunk
            # (intentionally exceeds the soft limit to preserve structure).
            if block_type in self.PROTECTED and block_len > self.max_chunk_size:
                flush()
                meta = {
                    "chunk_index": chunk_index,
                    "block_types": [block_type],
                    "oversized": True,
                }
                out.append((body, meta))
                chunk_index += 1
                continue

            # A regular block larger than max_chunk_size: still emit as its own
            # chunk (the strategy's contract is "never split a structural block";
            # callers who want hard cuts should use a different chunker).
            if block_type == self.BLOCK_PARAGRAPH and block_len > self.max_chunk_size:
                flush()
                meta = {
                    "chunk_index": chunk_index,
                    "block_types": [block_type],
                    "oversized": True,
                }
                out.append((body, meta))
                chunk_index += 1
                continue

            sep = "\n\n" if buf_text else ""
            candidate_len = len(buf_text) + len(sep) + block_len

            if candidate_len <= self.max_chunk_size:
                buf_text += sep + body
                buf_types.append(block_type)
            else:
                # Heading should stay glued to the following block — don't flush
                # right after a heading; instead, flush the prior buffer and
                # start a new one with the heading.
                flush()
                buf_text = body
                buf_types = [block_type]

        flush()
        return out
