"""Progress bridge: asyncio.Queue per task → SSE stream.

The uploader code (`uploader/*/main.py`) calls a synchronous or async
callback registered by `cli_runner`. We don't want that callback to block
the uploader, so we route every event through an `asyncio.Queue` that the
SSE handler drains in its own task.

The bridge also writes a snapshot into the `tasks` table so a polling
client (or a reconnecting SSE client) can recover the latest known state.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, Mapping

import sau_backend_v2.services.db as db

logger = logging.getLogger("sau.v2.progress")


class TaskProgressBridge:
    """One bridge per running task. Holds a Queue and the latest snapshot."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._closed = False
        self._last_step: str | None = None
        self._last_percent: int = 0

    def callback(self, event: str, payload: Mapping[str, Any]) -> Any:
        """Build a closure that matches `BaseVideoUploader._emit_progress`.

        Sync or async is handled inside `_safe_call`.
        """
        return _safe_call(self._enqueue, event, payload)

    async def _enqueue(self, event: str, payload: Mapping[str, Any]) -> None:
        if self._closed:
            return
        normalized = dict(payload) if payload else {}
        normalized.setdefault("event", event)
        normalized.setdefault("ts", datetime.utcnow().isoformat() + "Z")

        # Coarse progress percent derived from event name. The uploader can
        # also pass an explicit `percent` in payload, which wins.
        if "percent" in normalized:
            try:
                self._last_percent = max(0, min(100, int(normalized["percent"])))
            except (TypeError, ValueError):
                pass
        else:
            self._last_percent = _percent_for_event(event, self._last_percent)
        normalized["percent"] = self._last_percent

        if "current_step" in normalized:
            self._last_step = str(normalized["current_step"])
        else:
            self._last_step = event

        # Persist the snapshot so reconnects can read it without losing context.
        try:
            db.update_task(
                self.task_id,
                progress=self._last_percent,
                current_step=self._last_step,
                status=_status_for_event(event),
            )
        except Exception:  # noqa: BLE001 — DB write is best-effort, never break the uploader
            logger.exception("failed to update task %s progress", self.task_id)

        await self._queue.put(normalized)

    async def stream(self) -> Any:
        """Async generator that yields JSON-encoded SSE events until the bridge closes."""
        terminal = {"success", "failed", "cancelled"}
        while True:
            event = await self._queue.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("event") in terminal:
                self._closed = True
                return

    def close(self, event: str = "cancelled", payload: Mapping[str, Any] | None = None) -> None:
        """Drop a terminal event so the SSE generator can exit.

        Called from the CLI runner when the underlying uploader finishes
        (success or failure). Safe to call multiple times.
        """
        if self._closed:
            return
        full_payload = dict(payload) if payload else {}
        full_payload.setdefault("event", event)
        full_payload.setdefault("ts", datetime.utcnow().isoformat() + "Z")
        full_payload.setdefault("percent", self._last_percent)
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._enqueue(event, full_payload))
        except RuntimeError:
            # No running loop (e.g. called from sync code). Fall back to a
            # best-effort queue.put_nowait.
            try:
                self._queue.put_nowait(full_payload)
            except Exception:  # noqa: BLE001
                logger.exception("failed to enqueue terminal event for %s", self.task_id)
        self._closed = True


async def _safe_call(fn: Callable[..., Awaitable[None] | None], event: str, payload: Mapping[str, Any]) -> None:
    """Invoke an event sink whether it's sync or async without blocking the uploader.

    The uploader `await`s callbacks, so the FastAPI path must always return
    either `None` (for sync) or a coroutine we can await.
    """
    try:
        result = fn(event, payload)
    except Exception:  # noqa: BLE001 — never let a callback crash the uploader
        logger.exception("progress sink raised (event=%s)", event)
        return
    if inspect.isawaitable(result):
        await result


def _percent_for_event(event: str, previous: int) -> int:
    """Coarse progress mapping when the uploader doesn't send `percent`."""
    table = {
        "publish_started": max(previous, 5),
        "login_check_ok": max(previous, 10),
        "video_uploading": max(previous, 40),
        "video_uploaded": max(previous, 70),
        "metadata_filled": max(previous, 85),
        "publish_submitted": max(previous, 95),
        "publish_completed": 100,
        "publish_failed": previous,
    }
    return table.get(event, previous)


def _status_for_event(event: str) -> str:
    if event in {"publish_started", "login_check_ok", "video_uploading", "video_uploaded", "metadata_filled", "publish_submitted"}:
        return "running"
    if event == "publish_completed":
        return "success"
    if event in {"publish_failed"}:
        return "failed"
    return "running"
