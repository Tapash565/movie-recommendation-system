from rapidfuzz import process, fuzz
import joblib
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
import os
import math
import pandas as pd
import ast
from datetime import datetime
from langchain_core.documents import Document
from .logger import get_logger
from pathlib import Path

# Initialize logger for services
logger = get_logger("services")

# Define Data Paths
BASE_DIR = Path(__file__).resolve().parent.parent 
DATA_DIR = BASE_DIR / "data"
MOVIE_LIST_PATH = DATA_DIR / "movie_list.pkl"
FAISS_INDEX_PATH = DATA_DIR / "movie_recommendation_faiss"


def sanitize_for_json(data):
    """
    Recursively clean data to ensure it is JSON compliant.
    - Replaces NaN/Infinity with None
    - Handles nested dicts and lists
    """
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(i) for i in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return 0.0 # Or None, depending on preference. 0.0 is safer for UI math.
        return data
    elif pd.isna(data): # Catch numpy.nan, pd.NA, etc.
        return None
    return data


# Helper functions
def get_poster_url(poster_path):
    """Construct full TMDB image URL"""
    if poster_path and isinstance(poster_path, str):
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return "https://via.placeholder.com/500x750?text=No+Poster"

def format_number(value):
    """Format number with commas"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    try:
        return "{:,}".format(int(value))
    except:
        return str(value)

def format_float(value, decimals=1):
    """Format float with specified decimals"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}"
    except:
        return str(value)

def render_stars(vote_average):
    """Return star rating string"""
    if pd.isna(vote_average):
        return "N/A"
    stars = int(round(vote_average / 2))
    return "★" * stars + "☆" * (5 - stars)

def get_movie_details(identifier, df):
    """
    Get detailed information about a movie.
    identifier: can be a title (str) or a TMDB ID (int).
    """
    if isinstance(identifier, int):
        match = df[df['id'] == identifier]
    else:
        match = df[df['title'].str.lower() == str(identifier).lower()]
        
    if not match.empty:
        details = match.iloc[0].to_dict()
        
        # Ensure list fields are properly formatted
        for field in ['cast', 'crew', 'genres', 'keywords', 'production_companies']:
            if field in details:
                raw_value = details[field]

                # Normalize to list
                if not isinstance(raw_value, list):
                    if isinstance(raw_value, str) and raw_value:
                        try:
                            parsed = ast.literal_eval(raw_value)
                            raw_value = parsed if isinstance(parsed, list) else [parsed]
                        except Exception:
                            # Keep original string so we don't lose info
                            raw_value = [raw_value]
                    else:
                        raw_value = []

                # Extract names from dictionaries or convert to string
                processed_items = []
                for item in raw_value:
                    if isinstance(item, dict):
                        # Try different keys: 'name', 'character', 'job', or first available value
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
        
        # Ensure overview is a string
        overview_value = details.get('overview')
        if overview_value is None or (isinstance(overview_value, float) and str(overview_value) == 'nan'):
            details['overview'] = ""
        else:
            details['overview'] = str(overview_value)
        
        # Handle numeric fields
        for field in ['budget', 'revenue', 'runtime', 'vote_average', 'vote_count', 'popularity']:
            if field in details:
                val = details[field]
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    details[field] = 0.0 if field in ['vote_average', 'popularity'] else 0
                elif isinstance(val, (int, float)):
                    details[field] = val
                else:
                    details[field] = 0

        
        # Release date formatting can stay as it's often needed in data, but purely UI strings should go
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
    """
    Search for movies using a tiered "Smart Search" approach.
    
    Args:
        query: Search query string
        df: Movie dataframe
        limit: Maximum number of results to return
        order_by: Optional ordering - 'rating' (by vote_average desc), 'name' (alphabetical), or None (relevance)
    """
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

    # Tier 1: Direct Title Match (Substring or Exact)
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

    # Tier 2: Fuzzy Title Match
    titles_list = df['title'].tolist()
    fuzzy_results = process.extract(query, titles_list, scorer=fuzz.token_set_ratio, limit=limit)
    fuzzy_matches = [match[0] for match in fuzzy_results if match[1] >= 80]
    if add_unique(fuzzy_matches): 
        movies = [get_movie_details(t, df) for t in results_ordered]
        return _order_movies(movies, order_by)

    # Tier 3: Keyword Match
    if 'keywords' in df.columns:
        keyword_matches = df[df['keywords'].str.lower().str.contains(query, na=False)]['title'].tolist()
        if add_unique(keyword_matches): 
            movies = [get_movie_details(t, df) for t in results_ordered]
            return _order_movies(movies, order_by)

    movies = [get_movie_details(t, df) for t in results_ordered]
    return _order_movies(movies, order_by)

def _order_movies(movies, order_by):
    """
    Helper function to order movie results.
    
    Args:
        movies: List of movie detail dictionaries
        order_by: 'rating', 'name', or None
    
    Returns:
        Ordered list of movies
    """
    if not movies:
        return movies
    
    if order_by == 'rating':
        # Sort by vote_average descending (highest rated first)
        return sorted(movies, key=lambda x: x.get('vote_average') or 0, reverse=True)
    elif order_by == 'name':
        # Sort alphabetically by title
        return sorted(movies, key=lambda x: x.get('title', '').lower())
    else:
        # Keep relevance-based ordering (default)
        return movies

