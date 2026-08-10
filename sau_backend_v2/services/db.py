"""SQLite access for the v2 backend.

The v2 backend re-uses the legacy `database.db` file so account data lives in
one place. It owns a single `tasks` table for publish/comment task tracking
and a `comment_jobs` table reserved for M2 (auto-comment).

All helpers return plain dictionaries so route handlers can map them straight
into Pydantic responses without coupling to sqlite3.Row.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from sau_backend_v2.config import DATABASE_PATH


# sqlite3 connections are not safe to share across threads; one per request is
# the simplest correct model for an async FastAPI app that uses a thread pool
# for sync DB work.
_local = threading.local()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Yield a short-lived sqlite3 connection. Closes on exit."""
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema migrations
# ---------------------------------------------------------------------------

SCHEMA_STATEMENTS: tuple[str, ...] = (
    # Legacy tables — created on first run if they don't exist. Their shape is
    # documented in CLAUDE.md and `db/createTable.py`; we mirror it here so
    # the v2 backend can boot against a fresh `database.db`.
    """
    CREATE TABLE IF NOT EXISTS user_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type INTEGER NOT NULL,
        filePath TEXT NOT NULL,
        userName TEXT NOT NULL,
        status INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS file_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        filesize REAL,
        upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        file_path TEXT
    )
    """,
    # v2 tables.
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,                  -- 'publish' | 'comment'
        platform TEXT NOT NULL,
        account_name TEXT NOT NULL,
        title TEXT,
        status TEXT NOT NULL,                -- 'queued' | 'running' | 'success' | 'failed'
        progress INTEGER NOT NULL DEFAULT 0, -- 0..100
        current_step TEXT,
        error TEXT,
        request_payload TEXT NOT NULL,       -- JSON
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS comment_jobs (
        id TEXT PRIMARY KEY,
        rule_id TEXT,
        platform TEXT NOT NULL,
        account_name TEXT NOT NULL,
        video_id TEXT NOT NULL,
        comment_text TEXT NOT NULL,
        status TEXT NOT NULL,
        error TEXT,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    )
    """,
)


def run_migrations() -> None:
    """Idempotently create the v2 schema. Safe to call on every startup."""
    with connection() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.commit()


# ---------------------------------------------------------------------------
# Task helpers
# ---------------------------------------------------------------------------


def create_task(task: dict) -> None:
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO tasks (
                id, type, platform, account_name, title, status, progress,
                current_step, request_payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task["id"],
                task["type"],
                task["platform"],
                task["account_name"],
                task.get("title", ""),
                task["status"],
                task.get("progress", 0),
                task.get("current_step"),
                json.dumps(task["request_payload"], ensure_ascii=False),
                task["created_at"],
                task["updated_at"],
            ),
        )
        conn.commit()


def update_task(task_id: str, **fields) -> None:
    if not fields:
        return
    fields["updated_at"] = datetime.utcnow()
    columns = ", ".join(f"{name} = ?" for name in fields)
    values: list = list(fields.values())
    values.append(task_id)
    with connection() as conn:
        conn.execute(f"UPDATE tasks SET {columns} WHERE id = ?", values)
        conn.commit()


def get_task(task_id: str) -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    return _row_to_task(row)


def list_tasks(limit: int = 100, platform: str | None = None) -> list[dict]:
    query = "SELECT * FROM tasks"
    args: list = []
    if platform:
        query += " WHERE platform = ?"
        args.append(platform)
    query += " ORDER BY created_at DESC LIMIT ?"
    args.append(limit)
    with connection() as conn:
        rows = conn.execute(query, args).fetchall()
    return [_row_to_task(row) for row in rows]


def _row_to_task(row: sqlite3.Row) -> dict:
    payload = row["request_payload"]
    if payload:
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            payload = None
    else:
        payload = None
    return {
        "id": row["id"],
        "type": row["type"],
        "platform": row["platform"],
        "account_name": row["account_name"],
        "title": row["title"],
        "status": row["status"],
        "progress": row["progress"],
        "current_step": row["current_step"],
        "error": row["error"],
        "request_payload": payload,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ---------------------------------------------------------------------------
# Account / file_record helpers (read-only views over legacy tables)
# ---------------------------------------------------------------------------


def list_accounts(platform: str | None = None) -> list[dict]:
    # type mapping mirrors `sau_frontend/src/stores/account.js` and the legacy
    # `myUtils/postVideo.py` integer codes. Keep them in sync.
    platform_to_type = {
        "douyin": 3,
        "kuaishou": 4,
        "xiaohongshu": 1,
        "tencent": 2,
        "bilibili": 5,
        "youtube": None,
    }

    with connection() as conn:
        if platform:
            type_code = platform_to_type.get(platform)
            if type_code is None:
                return []
            rows = conn.execute(
                "SELECT * FROM user_info WHERE type = ? ORDER BY id DESC",
                (type_code,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM user_info ORDER BY id DESC").fetchall()
    return [_row_to_account(row) for row in rows]


def get_account_by_id(account_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM user_info WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        return None
    return _row_to_account(row)


def update_account_status(account_id: int, status: int) -> None:
    with connection() as conn:
        conn.execute("UPDATE user_info SET status = ? WHERE id = ?", (status, account_id))
        conn.commit()


def insert_account(platform: str, file_path: str, user_name: str) -> int:
    platform_to_type = {
        "douyin": 3,
        "kuaishou": 4,
        "xiaohongshu": 1,
        "tencent": 2,
        "bilibili": 5,
    }
    type_code = platform_to_type[platform]
    with connection() as conn:
        cursor = conn.execute(
            "INSERT INTO user_info (type, filePath, userName, status) VALUES (?, ?, ?, 0)",
            (type_code, file_path, user_name),
        )
        conn.commit()
        return int(cursor.lastrowid)


def delete_account(account_id: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
        conn.commit()


def _row_to_account(row: sqlite3.Row) -> dict:
    type_to_platform = {1: "xiaohongshu", 2: "tencent", 3: "douyin", 4: "kuaishou", 5: "bilibili"}
    return {
        "id": row["id"],
        "platform": type_to_platform.get(row["type"], "unknown"),
        "type": row["type"],
        "file_path": row["filePath"],
        "user_name": row["userName"],
        "status": row["status"],
    }


def list_file_records() -> list[dict]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM file_records ORDER BY upload_time DESC").fetchall()
    return [dict(row) for row in rows]


def insert_file_record(filename: str, file_path: str, filesize: float) -> int:
    with connection() as conn:
        cursor = conn.execute(
            "INSERT INTO file_records (filename, file_path, filesize) VALUES (?, ?, ?)",
            (filename, file_path, filesize),
        )
        conn.commit()
        return int(cursor.lastrowid)


def delete_file_record(record_id: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM file_records WHERE id = ?", (record_id,))
        conn.commit()
