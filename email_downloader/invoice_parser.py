"""Extract invoice date, category, and amount from subject / PDF text."""
import re
import zipfile
import tempfile
import os
from datetime import datetime


# ── Date patterns ────────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    # 2026年04月07日  or  2026年4月7日
    (re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"), lambda m: f"{m[1]}{int(m[2]):02d}{int(m[3]):02d}"),
    # 2026-04-07  or  2026/04/07  or  2026.04.07
    (re.compile(r"(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})"), lambda m: f"{m[1]}{int(m[2]):02d}{int(m[3]):02d}"),
    # 20260407
    (re.compile(r"(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"), lambda m: f"{m[1]}{m[2]}{m[3]}"),
]

# ── Amount patterns ───────────────────────────────────────────────────────────

_AMOUNT_PATTERNS = [
    re.compile(r"[¥￥]\s*(\d+(?:\.\d{1,2})?)"),
    re.compile(r"价税合计[^0-9]*(\d+(?:\.\d{1,2})?)"),
    re.compile(r"合计金额[^0-9]*(\d+(?:\.\d{1,2})?)"),
    re.compile(r"(\d+\.\d{2})\s*元"),
    # plain number like 179.00 or 179 in subject
    re.compile(r"(\d+(?:\.\d{1,2})?)"),
]

# ── Category keywords ─────────────────────────────────────────────────────────

_CATEGORIES = [
    "餐费", "差旅", "交通", "住宿", "办公", "培训", "通讯", "快递",
    "医疗", "采购", "服务", "咨询", "广告", "水电", "租金",
]


def extract_date(text: str) -> str | None:
    """Return YYYYMMDD or None."""
    for pattern, fmt in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            return fmt(m.groups())
    return None


def extract_amount(text: str) -> str | None:
    """Return amount string like '179.00' or None."""
    for pattern in _AMOUNT_PATTERNS[:-1]:  # try specific patterns first
        m = pattern.search(text)
        if m:
            val = float(m.group(1))
            return f"{val:.2f}"
    return None


def extract_amount_from_subject(subject: str) -> str | None:
    """Try to pull amount from email subject."""
    # e.g.  "餐费发票 179.00" or "发票179元"
    m = re.search(r"(\d+(?:\.\d{1,2})?)\s*元", subject)
    if m:
        return f"{float(m.group(1)):.2f}"
    m = re.search(r"[¥￥]\s*(\d+(?:\.\d{1,2})?)", subject)
    if m:
        return f"{float(m.group(1)):.2f}"
    # bare decimal number that looks like a price
    m = re.search(r"\b(\d{1,6}\.\d{2})\b", subject)
    if m:
        return m.group(1)
    return None


def extract_category(text: str) -> str:
    """Return category keyword found in text, or '其他'."""
    for cat in _CATEGORIES:
        if cat in text:
            return cat
    return "其他"


def pdf_text(path: str) -> str:
    """Extract all text from a PDF file."""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return ""


def extract_zip_pdfs(zip_path: str, extract_to: str) -> list[str]:
    """Extract PDF/OFD files from a ZIP and return their paths."""
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.lower().endswith((".pdf", ".ofd")):
                dest = os.path.join(extract_to, os.path.basename(name))
                with zf.open(name) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                extracted.append(dest)
    return extracted


def build_filename(date: str | None, category: str, amount: str | None, original: str, index: int = 0) -> str:
    """
    Build filename like: 20260407-餐费-发票-179.00.pdf
    Falls back gracefully when date / amount are unknown.
    """
    date_part = date or "未知日期"
    amount_part = amount or "未知金额"
    ext = os.path.splitext(original)[1].lower() or ".pdf"
    suffix = f"_{index}" if index else ""
    return f"{date_part}-{category}-发票-{amount_part}{suffix}{ext}"
