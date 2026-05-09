"""Feishu mail API wrapper using lark-oapi SDK."""
import os
import requests
import lark_oapi
from lark_oapi.api.mail.v1 import (
    ListUserMailboxMessageRequestBuilder,
    GetUserMailboxMessageRequestBuilder,
    DownloadUrlUserMailboxMessageAttachmentRequestBuilder,
)
from . import config


def _build_client() -> lark_oapi.Client:
    return (
        lark_oapi.Client.builder()
        .app_id(config.APP_ID)
        .app_secret(config.APP_SECRET)
        .log_level(lark_oapi.LogLevel.WARNING)
        .build()
    )


def _request_option():
    if config.USER_ACCESS_TOKEN:
        return lark_oapi.RequestOption.builder().user_access_token(config.USER_ACCESS_TOKEN).build()
    return None


def list_invoice_messages(client: lark_oapi.Client, folder_id: str = "inbox") -> list[dict]:
    """Return all messages whose subject contains '发票'."""
    messages = []
    page_token = None

    while True:
        builder = (
            ListUserMailboxMessageRequestBuilder()
            .user_mailbox_id(config.USER_EMAIL)
            .folder_id(folder_id)
            .page_size(50)
        )
        if page_token:
            builder = builder.page_token(page_token)

        req = builder.build()
        opt = _request_option()
        resp = client.mail.v1.user_mailbox_message.list(req, opt) if opt else client.mail.v1.user_mailbox_message.list(req)

        if not resp.success():
            raise RuntimeError(f"列举邮件失败: code={resp.code} msg={resp.msg}")

        for msg in (resp.data.items or []):
            subject = getattr(msg, "subject", "") or ""
            if "发票" in subject:
                messages.append({"message_id": msg.message_id, "subject": subject})

        if not resp.data.has_more:
            break
        page_token = resp.data.page_token

    return messages


def get_message_detail(client: lark_oapi.Client, message_id: str) -> dict:
    """Return message detail including attachment list."""
    req = (
        GetUserMailboxMessageRequestBuilder()
        .user_mailbox_id(config.USER_EMAIL)
        .message_id(message_id)
        .build()
    )
    opt = _request_option()
    resp = client.mail.v1.user_mailbox_message.get(req, opt) if opt else client.mail.v1.user_mailbox_message.get(req)

    if not resp.success():
        raise RuntimeError(f"获取邮件详情失败: code={resp.code} msg={resp.msg}")

    msg = resp.data.message
    attachments = []
    for att in (getattr(msg, "attachments", None) or []):
        attachments.append({
            "attachment_id": att.attachment_id,
            "name": att.name or "",
            "size": getattr(att, "size", 0),
        })

    return {
        "message_id": message_id,
        "subject": getattr(msg, "subject", "") or "",
        "received_time": getattr(msg, "received_time", None),
        "body_text": _extract_body_text(msg),
        "attachments": attachments,
    }


def _extract_body_text(msg) -> str:
    body = getattr(msg, "body", None)
    if not body:
        return ""
    return getattr(body, "content", "") or ""


def get_attachment_download_urls(client: lark_oapi.Client, message_id: str, attachment_ids: list[str]) -> dict[str, str]:
    """Return {attachment_id: download_url}."""
    req = (
        DownloadUrlUserMailboxMessageAttachmentRequestBuilder()
        .user_mailbox_id(config.USER_EMAIL)
        .message_id(message_id)
        .attachment_ids(attachment_ids)
        .build()
    )
    opt = _request_option()
    resp = (
        client.mail.v1.user_mailbox_message_attachment.download_url(req, opt)
        if opt
        else client.mail.v1.user_mailbox_message_attachment.download_url(req)
    )

    if not resp.success():
        raise RuntimeError(f"获取附件下载链接失败: code={resp.code} msg={resp.msg}")

    return {item.attachment_id: item.download_url for item in (resp.data.attachment_download_url_list or [])}


def download_file(url: str, dest_path: str) -> None:
    """Download a file from url to dest_path."""
    headers = {}
    if config.USER_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {config.USER_ACCESS_TOKEN}"

    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        r.raise_for_status()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def build_client() -> lark_oapi.Client:
    return _build_client()
