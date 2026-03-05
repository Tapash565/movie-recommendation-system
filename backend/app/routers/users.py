from fastapi import APIRouter, HTTPException, Depends, Query, status
from ..schemas import BookmarkRequest, RatingRequest, RemoveBookmarkRequest

from .. import services
from .. import database as db
from ..dependencies import get_df, get_current_user
from ..rate_limit import limiter
from fastapi import Request
from ..logger import get_logger
from ..services.firebase_service import delete_firebase_user


# Initialize logger for users
logger = get_logger("users")

router = APIRouter()

@router.get("/library")
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

    logger.info(f"User UID: {firebase_uid} is viewing their library (Page: {page}).")

    if df.empty:
        logger.error("Movie data not available")
        return {
            "user": email,
            "to_watch": [],
            "watched": [],
            "rated_movies": [],
            "pagination": {"page": page, "page_size": page_size, "total": 0}
        }

    return services.get_user_library(firebase_uid, email, df, page, page_size)

# --- API Endpoints ---

@router.post("/bookmark")
@limiter.limit("10/minute")
async def add_bookmark(request: Request, data: BookmarkRequest, user=Depends(get_current_user)):
    """API endpoint to add a movie to the user's library."""
    firebase_uid = user["uid"]
    logger.info(f"User UID: {firebase_uid} setting bookmark for '{data.movie_title}' (ID: {data.movie_id}) to {data.status}")
    success = services.add_bookmark(firebase_uid, data.movie_id, data.movie_title, data.status)
    return {"success": success}

@router.post("/remove_bookmark")
async def remove_bookmark(data: RemoveBookmarkRequest, user=Depends(get_current_user)):
    """API endpoint to remove a movie from the user's library."""
    firebase_uid = user["uid"]
    logger.info(f"User UID: {firebase_uid} removing bookmark for movie ID: {data.movie_id}")
    result = services.remove_bookmark(firebase_uid, data.movie_id)
    return {"success": result}

@router.post("/rate")
@limiter.limit("10/minute")
async def rate_movie(request: Request, data: RatingRequest, user=Depends(get_current_user)):
    """API endpoint to rate a movie."""
    firebase_uid = user["uid"]
    logger.info(f"User UID: {firebase_uid} rated movie '{data.movie_title}' (ID: {data.movie_id}) as {data.rating}")
    success = services.add_rating(firebase_uid, data.movie_id, data.movie_title, data.rating)
    return {"success": success}

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(user=Depends(get_current_user)):
    """
    Delete the current user's account.
    This will:
    1. Delete all user data from the database (bookmarks, ratings)
    2. Delete the Firebase authentication user
    """
    firebase_uid = user["uid"]
    email = user.get("email", "Unknown")

    logger.warning(f"User UID: {firebase_uid} ({email}) is requesting account deletion.")

    # Step 1: Delete all user data from PostgreSQL
    db_deleted = services.delete_user_data(firebase_uid)
    if not db_deleted:
        logger.error(f"Failed to delete database data for user {firebase_uid}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user data. Please try again."
        )

    # Step 2: Delete the Firebase Auth user
    try:
        delete_firebase_user(firebase_uid)
    except Exception as e:
        # Log the error but don't block - database data is already deleted
        # The user won't be able to log in anyway
        logger.exception(f"Failed to delete Firebase user {firebase_uid}: {e}")
        # We could raise an exception here, but the user data is already deleted
        # and they won't be able to log in anyway

    logger.info(f"Successfully deleted account for user {firebase_uid}")
    return None
