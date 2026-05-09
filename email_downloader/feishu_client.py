"""Feishu mail operations via lark-cli subprocess calls."""
import json
import subprocess
import shutil
import sys

LARK_CLI = (
    shutil.which("lark-cli")
    or "/opt/node22/lib/node_modules/@larksuite/cli/bin/lark-cli"
)


def _run(args: list[str]) -> dict:
    """Run a lark-cli command and return parsed JSON output."""
    cmd = [LARK_CLI] + args + ["--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Check for auth/config errors
        try:
            err = json.loads(stderr or result.stdout)
            if isinstance(err, dict) and err.get("ok") is False:
                etype = err.get("error", {}).get("type", "")
                if etype in ("auth", "config"):
                    print("\n[错误] lark-cli 未登录，请先运行：")
                    print("  lark-cli config init")
                    print("  lark-cli auth login --recommend")
                    sys.exit(1)
        except (json.JSONDecodeError, AttributeError):
            pass
        raise RuntimeError(f"lark-cli 执行失败: {stderr or result.stdout}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"lark-cli 返回非 JSON 输出: {result.stdout[:200]}")


def search_invoice_messages(max_count: int = 400) -> list[dict]:
    """Return messages whose subject/body contains '发票'."""
    data = _run([
        "mail", "+triage",
        "--query", "发票",
        "--max", str(max_count),
    ])
    items = data if isinstance(data, list) else data.get("items", [])
    return [
        {"message_id": m["message_id"], "subject": m.get("subject", "")}
        for m in items
        if m.get("message_id")
    ]


def get_message_detail(message_id: str) -> dict:
    """Return full message detail including attachments list."""
    data = _run([
        "mail", "+message",
        "--message-id", message_id,
    ])
    msg = data if not data.get("message") else data["message"]
    attachments = []
    for att in msg.get("attachments", []):
        attachments.append({
            "attachment_id": att.get("attachment_id", ""),
            "name": att.get("name", ""),
            "size": att.get("size", 0),
        })
    return {
        "message_id": message_id,
        "subject": msg.get("subject", ""),
        "received_time": msg.get("received_time"),
        "body_text": msg.get("body_plain", "") or msg.get("body", ""),
        "attachments": attachments,
    }


def get_attachment_download_urls(message_id: str, attachment_ids: list[str]) -> dict[str, str]:
    """Return {attachment_id: download_url}."""
    params = {
        "user_mailbox_id": "me",
        "message_id": message_id,
        "attachment_ids": attachment_ids,
    }
    data = _run([
        "mail", "user_mailbox.message.attachments", "download_url",
        "--params", json.dumps(params),
    ])
    result = {}
    for item in data.get("download_urls", []):
        result[item["attachment_id"]] = item["download_url"]
    return result
