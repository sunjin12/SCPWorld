"""SCP World — FastAPI Application Entrypoint."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import close_clients, get_embedding_service
from app.routers import auth, chat, health, personas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _preload_embedding() -> None:
    """Load BGE-M3 in a worker thread so the first chat request doesn't pay
    the cost. Runs in the background — startup must NOT block on it, or
    Cloud Run's startup probe times out before the container is reachable."""
    try:
        await asyncio.to_thread(get_embedding_service)
        logger.info("✅ Embedding model ready.")
    except Exception as e:  # pragma: no cover - logged for observability
        logger.exception("Failed to preload embedding model: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 SCP World Backend starting up...")
    logger.info("📐 Scheduling embedding model preload in background...")
    asyncio.create_task(_preload_embedding())
    yield
    logger.info("🛑 Shutting down — closing clients...")
    await close_clients()
    logger.info("✅ Shutdown complete.")


app = FastAPI(
    title="SCP World API",
    description=(
        "SCP Foundation AI Persona Chatbot — "
        "RAG-based knowledge retrieval with SSE streaming responses. "
        "Content based on the SCP Foundation Wiki (CC-BY-SA 3.0)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — Flutter web (Firebase Hosting) + local dev (any localhost port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://scpworld.web.app",
        "https://scpworld.firebaseapp.com",
    ],
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(personas.router)


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "name": "SCP World API",
        "version": "0.1.0",
        "docs": "/docs",
        "license": "CC-BY-SA 3.0 (Source: SCP Foundation)",
    }
