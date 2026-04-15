"""Auth router — Google OAuth 2.0 token verification."""

import logging

from fastapi import APIRouter, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings
from app.dependencies import get_storage_service
from app.models.schemas import AuthRequest, AuthResponse, AuthUser

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


@router.post("/api/auth/verify", response_model=AuthResponse)
async def verify_login(request: AuthRequest):
    """
    Verify a Google ID Token received from Flutter's google_sign_in.

    Returns verified user info. The client should store the ID token
    and include it as a Bearer token in subsequent API calls.
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            request.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        logger.warning("OAuth token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid Google ID Token")

    user = AuthUser(
        user_id=idinfo["sub"],
        email=idinfo.get("email", ""),
        name=idinfo.get("name", ""),
        picture=idinfo.get("picture", ""),
    )

    storage_service = get_storage_service()
    await storage_service.save_user(user.model_dump())

    logger.info("User verified: %s (%s)", user.email, user.user_id)
    return AuthResponse(user=user, status="verified")
