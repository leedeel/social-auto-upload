"""sau_backend_v2 runtime config.

Mirrors the legacy `conf.py` shape but exposes only what the new HTTP layer
needs. The CLI uploader code keeps reading from the project-root `conf.py`
unchanged — we do not import the new layer there.
"""
from __future__ import annotations

from pathlib import Path

# Project root is the directory that contains both `conf.py` and `cookies/`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cookie storage is the new directory the CLI uses (`<platform>_<account>.json`).
COOKIES_DIR = PROJECT_ROOT / "cookies"

# Material library. New uploads land here with a uuid prefix to avoid collisions.
# The CLI also reads from `videos/` for sample assets, but the v2 backend writes
# only to MATERIALS_DIR so we can list/delete with confidence.
MATERIALS_DIR = PROJECT_ROOT / "videos"

# Logs for the v2 service itself (separate from the per-uploader logs/).
LOG_DIR = PROJECT_ROOT / "logs" / "v2"

# SQLite database file. We re-use the legacy `database.db` so account records
# stay in one place; the v2 backend adds a `tasks` table alongside the legacy
# `user_info` and `file_records`.
DATABASE_PATH = PROJECT_ROOT / "database.db"

# CORS allow-list for the new React dev server. The production build serves from
# the same origin so this is mostly a dev convenience.
DEV_ORIGINS = [
    "http://localhost:6173",
    "http://127.0.0.1:6173",
]

# Authentication. The v2 layer ships a single shared token loaded from env, so
# the React shell can present a static login form. Rotating the token requires
# updating both the env and the front-end `.env` file.
DEFAULT_API_TOKEN = "sau-dev-token-change-me"

# SSE keepalive. The front-end's EventSource drops the connection if it sees
# no traffic for ~30s, so we emit a comment line at this interval.
SSE_KEEPALIVE_SECONDS = 15


def ensure_directories() -> None:
    """Create runtime directories on startup. Idempotent."""
    for path in (COOKIES_DIR, MATERIALS_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
