import os
import joblib
import pandas as pd
import ast
from pathlib import Path
from rapidfuzz import process, fuzz
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_core.documents import Document
from langchain_core.retrievers import RetrieverLike
from ..logger import get_logger
from .utils import sanitize_for_json, get_poster_url
from datetime import datetime
from typing import Any

logger = get_logger("movie_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MOVIE_LIST_PATH = DATA_DIR / "movie_list.pkl"
FAISS_INDEX_PATH = DATA_DIR / "movie_recommendation_faiss"


def load_movie_data(path: Path = MOVIE_LIST_PATH) -> pd.DataFrame:
    """Load movie data from pickle file."""
    try:
        return joblib.load(path)
    except Exception:
        logger.exception("Error loading movie list")
        raise


def _hydrate_row(details: dict[str, Any]) -> dict[str, Any]:
    """Process a raw DataFrame row dict into a fully normalised movie dict.

    Extracted so that callers who already hold a row (e.g. get_details_bulk)
    can hydrate it directly without triggering a second DataFrame lookup.
    """
    for field in ['cast', 'crew', 'genres', 'keywords', 'production_companies']:
        if field in details:
            raw_value = details[field]
            if not isinstance(raw_value, list):
                if isinstance(raw_value, str) and raw_value:
                    try:
                        parsed = ast.literal_eval(raw_value)
                        raw_value = parsed if isinstance(parsed, list) else [parsed]
                    except Exception:
                        raw_value = [raw_value]
                else:
                    raw_value = []
            processed_items = []
            for item in raw_value:
                if isinstance(item, dict):
                    name = item.get('name') or item.get('character') or item.get('job')
                    if not name and item:
                        name = next((v for v in item.values() if v and isinstance(v, str)), None)
                    if name:
                        processed_items.append(str(name).strip())
                elif item:
                    processed_items.append(str(item).strip())
            details[field] = [i for i in processed_items if i and i.strip()]
        else:
            details[field] = []

    overview_value = details.get('overview')
    if overview_value is None or (isinstance(overview_value, float) and str(overview_value) == 'nan'):
        details['overview'] = ""
    else:
        details['overview'] = str(overview_value)

    for field in ['budget', 'revenue', 'runtime', 'vote_average', 'vote_count', 'popularity']:
        if field in details:
            val = details[field]
            if val is None or (isinstance(val, float) and pd.isna(val)):
                details[field] = 0.0 if field in ['vote_average', 'popularity'] else 0
            elif isinstance(val, (int, float)):
                details[field] = val
            else:
                details[field] = 0

    if 'release_date' in details and details['release_date']:
        try:
            if isinstance(details['release_date'], str):
                date_obj = datetime.strptime(details['release_date'], '%Y-%m-%d')
                details['year'] = str(date_obj.year)
            else:
                details['year'] = 'N/A'
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse release date '{details.get('release_date')}': {e}")
            details['year'] = 'N/A'
    elif 'year' not in details:
        details['year'] = 'N/A'

    details['adult'] = parse_adult_value(details.get('adult', False))
    details['poster_url'] = get_poster_url(details.get('poster_path'))
    return sanitize_for_json(details)


def get_movie_details(identifier: int | str, df: pd.DataFrame) -> dict[str, Any] | None:
    """Get detailed information for a movie by ID or title."""
    if isinstance(identifier, int):
        match = df[df['id'] == identifier]
    else:
        match = df[df['title'].str.lower() == str(identifier).lower()]

    if not match.empty:
        return _hydrate_row(match.iloc[0].to_dict())
    return None


def _collect_matching_titles(query: str, df: pd.DataFrame) -> list[str]:
    """Collect all matching movie titles in relevance order without hydrating details.

    Returns a deduplicated ordered list of titles across all match tiers
    (exact → starts-with → contains → fuzzy → keywords). No limit is applied
    so the caller gets the full result set for accurate pagination counts.
    """
    results_ordered: list[str] = []
    seen_titles: set[str] = set()

    def add_unique(titles: list[str]) -> None:
        for t in titles:
            if t not in seen_titles:
                results_ordered.append(t)
                seen_titles.add(t)

    add_unique(df[df['title'].str.lower() == query]['title'].tolist())
    add_unique(df[df['title'].str.lower().str.startswith(query, na=False)]['title'].tolist())
    add_unique(df[df['title'].str.lower().str.contains(query, na=False)]['title'].tolist())

    fuzzy_results = process.extract(query, df['title'].tolist(), scorer=fuzz.token_set_ratio, limit=50)
    add_unique([m[0] for m in fuzzy_results if m[1] >= 80])

    if 'keywords' in df.columns:
        add_unique(df[df['keywords'].str.lower().str.contains(query, na=False)]['title'].tolist())

    return results_ordered


def search_movies_paginated(
    query: str,
    df: pd.DataFrame,
    page: int = 1,
    page_size: int = 24,
    order_by: str | None = None,
    filter_adult: bool = False,
) -> tuple[int, list[dict[str, Any]]]:
    """Search movies with efficient pagination.

    Collects all matching titles first (cheap string ops), then hydrates only
    the requested page slice (expensive detail parsing). This avoids the old
    pattern of hydrating up to 1000 movies just to count them.

    Returns:
        (total_count, page_results)
    """
    df = apply_adult_filter(df, filter_adult)
    query = query.strip().lower()
    if not query:
        return 0, []

    all_titles = _collect_matching_titles(query, df)
    total = len(all_titles)

    if total == 0:
        return 0, []

    # Sort the title list using lightweight df lookups before slicing,
    # so we only ever hydrate the one page we actually need.
    if order_by == 'rating':
        rating_map = df.set_index('title')['vote_average'].to_dict() if 'vote_average' in df.columns else {}
        all_titles = sorted(all_titles, key=lambda t: rating_map.get(t, 0) or 0, reverse=True)
    elif order_by == 'name':
        all_titles = sorted(all_titles, key=lambda t: t.lower())

    start = (page - 1) * page_size
    page_titles = all_titles[start:start + page_size]

    # Hydrate only the page slice
    page_movies = [m for m in (get_movie_details(t, df) for t in page_titles) if m]
    return total, page_movies


def search_movies(query: str, df: pd.DataFrame, limit: int = 12, order_by: str | None = None, filter_adult: bool = False) -> list[dict[str, Any]]:
    """Search movies by title with fuzzy matching.

    For paginated API search, prefer search_movies_paginated which avoids
    hydrating the full result set just to get a count.
    """
    df = apply_adult_filter(df, filter_adult)
    query = query.strip().lower()
    if not query:
        return []

    all_titles = _collect_matching_titles(query, df)
    page_titles = all_titles[:limit]
    movies = [m for m in (get_movie_details(t, df) for t in page_titles) if m]
    return _order_movies(movies, order_by)


def _order_movies(movies: list[dict[str, Any]], order_by: str | None) -> list[dict[str, Any]]:
    """Order movies by specified criteria."""
    if not movies:
        return movies
    if order_by == 'rating':
        return sorted(movies, key=lambda x: x.get('vote_average') or 0, reverse=True)
    elif order_by == 'name':
        return sorted(movies, key=lambda x: x.get('title', '').lower())
    else:
        return movies


_ADULT_TRUTHY: frozenset[str] = frozenset({'true', '1', 'yes'})


def parse_adult_value(val) -> bool:
    """Coerce a raw adult-field value to a canonical boolean."""
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in _ADULT_TRUTHY


def apply_adult_filter(df: pd.DataFrame, filter_adult: bool) -> pd.DataFrame:
    """Filter out adult content if filter_adult is True."""
    if not filter_adult or 'adult' not in df.columns:
        return df
    return df[~df['adult'].astype(str).str.lower().isin(_ADULT_TRUTHY)]


def load_retriever(path: Path = FAISS_INDEX_PATH) -> RetrieverLike | None:
    """Load the FAISS retriever for movie recommendations."""
    logger.info(f"Loading Recommendation Model from {path}...")
    try:
        if not os.path.exists(path):
            logger.warning(f"FAISS index directory {path} not found.")
            return None
        embedding = HuggingFaceEndpointEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2')
        vectorstore = FAISS.load_local(path, embedding, allow_dangerous_deserialization=True)
        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6, "fetch_k": 30})
    except Exception:
        logger.exception("Error loading FAISS model")
        return None


