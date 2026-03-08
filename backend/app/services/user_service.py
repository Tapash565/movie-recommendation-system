from typing import Any
import pandas as pd
from ..repositories import user_repo
from .movie_service import get_movie_details
from ..logger import get_logger

logger = get_logger("user_service")


def get_user_library(
    firebase_uid: str,
    email: str,
    df: pd.DataFrame,
    page: int = 1,
    page_size: int = 12
) -> dict[str, Any]:
    """
    Get and paginate the user's movie library.
    """
    # Get user data from database
    bookmarks_raw = user_repo.get_user_bookmarks(firebase_uid)
    ratings_raw = user_repo.get_user_ratings(firebase_uid)

    # Filter by status
    all_to_watch = [b for b in bookmarks_raw if b['status'] == 'to_watch']
    all_watched = [b for b in bookmarks_raw if b['status'] == 'watched']

    # Paginate helper
    def paginate(items: list, p: int, ps: int) -> list:
        start = (p - 1) * ps
        return items[start: start + ps]

    to_watch_page = paginate(all_to_watch, page, page_size)
    watched_page = paginate(all_watched, page, page_size)
    rated_page = paginate(ratings_raw, page, page_size)

    # Hydrate with details
    def get_details_bulk(
        raw_items: list[dict],
        status_field: str | None = None,
        rating_field: str | None = None
    ) -> list[dict[str, Any]]:
        movie_ids = [item['movie_id'] for item in raw_items]
        if not movie_ids:
            return []

        # Filter DF for all IDs at once
        matches = df[df['id'].isin(movie_ids)]

        # Create a mapping for quick lookup
        details_map: dict[int, dict[str, Any]] = {}
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


def add_bookmark(firebase_uid: str, movie_id: int, movie_title: str, status: str) -> bool:
    """Add a movie bookmark for a user. Returns True on success, False on failure."""
    return user_repo.add_bookmark(firebase_uid, movie_id, movie_title, status)


def remove_bookmark(firebase_uid: str, movie_id: int) -> bool:
    """Remove a movie bookmark for a user. Returns True on success, False on failure."""
    return user_repo.remove_bookmark(firebase_uid, movie_id)


def add_rating(firebase_uid: str, movie_id: int, movie_title: str, rating: float) -> bool:
    """Add or update a movie rating for a user. Returns True on success, False on failure."""
    return user_repo.add_rating(firebase_uid, movie_id, movie_title, rating)


def _redact_uid(uid: str) -> str:
    """Create a short hash of UID for logging purposes (privacy-friendly)."""
    import hashlib
    return hashlib.sha256(uid.encode()).hexdigest()[:8]


def delete_user_data(firebase_uid: str) -> bool:
    """Delete all user data from the database (bookmarks and ratings) in a single transaction."""
    redacted_uid = _redact_uid(firebase_uid)
    # Use the transactional repository method if available
    try:
        result = user_repo.delete_user_data_transactional(firebase_uid)
        if result:
            logger.info(f"Successfully deleted all user data for UID: {redacted_uid}")
        else:
            logger.error(f"Failed to delete user data for UID: {redacted_uid}")
        return result
    except Exception:
        logger.exception(f"Failed to delete user data for UID: {redacted_uid}")
        return False

def get_preferences(firebase_uid: str) -> dict:
    """Get user content preferences."""
    return user_repo.get_user_preferences(firebase_uid)


def update_preferences(firebase_uid: str, filter_adult: bool) -> dict:
    """Update user content preferences."""
    success = user_repo.set_user_preferences(firebase_uid, filter_adult)
    if not success:
        raise RuntimeError(
            f"Failed to save preferences for UID {_redact_uid(firebase_uid)}: "
            f"filter_adult={filter_adult}"
        )
    return {"filter_adult": filter_adult}