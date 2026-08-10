"""FastAPI entrypoint for sau_backend_v2.

Run locally:
    uvicorn sau_backend_v2.main:app --reload --port 6409

The dev React app talks to this through a Vite proxy on `/api`. CORS is
allowed for the standard Vite ports (6173).
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sau_backend_v2.config import DEV_ORIGINS, ensure_directories
from sau_backend_v2.routers import accounts, auth, materials, publish, tasks
from sau_backend_v2.services import db

# Ensure logs/ exists for our own log handler.
LOG_DIR = Path(__file__).resolve().parent.parent / "logs" / "v2"


def _configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=os.environ.get("SAU_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_DIR / "sau_backend_v2.log", encoding="utf-8"),
        ],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    ensure_directories()
    db.run_migrations()
    yield


app = FastAPI(
    title="sau_backend_v2",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "sau_backend_v2", "status": "ok"}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(materials.router)
app.include_router(publish.router)
app.include_router(tasks.router)
