"""Wrap `sau_cli.upload_*` so the FastAPI layer can dispatch in-process.

We import the CLI module and call its async helpers directly. The CLI
expects `*UploadRequest` dataclasses; we mirror their fields in Pydantic
and convert just before the call. This keeps the dataclass contracts
authoritative — the route layer is a thin adapter.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import sau_cli
from sau_backend_v2.services.progress_bridge import TaskProgressBridge
from uploader.bilibili_uploader.runtime import run_biliup_command

logger = logging.getLogger("sau.v2.cli_runner")


# Map platform name → (CLI request dataclass, CLI upload function, request kind).
PLATFORM_BINDINGS: dict[str, dict[str, Any]] = {
    "douyin": {
        "video": (sau_cli.DouyinVideoUploadRequest, sau_cli.upload_video),
        "note": (sau_cli.DouyinNoteUploadRequest, sau_cli.upload_note),
    },
    "kuaishou": {
        "video": (sau_cli.KuaishouVideoUploadRequest, sau_cli.upload_kuaishou_video),
        "note": (sau_cli.KuaishouNoteUploadRequest, sau_cli.upload_kuaishou_note),
    },
    "xiaohongshu": {
        "video": (sau_cli.XiaohongshuVideoUploadRequest, sau_cli.upload_xiaohongshu_video),
        "note": (sau_cli.XiaohongshuNoteUploadRequest, sau_cli.upload_xiaohongshu_note),
    },
    "bilibili": {
        "video": (sau_cli.BilibiliVideoUploadRequest, None),  # bilibili is sync (subprocess)
    },
    "tencent": {
        "video": (sau_cli.TencentVideoUploadRequest, None),  # placeholder; tencent not all wired here
    },
    "youtube": {
        "video": (sau_cli.YouTubeVideoUploadRequest, None),
    },
}


def supported_platforms() -> list[str]:
    return list(PLATFORM_BINDINGS.keys())


async def dispatch_publish(
    platform: str,
    kind: str,
    payload: dict,
    *,
    bridge: TaskProgressBridge | None = None,
) -> dict:
    """Run a single publish task. Returns a small result dict for the router.

    `payload` is a Pydantic-shaped dict whose keys mirror the CLI dataclass
    fields. The bilibili path is special: it shells out to `biliup` and has
    no progress bridge — we surface the returncode as a terminal event.
    """
    binding = PLATFORM_BINDINGS.get(platform, {}).get(kind)
    if binding is None:
        raise ValueError(f"unsupported publish: platform={platform} kind={kind}")

    if platform == "bilibili":
        return _run_bilibili(payload, bridge)

    request_cls, runner = binding
    progress_callback = bridge.callback if bridge is not None else None
    request = _build_request(request_cls, platform, payload)

    try:
        if bridge is not None:
            await bridge._enqueue("publish_started", {"platform": platform, "account_name": request.account_name, "title": request.title})
        result_path: Path = await runner(request, progress_callback=progress_callback)
        if bridge is not None:
            await bridge._enqueue("publish_completed", {"platform": platform, "account_name": request.account_name, "result_path": str(result_path)})
            bridge.close("publish_completed", {"platform": platform, "account_name": request.account_name})
        return {"status": "success", "account_file": str(result_path)}
    except Exception as exc:  # noqa: BLE001
        if bridge is not None:
            await bridge._enqueue("publish_failed", {"platform": platform, "account_name": payload.get("account_name"), "error": str(exc)})
            bridge.close("publish_failed", {"platform": platform, "error": str(exc)})
        raise


def _build_request(request_cls: type, platform: str, payload: dict) -> Any:
    """Instantiate a CLI request dataclass from a payload dict.

    We pull only fields the dataclass declares — the payload may carry
    extra fields from the Pydantic schema that aren't used by some
    platforms.
    """
    import dataclasses

    valid_fields = {f.name for f in dataclasses.fields(request_cls)}
    filtered = {key: value for key, value in payload.items() if key in valid_fields}
    if "publish_date" in filtered:
        filtered["publish_date"] = _coerce_publish_date(filtered["publish_date"])
    return request_cls(**filtered)


def _coerce_publish_date(value: Any) -> datetime | int:
    if value in (None, 0, "", "0"):
        return 0
    if isinstance(value, datetime):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"unsupported publish_date: {value!r}")


def _run_bilibili(payload: dict, bridge: TaskProgressBridge | None) -> dict:
    """Synchronous biliup invocation. We still surface progress through the bridge."""
    account_name = payload["account_name"]
    title = payload.get("title", "")

    arguments = [
        "-u",
        str(sau_cli.resolve_account_file("bilibili", account_name)),
        "upload",
        str(payload["video_file"]),
        "--title",
        title,
        "--desc",
        payload.get("description", ""),
        "--tid",
        str(payload.get("tid")),
    ]
    if payload.get("tags"):
        arguments.extend(["--tag", ",".join(payload["tags"])])
    if payload.get("thumbnail_file"):
        arguments.extend(["--cover", str(payload["thumbnail_file"])])
    publish_date = payload.get("publish_date")
    if isinstance(publish_date, datetime):
        arguments.extend(["--dtime", str(int(publish_date.timestamp()))])

    async def _drive() -> dict:
        if bridge is not None:
            await bridge._enqueue("publish_started", {"platform": "bilibili", "account_name": account_name, "title": title})
        # biliup is a sync subprocess; run it in a thread so we don't block the loop.
        result = await asyncio.to_thread(run_biliup_command, arguments)
        ok = result.returncode == 0
        if bridge is not None:
            terminal_event = "publish_completed" if ok else "publish_failed"
            payload_extra: dict[str, Any] = {"platform": "bilibili", "account_name": account_name, "returncode": result.returncode}
            if not ok:
                payload_extra["error"] = (result.stderr or result.stdout or "").strip()
            await bridge._enqueue(terminal_event, payload_extra)
            bridge.close(terminal_event, payload_extra)
        if not ok:
            raise RuntimeError((result.stderr or result.stdout or "").strip() or "Bilibili upload failed")
        return {"status": "success", "account_file": str(sau_cli.resolve_account_file("bilibili", account_name))}

    return asyncio.create_task(_drive())


async def resolve_account_file(platform: str, account_name: str) -> Path:
    return Path(sau_cli.resolve_account_file(platform, account_name))
