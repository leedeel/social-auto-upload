from __future__ import annotations

import inspect
from datetime import datetime, timedelta
from pathlib import Path
from typing import Awaitable, Callable, Mapping

ProgressCallback = Callable[[str, Mapping[str, object]], Awaitable[None] | None]


class BaseVideoUploader:
    SUPPORTED_VIDEO_EXTENSIONS = {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".m4v",
        ".webm",
        ".flv",
        ".wmv",
    }
    SUPPORTED_IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
    }
    MIN_SCHEDULE_LEAD_TIME = timedelta(hours=2)

    def __init__(self, *args, progress_callback: ProgressCallback | None = None, **kwargs) -> None:
        # Default sink is a no-op. Platform-specific `__init__` overrides
        # should forward `progress_callback` here so `_emit_progress`
        # becomes a single point of fan-out for both CLI and FastAPI paths.
        self.progress_callback = progress_callback

    async def _emit_progress(self, event: str, payload: Mapping[str, object] | None = None) -> None:
        callback = getattr(self, "progress_callback", None)
        if not callback:
            return

        result = callback(event, dict(payload) if payload else {})
        if inspect.isawaitable(result):
            await result

    @classmethod
    def validate_video_file(cls, file_path: str | Path) -> Path:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"视频文件不存在: {path}")
        if not path.is_file():
            raise ValueError(f"视频路径不是文件: {path}")
        if path.suffix.lower() not in cls.SUPPORTED_VIDEO_EXTENSIONS:
            raise ValueError(
                f"不支持的视频格式: {path.suffix}，当前支持: {', '.join(sorted(cls.SUPPORTED_VIDEO_EXTENSIONS))}"
            )

        return path

    @classmethod
    def validate_image_file(cls, file_path: str | Path) -> Path:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {path}")
        if not path.is_file():
            raise ValueError(f"图片路径不是文件: {path}")
        if path.suffix.lower() not in cls.SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"不支持的图片格式: {path.suffix}，当前支持: {', '.join(sorted(cls.SUPPORTED_IMAGE_EXTENSIONS))}"
            )
        return path

    @classmethod
    def validate_publish_date(cls, publish_date: datetime | int | None) -> datetime | int:
        if publish_date in (None, 0):
            return 0

        if not isinstance(publish_date, datetime):
            raise TypeError("publish_date 必须是 datetime 类型或 0")

        now = datetime.now(tz=publish_date.tzinfo) if publish_date.tzinfo else datetime.now()
        if publish_date <= now:
            raise ValueError("定时发布时间必须晚于当前时间")

        min_publish_time = now + cls.MIN_SCHEDULE_LEAD_TIME
        if publish_date <= min_publish_time:
            raise ValueError("定时发布时间必须大于当前时间 2 小时")

        return publish_date
