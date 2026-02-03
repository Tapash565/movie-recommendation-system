from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import services
import database as db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/library", response_class=HTMLResponse)
def library(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return templates.TemplateResponse(request=request, name="login.html", context={
            "error": "Please login to view your library"
        })
        
    df = request.app.state.df
    
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
            
    return templates.TemplateResponse(request=request, name="library.html", context={
        "user": request.session.get("user"),
        "to_watch": to_watch,
        "watched": watched,
        "rated_movies": rated_movies,
        "active_page": "library"
    })

# API Endpoints for Javascript interactions

@router.post("/api/bookmark")
async def add_bookmark(request: Request):
    data = await request.json()
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    movie_id = data.get('movie_id')
    movie_title = data.get('movie_title')
    status = data.get('status')
    
    success = db.add_bookmark(user_id, movie_id, movie_title, status)
    return {"success": success}

@router.post("/api/remove_bookmark")
async def remove_bookmark(request: Request):
    data = await request.json()
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    movie_id = data.get('movie_id')
    db.remove_bookmark(user_id, movie_id)
    return {"success": True}

@router.post("/api/rate")
async def rate_movie(request: Request):
    data = await request.json()
    user_id = request.session.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    movie_id = data.get('movie_id')
    movie_title = data.get('movie_title')
    rating = data.get('rating')
    
    success = db.add_rating(user_id, movie_id, movie_title, float(rating))
    return {"success": success}