def get_recommendations(title: str, df: pd.DataFrame, retriever: RetrieverLike | None, k: int = 5, filter_adult: bool = False) -> list[dict[str, Any]]:
    """Get movie recommendations based on a title."""
    try:
        title = title.strip()
        df = apply_adult_filter(df, filter_adult)
        if title not in df['title'].values or retriever is None:
            return []
        results = retriever.invoke(title)
        recommendation_titles = [
            t for doc in results
            if (t := doc.metadata.get('title')) and t != title
        ][:k]
        return [m for m in (get_movie_details(t, df) for t in recommendation_titles) if m]
    except Exception:
        logger.exception("Error generating recommendations")
        return []


def get_personalized_recommendations(
    user_library_ids: list[int],
    df: pd.DataFrame,
    retriever: RetrieverLike | None,
    limit: int = 16,
    filter_adult: bool = False
) -> list[dict[str, Any]]:
    """Get personalized recommendations based on user's movie library."""
    try:
        df = apply_adult_filter(df, filter_adult)
        if not user_library_ids or retriever is None:
            return []
        library_titles = []
        for movie_id in user_library_ids:
            details = get_movie_details(movie_id, df)
            if details:
                library_titles.append(details['title'])
        if not library_titles:
            return []
        recommendation_scores: dict[int, dict[str, Any]] = {}
        user_library_set = set(user_library_ids)
        for title in library_titles:
            try:
                recs = get_recommendations(title, df, retriever, k=10, filter_adult=filter_adult)
                for rec in recs:
                    movie_id = rec['id']
                    if movie_id in user_library_set:
                        continue
                    if movie_id not in recommendation_scores:
                        recommendation_scores[movie_id] = {'score': 0, 'details': rec}
                    recommendation_scores[movie_id]['score'] += 1
            except (KeyError, TypeError, ValueError):
                logger.warning(f"Failed to get recommendations for '{title}'", exc_info=True)
                continue
        sorted_recommendations = sorted(
            recommendation_scores.values(),
            key=lambda x: (x['score'], x['details'].get('vote_average', 0) or 0),
            reverse=True
        )
        return [item['details'] for item in sorted_recommendations[:limit]]
    except Exception:
        logger.exception("Error generating personalized recommendations")
        return []