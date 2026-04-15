"""GET /health — liveness + dependency status."""
from __future__ import annotations

from fastapi import APIRouter

from services import temporal_client, langfuse_client

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    temporal_ok = await temporal_client.is_connected()
    langfuse_ok = await langfuse_client.is_connected()
    return {
        "status": "ok",
        "temporal": temporal_ok,
        "langfuse": langfuse_ok,
    }
