from typing import Any
import pandas as pd
from ..repositories import user_repo
from .movie_service import get_movie_details, apply_adult_filter, _hydrate_row
from ..logger import get_logger

logger = get_logger("user_service")


def get_user_library(
    firebase_uid: str,
    email: str,
    df: pd.DataFrame,
    page: int = 1,
    page_size: int = 12,
    filter_adult: bool = False
) -> dict[str, Any]:
    """Get and paginate the user's movie library."""
    # Apply adult filter so adult movies are invisible during hydration
    df = apply_adult_filter(df, filter_adult)

    # Get user data from database
    bookmarks_raw = user_repo.get_user_bookmarks(firebase_uid)
    ratings_raw = user_repo.get_user_ratings(firebase_uid)

    # Restrict to IDs that exist in the (possibly adult-filtered) DataFrame so that
    # pagination totals always match what get_details_bulk can actually hydrate
    valid_ids = set(df['id'].tolist())
    bookmarks_raw = [b for b in bookmarks_raw if b['movie_id'] in valid_ids]
    ratings_raw = [r for r in ratings_raw if r['movie_id'] in valid_ids]

    # Split bookmarks by status
    all_to_watch = [b for b in bookmarks_raw if b['status'] == 'to_watch']
    all_watched = [b for b in bookmarks_raw if b['status'] == 'watched']

    # Paginate helper
    def paginate(items: list, p: int, ps: int) -> list:
        start = (p - 1) * ps
        return items[start: start + ps]

    to_watch_page = paginate(all_to_watch, page, page_size)
    watched_page = paginate(all_watched, page, page_size)
    rated_page = paginate(ratings_raw, page, page_size)

    def get_details_bulk(
        raw_items: list[dict],
        status_field: str | None = None,
        rating_field: str | None = None
    ) -> list[dict[str, Any]]:
        """Hydrate movie details for a list of user library items.

        Filters the DataFrame once for all IDs, then calls _hydrate_row on each
        matched row directly — avoiding a second per-movie DataFrame lookup.
        """
        if not raw_items:
            return []

        movie_ids = [item['movie_id'] for item in raw_items]

        # Single DataFrame filter for all IDs at once
        matches = df[df['id'].isin(movie_ids)]

        # Build id → hydrated dict map using the rows we already have
        details_map: dict[int, dict[str, Any]] = {
            int(row['id']): _hydrate_row(row.to_dict())
            for _, row in matches.iterrows()
        }

        res = []
        for item in raw_items:
            m_id = item['movie_id']
            if m_id not in details_map:
                continue
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
    return user_repo.set_user_preferences(firebase_uid, filter_adult)