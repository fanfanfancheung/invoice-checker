"""Main download orchestration."""
import json
import os
import tempfile
import requests
from datetime import datetime, timedelta

from . import config
from . import feishu_client as fc
from . import invoice_parser as parser


_RECORD_FILE = ".downloaded.json"


def _load_downloaded(output_dir: str) -> set[str]:
    path = os.path.join(output_dir, _RECORD_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return set(json.load(f))
    return set()


def _save_downloaded(output_dir: str, ids: set[str]) -> None:
    path = os.path.join(output_dir, _RECORD_FILE)
    with open(path, "w") as f:
        json.dump(sorted(ids), f, indent=2)


def _unique_path(directory: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    idx = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}_{idx}{ext}")
        idx += 1
    return candidate


def _download_file(url: str, dest_path: str) -> None:
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def _process_pdf(pdf_path: str, subject: str, received_ts: int | None, output_dir: str) -> str:
    text = parser.pdf_text(pdf_path)
    combined = subject + "\n" + text

    date = parser.extract_date(combined)
    if not date and received_ts:
        date = datetime.fromtimestamp(int(received_ts) / 1000).strftime("%Y%m%d")

    amount = parser.extract_amount(text) or parser.extract_amount_from_subject(subject)
    category = parser.extract_category(combined)

    original = os.path.basename(pdf_path)
    filename = parser.build_filename(date, category, amount, original)
    dest = _unique_path(output_dir, filename)
    os.rename(pdf_path, dest)
    return dest


def run(output_dir: str | None = None, days_back: int | None = None) -> None:
    output_dir = output_dir or config.DOWNLOAD_DIR
    days_back = days_back if days_back is not None else config.DAYS_BACK
    os.makedirs(output_dir, exist_ok=True)

    downloaded = _load_downloaded(output_dir)

    print(f"正在搜索「发票」相关邮件（最近 {days_back} 天）…")
    messages = fc.search_invoice_messages()

    cutoff_ms = 0
    if days_back > 0:
        cutoff_ms = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    new_count = 0

    for meta in messages:
        msg_id = meta["message_id"]
        subject = meta["subject"]

        detail = fc.get_message_detail(msg_id)
        received_ts = detail.get("received_time")

        if cutoff_ms and received_ts and int(received_ts) < cutoff_ms:
            continue

        attachments = detail["attachments"]
        if not attachments:
            continue

        # Filter to supported file types
        valid_atts = [
            a for a in attachments
            if a["name"].lower().endswith((".pdf", ".zip", ".ofd"))
        ]
        if not valid_atts:
            continue

        for att in valid_atts:
            att_id = att["attachment_id"]
            att_name: str = att["name"]
            record_key = f"{msg_id}:{att_id}"

            if record_key in downloaded:
                continue

            url_map = fc.get_attachment_download_urls(msg_id, [att_id])
            url = url_map.get(att_id)
            if not url:
                print(f"  [跳过] 无法获取下载链接: {att_name}")
                continue

            with tempfile.TemporaryDirectory() as tmp:
                raw_path = os.path.join(tmp, att_name)
                _download_file(url, raw_path)

                if att_name.lower().endswith(".zip"):
                    pdf_files = parser.extract_zip_pdfs(raw_path, tmp)
                else:
                    pdf_files = [raw_path]

                for pdf in pdf_files:
                    dest = _process_pdf(pdf, subject, received_ts, output_dir)
                    print(f"  [保存] {os.path.basename(dest)}")
                    new_count += 1

            downloaded.add(record_key)
            _save_downloaded(output_dir, downloaded)

    if new_count == 0:
        print("没有发现新的发票附件。")
    else:
        print(f"\n共下载 {new_count} 个发票文件，保存至: {os.path.abspath(output_dir)}")
