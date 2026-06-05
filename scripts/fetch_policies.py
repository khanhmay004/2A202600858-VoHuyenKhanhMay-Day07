"""Fetch + clean Cellphones.com.vn policy pages into Markdown files."""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "cellphones"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

TARGETS: list[tuple[str, str, str]] = [
    ("tos.md", "https://cellphones.com.vn/tos", "tos"),
    ("chinh_sach_giao_hang.md", "https://cellphones.com.vn/chinh-sach-giao-hang", "delivery"),
    ("chinh_sach_khui_hop_apple.md", "https://cellphones.com.vn/chinh-sach-khui-hop-apple", "unbox_apple"),
    ("quy_dinh_sao_luu_du_lieu.md", "https://cellphones.com.vn/quy-dinh-ve-viec-sao-luu-du-lieu", "data_backup"),
    ("bieu_phi_bao_hanh_mo_rong.md", "https://cellphones.com.vn/bieu-phi-bao-hanh-mo-rong", "warranty_fee"),
    (
        "huong_dan_mua_tra_gop.md",
        "https://cellphones.com.vn/huong-dan-mua-hang-tra-gop-bang-the-tin-dung-tai-cellphones",
        "installment",
    ),
]


def fetch(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def extract_main(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Strip noise
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav", "aside", "form", "button"]):
        tag.decompose()
    # Heuristic: remove obvious chrome by class/id contains
    drop_keywords = (
        "menu", "navigation", "breadcrumb", "footer", "header", "sidebar",
        "banner", "social", "share", "popup", "modal", "advert", "ads",
        "subscribe", "newsletter", "cookie", "chat", "support-widget",
    )
    to_drop = []
    for el in soup.find_all(True):
        attrs_d = getattr(el, "attrs", None) or {}
        cls_val = attrs_d.get("class")
        cls = " ".join(cls_val or []).lower() if cls_val else ""
        idv = (attrs_d.get("id") or "").lower()
        blob = f"{cls} {idv}"
        if any(k in blob for k in drop_keywords):
            to_drop.append(el)
    for el in to_drop:
        try:
            el.decompose()
        except Exception:
            pass
    # Candidate containers (typical Cellphones layout)
    candidates = [
        ("div", {"class": re.compile(r"(content-policy|policy-detail|cms-content|page-content|wrapper-content|content-static|cps-block-content)", re.I)}),
        ("article", {}),
        ("main", {}),
    ]
    for name, attrs in candidates:
        node = soup.find(name, attrs=attrs)
        if node and len(node.get_text(strip=True)) > 400:
            return str(node)
    # Fallback: pick the largest <div> by text length
    best = None
    best_len = 0
    for div in soup.find_all("div"):
        txt = div.get_text(" ", strip=True)
        if len(txt) > best_len:
            best_len = len(txt)
            best = div
    if best is None:
        return str(soup.body or soup)
    return str(best)


def clean_markdown(text: str) -> str:
    # Normalize nbsp & other invisible chars
    text = text.replace("\xa0", " ").replace("\u200b", "")
    # Collapse repeated whitespace within lines (but preserve markdown tables/lines)
    lines = []
    for line in text.splitlines():
        if "|" in line:  # likely a table row - keep spacing
            lines.append(line.rstrip())
        else:
            lines.append(re.sub(r"[ \t]+", " ", line).rstrip())
    text = "\n".join(lines)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Drop standalone navigation lines that survived (very short lines that are pure links list residue)
    cleaned = []
    prev_blank = False
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            if prev_blank:
                continue
            prev_blank = True
            cleaned.append("")
            continue
        prev_blank = False
        # Drop bullet rows that are just a single short word/link (likely menu leftover)
        if re.fullmatch(r"[-*]\s+\S{1,30}", s) and "[" not in s and "|" not in s:
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).strip() + "\n"


def process(url: str) -> str:
    html = fetch(url)
    main_html = extract_main(html)
    raw_md = md(main_html, heading_style="ATX", strip=["a", "img"])
    return clean_markdown(raw_md)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, int, bool]] = []
    for filename, url, category in TARGETS:
        out_path = OUT_DIR / filename
        print(f"[fetch] {url}")
        try:
            content = process(url)
        except Exception as exc:
            print(f"  ! FAILED: {exc}")
            results.append((filename, 0, False))
            continue
        has_table = bool(re.search(r"^\s*\|.+\|\s*$", content, flags=re.MULTILINE))
        header = (
            f"<!-- source_url: {url} -->\n"
            f"<!-- category: {category} -->\n\n"
        )
        out_path.write_text(header + content, encoding="utf-8")
        n = len(content)
        print(f"  -> {out_path.relative_to(ROOT)}  chars={n}  table={'yes' if has_table else 'no'}")
        results.append((filename, n, has_table))
        time.sleep(0.8)

    print("\n=== SUMMARY ===")
    for name, n, has_table in results:
        flag = "OK" if n >= 1000 else "SHORT"
        print(f"  {flag:5s}  {name:40s} chars={n:6d}  table={'Y' if has_table else 'n'}")
    return 0 if all(n >= 1000 for _, n, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
