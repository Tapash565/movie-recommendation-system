from fastapi import APIRouter, Request, HTTPException, Depends
from ..schemas import BookmarkRequest, RatingRequest, RemoveBookmarkRequest

from .. import services
from .. import database as db
from ..dependencies import get_df
from ..logger import get_logger


# Initialize logger for users
logger = get_logger("users")

router = APIRouter()

@router.get("/library")
def get_library(request: Request, df=Depends(get_df)):
    """Get the user's movie library."""
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized access attempt to library.")
        raise HTTPException(status_code=401, detail="Please login to view your library")
        
    logger.info(f"User '{username}' (ID: {user_id}) is viewing their library.")
    
    # Check if data is available
    if df.empty:
        logger.error("Movie data not available - returning empty library")
        return {
            "user": username,
            "to_watch": [],
            "watched": [],
            "rated_movies": []
        }
    
    # Get user data
    bookmarks_raw = db.get_user_bookmarks(user_id)
    ratings_raw = db.get_user_ratings(user_id)
    
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
        "user": username,
        "to_watch": to_watch,
        "watched": watched,
        "rated_movies": rated_movies
    }

# --- API Endpoints ---

@router.post("/bookmark")
async def add_bookmark(request: Request, data: BookmarkRequest):
    """API endpoint to add a movie to the user's library."""
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized API call to /api/bookmark")
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    logger.info(f"User '{username}' (ID: {user_id}) setting bookmark for '{data.movie_title}' (ID: {data.movie_id}) to {data.status}")
    success = db.add_bookmark(user_id, data.movie_id, data.movie_title, data.status)
    return {"success": success}

@router.post("/remove_bookmark")
async def remove_bookmark(request: Request, data: RemoveBookmarkRequest):
    """API endpoint to remove a movie from the user's library."""
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized API call to /api/remove_bookmark")
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    logger.info(f"User '{username}' (ID: {user_id}) removing bookmark for movie ID: {data.movie_id}")
    result = db.remove_bookmark(user_id, data.movie_id)
    
    if not result:
        logger.error(f"Failed to remove bookmark for user '{username}' (ID: {user_id}), movie ID: {data.movie_id}")
    
    return {"success": result}

@router.post("/rate")
async def rate_movie(request: Request, data: RatingRequest):
    """API endpoint to rate a movie."""
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized API call to /api/rate")
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    logger.info(f"User '{username}' (ID: {user_id}) rated movie '{data.movie_title}' (ID: {data.movie_id}) as {data.rating}")
    success = db.add_rating(user_id, data.movie_id, data.movie_title, data.rating)
    return {"success": success}

