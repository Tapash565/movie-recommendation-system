from fastapi import APIRouter, Depends, Request
from ..dependencies import get_current_user
from ..logger import get_logger

# Initialize logger for auth
logger = get_logger("auth")

from ..rate_limit import limiter

router = APIRouter()

@router.get("/auth/me")
@limiter.limit("5/minute")
async def get_current_user_info(request: Request, user=Depends(get_current_user)):
    """Check current identity using Firebase token."""
    uid = user.get("uid", "unknown")
    uid_tail = uid[-4:] if isinstance(uid, str) and len(uid) >= 4 else uid
    logger.info(f"Identity check for UID: ...{uid_tail}")
    return {
        "uid": uid,
        "email": user.get("email"),
        "authenticated": True
    }

