from fastapi import APIRouter, HTTPException, Depends
from ..schemas import BookmarkRequest, RatingRequest, RemoveBookmarkRequest

from .. import services
from .. import database as db
from ..dependencies import get_df, get_current_user
from ..logger import get_logger


# Initialize logger for users
logger = get_logger("users")

router = APIRouter()

@router.get("/library")
def get_library(user=Depends(get_current_user), df=Depends(get_df)):
    """Get the user's movie library."""
    firebase_uid = user["uid"]
    email = user.get("email", "User")
    
    logger.info(f"User '{email}' (UID: {firebase_uid}) is viewing their library.")
    
    # Check if data is available
    if df.empty:
        logger.error("Movie data not available - returning empty library")
        return {
            "user": email,
            "to_watch": [],
            "watched": [],
            "rated_movies": []
        }
    
    # Get user data using firebase_uid
    bookmarks_raw = db.get_user_bookmarks(firebase_uid)
    ratings_raw = db.get_user_ratings(firebase_uid)
    
    # Process bookmarks
    to_watch = []
    watched = []
    for b in bookmarks_raw:
        details = services.get_movie_details(b['movie_id'], df)
        if details:
            details['user_status'] = b['status']
            if b['status'] == 'to_watch':
                to_watch.append(details)
            elif b['status'] == 'watched':
                watched.append(details)
                
    # Process ratings
    rated_movies = []
    for r in ratings_raw:
        details = services.get_movie_details(r['movie_id'], df)
        if details:
            details['user_rating'] = r['rating']
            rated_movies.append(details)
            
    return {
        "user": email,
        "to_watch": to_watch,
        "watched": watched,
        "rated_movies": rated_movies
    }

# --- API Endpoints ---

@router.post("/bookmark")
async def add_bookmark(data: BookmarkRequest, user=Depends(get_current_user)):
    """API endpoint to add a movie to the user's library."""
    firebase_uid = user["uid"]
    
    logger.info(f"User UID: {firebase_uid} setting bookmark for '{data.movie_title}' (ID: {data.movie_id}) to {data.status}")
    success = db.add_bookmark(firebase_uid, data.movie_id, data.movie_title, data.status)
    return {"success": success}

@router.post("/remove_bookmark")
async def remove_bookmark(data: RemoveBookmarkRequest, user=Depends(get_current_user)):
    """API endpoint to remove a movie from the user's library."""
    firebase_uid = user["uid"]
    
    logger.info(f"User UID: {firebase_uid} removing bookmark for movie ID: {data.movie_id}")
    result = db.remove_bookmark(firebase_uid, data.movie_id)
    
    if not result:
        logger.error(f"Failed to remove bookmark for UID: {firebase_uid}, movie ID: {data.movie_id}")
    
    return {"success": result}

@router.post("/rate")
async def rate_movie(data: RatingRequest, user=Depends(get_current_user)):
    """API endpoint to rate a movie."""
    firebase_uid = user["uid"]
    
    logger.info(f"User UID: {firebase_uid} rated movie '{data.movie_title}' (ID: {data.movie_id}) as {data.rating}")
    success = db.add_rating(firebase_uid, data.movie_id, data.movie_title, data.rating)
    return {"success": success}

