import os
from typing import Optional
import firebase_admin.auth as firebase_auth
from fastapi import Request, HTTPException, Header
from . import services

from .logger import get_logger

logger = get_logger("dependencies")

# Mock user for testing purposes
MOCK_USER = {
    "uid": "test_user_id",
    "email": "test@example.com",
    "email_verified": True,
    "name": "Test User"
}

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
    # 1. Bypass real Firebase if in TESTING mode
    if os.getenv("TESTING") == "true":
        return MOCK_USER

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty authentication token")
        
    try:
        # Verify the ID token and get decoded token content
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token  # Contains uid, email, etc.
    except Exception as e:
        logger.exception(f"Auth verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication token") from e

async def get_optional_user(authorization: Optional[str] = Header(None)):
    """Optional dependency to get Firebase user if token is present, otherwise returns None."""
    # 1. Bypass real Firebase if in TESTING mode
    if os.getenv("TESTING") == "true":
        return MOCK_USER

    if not authorization or not authorization.startswith("Bearer "):
        return None
        
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
        
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        # Silently fail for optional user but log the error
        logger.exception(f"Optional auth verification failed: {str(e)}")
        return None
