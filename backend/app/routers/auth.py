from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..logger import get_logger

# Initialize logger for auth
logger = get_logger("auth")

router = APIRouter()

@router.get("/auth/me")
async def get_current_user_info(user=Depends(get_current_user)):
    """Check current identity using Firebase token."""
    logger.info(f"Identity check for UID: ...{user['uid'][-4:]}")
    return {
        "uid": user["uid"],
        "email": user.get("email"),
        "authenticated": True
    }

