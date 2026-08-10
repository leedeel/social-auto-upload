"""Authentication routes. Single shared bearer token for now; replace with
a real user store before any non-local deployment.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sau_backend_v2.config import DEFAULT_API_TOKEN
from sau_backend_v2.models.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Token source: env var > default. The front-end reads its expected token
# from a build-time env var (`VITE_API_TOKEN`); keeping the same default
# here lets the dev experience "just work" out of the box.
EXPECTED_TOKEN = os.environ.get("SAU_API_TOKEN", DEFAULT_API_TOKEN)
EXPECTED_USERNAME = os.environ.get("SAU_API_USERNAME", "admin")
EXPECTED_PASSWORD = os.environ.get("SAU_API_PASSWORD", "admin")

bearer_scheme = HTTPBearer(auto_error=False)


def require_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> str:
    if credentials is None or credentials.credentials != EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if payload.username != EXPECTED_USERNAME or payload.password != EXPECTED_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return TokenResponse(access_token=EXPECTED_TOKEN)


@router.get("/me", dependencies=[Depends(require_token)])
def whoami() -> dict[str, str]:
    return {"username": EXPECTED_USERNAME, "token": EXPECTED_TOKEN[:8] + "..."}
