"""Extract all 7 TOS parts from the /tos NUXT JS state and stitch into one Markdown file.

The /tos page is a Nuxt SPA — server returns identical HTML for any ?part= URL,
and the actual section bodies live inside a JS-encoded string in window.__NUXT__.
Our previous BeautifulSoup-based extractor only captured the default-visible
section (Phần IV, refund-policy). This script decodes the JS strings for ALL 7
sections and rebuilds the file with full content.
"""
from __future__ import annotations

import html as htmllib
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "cellphones" / "tos.md"
URL = "https://cellphones.com.vn/tos"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

ROMAN_SECTIONS = ["I", "II", "III", "IV", "V", "VI", "VII"]


def find_string_bounds(text: str, pos: int) -> tuple[int, int]:
    """Walk back to the opening unescaped '"' and forward to the closing unescaped '"'."""
    i = pos
    while i > 0:
        if text[i] == '"' and text[i - 1] != "\\":
            start = i
            break
        i -= 1
    else:
        return -1, -1
    j = start + 1
    while j < len(text):
        if text[j] == '"' and text[j - 1] != "\\":
            return start, j
        j += 1
    return start, -1


def decode_section(raw_html_str: str) -> str:
    """Decode JS-encoded string then convert HTML to clean Markdown."""
    try:
        decoded = json.loads('"' + raw_html_str + '"')
    except Exception:
        decoded = raw_html_str
    decoded = htmllib.unescape(decoded)
    md_text = md(decoded, heading_style="ATX", strip=["a", "img"])
    md_text = md_text.replace("\xa0", " ").replace("\u200b", "")
    md_text = re.sub(r"[ \t]+", " ", md_text)
    md_text = re.sub(r"\n{3,}", "\n\n", md_text)
    return md_text.strip()


def main() -> int:
    print(f"[fetch] {URL}")
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
    r.encoding = r.apparent_encoding or "utf-8"
    text = r.text

    # PHẦN markers appear both as literal "PHẦN" and as JS-escaped "PH\u1ea6N".
    # Collect unique JS-string boundaries (one big string may hold multiple PHẦN).
    marker_re = re.compile(r"(PHẦN|PH\\u1ea6N)\s+", re.IGNORECASE)
    seen_bounds: set[tuple[int, int]] = set()
    sections: dict[str, str] = {}

    for m in marker_re.finditer(text):
        start, end = find_string_bounds(text, m.start())
        if start < 0 or end < 0 or (end - start) < 500:
            continue
        if (start, end) in seen_bounds:
            continue
        seen_bounds.add((start, end))
        body = decode_section(text[start + 1 : end])
        # Split body into individual sections by PHẦN markers
        split_re = re.compile(r"(?=PHẦN\s+(?:VII|VI|IV|V|III|II|I)\.)")
        chunks = split_re.split(body)
        for chunk in chunks:
            roman_match = re.match(r"PHẦN\s+(VII|VI|IV|V|III|II|I)\.", chunk)
            if not roman_match:
                continue
            roman = roman_match.group(1)
            if roman in sections:
                continue
            cleaned = chunk.strip()
            if len(cleaned) < 200:
                continue
            sections[roman] = cleaned
            print(f"  PHẦN {roman}: {len(cleaned)} chars  (from string {start}-{end})")

    if len(sections) < 7:
        missing = [r for r in ROMAN_SECTIONS if r not in sections]
        print(f"  ! missing parts: {missing}")

    header = (
        f"<!-- source_url: {URL} -->\n"
        f"<!-- category: tos -->\n\n"
        f"# Quy chế hoạt động website Cellphones.com.vn\n\n"
    )

    parts_md = []
    for roman in ROMAN_SECTIONS:
        if roman in sections:
            parts_md.append(sections[roman])

    content = header + "\n\n---\n\n".join(parts_md) + "\n"
    OUT.write_text(content, encoding="utf-8")
    print(f"  -> {OUT.relative_to(ROOT)}  total_chars={len(content)}")
    return 0 if len(sections) == 7 else 1


if __name__ == "__main__":
    sys.exit(main())
