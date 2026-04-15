"""Google OAuth 2.0 JWT verification middleware.

Used as a FastAPI Dependency on all /api/* routes except /api/auth/verify.
Extracts the Bearer token from the Authorization header, verifies it
against Google's public keys, and returns the authenticated user info.
"""

import logging

from fastapi import Depends, HTTPException, Header
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings
from app.models.schemas import AuthUser

logger = logging.getLogger(__name__)


async def verify_google_token(
    authorization: str = Header(..., description="Bearer <id_token>"),
) -> AuthUser:
    """
    FastAPI Dependency that validates Google ID tokens.

    Usage:
        @router.get("/api/protected")
        async def protected(user: AuthUser = Depends(verify_google_token)):
            ...
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization[7:]  # Strip "Bearer "

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        return AuthUser(
            user_id=idinfo["sub"],
            email=idinfo.get("email", ""),
            name=idinfo.get("name", ""),
            picture=idinfo.get("picture", ""),
        )
    except ValueError as e:
        logger.warning("Token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")
