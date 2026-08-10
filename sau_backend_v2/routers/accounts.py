"""Account CRUD + SSE login flow + cookie upload/download."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

import sau_cli
from sau_backend_v2.config import COOKIES_DIR
from sau_backend_v2.models.schemas import AccountCreate, AccountOut, AccountStatusUpdate
from sau_backend_v2.routers.auth import require_token
from sau_backend_v2.services import db
from sau_backend_v2.services.login_stream import manual_login_message, stream_login

logger = logging.getLogger("sau.v2.accounts")

router = APIRouter(prefix="/api/accounts", tags=["accounts"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[AccountOut])
def list_accounts(platform: str | None = None) -> list[AccountOut]:
    rows = db.list_accounts(platform)
    return [AccountOut(**row) for row in rows]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate) -> AccountOut:
    # Mirror the legacy convention: cookie file lives at cookies/<platform>_<account>.json.
    filename = f"{payload.platform}_{payload.user_name}.json"
    file_path = str(COOKIES_DIR / filename)
    if not Path(file_path).exists():
        # Make sure the cookies directory exists even before the cookie is generated.
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(file_path).write_text(json.dumps({"cookies": [], "origins": []}))
    account_id = db.insert_account(payload.platform, file_path, payload.user_name)
    return AccountOut(
        id=account_id,
        platform=payload.platform,
        type=_platform_to_type(payload.platform),
        file_path=file_path,
        user_name=payload.user_name,
        status=0,
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int) -> None:
    account = db.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    db.delete_account(account_id)
    cookie_file = Path(account["file_path"])
    if cookie_file.exists():
        cookie_file.unlink()


@router.post("/{account_id}/check", response_model=AccountOut)
async def check_account(account_id: int) -> AccountOut:
    """Re-validate the account's cookie by hitting each platform's check_cookie."""
    account = db.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    is_ready = await _run_cookie_auth(account["platform"], account["file_path"])
    db.update_account_status(account_id, 1 if is_ready else 0)
    refreshed = db.get_account_by_id(account_id)
    return AccountOut(**refreshed)


@router.get("/{account_id}/login")
async def login_account(account_id: int) -> StreamingResponse:
    """SSE stream of the login flow (QR codes + status)."""
    account = db.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")

    async def event_source():
        manual = manual_login_message(account["platform"], account["user_name"])
        if manual is not None:
            yield _sse("info", {"message": manual})
            yield _sse("failed", {"message": "manual login required"})
            return
        async for chunk in stream_login(account["platform"], account["user_name"]):
            yield chunk
        # Mark the account as freshly logged in. We assume success when the
        # SSE generator returns without a `failed` event; the stream_login
        # wrapper guarantees a `result` event on the terminal branch.
        db.update_account_status(account_id, 1)

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.get("/{account_id}/cookie/download")
def download_cookie(account_id: int):
    account = db.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    file_path = Path(account["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cookie file missing")
    return StreamingResponse(
        iter([file_path.read_bytes()]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{file_path.name}"',
        },
    )


@router.post("/{account_id}/cookie/upload", response_model=AccountOut)
async def upload_cookie(account_id: int, file: UploadFile = File(...)) -> AccountOut:
    account = db.get_account_by_id(account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    contents = await file.read()
    try:
        json.loads(contents)  # validate shape
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"invalid cookie JSON: {exc}")
    file_path = Path(account["file_path"])
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(contents)
    db.update_account_status(account_id, 1)
    refreshed = db.get_account_by_id(account_id)
    return AccountOut(**refreshed)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sse(event: str, payload: dict) -> str:
    enriched = {"event": event, "ts": datetime.utcnow().isoformat() + "Z", **payload}
    return f"data: {json.dumps(enriched, ensure_ascii=False)}\n\n"


def _platform_to_type(platform: str) -> int:
    return {
        "xiaohongshu": 1,
        "tencent": 2,
        "douyin": 3,
        "kuaishou": 4,
        "bilibili": 5,
        "youtube": 0,
    }[platform]


async def _run_cookie_auth(platform: str, file_path: str) -> bool:
    """Call the platform's `cookie_auth` in-process."""
    if platform == "douyin":
        from uploader.douyin_uploader.main import cookie_auth as douyin_cookie_auth

        return await douyin_cookie_auth(file_path)
    if platform == "kuaishou":
        from uploader.ks_uploader.main import cookie_auth as ks_cookie_auth

        return await ks_cookie_auth(file_path)
    if platform == "xiaohongshu":
        from uploader.xiaohongshu_uploader.main import cookie_auth as xhs_cookie_auth

        return await xhs_cookie_auth(file_path)
    if platform == "tencent":
        from uploader.tencent_uploader.main import cookie_auth as tencent_cookie_auth

        return await tencent_cookie_auth(file_path)
    if platform == "youtube":
        from uploader.youtube_uploader.main import cookie_auth as yt_cookie_auth

        return await yt_cookie_auth(file_path)
    if platform == "bilibili":
        # biliup stores its own login state; the file's existence is the only
        # signal we have at the FastAPI layer.
        return Path(file_path).exists()
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"unsupported platform: {platform}")
