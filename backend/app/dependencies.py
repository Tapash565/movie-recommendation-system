import os
from typing import Optional
import firebase_admin.auth as firebase_auth
from fastapi import Request, HTTPException, Header
from . import services

from .logger import get_logger

logger = get_logger("dependencies")

# Mock user for testing purposes (returned as a copy to prevent mutation bleed)
_MOCK_USER = {
    "uid": "test_user_id",
    "email": "test@example.com",
    "email_verified": True,
    "name": "Test User"
}


def _is_auth_bypass_enabled() -> bool:
    """Check if auth bypass is explicitly enabled (requires both TESTING and ALLOW_AUTH_BYPASS)."""
    return os.getenv("TESTING") == "true" and os.getenv("ALLOW_AUTH_BYPASS") == "true"


def get_df(request: Request):
    """Dependency to get the movie dataframe from app state."""
    return request.app.state.df

def get_retriever(request: Request):
    """Dependency to get the lazy-loaded retriever from app state."""
    if request.app.state.retriever is None:
        request.app.state.retriever = services.load_retriever()
    return request.app.state.retriever

async def get_current_user(authorization: str = Header(None)):
    """Dependency to verify Firebase ID token and return user identity."""
    if _is_auth_bypass_enabled():
        logger.warning("AUTH BYPASS ACTIVE: Returning mock user (TESTING + ALLOW_AUTH_BYPASS)")
        return _MOCK_USER.copy()

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty authentication token")
        
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.exception(f"Auth verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication token") from e

async def get_optional_user(authorization: Optional[str] = Header(None)):
    """Optional dependency to get Firebase user if token is present, otherwise returns None."""
    if _is_auth_bypass_enabled():
        # Allow tests to simulate anonymous users via TEST_FORCE_ANONYMOUS
        if os.getenv("TEST_FORCE_ANONYMOUS") == "true":
            return None
        logger.warning("AUTH BYPASS ACTIVE: Returning mock user (TESTING + ALLOW_AUTH_BYPASS)")
        return _MOCK_USER.copy()

    if not authorization or not authorization.startswith("Bearer "):
        return None
        
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
        
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.exception(f"Optional auth verification failed: {str(e)}")
        return None
