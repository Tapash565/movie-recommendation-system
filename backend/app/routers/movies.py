from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional

from .. import services
from ..repositories import user_repo
from ..dependencies import get_df, get_retriever, get_optional_user
from ..rate_limit import limiter
from fastapi import Request
from ..logger import get_logger
from ..schemas import Movie, SearchResponse, MovieDetail

# Initialize logger for movies
logger = get_logger("movies")

router = APIRouter()

@router.get("/movies/trending", response_model=List[Movie])
@limiter.limit("10/minute")
def get_trending_movies(
    request: Request,
    filter_adult: bool = Query(False, description="Filter out adult content"),
    df=Depends(get_df)
):
    """Get trending movies (random sample of 12)."""
    # Check if data is available
    if df.empty:
        logger.error("Movie data not available - returning empty list")
        return []

    # Apply adult content filter
    filtered_df = services.apply_adult_filter(df, filter_adult)

    # Sample 12 random movies
    trending = filtered_df.sample(min(12, len(filtered_df)))
    trending_movies = []

    for _, row in trending.iterrows():
        trending_movies.append(services.get_movie_details(row['id'], df))

    return trending_movies

@router.get("/movies/search", response_model=SearchResponse)
@limiter.limit("20/minute")
def search_movies(
    request: Request,
    q: str = Query(""), 
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    order_by: Optional[str] = None,
    filter_adult: bool = Query(False, description="Filter out adult content"),
    df=Depends(get_df)
):
    """Search for movies with pagination."""
    results = []
    total_results = 0
    
    # Check if data is available
    if df.empty:
        logger.error("Movie data not available - returning empty results")
        return {
            "search_query": q,
            "movies": [],
            "result_count": 0,
            "total_results": 0,
            "page": page,
            "page_size": page_size,
            "order_by": order_by or ""
        }
    
    if q:
        logger.info(f"Searching for movies with query: '{q}', page: {page}, order_by: '{order_by}'")
        # Search all first to get total count (this could be optimized later)
        all_results = services.search_movies(q, df, limit=1000, order_by=order_by, filter_adult=filter_adult)
        total_results = len(all_results)
        
        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        results = all_results[start_idx:end_idx]
    
    return {
        "search_query": q,
        "movies": results,
        "result_count": len(results),
        "total_results": total_results,
        "page": page,
        "page_size": page_size,
        "order_by": order_by or ""
    }

@router.get("/movies/{movie_id}", response_model=MovieDetail)
@limiter.limit("30/minute")
def get_movie_details_api(
    request: Request,
    movie_id: int, 
    filter_adult: bool = Query(False, description="Filter out adult content"),
    user=Depends(get_optional_user),
    df=Depends(get_df),
    retriever=Depends(get_retriever)
):
    """Get details for a specific movie."""
    movie = services.get_movie_details(movie_id, df)
    if not movie:
        logger.warning(f"Movie ID {movie_id} not found.")
        raise HTTPException(status_code=404, detail="Movie not found")

    if filter_adult and str(movie.get("adult", "")).lower() in ("true", "1", "yes"):
        logger.warning(f"Movie ID {movie_id} hidden: adult content filter is active.")
        raise HTTPException(status_code=404, detail="Movie not found")

    # Get recommendations
    logger.info(f"Generating recommendations for movie: '{movie['title']}' (ID: {movie_id})")
    recommendations = services.get_recommendations(movie['title'], df, retriever, filter_adult=filter_adult)
    
    # Get user interaction status if logged in via Firebase
    bookmark_status = None
    user_rating = 0
    
    if user:
        firebase_uid = user.get("uid")
        if firebase_uid:
            bookmark_status = user_repo.get_bookmark_status(firebase_uid, movie_id)
            rating_val = user_repo.get_rating(firebase_uid, movie_id)
            if rating_val is not None:
                user_rating = rating_val
            
    # Combine data
    movie_data = movie.copy()
    movie_data['recommendations'] = recommendations
    movie_data['bookmark_status'] = bookmark_status
    movie_data['user_rating'] = user_rating
    
    return movie_data
