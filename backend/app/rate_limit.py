from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_rate_limit_key(request: Request) -> str:
    """
    Custom rate limit key function.

    Uses Firebase UID when user is authenticated, falls back to IP address.
    This prevents users behind NAT from sharing rate limits and provides
    per-user rate limiting for authenticated endpoints.
    """
    # Try to get Firebase UID from request state (set by auth middleware)
    firebase_uid = getattr(request.state, "firebase_uid", None)
    if firebase_uid:
        return f"firebase:{firebase_uid}"

    # Fall back to IP address for unauthenticated requests
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=get_rate_limit_key)
