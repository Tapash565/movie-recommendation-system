from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse

import services
import database as db
from dependencies import templates, get_df
from logger import get_logger

# Initialize logger for users
logger = get_logger("users")

router = APIRouter()

@router.get("/library", response_class=HTMLResponse)
def library(request: Request, df=Depends(get_df)):
    """Render the user's movie library."""
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized access attempt to library.")
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"error": "Please login to view your library"}
        )
        
    logger.info(f"User '{username}' (ID: {user_id}) is viewing their library.")
    
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
            
    return templates.TemplateResponse(
        request=request, 
        name="library.html", 
        context={
            "user": username,
            "to_watch": to_watch,
            "watched": watched,
            "rated_movies": rated_movies,
            "active_page": "library"
        }
    )

# --- API Endpoints for Javascript Interactions ---

@router.post("/api/bookmark")
async def add_bookmark(request: Request):
    """API endpoint to add a movie to the user's library."""
    data = await request.json()
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized API call to /api/bookmark")
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    movie_id = data.get('movie_id')
    movie_title = data.get('movie_title')
    status = data.get('status')
    
    logger.info(f"User '{username}' (ID: {user_id}) setting bookmark for '{movie_title}' (ID: {movie_id}) to {status}")
    success = db.add_bookmark(user_id, movie_id, movie_title, status)
    return {"success": success}

@router.post("/api/remove_bookmark")
async def remove_bookmark(request: Request):
    """API endpoint to remove a movie from the user's library."""
    data = await request.json()
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized API call to /api/remove_bookmark")
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    movie_id = data.get('movie_id')
    logger.info(f"User '{username}' (ID: {user_id}) removing bookmark for movie ID: {movie_id}")
    db.remove_bookmark(user_id, movie_id)
    return {"success": True}

@router.post("/api/rate")
async def rate_movie(request: Request):
    """API endpoint to rate a movie."""
    data = await request.json()
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized API call to /api/rate")
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    movie_id = data.get('movie_id')
    movie_title = data.get('movie_title')
    rating = data.get('rating')
    
    logger.info(f"User '{username}' (ID: {user_id}) rated movie '{movie_title}' (ID: {movie_id}) as {rating}")
    success = db.add_rating(user_id, movie_id, movie_title, float(rating))
    return {"success": success}

