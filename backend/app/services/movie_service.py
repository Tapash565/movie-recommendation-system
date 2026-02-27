import os
import joblib
import pandas as pd
import ast
from pathlib import Path
from rapidfuzz import process, fuzz
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_core.documents import Document
from ..logger import get_logger
from .utils import sanitize_for_json, get_poster_url
from datetime import datetime

logger = get_logger("movie_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MOVIE_LIST_PATH = DATA_DIR / "movie_list.pkl"
FAISS_INDEX_PATH = DATA_DIR / "movie_recommendation_faiss"

def load_movie_data(path=MOVIE_LIST_PATH):
    try:
        return joblib.load(path)
    except Exception as e:
        logger.error(f"Error loading movie list: {e}")
        return pd.DataFrame()

def get_movie_details(identifier, df):
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
            except:
                details['year'] = 'N/A'
        
        details['poster_url'] = get_poster_url(details.get('poster_path'))
        return sanitize_for_json(details)
    return None

def search_movies(query, df, limit=12, order_by=None):
    query = query.strip().lower()
    if not query:
        return []
    
    results_ordered = []
    seen_titles = set()

    def add_unique(titles):
        for t in titles:
            if t not in seen_titles:
                results_ordered.append(t)
                seen_titles.add(t)
            if len(results_ordered) >= limit:
                return True
        return False

    exact_matches = df[df['title'].str.lower() == query]['title'].tolist()
    if add_unique(exact_matches): 
        movies = [get_movie_details(t, df) for t in results_ordered]
        return _order_movies(movies, order_by)
    
    starts_with = df[df['title'].str.lower().str.startswith(query)]['title'].tolist()
    if add_unique(starts_with): 
        movies = [get_movie_details(t, df) for t in results_ordered]
        return _order_movies(movies, order_by)
    
    contains = df[df['title'].str.lower().str.contains(query, na=False)]['title'].tolist()
    if add_unique(contains): 
        movies = [get_movie_details(t, df) for t in results_ordered]
        return _order_movies(movies, order_by)

    titles_list = df['title'].tolist()
    fuzzy_results = process.extract(query, titles_list, scorer=fuzz.token_set_ratio, limit=limit)
    fuzzy_matches = [match[0] for match in fuzzy_results if match[1] >= 80]
    if add_unique(fuzzy_matches): 
        movies = [get_movie_details(t, df) for t in results_ordered]
        return _order_movies(movies, order_by)

    if 'keywords' in df.columns:
        keyword_matches = df[df['keywords'].str.lower().str.contains(query, na=False)]['title'].tolist()
        if add_unique(keyword_matches): 
            movies = [get_movie_details(t, df) for t in results_ordered]
            return _order_movies(movies, order_by)

    movies = [get_movie_details(t, df) for t in results_ordered]
    return _order_movies(movies, order_by)

def _order_movies(movies, order_by):
    if not movies:
        return movies
    if order_by == 'rating':
        return sorted(movies, key=lambda x: x.get('vote_average') or 0, reverse=True)
    elif order_by == 'name':
        return sorted(movies, key=lambda x: x.get('title', '').lower())
    else:
        return movies

def load_retriever(path=FAISS_INDEX_PATH):
    logger.info(f"Loading Recommendation Model from {path}...")
    try:
        if not os.path.exists(path):
            logger.warning(f"FAISS index directory {path} not found.")
            return None
        embedding = HuggingFaceEndpointEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2')
        vectorstore = FAISS.load_local(path, embedding, allow_dangerous_deserialization=True)
        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"fetch_k": 30})
    except Exception as e:
        logger.error(f"Error loading FAISS model: {e}")
        return None

def get_recommendations(title, df, retriever, k=5):
    try:
        title = title.strip()
        if title not in df['title'].values or retriever is None:
            return []
        results = retriever.invoke(title, k=k+1)
        recommendation_titles = [doc.metadata['title'] for doc in results if doc.metadata['title'] != title][:k]
        return [get_movie_details(t, df) for t in recommendation_titles]
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return []

def get_personalized_recommendations(user_library_ids, df, retriever, limit=16):
    try:
        if not user_library_ids or retriever is None:
            return []
        library_titles = []
        for movie_id in user_library_ids:
            details = get_movie_details(movie_id, df)
            if details:
                library_titles.append(details['title'])
        if not library_titles:
            return []
        recommendation_scores = {}
        for title in library_titles:
            try:
                recs = get_recommendations(title, df, retriever, k=10)
                for rec in recs:
                    movie_id = rec['id']
                    if movie_id in user_library_ids:
                        continue
                    if movie_id not in recommendation_scores:
                        recommendation_scores[movie_id] = {'score': 0, 'details': rec}
                    recommendation_scores[movie_id]['score'] += 1
            except:
                continue
        sorted_recommendations = sorted(recommendation_scores.values(), key=lambda x: (x['score'], x['details'].get('vote_average', 0) or 0), reverse=True)
        return [item['details'] for item in sorted_recommendations[:limit]]
    except Exception as e:
        logger.error(f"Error generating personalized recommendations: {e}")
        return []
