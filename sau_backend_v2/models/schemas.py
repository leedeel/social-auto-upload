"""Pydantic schemas for the v2 API.

These mirror the CLI's `*UploadRequest` dataclasses in `sau_cli.py`. Keep
field names and types in sync — `_services/cli_runner.py` filters payload
keys against the dataclass fields before construction, so a missing key
here doesn't crash the dispatch but it does silently drop the value.

The front-end's Zod schema (`sau_frontend_v2/src/shared/types.ts`) is the
authoritative shared contract; whenever you change a field here, mirror it
in Zod and bump a version constant in `shared/constants.ts`.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent", "youtube"]
Kind = Literal["video", "note"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


class AccountOut(BaseModel):
    id: int
    platform: Platform
    type: int
    file_path: str
    user_name: str
    status: int  # 0 = unknown, 1 = last check passed


class AccountCreate(BaseModel):
    platform: Platform
    user_name: str = Field(min_length=1)


class AccountStatusUpdate(BaseModel):
    status: int


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


class MaterialOut(BaseModel):
    id: int
    filename: str
    file_path: str
    filesize: float
    upload_time: datetime | None = None


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------


class DouyinVideoPublish(BaseModel):
    platform: Literal["douyin"]
    kind: Literal["video"]
    account_name: str
    title: str
    description: str = ""
    tags: list[str] = []
    video_file: str
    publish_date: datetime | int = 0
    thumbnail_file: str | None = None
    thumbnail_landscape_file: str | None = None
    thumbnail_portrait_file: str | None = None
    product_link: str = ""
    product_title: str = ""
    publish_strategy: str = "immediate"
    declaration: str | None = None


class DouyinNotePublish(BaseModel):
    platform: Literal["douyin"]
    kind: Literal["note"]
    account_name: str
    title: str
    note: str
    tags: list[str] = []
    image_files: list[str]
    publish_date: datetime | int = 0
    publish_strategy: str = "immediate"
    bgm: str = ""


class KuaishouVideoPublish(BaseModel):
    platform: Literal["kuaishou"]
    kind: Literal["video"]
    account_name: str
    title: str
    description: str = ""
    tags: list[str] = []
    video_file: str
    publish_date: datetime | int = 0
    thumbnail_file: str | None = None
    publish_strategy: str = "immediate"


class KuaishouNotePublish(BaseModel):
    platform: Literal["kuaishou"]
    kind: Literal["note"]
    account_name: str
    title: str
    note: str
    tags: list[str] = []
    image_files: list[str]
    publish_date: datetime | int = 0
    publish_strategy: str = "immediate"


class XiaohongshuVideoPublish(BaseModel):
    platform: Literal["xiaohongshu"]
    kind: Literal["video"]
    account_name: str
    title: str
    description: str = ""
    tags: list[str] = []
    video_file: str
    publish_date: datetime | int = 0
    thumbnail_file: str | None = None
    publish_strategy: str = "immediate"


class XiaohongshuNotePublish(BaseModel):
    platform: Literal["xiaohongshu"]
    kind: Literal["note"]
    account_name: str
    title: str
    note: str
    tags: list[str] = []
    image_files: list[str]
    publish_date: datetime | int = 0
    publish_strategy: str = "immediate"


class BilibiliVideoPublish(BaseModel):
    platform: Literal["bilibili"]
    kind: Literal["video"]
    account_name: str
    title: str
    description: str = ""
    tags: list[str] = []
    video_file: str
    publish_date: datetime | int = 0
    thumbnail_file: str | None = None
    tid: int


class TencentVideoPublish(BaseModel):
    platform: Literal["tencent"]
    kind: Literal["video"]
    account_name: str
    title: str
    description: str = ""
    tags: list[str] = []
    video_file: str
    publish_date: datetime | int = 0
    thumbnail_file: str | None = None
    publish_strategy: str = "immediate"


class YouTubeVideoPublish(BaseModel):
    platform: Literal["youtube"]
    kind: Literal["video"]
    account_name: str
    title: str
    description: str = ""
    tags: list[str] = []
    video_file: str
    publish_date: datetime | int = 0
    thumbnail_file: str | None = None
    playlist: str | None = None
    visibility: str = "public"


PublishRequest = (
    DouyinVideoPublish
    | DouyinNotePublish
    | KuaishouVideoPublish
    | KuaishouNotePublish
    | XiaohongshuVideoPublish
    | XiaohongshuNotePublish
    | BilibiliVideoPublish
    | TencentVideoPublish
    | YouTubeVideoPublish
)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


class TaskOut(BaseModel):
    id: str
    type: str
    platform: str
    account_name: str
    title: str | None = None
    status: str
    progress: int = 0
    current_step: str | None = None
    error: str | None = None
    request_payload: dict | None = None
    created_at: datetime
    updated_at: datetime
