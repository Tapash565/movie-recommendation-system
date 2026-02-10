from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List
from ..schemas import Movie

from .. import services
from .. import database as db
from ..dependencies import get_df, get_retriever
from ..logger import get_logger

# Initialize logger for recommendations
logger = get_logger("recommendations")

router = APIRouter()

@router.get("/api/discover", response_model=List[Movie])
def get_recommendations_page(
    request: Request, 
    df=Depends(get_df), 
    retriever=Depends(get_retriever)
):
    """Get personalized recommendations."""
    user_id = request.session.get("user_id")
    username = request.session.get("user")
    
    if not user_id:
        logger.warning("Unauthorized access attempt to discover page.")
        raise HTTPException(status_code=401, detail="Please login to view personalized recommendations")
        
    logger.info(f"User '{username}' (ID: {user_id}) is viewing discover page.")
    
    # Get user's library data
    bookmarks_raw = db.get_user_bookmarks(user_id)
    ratings_raw = db.get_user_ratings(user_id)
    
    # Collect movie IDs from watched movies and highly rated movies
    library_ids = set()
    
    # Add watched movies
    for b in bookmarks_raw:
        if b['status'] == 'watched':
            library_ids.add(b['movie_id'])
    
    # Add highly rated movies (4+ stars out of 5)
    for r in ratings_raw:
        if r['rating'] >= 4.0:
            library_ids.add(r['movie_id'])
    
    # Generate personalized recommendations
    recommendations = services.get_personalized_recommendations(
        user_library_ids=list(library_ids),
        df=df,
        retriever=retriever,
        limit=16
    )
    
    return recommendations
