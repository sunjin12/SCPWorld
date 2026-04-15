"""Pydantic Settings for SCP World Backend."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings

# Minimal .env loader — populates os.environ so vars consumed directly by
# third-party libs (e.g. GOOGLE_APPLICATION_CREDENTIALS for google-auth) are
# visible at the process level, not just on the Settings instance.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or .env file."""

    # --- Firestore (RAG & Session) ---
    FIRESTORE_PROJECT_ID: str = "scpworld"
    FIRESTORE_DATABASE_ID: str = "(default)"
    FIRESTORE_COLLECTION: str = "scp_documents"
    FIRESTORE_SESSION_COLLECTION: str = "sessions"

    # --- vLLM: LLM (Qwen2.5-7B-Instruct on Cloud Run) ---
    VLLM_LLM_URL: str = "https://vllm-server-v3-hduoqgwvoq-as.a.run.app/v1"
    VLLM_LLM_MODEL: str = "qwen2.5-7b"

    # --- Embedding: CPU-based sentence-transformers (BGE-M3, 1024-dim) ---
    EMBED_MODEL_NAME: str = "BAAI/bge-m3"

    # --- Session ---
    MAX_CONVERSATION_TURNS: int = 10

    # --- Google OAuth 2.0 ---
    GOOGLE_CLIENT_ID: str = ""

    # Ignore env vars consumed directly by Google libs (e.g.
    # GOOGLE_APPLICATION_CREDENTIALS) so they can live in `.env` for local
    # dev without tripping pydantic's default `extra='forbid'`.
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
