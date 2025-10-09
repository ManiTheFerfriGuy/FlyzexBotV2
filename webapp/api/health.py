"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    storage_loaded = getattr(request.app.state, "storage", None) is not None
    storage_read_only = bool(getattr(request.app.state, "storage_read_only", False))
    return HealthResponse(
        status="ok",
        storage_loaded=storage_loaded,
        storage_read_only=storage_read_only,
    )
