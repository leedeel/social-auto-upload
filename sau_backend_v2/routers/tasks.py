"""Task listing and live event streams."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from sau_backend_v2.config import SSE_KEEPALIVE_SECONDS
from sau_backend_v2.models.schemas import TaskOut
from sau_backend_v2.routers.auth import require_token
from sau_backend_v2.services import db

logger = logging.getLogger("sau.v2.tasks")

router = APIRouter(prefix="/api/tasks", tags=["tasks"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[TaskOut])
def list_tasks(platform: str | None = None, limit: int = 100) -> list[TaskOut]:
    rows = db.list_tasks(limit=limit, platform=platform)
    return [TaskOut(**row) for row in rows]


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str) -> TaskOut:
    row = db.get_task(task_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return TaskOut(**row)


@router.get("/{task_id}/events")
async def stream_events(task_id: str) -> StreamingResponse:
    row = db.get_task(task_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")

    async def event_source() -> AsyncIterator[bytes]:
        # Replay the latest snapshot so a reconnecting client gets the current
        # state without losing context.
        snapshot = {
            "event": "snapshot",
            "ts": datetime.utcnow().isoformat() + "Z",
            "status": row["status"],
            "progress": row["progress"],
            "current_step": row["current_step"],
            "error": row["error"],
        }
        yield f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n".encode()

        if row["status"] in {"success", "failed"}:
            return

        last_keepalive = datetime.utcnow()
        while True:
            current = db.get_task(task_id)
            if current is None:
                return
            if current["status"] in {"success", "failed"}:
                terminal = {
                    "event": "publish_completed" if current["status"] == "success" else "publish_failed",
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "status": current["status"],
                    "progress": current["progress"],
                    "error": current["error"],
                }
                yield f"data: {json.dumps(terminal, ensure_ascii=False)}\n\n".encode()
                return
            now = datetime.utcnow()
            if (now - last_keepalive).total_seconds() >= SSE_KEEPALIVE_SECONDS:
                yield b": keepalive\n\n"
                last_keepalive = now
            await _sleep(1.0)

    return StreamingResponse(event_source(), media_type="text/event-stream")


async def _sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)
