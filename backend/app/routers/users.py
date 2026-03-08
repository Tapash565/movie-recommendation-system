from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
import hashlib
from ..schemas import BookmarkRequest, RatingRequest, RemoveBookmarkRequest, UserPreferences, UserPreferencesUpdate

from .. import services
from ..dependencies import get_df, get_current_user
from ..rate_limit import limiter
from ..logger import get_logger
from ..services.firebase_service import delete_firebase_user
from ..repositories import user_repo


# Initialize logger for users
logger = get_logger("users")

router = APIRouter()


def _redact_uid(uid: str) -> str:
    """Create a short hash of UID for logging purposes (privacy-friendly)."""
    return hashlib.sha256(uid.encode()).hexdigest()[:8]


@router.get("/library")
@limiter.limit("20/minute")
def get_library(
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

    prefs = user_repo.get_user_preferences(firebase_uid)
    filter_adult = prefs.get("filter_adult", False)

    return services.get_user_library(firebase_uid, email, df, page, page_size, filter_adult=filter_adult)


# --- API Endpoints ---


@router.post("/bookmark")
@limiter.limit("10/minute")
async def add_bookmark(request: Request, data: BookmarkRequest, user=Depends(get_current_user)):
    """API endpoint to add a movie to the user's library."""
    firebase_uid = user["uid"]
    logger.info(f"User {_redact_uid(firebase_uid)} setting bookmark for '{data.movie_title}' (ID: {data.movie_id}) to {data.status}")
    success = services.add_bookmark(firebase_uid, data.movie_id, data.movie_title, data.status)
    return {"success": success}


@router.post("/remove_bookmark")
@limiter.limit("10/minute")
async def remove_bookmark(request: Request, data: RemoveBookmarkRequest, user=Depends(get_current_user)):
    """API endpoint to remove a movie from the user's library."""
    firebase_uid = user["uid"]
    logger.info(f"User {_redact_uid(firebase_uid)} removing bookmark for movie ID: {data.movie_id}")
    result = services.remove_bookmark(firebase_uid, data.movie_id)
    return {"success": result}


@router.post("/rate")
@limiter.limit("10/minute")
async def rate_movie(request: Request, data: RatingRequest, user=Depends(get_current_user)):
    """API endpoint to rate a movie."""
    firebase_uid = user["uid"]
    logger.info(f"User {_redact_uid(firebase_uid)} rated movie '{data.movie_title}' (ID: {data.movie_id}) as {data.rating}")
    success = services.add_rating(firebase_uid, data.movie_id, data.movie_title, data.rating)
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
        db_deleted = services.delete_user_data(firebase_uid)
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
        # DB data is gone; log critically so manual/automated cleanup can remove the orphaned
        # Firebase Auth account.
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
def get_preferences(request: Request, user=Depends(get_current_user)):
    """Get user content preferences."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    return services.get_preferences(firebase_uid)


@router.patch("/preferences", response_model=UserPreferences)
@limiter.limit("30/minute")
def update_preferences(request: Request, prefs: UserPreferencesUpdate, user=Depends(get_current_user)):
    """Update user content preferences."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        return services.update_preferences(firebase_uid, prefs.filter_adult)
    except Exception:
        logger.exception(f"Failed to update preferences for {_redact_uid(firebase_uid)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save preferences. Please try again.",
        )
