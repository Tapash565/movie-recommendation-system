from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
import asyncio
from functools import partial
from ..schemas import BookmarkRequest, RatingRequest, UserPreferences, UserPreferencesUpdate

from .. import services
from ..dependencies import get_df, get_current_user
from ..rate_limit import limiter
from ..logger import get_logger
from ..services.firebase_service import delete_firebase_user
# _redact_uid lives in user_service — import it from there to avoid duplication (#6)
from ..services.user_service import _redact_uid


# Initialize logger for users
logger = get_logger("users")

router = APIRouter()


def _run_sync(func, *args):
    """Run a synchronous blocking function in a thread pool so it doesn't
    block the async event loop (#8)."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, partial(func, *args))


@router.get("/library")
@limiter.limit("20/minute")
async def get_library(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    user=Depends(get_current_user),
    df=Depends(get_df)
):
    """Get the user's movie library with pagination."""
    firebase_uid = user["uid"]
    email = user.get("email", "User")

    logger.info(f"User {_redact_uid(firebase_uid)} is viewing their library (Page: {page}).")

    if df.empty:
        logger.error("Movie data not available")
        return {
            "user": email,
            "to_watch": [],
            "watched": [],
            "rated_movies": [],
            "pagination": {"page": page, "page_size": page_size, "total": 0}
        }

    prefs = await _run_sync(services.get_preferences, firebase_uid)
    filter_adult = prefs.get("filter_adult", False)

    return await _run_sync(
        services.get_user_library, firebase_uid, email, df, page, page_size, filter_adult
    )


# --- API Endpoints ---


@router.post("/bookmark")
@limiter.limit("10/minute")
async def add_bookmark(request: Request, data: BookmarkRequest, user=Depends(get_current_user)):
    """API endpoint to add a movie to the user's library."""
    firebase_uid = user["uid"]
    logger.info(f"User {_redact_uid(firebase_uid)} setting bookmark for '{data.movie_title}' (ID: {data.movie_id}) to {data.status}")
    success = await _run_sync(services.add_bookmark, firebase_uid, data.movie_id, data.movie_title, data.status)
    return {"success": success}


@router.delete("/bookmark/{movie_id}")
@limiter.limit("10/minute")
async def remove_bookmark(request: Request, movie_id: int, user=Depends(get_current_user)):
    """API endpoint to remove a movie from the user's library (#7: was POST /remove_bookmark)."""
    firebase_uid = user["uid"]
    logger.info(f"User {_redact_uid(firebase_uid)} removing bookmark for movie ID: {movie_id}")
    result = await _run_sync(services.remove_bookmark, firebase_uid, movie_id)
    return {"success": result}


@router.post("/rate")
@limiter.limit("10/minute")
async def rate_movie(request: Request, data: RatingRequest, user=Depends(get_current_user)):
    """API endpoint to rate a movie."""
    firebase_uid = user["uid"]
    logger.info(f"User {_redact_uid(firebase_uid)} rated movie '{data.movie_title}' (ID: {data.movie_id}) as {data.rating}")
    success = await _run_sync(services.add_rating, firebase_uid, data.movie_id, data.movie_title, data.rating)
    return {"success": success}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_my_account(request: Request, user=Depends(get_current_user)):
    """
    Delete the current user's account.

    Order of operations (critical for data safety):
    1. Delete all user data from the database (bookmarks, ratings)
    2. Delete Firebase authentication user

    If the database deletion fails, the Firebase account is preserved.
    If Firebase deletion fails after DB data is removed, the failure is logged
    critically for manual/automated cleanup — the user's auth token will expire naturally.
    """
    firebase_uid = user["uid"]
    redacted_uid = _redact_uid(firebase_uid)

    logger.warning(f"User {redacted_uid} is requesting account deletion.")

    # Step 1: Delete all user data from PostgreSQL first (Firebase preserved if this fails)
    try:
        db_deleted = await _run_sync(services.delete_user_data, firebase_uid)
        if not db_deleted:
            logger.error(f"Database cleanup returned False for {redacted_uid}; aborting account deletion.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user data. Please try again or contact support."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Database cleanup failed for {redacted_uid}:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user data. Please contact support."
        ) from e

    # Step 2: Delete Firebase Auth user (DB data already removed)
    try:
        delete_firebase_user(firebase_uid)
    except Exception:
        logger.critical(
            f"Firebase account deletion failed for {redacted_uid} after successful DB cleanup. "
            "Manual removal of the Firebase Auth user is required."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account data deleted but authentication cleanup failed. Please contact support."
        )

    logger.info(f"Successfully deleted account for user {redacted_uid}")
    return None


@router.get("/preferences", response_model=UserPreferences)
@limiter.limit("30/minute")
async def get_preferences(request: Request, user=Depends(get_current_user)):
    """Get user content preferences."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    return await _run_sync(services.get_preferences, firebase_uid)


@router.patch("/preferences", response_model=UserPreferences)
@limiter.limit("30/minute")
async def update_preferences(request: Request, prefs: UserPreferencesUpdate, user=Depends(get_current_user)):
    """Update user content preferences."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        return await _run_sync(services.update_preferences, firebase_uid, prefs.filter_adult)
    except Exception:
        logger.exception(f"Failed to update preferences for {_redact_uid(firebase_uid)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save preferences. Please try again.",
        )