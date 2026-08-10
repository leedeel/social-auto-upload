"""Publish endpoints: submit a single publish task, or fan out a batch.

The single-publish path is the workhorse — it persists a `tasks` row, then
schedules a background coroutine that runs the uploader and pushes events
into a per-task `TaskProgressBridge`. The `/api/tasks/{id}/events` SSE
stream drains that bridge.

Batch dispatch is intentionally simple: it spawns N concurrent single
publishes (with same-account lock-out deferred to the front-end for M1).
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from sau_backend_v2.models.schemas import PublishRequest
from sau_backend_v2.routers.auth import require_token
from sau_backend_v2.services import db
from sau_backend_v2.services.cli_runner import dispatch_publish
from sau_backend_v2.services.progress_bridge import TaskProgressBridge

logger = logging.getLogger("sau.v2.publish")

router = APIRouter(prefix="/api/publish", tags=["publish"], dependencies=[Depends(require_token)])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def submit_publish(request: PublishRequest, background_tasks: BackgroundTasks) -> dict:
    payload = request.model_dump(mode="json")
    task_id = uuid.uuid4().hex
    now = datetime.utcnow()
    db.create_task(
        {
            "id": task_id,
            "type": "publish",
            "platform": request.platform,
            "account_name": request.account_name,
            "title": request.title if hasattr(request, "title") else "",
            "status": "queued",
            "progress": 0,
            "current_step": "queued",
            "request_payload": payload,
            "created_at": now,
            "updated_at": now,
        }
    )
    bridge = TaskProgressBridge(task_id)
    background_tasks.add_task(_run_publish_task, task_id, request.platform, request.kind, payload, bridge)
    return {"task_id": task_id, "status": "queued"}


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def submit_batch(requests: list[PublishRequest]) -> dict:
    if not requests:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty batch")
    # Reject obvious same-account collisions so we don't trip the per-cookie
    # lock-out at runtime. Different platforms/accounts can run concurrently.
    seen: set[tuple[str, str]] = set()
    for r in requests:
        key = (r.platform, r.account_name)
        if key in seen:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"duplicate account in batch: {r.platform}/{r.account_name}",
            )
        seen.add(key)
    task_ids = []
    for r in requests:
        payload = r.model_dump(mode="json")
        task_id = uuid.uuid4().hex
        now = datetime.utcnow()
        db.create_task(
            {
                "id": task_id,
                "type": "publish",
                "platform": r.platform,
                "account_name": r.account_name,
                "title": r.title if hasattr(r, "title") else "",
                "status": "queued",
                "progress": 0,
                "current_step": "queued",
                "request_payload": payload,
                "created_at": now,
                "updated_at": now,
            }
        )
        bridge = TaskProgressBridge(task_id)
        asyncio.create_task(_run_publish_task(task_id, r.platform, r.kind, payload, bridge))
        task_ids.append(task_id)
    return {"task_ids": task_ids, "status": "queued"}


async def _run_publish_task(
    task_id: str,
    platform: str,
    kind: str,
    payload: dict,
    bridge: TaskProgressBridge,
) -> None:
    try:
        await dispatch_publish(platform, kind, payload, bridge=bridge)
    except Exception as exc:  # noqa: BLE001
        logger.exception("publish task %s failed", task_id)
        db.update_task(task_id, status="failed", error=str(exc), progress=bridge._last_percent)
        bridge.close("publish_failed", {"error": str(exc)})
