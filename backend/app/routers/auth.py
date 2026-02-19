from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..logger import get_logger

# Initialize logger for auth
logger = get_logger("auth")

router = APIRouter()

@router.get("/auth/me")
async def get_current_user_info(user=Depends(get_current_user)):
    """Check current identity using Firebase token."""
    uid = user.get("uid", "unknown")
    uid_tail = uid[-4:] if isinstance(uid, str) and len(uid) >= 4 else uid
    logger.info(f"Identity check for UID: ...{uid_tail}")
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "authenticated": True
    }

