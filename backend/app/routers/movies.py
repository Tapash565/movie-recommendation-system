from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional

from .. import services
from .. import database as db
from ..dependencies import get_df, get_retriever, get_optional_user
from ..logger import get_logger
from ..schemas import Movie, SearchResponse, MovieDetail

# Initialize logger for movies
logger = get_logger("movies")

router = APIRouter()

@router.get("/movies/trending", response_model=List[Movie])
def get_trending_movies(df=Depends(get_df)):
    """Get trending movies (random sample of 12)."""
    # Check if data is available
    if df.empty:
        logger.error("Movie data not available - returning empty list")
        return []
    
    # Sample 12 random movies
    trending = df.sample(min(12, len(df)))
    trending_movies = []
    
    for _, row in trending.iterrows():
        trending_movies.append(services.get_movie_details(row['id'], df))
        
    return trending_movies

@router.get("/movies/search", response_model=SearchResponse)
def search_movies(
    q: str = Query(""), 
    limit: int = 24,
    order_by: Optional[str] = None,
    df=Depends(get_df)
):
    """Search for movies."""
    results = []
    result_count = 0
    
    # Check if data is available
    if df.empty:
        logger.error("Movie data not available - returning empty results")
        return {
            "search_query": q,
            "movies": [],
            "result_count": 0,
            "order_by": order_by or ""
        }
    
    if q:
        logger.info(f"Searching for movies with query: '{q}', order_by: '{order_by}'")
        results = services.search_movies(q, df, limit=limit, order_by=order_by)
        result_count = len(results)
    
    return {
        "search_query": q,
        "movies": results,
        "result_count": result_count,
        "order_by": order_by or ""
    }

@router.get("/movies/{movie_id}", response_model=MovieDetail)
def get_movie_details_api(
    movie_id: int, 
    user=Depends(get_optional_user),
    df=Depends(get_df),
    retriever=Depends(get_retriever)
):
    """Get details for a specific movie."""
    movie = services.get_movie_details(movie_id, df)
    if not movie:
        logger.warning(f"Movie ID {movie_id} not found.")
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Get recommendations
    logger.info(f"Generating recommendations for movie: '{movie['title']}' (ID: {movie_id})")
    recommendations = services.get_recommendations(movie['title'], df, retriever)
    
    # Get user interaction status if logged in via Firebase
    bookmark_status = None
    user_rating = 0
    
    if user:
        firebase_uid = user.get("uid")
        if firebase_uid:
            bookmark_status = db.get_bookmark(firebase_uid, movie_id)
            rating_val = db.get_rating(firebase_uid, movie_id)
            if rating_val is not None:
                user_rating = rating_val
            
    # Combine data
    movie_data = movie.copy()
    movie_data['recommendations'] = recommendations
    movie_data['bookmark_status'] = bookmark_status
    movie_data['user_rating'] = user_rating
    
    return movie_data

