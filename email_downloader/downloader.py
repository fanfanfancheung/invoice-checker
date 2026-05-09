"""Main download orchestration."""
import json
import os
import tempfile
import requests
from datetime import datetime, timedelta

from . import config
from . import feishu_client as fc
from . import invoice_parser as parser


_STATE_FILE = ".state.json"


def _load_state(output_dir: str) -> dict:
    path = os.path.join(output_dir, _STATE_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"downloaded": [], "last_run_ms": None}


def _save_state(output_dir: str, state: dict) -> None:
    path = os.path.join(output_dir, _STATE_FILE)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


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


def run(output_dir: str | None = None, since_ms: int | None = None) -> None:
    """
    Run one download pass.

    since_ms: only process emails received after this Unix-ms timestamp.
              If None, falls back to state file, then to config.DAYS_BACK.
    """
    output_dir = output_dir or config.DOWNLOAD_DIR
    os.makedirs(output_dir, exist_ok=True)

    state = _load_state(output_dir)
    downloaded: set[str] = set(state.get("downloaded", []))

    # Determine cutoff timestamp
    if since_ms is not None:
        cutoff_ms = since_ms
        label = datetime.fromtimestamp(cutoff_ms / 1000).strftime("%Y-%m-%d %H:%M")
    elif state.get("last_run_ms"):
        cutoff_ms = state["last_run_ms"]
        label = datetime.fromtimestamp(cutoff_ms / 1000).strftime("%Y-%m-%d %H:%M")
    else:
        cutoff_ms = int((datetime.now() - timedelta(days=config.DAYS_BACK)).timestamp() * 1000)
        label = f"最近 {config.DAYS_BACK} 天"

    run_start_ms = int(datetime.now().timestamp() * 1000)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始扫描，搜索范围：{label} 至今")

    messages = fc.search_invoice_messages()
    new_count = 0

    for meta in messages:
        msg_id = meta["message_id"]
        subject = meta["subject"]

        detail = fc.get_message_detail(msg_id)
        received_ts = detail.get("received_time")

        if received_ts and int(received_ts) < cutoff_ms:
            continue

        valid_atts = [
            a for a in detail["attachments"]
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

                pdf_files = parser.extract_zip_pdfs(raw_path, tmp) if att_name.lower().endswith(".zip") else [raw_path]

                for pdf in pdf_files:
                    dest = _process_pdf(pdf, subject, received_ts, output_dir)
                    print(f"  [保存] {os.path.basename(dest)}")
                    new_count += 1

            downloaded.add(record_key)
            # Save state after each attachment so progress isn't lost on crash
            state["downloaded"] = sorted(downloaded)
            state["last_run_ms"] = run_start_ms
            _save_state(output_dir, state)

    # Always update last_run_ms even when nothing new was found
    state["last_run_ms"] = run_start_ms
    _save_state(output_dir, state)

    if new_count == 0:
        print("  没有发现新的发票附件。")
    else:
        print(f"  共下载 {new_count} 个文件，保存至: {os.path.abspath(output_dir)}")
