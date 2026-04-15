"""Shared dependencies for FastAPI dependency injection."""

import logging
import time
from functools import lru_cache
from urllib.parse import urlparse

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.cloud import firestore
from google.oauth2 import id_token as google_id_token

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


@lru_cache
def get_firestore_client() -> firestore.Client:
    """Singleton Firestore client."""
    return firestore.Client(
        project=settings.FIRESTORE_PROJECT_ID,
        database=settings.FIRESTORE_DATABASE_ID,
    )


def get_storage_service() -> StorageService:
    """Singleton Storage Service."""
    return StorageService(get_firestore_client())


_llm_http_client: httpx.AsyncClient | None = None
_embedding_service: EmbeddingService | None = None

# ID token cache: Cloud Run tokens live 1h; refresh every 50 min.
_ID_TOKEN_TTL = 50 * 60
_cached_id_token: str | None = None
_cached_id_token_expires_at: float = 0.0


def _vllm_audience() -> str:
    """Audience for Cloud Run ID token: the service base URL without path."""
    parsed = urlparse(settings.VLLM_LLM_URL)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_vllm_id_token() -> str | None:
    """Fetch a Google-signed ID token audience-bound to the vLLM Cloud Run service.

    Returns None in local development where the metadata server is unreachable.
    """
    global _cached_id_token, _cached_id_token_expires_at
    now = time.time()
    if _cached_id_token and now < _cached_id_token_expires_at:
        return _cached_id_token

    try:
        auth_req = GoogleAuthRequest()
        token = google_id_token.fetch_id_token(auth_req, _vllm_audience())
    except Exception as e:
        logger.warning("fetch_id_token failed (local dev assumed): %s", e)
        return None

    _cached_id_token = token
    _cached_id_token_expires_at = now + _ID_TOKEN_TTL
    return token


async def get_llm_http_client() -> httpx.AsyncClient:
    """HTTP client for vLLM LLM endpoint."""
    global _llm_http_client
    if _llm_http_client is None:
        _llm_http_client = httpx.AsyncClient(
            base_url=settings.VLLM_LLM_URL,
            timeout=httpx.Timeout(300.0, connect=30.0),
        )
    return _llm_http_client


def get_embedding_service() -> EmbeddingService:
    """Singleton CPU-based EmbeddingService (sentence-transformers)."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
        _embedding_service.load()
    return _embedding_service


async def close_clients():
    """Cleanup all clients on app shutdown."""
    global _llm_http_client
    if _llm_http_client:
        await _llm_http_client.aclose()
        _llm_http_client = None
