"""SSE-friendly wrappers around each platform's `*_setup` login flow.

The uploader code already accepts a `qrcode_callback` that yields the QR
image as `image_path` / `image_data_url` and ultimately a terminal status
("success" / "failed"). We forward those into an asyncio.Queue so a
SSE handler can stream them to the browser.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Mapping

import sau_cli

logger = logging.getLogger("sau.v2.login")


# Lazy uploader imports — same rationale as `sau_cli.__getattr__`. The login
# helpers all live in modules that import patchright; we only want to pay
# that cost when the user actually triggers a login flow.
def _setup_fn(platform: str) -> Callable[..., Awaitable[Any]]:
    import importlib

    module_name, attr = {
        "douyin": ("uploader.douyin_uploader.main", "douyin_setup"),
        "kuaishou": ("uploader.ks_uploader.main", "ks_setup"),
        "xiaohongshu": ("uploader.xiaohongshu_uploader.main", "xiaohongshu_setup"),
        "tencent": ("uploader.tencent_uploader.main", "tencent_setup"),
    }[platform]
    return getattr(importlib.import_module(module_name), attr)


# Platforms that don't fit the QR-code SSE flow. We tell the front-end to
# prompt the user to run the CLI locally.
MANUAL_LOGIN_PLATFORMS: dict[str, str] = {
    "bilibili": "请在服务器终端运行: sau bilibili login --account {account_name} （B 站扫码需要交互式终端）",
    "youtube": "请在服务器终端运行: sau youtube login --account {account_name} （YouTube 登录需浏览器内手动输入 Google 账号）",
}


def manual_login_message(platform: str, account_name: str) -> str | None:
    template = MANUAL_LOGIN_PLATFORMS.get(platform)
    if not template:
        return None
    return template.format(account_name=account_name)


async def stream_login(platform: str, account_name: str) -> AsyncIterator[str]:
    """Yield SSE-formatted strings for a login flow.

    The front-end renders the QR (base64 PNG) and a status text. We close
    the stream with a `success` / `failed` event.
    """
    setup_fn = _setup_fn(platform) if platform in {"douyin", "kuaishou", "xiaohongshu", "tencent"} else None
    if setup_fn is None:
        msg = manual_login_message(platform, account_name) or f"unsupported platform: {platform}"
        yield _sse("error", {"message": msg})
        return

    queue: asyncio.Queue[dict] = asyncio.Queue()

    def qrcode_callback(payload: Mapping[str, Any]) -> Awaitable[None] | None:
        return _enqueue_login_event(queue, payload)

    account_file = sau_cli.resolve_account_file(platform, account_name)
    account_file.parent.mkdir(parents=True, exist_ok=True)

    yield _sse("info", {"message": f"正在打开 {platform} 登录页..."})

    async def _drive() -> dict:
        return await setup_fn(
            str(account_file),
            handle=True,
            return_detail=True,
            qrcode_callback=qrcode_callback,
        )

    runner = asyncio.create_task(_drive())

    while True:
        get_task = asyncio.create_task(queue.get())
        done, _ = await asyncio.wait({get_task, runner}, return_when=asyncio.FIRST_COMPLETED)
        if get_task in done:
            payload = get_task.result()
            # Tag the payload with an event name so the front-end can route on it.
            # QR payloads are identified by the presence of image_data_url /
            # image_path (set by every uploader's `_emit_qrcode_callback`).
            event_name = "qrcode" if ("image_data_url" in payload or "image_path" in payload) else "info"
            yield _sse(event_name, payload)
        if runner in done:
            # Drain any final events the uploader queued before exiting.
            while not queue.empty():
                payload = queue.get_nowait()
                event_name = "qrcode" if ("image_data_url" in payload or "image_path" in payload) else "info"
                yield _sse(event_name, payload)
            try:
                result = runner.result()
            except Exception as exc:  # noqa: BLE001
                yield _sse("failed", {"message": str(exc)})
                return
            yield _sse("result", result)
            return


async def _enqueue_login_event(queue: asyncio.Queue[dict], payload: Mapping[str, Any]) -> None:
    await queue.put(dict(payload))


def _sse(event: str, data: Mapping[str, Any]) -> str:
    enriched = {"event": event, "ts": datetime.utcnow().isoformat() + "Z", **data}
    return f"data: {json.dumps(enriched, ensure_ascii=False)}\n\n"
