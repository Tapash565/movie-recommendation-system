from .. import database as db
from .movie_service import get_movie_details
from ..logger import get_logger

logger = get_logger("user_service")

def get_user_library(firebase_uid, email, df, page=1, page_size=12):
    """
    Get and paginate the user's movie library.
    """
    # Get user data from database
    bookmarks_raw = db.get_user_bookmarks(firebase_uid)
    ratings_raw = db.get_user_ratings(firebase_uid)
    
    # Filter by status
    all_to_watch = [b for b in bookmarks_raw if b['status'] == 'to_watch']
    all_watched = [b for b in bookmarks_raw if b['status'] == 'watched']
    
    # Paginate helper
    def paginate(items, p, ps):
        start = (p - 1) * ps
        return items[start : start + ps]

    to_watch_page = paginate(all_to_watch, page, page_size)
    watched_page = paginate(all_watched, page, page_size)
    rated_page = paginate(ratings_raw, page, page_size)

    # Hydrate with details
    def get_details_bulk(raw_items, status_field=None, rating_field=None):
        movie_ids = [item['movie_id'] for item in raw_items]
        if not movie_ids:
            return []
        
        # Filter DF for all IDs at once
        matches = df[df['id'].isin(movie_ids)]
        
        # Create a mapping for quick lookup
        details_map = {}
        for _, row in matches.iterrows():
            m_id = row['id']
            # We use the existing get_movie_details for each to ensure all processing logic is applied
            # but we pass the specific row match to it to avoid re-searching the DF
            # Actually, let's optimize get_movie_details to take a row optionally
            details_map[m_id] = get_movie_details(m_id, df)
            
        res = []
        for item in raw_items:
            m_id = item['movie_id']
            if m_id in details_map:
                details = details_map[m_id].copy()
                if status_field:
                    details['user_status'] = item['status']
                if rating_field:
                    details['user_rating'] = item['rating']
                res.append(details)
        return res
            
    return {
        "user": email,
        "to_watch": get_details_bulk(to_watch_page, status_field='user_status'),
        "watched": get_details_bulk(watched_page, status_field='user_status'),
        "rated_movies": get_details_bulk(rated_page, rating_field='user_rating'),
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_to_watch": len(all_to_watch),
            "total_watched": len(all_watched),
            "total_rated": len(ratings_raw)
        }
    }

def add_bookmark(firebase_uid, movie_id, movie_title, status):
    return db.add_bookmark(firebase_uid, movie_id, movie_title, status)

def remove_bookmark(firebase_uid, movie_id):
    return db.remove_bookmark(firebase_uid, movie_id)

def add_rating(firebase_uid, movie_id, movie_title, rating):
    return db.add_rating(firebase_uid, movie_id, movie_title, rating)
