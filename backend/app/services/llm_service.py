"""LLM service — vLLM OpenAI-compatible API with SSE streaming support."""

import json
from collections.abc import AsyncGenerator

import httpx

from app.config import settings
from app.dependencies import get_vllm_id_token


def _auth_headers() -> dict:
    """Build Authorization header with a Cloud Run ID token when available."""
    token = get_vllm_id_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


class LLMService:
    """Calls vLLM's /v1/chat/completions endpoint (streaming + non-streaming)."""

    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client
        self.model = settings.VLLM_LLM_MODEL

    async def generate_stream(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from vLLM one at a time."""
        async with self.client.stream(
            "POST",
            "/chat/completions",
            headers=_auth_headers(),
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    async def generate(
        self,
        messages: list[dict],
        *,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
    ) -> str:
        """Non-streaming generation (fallback)."""
        response = await self.client.post(
            "/chat/completions",
            headers=_auth_headers(),
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def health_check(self) -> bool:
        """Check if the LLM endpoint is reachable."""
        try:
            response = await self.client.get("/models", headers=_auth_headers())
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
