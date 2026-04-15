"""Health check router — checks all backend dependencies."""

import logging

from fastapi import APIRouter

from app.dependencies import (
    get_embedding_service,
    get_llm_http_client,
    get_firestore_client,
)
from app.models.schemas import HealthResponse
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint (unauthenticated).

    Checks connectivity to Firestore, vLLM LLM, and CPU Embedding.
    Used by Cloud Run startup probes and Flutter splash screen.
    """
    status = "healthy"
    checks = {}

    # Firestore
    try:
        db = get_firestore_client()
        # Basic connectivity check: list collections
        db.collections()
        checks["firestore"] = "healthy"
    except Exception as e:
        checks["firestore"] = f"unhealthy: {e}"
        status = "degraded"

    # vLLM LLM
    try:
        llm_client = await get_llm_http_client()
        llm_svc = LLMService(llm_client)
        if await llm_svc.health_check():
            checks["vllm_llm"] = "healthy"
        else:
            checks["vllm_llm"] = "unhealthy"
            status = "degraded"
    except Exception as e:
        checks["vllm_llm"] = f"unhealthy: {e}"
        status = "degraded"

    # CPU Embedding (sentence-transformers, in-process)
    try:
        embed_svc = get_embedding_service()
        if await embed_svc.health_check():
            checks["embedding"] = "healthy (CPU)"
        else:
            checks["embedding"] = "unhealthy"
            status = "degraded"
    except Exception as e:
        checks["embedding"] = f"unhealthy: {e}"
        status = "degraded"

    return HealthResponse(status=status, **checks)


@router.get("/ready")
async def ready():
    """Simple readiness probe for Cloud Run."""
    return {"status": "ready"}
