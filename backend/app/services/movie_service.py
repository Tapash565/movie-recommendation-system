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


def get_movie_details(identifier: int | str, df: pd.DataFrame) -> dict[str, Any] | None:
    """Get detailed information for a movie by ID or title."""
    if isinstance(identifier, int):
        match = df[df['id'] == identifier]
    else:
        match = df[df['title'].str.lower() == str(identifier).lower()]

    if not match.empty:
        details = match.iloc[0].to_dict()
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
                details[field] = [item for item in processed_items if item and item.strip()]
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

        details['poster_url'] = get_poster_url(details.get('poster_path'))
        return sanitize_for_json(details)
    return None


def search_movies(query: str, df: pd.DataFrame, limit: int = 12, order_by: str | None = None, filter_adult: bool = False) -> list[dict[str, Any]]:
    """Search movies by title with fuzzy matching."""
    df = _apply_adult_filter(df, filter_adult)
    query = query.strip().lower()
    if not query:
        return []

    results_ordered: list[str] = []
    seen_titles: set[str] = set()

    def add_unique(titles: list[str]) -> bool:
        for t in titles:
            if t not in seen_titles:
                results_ordered.append(t)
                seen_titles.add(t)
            if len(results_ordered) >= limit:
                return True
        return False

    exact_matches = df[df['title'].str.lower() == query]['title'].tolist()
    if add_unique(exact_matches):
        movies = [m for m in (get_movie_details(t, df) for t in results_ordered) if m]
        return _order_movies(movies, order_by)

    starts_with = df[df['title'].str.lower().str.startswith(query, na=False)]['title'].tolist()
    if add_unique(starts_with):
        movies = [m for m in (get_movie_details(t, df) for t in results_ordered) if m]
        return _order_movies(movies, order_by)

    contains = df[df['title'].str.lower().str.contains(query, na=False)]['title'].tolist()
    if add_unique(contains):
        movies = [m for m in (get_movie_details(t, df) for t in results_ordered) if m]
        return _order_movies(movies, order_by)

    titles_list = df['title'].tolist()
    fuzzy_results = process.extract(query, titles_list, scorer=fuzz.token_set_ratio, limit=limit)
    fuzzy_matches = [match[0] for match in fuzzy_results if match[1] >= 80]
    if add_unique(fuzzy_matches):
        movies = [m for m in (get_movie_details(t, df) for t in results_ordered) if m]
        return _order_movies(movies, order_by)

    if 'keywords' in df.columns:
        keyword_matches = df[df['keywords'].str.lower().str.contains(query, na=False)]['title'].tolist()
        if add_unique(keyword_matches):
            movies = [m for m in (get_movie_details(t, df) for t in results_ordered) if m]
            return _order_movies(movies, order_by)

    movies = [m for m in (get_movie_details(t, df) for t in results_ordered) if m]
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


def _apply_adult_filter(df: pd.DataFrame, filter_adult: bool) -> pd.DataFrame:
    """Filter out adult content if filter_adult is True."""
    if not filter_adult or 'adult' not in df.columns:
        return df
    return df[~df['adult'].astype(str).str.lower().isin(['true', '1', 'yes'])]


def load_retriever(path: Path = FAISS_INDEX_PATH) -> RetrieverLike | None:
    """Load the FAISS retriever for movie recommendations.

    Note: allow_dangerous_deserialization=True is required because FAISS uses
    pickle serialization. This is safe when:
    1. The index files are stored in a secure, non-public location
    2. The files are generated by a trusted pipeline
    3. Consider adding file checksum validation for production
    """
    logger.info(f"Loading Recommendation Model from {path}...")
    try:
        if not os.path.exists(path):
            logger.warning(f"FAISS index directory {path} not found.")
            return None
        embedding = HuggingFaceEndpointEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2')
        # Security: Only enable if index files are from trusted sources
        vectorstore = FAISS.load_local(path, embedding, allow_dangerous_deserialization=True)
        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6, "fetch_k": 30})
    except Exception:
        logger.exception("Error loading FAISS model")
        return None


def get_recommendations(title: str, df: pd.DataFrame, retriever: RetrieverLike | None, k: int = 5, filter_adult: bool = False) -> list[dict[str, Any]]:
    """Get movie recommendations based on a title."""
    try:
        title = title.strip()
        df = _apply_adult_filter(df, filter_adult)
        if title not in df['title'].values or retriever is None:
            return []
        results = retriever.invoke(title)
        recommendation_titles = [
            t for doc in results
            if (t := doc.metadata.get('title')) and t != title
        ][:k]
        # Filter out None values from get_movie_details
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
        df = _apply_adult_filter(df, filter_adult)
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
                recs = get_recommendations(title, df, retriever, k=10)
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
