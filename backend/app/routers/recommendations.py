from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..schemas import Movie

from .. import services
from .. import database as db
from ..dependencies import get_df, get_retriever, get_current_user
from ..logger import get_logger

# Initialize logger for recommendations
logger = get_logger("recommendations")

router = APIRouter()

@router.get("/discover", response_model=List[Movie])
def get_recommendations_page(
    user=Depends(get_current_user), 
    df=Depends(get_df), 
    retriever=Depends(get_retriever)
):
    """Get personalized recommendations."""
    firebase_uid = user.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=403, detail="Forbidden: Valid user UID required for recommendations")
        
    email = user.get("email", "User")
    
    # Check if data is available
    if df.empty:
        logger.error("Movie data not available - returning empty recommendations")
        return []
        
    logger.info(f"User '{email}' (UID: {firebase_uid}) is viewing discover page.")
    
    # Get user's library data using firebase_uid
    bookmarks_raw = db.get_user_bookmarks(firebase_uid)
    ratings_raw = db.get_user_ratings(firebase_uid)
    
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