def get_recommendations(title, df, retriever, k=5):
    try:
        title = title.strip()
        if title not in df['title'].values:
            return []
        
        if retriever is None:
            return []
            
        results = retriever.invoke(title, k=k+1)
        recommendation_titles = [doc.metadata['title'] for doc in results if doc.metadata['title'] != title][:k]
        
        return [get_movie_details(t, df) for t in recommendation_titles]
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return []

def load_movie_data(path=MOVIE_LIST_PATH):
    """Load the movie dataframe."""
    try:
        return joblib.load(path)
    except Exception as e:
        logger.error(f"Error loading movie list: {e}")
        return []

def create_faiss_index(df, path=FAISS_INDEX_PATH):
    """Create a new FAISS index from the movie dataframe."""
    logger.info("Creating new FAISS index. This may take a few minutes...")
    try:
        if df is None or (isinstance(df, list) and not df):
            logger.error("Cannot create index: Movie data is empty.")
            return None

        # Prepare documents for embedding
        documents = []
        for _, row in df.iterrows():
            # Join tags into a single string if it's a list
            tags = row.get('tags', '')
            if isinstance(tags, list):
                tags = " ".join(tags)
            
            # Create document with metadata
            doc = Document(
                page_content=str(tags),
                metadata={
                    "id": int(row['id']),
                    "title": str(row['title'])
                }
            )
            documents.append(doc)
        
        # Initialize embedding model
        embedding = HuggingFaceEndpointEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2')
        
        # Create and save vectorstore
        vectorstore = FAISS.from_documents(documents, embedding)
        vectorstore.save_local(path)
        
        logger.info(f"FAISS index created and saved to {path}.")
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"fetch_k": 30}
        )
    except Exception as e:
        logger.error(f"Error creating FAISS index: {e}")
        return None

def load_retriever(path=FAISS_INDEX_PATH):
    """
    Lazy-load the FAISS retriever.
    If missing, attempts to create one from movie_list.pkl.
    """
    logger.info(f"Loading Recommendation Model from {path}...")
    try:
        # Check if directory exists
        if not os.path.exists(path):
            logger.warning(f"FAISS index directory {path} not found. Triggering auto-creation...")
            df = load_movie_data()
            return create_faiss_index(df, path)

        # Use CPU explicitly and small model
        embedding = HuggingFaceEndpointEmbeddings(model='sentence-transformers/all-MiniLM-L6-v2')
        vectorstore = FAISS.load_local(
            path, 
            embedding, 
            allow_dangerous_deserialization=True
        )
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"fetch_k": 30}
        )
        logger.info("Recommendation Model loaded successfully.")
        return retriever
    except Exception as e:
        logger.error(f"Error loading FAISS model: {e}. Attempting recovery...")
        # If loading fails (e.g. corrupted file), try to recreate
        try:
            df = load_movie_data()
            return create_faiss_index(df, path)
        except Exception as re:
            logger.error(f"Critical error: Could not recreate index: {re}")
            return None

def get_personalized_recommendations(user_library_ids, df, retriever, limit=16):
    """
    Generate personalized recommendations based on user's library.
    
    Args:
        user_library_ids: List of movie IDs in user's library (watched/rated)
        df: Movie dataframe
        retriever: FAISS retriever for similarity search
        limit: Number of recommendations to return (default 15)
    
    Returns:
        List of movie details dictionaries
    """
    try:
        if not user_library_ids or retriever is None:
            return []
        
        # Convert library IDs to titles
        library_titles = []
        for movie_id in user_library_ids:
            details = get_movie_details(movie_id, df)
            if details:
                library_titles.append(details['title'])
        
        if not library_titles:
            return []
        
        # Collect recommendations from each library movie
        recommendation_scores = {}
        
        for title in library_titles:
            try:
                # Get recommendations for this movie
                recs = get_recommendations(title, df, retriever, k=10)
                
                # Score each recommendation (movies appearing more frequently get higher scores)
                for rec in recs:
                    movie_id = rec['id']
                    # Skip if already in library
                    if movie_id in user_library_ids:
                        continue
                    
                    if movie_id not in recommendation_scores:
                        recommendation_scores[movie_id] = {
                            'score': 0,
                            'details': rec
                        }
                    recommendation_scores[movie_id]['score'] += 1
            except Exception as e:
                logger.warning(f"Error getting recommendations for {title}: {e}")
                continue
        
        # Sort by score (frequency) and then by vote_average
        sorted_recommendations = sorted(
            recommendation_scores.values(),
            key=lambda x: (x['score'], x['details'].get('vote_average', 0) or 0),
            reverse=True
        )
        
        # Return top N recommendations
        return [item['details'] for item in sorted_recommendations[:limit]]
        
    except Exception as e:
        logger.error(f"Error generating personalized recommendations: {e}")
        return []
