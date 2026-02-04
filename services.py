from rapidfuzz import process, fuzz
import joblib
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os
import math
import pandas as pd
import ast
from datetime import datetime
from logger import get_logger

# Initialize logger for services
logger = get_logger("services")

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
                if isinstance(details[field], float) and math.isnan(details[field]):
                    details[field] = None
                elif details[field] == 0 and field in ['budget', 'revenue']:
                    details[field] = None
        
        # Format release_date
        if 'release_date' in details and details['release_date']:
            try:
                if isinstance(details['release_date'], str):
                    date_obj = datetime.strptime(details['release_date'], '%Y-%m-%d')
                    details['release_date_formatted'] = date_obj.strftime('%B %d, %Y')
                    details['year'] = str(date_obj.year)
                else:
                    details['release_date_formatted'] = str(details['release_date'])
                    details['year'] = 'N/A'
            except:
                details['release_date_formatted'] = str(details['release_date'])
                details['year'] = 'N/A'
        
        details['poster_url'] = get_poster_url(details.get('poster_path'))
        details['vote_average_formatted'] = format_float(details.get('vote_average'))
        details['budget_formatted'] = format_number(details.get('budget'))
        details['revenue_formatted'] = format_number(details.get('revenue'))
        
        return details
    return None

def search_movies(query, df, limit=12):
    """
    Search for movies using a tiered "Smart Search" approach.
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
    if add_unique(exact_matches): return [get_movie_details(t, df) for t in results_ordered]
    
    starts_with = df[df['title'].str.lower().str.startswith(query)]['title'].tolist()
    if add_unique(starts_with): return [get_movie_details(t, df) for t in results_ordered]
    
    contains = df[df['title'].str.lower().str.contains(query, na=False)]['title'].tolist()
    if add_unique(contains): return [get_movie_details(t, df) for t in results_ordered]

    # Tier 2: Fuzzy Title Match
    titles_list = df['title'].tolist()
    fuzzy_results = process.extract(query, titles_list, scorer=fuzz.token_set_ratio, limit=limit)
    fuzzy_matches = [match[0] for match in fuzzy_results if match[1] >= 80]
    if add_unique(fuzzy_matches): return [get_movie_details(t, df) for t in results_ordered]

    # Tier 3: Keyword Match
    if 'keywords' in df.columns:
        keyword_matches = df[df['keywords'].str.lower().str.contains(query, na=False)]['title'].tolist()
        if add_unique(keyword_matches): return [get_movie_details(t, df) for t in results_ordered]

    return [get_movie_details(t, df) for t in results_ordered]

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

def load_movie_data(path='movie_list.pkl'):
    """Load the movie dataframe."""
    try:
        return joblib.load(path)
    except Exception as e:
        logger.error(f"Error loading movie list: {e}")
        return []

def load_retriever(path='movie_recommendation_faiss'):
    """
    Lazy-load the FAISS retriever.
    Using MiniLM-L6-v2 for memory efficiency (approx 90MB).
    """
    logger.info(f"Loading Recommendation Model from {path}...")
    try:
        # Use CPU explicitly and small model
        embedding = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
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
        logger.error(f"Error loading FAISS model: {e}")
        return None
