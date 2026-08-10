"""Material library: upload, list, preview, delete.

Materials land in `videos/` (the same directory the legacy backend and CLI
samples use) and are tracked in the legacy `file_records` table. We do
NOT touch the existing samples; uploaded files get a uuid prefix to avoid
collisions.
"""
from __future__ import annotations

import logging
import mimetypes
import re
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from sau_backend_v2.config import MATERIALS_DIR
from sau_backend_v2.models.schemas import MaterialOut
from sau_backend_v2.routers.auth import require_token
from sau_backend_v2.services import db

logger = logging.getLogger("sau.v2.materials")

router = APIRouter(prefix="/api/materials", tags=["materials"], dependencies=[Depends(require_token)])


SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


@router.get("", response_model=list[MaterialOut])
def list_materials() -> list[MaterialOut]:
    rows = db.list_file_records()
    return [MaterialOut(**row) for row in rows]


@router.post("", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
async def upload_material(file: UploadFile = File(...)) -> MaterialOut:
    original_name = Path(file.filename or "upload").name
    safe = SAFE_NAME.sub("_", original_name)
    target_name = f"{uuid.uuid4().hex[:12]}_{safe}"
    target_path = MATERIALS_DIR / target_name
    contents = await file.read()
    target_path.write_bytes(contents)
    record_id = db.insert_file_record(original_name, target_name, len(contents) / (1024 * 1024))
    record = db.list_file_records()
    for row in record:
        if row["id"] == record_id:
            return MaterialOut(**row)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="inserted record not found")


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(record_id: int) -> None:
    rows = db.list_file_records()
    record = next((row for row in rows if row["id"] == record_id), None)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="material not found")
    target = MATERIALS_DIR / record["file_path"]
    if target.exists():
        target.unlink()
    db.delete_file_record(record_id)


@router.get("/{record_id}/preview")
def preview_material(record_id: int) -> FileResponse:
    rows = db.list_file_records()
    record = next((row for row in rows if row["id"] == record_id), None)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="material not found")
    target = MATERIALS_DIR / record["file_path"]
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file missing on disk")
    media_type, _ = mimetypes.guess_type(target.name)
    return FileResponse(target, media_type=media_type or "application/octet-stream")
