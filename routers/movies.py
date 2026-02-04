from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import services
import database as db
from logger import get_logger

# Initialize logger for movies
logger = get_logger("movies")

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    df = request.app.state.df
    # Sample 12 random movies
    trending = df.sample(min(12, len(df)))
    trending_movies = []
    
    for _, row in trending.iterrows():
        trending_movies.append(services.get_movie_details(row['id'], df))
        
    return templates.TemplateResponse(request=request, name="index.html", context={
        "movies": trending_movies,
        "user": request.session.get("user"),
        "active_page": "home"
    })

@router.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = Query("")):
    df = request.app.state.df
    logger.info(f"Searching for movies with query: {q}")
    results = services.search_movies(q, df)
    
    return templates.TemplateResponse(request=request, name="index.html", context={
        "search_query": q,
        "movies": results,
        "user": request.session.get("user"),
        "active_page": "home"
    })

@router.get("/movie/{movie_id}", response_class=HTMLResponse)
def movie_details(request: Request, movie_id: int):
    from main import get_retriever
    df = request.app.state.df
    retriever = get_retriever(request.app)
    
    movie = services.get_movie_details(movie_id, df)
    if not movie:
        logger.warning(f"Movie ID {movie_id} not found.")
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Get recommendations
    logger.info(f"Generating recommendations for movie: {movie['title']} (ID: {movie_id})")
    recommendations = services.get_recommendations(movie['title'], df, retriever)
    
    # Get user interaction status if logged in
    user_id = request.session.get("user_id")
    bookmark_status = None
    user_rating = 0
    
    if user_id:
        bookmark_status = db.get_bookmark(user_id, movie_id)
        rating_val = db.get_rating(user_id, movie_id)
        if rating_val is not None:
            user_rating = rating_val
            
    return templates.TemplateResponse(request=request, name="movie_details.html", context={
        "movie": movie,
        "recommendations": recommendations,
        "user": request.session.get("user"),
        "bookmark_status": bookmark_status,
        "user_rating": user_rating
    })
