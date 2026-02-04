import os
import warnings

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

import streamlit as st
import joblib
import math
import ast
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import pandas as pd
from rapidfuzz import process, fuzz
import json
from dotenv import load_dotenv
import database as db

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
db.init_db()

# Custom CSS for modern cinematic theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    /* Global Transitions */
    * {
        transition: all 0.2s ease-in-out;
    }

    /* Main Theme */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Glassmorphism Containers */
    .glass-panel {
        background: rgba(26, 28, 36, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Movie Cards */
    .movie-card {
        background: rgba(26, 28, 36, 0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 0;
        margin-bottom: 25px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.05);
        height: 100%;
        position: relative;
    }
    .movie-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 15px 30px rgba(124, 58, 237, 0.2);
        border-color: rgba(124, 58, 237, 0.5);
    }
    .movie-poster {
        width: 100%;
        height: 320px;
        object-fit: cover;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .movie-info {
        padding: 18px;
        background: linear-gradient(180deg, rgba(26,28,36,0) 0%, rgba(26,28,36,0.8) 100%);
    }
    
    /* Typography */
    h1, h2, h3, .stHeader {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    .title-text {
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 8px;
        color: white;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .subtitle-text {
        font-size: 0.95rem;
        color: rgba(255, 255, 255, 0.6);
    }
    
    /* Badges */
    .rating-badge {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.85rem;
        box-shadow: 0 4px 10px rgba(124, 58, 237, 0.3);
    }
    .genre-tag {
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        color: rgba(255, 255, 255, 0.85);
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-right: 6px;
        margin-bottom: 6px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
        opacity: 0.95;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 15px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
    }

    /* Hero Section */
    .hero-section {
        padding: 60px 40px;
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(14, 17, 23, 0) 100%), 
                    url('https://www.transparenttextures.com/patterns/dark-matter.png');
        border-radius: 24px;
        margin-bottom: 40px;
        border-left: 6px solid #7c3aed;
        position: relative;
        overflow: hidden;
    }
    .hero-section::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(124, 58, 237, 0.1) 0%, transparent 70%);
        z-index: 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
USER_DB_FILE = "users_db.json"

# Migration: Transfer users from json to sqlite if needed
def migrate_users():
    USER_DB_FILE = "users_db.json"
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r") as f:
                users = json.load(f)
            for username, hashed_pw in users.items():
                if db.get_user_id(username) is None:
                    db.add_user(username, "placeholder") # This will be overwritten by hashed_pw
                    # Manually update the hashed password since add_user hashes its input
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_pw, username))
                    conn.commit()
                    cursor.close()
                    db.release_connection(conn)
            os.rename(USER_DB_FILE, USER_DB_FILE + ".bak")
        except Exception as e:
            st.error(f"Migration error: {e}")

migrate_users()

if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None
if 'trending_movies' not in st.session_state:
    st.session_state.trending_movies = None
if 'view' not in st.session_state:
    st.session_state.view = "Home"

import services

# Load data and model
@st.cache_resource
def load_model():
    with st.spinner("Loading Recommendation Model..."):
        return services.load_retriever()

@st.cache_data
def load_data():
    with st.spinner("Loading Movie Database..."):
        return services.load_movie_data()

# Helper functions
def reset_selection():
    st.session_state.selected_movie = None

@st.fragment
def render_library_actions(user_id, movie_details):
    """Fragment to handle bookmarking and rating without full-page re-runs"""
    st.markdown("### 🏷️ Your Library")
    
    # Bookmark buttons
    current_status = db.get_bookmark(user_id, movie_details['id'])
    
    b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
    
    with b_col1:
        if st.button("📌 To Watch", width="stretch", 
                     type="primary" if current_status == "to_watch" else "secondary"):
            db.add_bookmark(user_id, movie_details['id'], movie_details['title'], "to_watch")
            st.toast(f"Added '{movie_details['title']}' to To Watch")
            # st.rerun()  # Removed to prevent full-page flicker
            
    with b_col2:
        if st.button("✅ Watched", width="stretch",
                     type="primary" if current_status == "watched" else "secondary"):
            db.add_bookmark(user_id, movie_details['id'], movie_details['title'], "watched")
            st.toast(f"Marked '{movie_details['title']}' as Watched")
            # st.rerun()  # Removed to prevent full-page flicker
    
    with b_col3:
        if current_status:
            if st.button("❌ Remove", width="stretch"):
                db.remove_bookmark(user_id, movie_details['id'])
                st.toast(f"Removed '{movie_details['title']}' from library")
                # st.rerun()  # Removed to prevent full-page flicker

    # Rating slider
    current_rating = db.get_rating(user_id, movie_details['id'])
    
    st.markdown("**Your Rating**")
    r_col1, r_col2 = st.columns([3, 1])
    with r_col1:
        new_rating = st.slider("Select rating", 0.0, 10.0, float(current_rating or 0), 0.5, label_visibility="collapsed")
    with r_col2:
        if st.button("Save Rating", width="stretch"):
            db.add_rating(user_id, movie_details['id'], movie_details['title'], float(new_rating))
            st.toast(f"Rated '{movie_details['title']}' as {new_rating}/10")
            # st.rerun()  # Removed to prevent full-page flicker

def get_poster_url(poster_path):
    """Construct full TMDB image URL"""
    if poster_path and isinstance(poster_path, str):
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return "https://via.placeholder.com/500x750?text=No+Poster"

def render_stars(vote_average):
    """Return star rating string"""
    if pd.isna(vote_average):
        return "N/A"
    stars = int(round(vote_average / 2))
    return "★" * stars + "☆" * (5 - stars)

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

def recommend(movie, df, retriever, k=5):
    try:
        movie = movie.strip()
        if movie not in df['title'].values:
            return []
        
        if retriever is None:
            st.error("Recommendation engine is not available.")
            return []
            
        results = retriever.invoke(movie, k=k+1)
        recommendations = [doc.metadata['title'] for doc in results if doc.metadata['title'] != movie][:k]
        return recommendations
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return []

def search(query, df, limit=12):
    """
    Search for movies using a tiered "Smart Search" approach:
    1. Direct Title Match (Substring/Exact)
    2. Similar Titles (Fuzzy matching for typos)
    3. Keywords (Metadata tags)
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
    # We prioritize exact names or titles starting with the query
    exact_matches = df[df['title'].str.lower() == query]['title'].tolist()
    if add_unique(exact_matches): return results_ordered
    
    starts_with = df[df['title'].str.lower().str.startswith(query)]['title'].tolist()
    if add_unique(starts_with): return results_ordered
    
    contains = df[df['title'].str.lower().str.contains(query, na=False)]['title'].tolist()
    if add_unique(contains): return results_ordered

    # Tier 2: Fuzzy Title Match (handles typos)
    titles_list = df['title'].tolist()
    fuzzy_results = process.extract(query, titles_list, scorer=fuzz.token_set_ratio, limit=limit)
    fuzzy_matches = [match[0] for match in fuzzy_results if match[1] >= 80] # High threshold for typos
    if add_unique(fuzzy_matches): return results_ordered

    # Tier 3: Keyword Match
    # Check if the query matches any keywords (stored as comma-separated or list-like strings)
    if 'keywords' in df.columns:
        # Simple string contains check on the keywords column
        keyword_matches = df[df['keywords'].str.lower().str.contains(query, na=False)]['title'].tolist()
        if add_unique(keyword_matches): return results_ordered

    return results_ordered

def get_movie_details(title, df):
    """Get detailed information about a movie"""
    match = df[df['title'].str.lower() == title.lower()]
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
                    details['release_date'] = date_obj.strftime('%B %d, %Y')
            except:
                pass
        
        return details
    return None

# Load resources
df = load_data()
if df is not None:
    retriever = load_model()

# Sidebar for authentication
with st.sidebar:
    st.title("🎬 Movie Recommender")
    
    if st.session_state.user:
        st.success(f"Welcome, {st.session_state.user}!")
        
        st.session_state.view = st.radio("Navigation", ["Home", "My Library"], index=0 if st.session_state.view == "Home" else 1)
        
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.user_id = None
            st.session_state.selected_movie = None
            st.session_state.view = "Home"
            st.rerun()
    else:
        auth_choice = st.radio("Choose action:", ["Login", "Sign Up"])
        
        if auth_choice == "Login":
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    user_id = db.verify_user(username, password)
                    if user_id:
                        st.session_state.user = username
                        st.session_state.user_id = user_id
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        else:  # Sign Up
            with st.form("signup_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign Up")
                
                if submit:
                    if db.get_user_id(username):
                        st.error("Username already exists")
                    elif len(password) < 4:
                        st.error("Password must be at least 4 characters")
                    else:
                        if db.add_user(username, password):
                            st.session_state.user = username
                            st.session_state.user_id = db.get_user_id(username)
                            st.success("Account created successfully!")
                            st.rerun()
                        else:
                            st.error("Error creating account")

# Main content
if df is None:
    st.error("Failed to load movie database. Please check the data files.")
else:
    st.title("🎬 Movie Recommendation System")
    
    # Search bar - Typing here will reset any selection
    search_query = st.text_input(
        "Search for a movie:", 
        placeholder="Enter movie title...", 
        on_change=reset_selection
    )
    
    # Search results - Only show if no movie is selected
    if search_query and not st.session_state.selected_movie:
        results = search(search_query, df)
        
        if results:
            st.subheader(f"Search Results ({len(results)})")
            
            with st.container(border=False):
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                # Display search results in a consistent grid
                cols = st.columns(4)
                for idx, movie_title in enumerate(results):
                    # Find movie in dataframe
                    matches = df[df['title'] == movie_title]
                    if not matches.empty:
                        row = matches.iloc[0]
                        with cols[idx % 4]:
                            poster_url = get_poster_url(row.get('poster_path'))
                            vote_average = row.get('vote_average', 0)
                            release_date = row.get('release_date', 'N/A')
                            year = str(release_date).split('-')[0] if '-' in str(release_date) else 'N/A'
                            
                            st.markdown(f"""
                            <div class="movie-card">
                                <img src="{poster_url}" class="movie-poster">
                                <div class="movie-info">
                                    <div class="title-text" title="{movie_title}">{movie_title}</div>
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <span class="subtitle-text">{year}</span>
                                        <span class="rating-badge">★ {format_float(vote_average)}</span>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Details", key=f"search_btn_{idx}", width="stretch"):
                                st.session_state.selected_movie = movie_title
                                st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning(f"No movies found matching '{search_query}'")
    
    # Display selected movie details
    if st.session_state.selected_movie:
        st.markdown("---")
        if st.button("← Back to List"):
            st.session_state.selected_movie = None
            st.rerun()

        movie_details = get_movie_details(st.session_state.selected_movie, df)
        
        if movie_details:
            # Layout: Poster (Left) + Details (Right)
            col1, col2 = st.columns([1, 2])
            
            with col1:
                poster_url = get_poster_url(movie_details.get('poster_path'))
                st.image(poster_url, width="stretch")
            
            with col2:
                st.markdown(f"# {movie_details.get('title', 'N/A')}")
                if 'tagline' in movie_details and movie_details['tagline']:
                    st.markdown(f"*{movie_details['tagline']}*")
                
                # Metadata Badges
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <span class="rating-badge">IMDb {format_float(movie_details.get('vote_average'))}</span>
                    <span style="margin-left: 10px;">{movie_details.get('release_date', 'N/A')}</span>
                    <span style="margin-left: 10px;">{format_number(movie_details.get('runtime'))} min</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Genres
                if movie_details.get('genres'):
                    genres_html = "".join([f'<span class="genre-tag">{g}</span>' for g in movie_details['genres']])
                    st.markdown(f'<div style="margin-bottom: 15px;">{genres_html}</div>', unsafe_allow_html=True)
                
                st.markdown("### Overview")
                st.write(movie_details.get('overview', 'No overview available.'))
                
                # Extended Info Tab
                tab1, tab2 = st.tabs(["Details", "Cast & Crew"])
                
                with tab1:
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Budget:** ${format_number(movie_details.get('budget'))}")
                    c1.markdown(f"**Revenue:** ${format_number(movie_details.get('revenue'))}")
                    c2.markdown(f"**Status:** {movie_details.get('status', 'N/A')}")
                    c2.markdown(f"**Original Language:** {movie_details.get('original_language', 'N/A').upper()}")
                    
                    if movie_details.get('production_companies'):
                        st.markdown(f"**Production:** {', '.join(movie_details['production_companies'][:3])}")
                
                with tab2:
                    if movie_details.get('cast'):
                        cast = movie_details['cast'] if isinstance(movie_details['cast'], list) else str(movie_details['cast']).split(',')
                        st.markdown(f"**Cast:** {', '.join(cast[:10])}")
                    if movie_details.get('crew'):
                        crew = movie_details['crew'] if isinstance(movie_details['crew'], list) else str(movie_details['crew']).split(',')
                        st.markdown(f"**Director/Crew:** {', '.join(crew[:5])}")

                # --- NEW SECTION: Bookmarking & Rating ---
                if st.session_state.user_id:
                    render_library_actions(st.session_state.user_id, movie_details)
                else:
                    st.info("💡 Login to bookmark and rate movies!")

            # Recommendations Section
            st.markdown("---")
            st.markdown("### 🎬 You Might Also Like")
            
            recommendations = recommend(st.session_state.selected_movie, df, retriever, k=4)
            
            if recommendations:
                cols = st.columns(4)
                for idx, rec_title in enumerate(recommendations):
                    # Lookup recommendation details
                    rec_matches = df[df['title'] == rec_title]
                    if not rec_matches.empty:
                        rec_row = rec_matches.iloc[0]
                        with cols[idx]:
                            rec_poster = get_poster_url(rec_row.get('poster_path'))
                            st.markdown(f"""
                            <div class="movie-card" style="margin-bottom: 10px;">
                                <img src="{rec_poster}" class="movie-poster" style="height: 200px;">
                                <div style="padding: 10px;">
                                    <div class="title-text" style="font-size: 0.9rem;" title="{rec_title}">{rec_title}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("View", key=f"rec_{idx}", width="stretch"):
                                st.session_state.selected_movie = rec_title
                                st.rerun()
            else:
                st.info("No recommendations available")
        
        if st.button("Clear Selection"):
            st.session_state.selected_movie = None
            st.rerun()
    
    elif st.session_state.view == "My Library":
        st.title("📚 My Movie Library")
        
        if not st.session_state.user_id:
            st.warning("Please login to view your library.")
        else:
            tab_tw, tab_w, tab_r = st.tabs(["📌 To Watch", "✅ Watched", "⭐ My Ratings"])
            
            def render_library_grid(movies, key_prefix):
                if not movies:
                    st.info("No movies in this list yet!")
                    return
                
                cols = st.columns(4)
                for idx, m in enumerate(movies):
                    movie_id = m['movie_id']
                    movie_title = m['movie_title']
                    
                    # Find movie in dataframe to get poster
                    matches = df[df['id'] == movie_id]
                    if not matches.empty:
                        row = matches.iloc[0]
                        poster_url = get_poster_url(row.get('poster_path'))
                        vote_average = row.get('vote_average', 0)
                        
                        with cols[idx % 4]:
                            poster_url = get_poster_url(row.get('poster_path'))
                            vote_average = row.get('vote_average', 0)
                            release_date = row.get('release_date', 'N/A')
                            year = str(release_date).split('-')[0] if '-' in str(release_date) else 'N/A'
                            
                            st.markdown(f"""
                            <div class="movie-card">
                                <img src="{poster_url}" class="movie-poster">
                                <div class="movie-info">
                                    <div class="title-text" title="{movie_title}">{movie_title}</div>
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <span class="subtitle-text">{year}</span>
                                        <span class="rating-badge">{"★ " + str(m.get('rating')) if 'rating' in m else "★ " + format_float(vote_average)}</span>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Details", key=f"{key_prefix}_{idx}", width="stretch"):
                                st.session_state.selected_movie = movie_title
                                st.session_state.view = "Home"
                                st.rerun()

            with tab_tw:
                bookmarks = db.get_user_bookmarks(st.session_state.user_id)
                to_watch = [b for b in bookmarks if b['status'] == 'to_watch']
                render_library_grid(to_watch, "library_tw")
                
            with tab_w:
                watched = [b for b in bookmarks if b['status'] == 'watched']
                render_library_grid(watched, "library_w")
                
            with tab_r:
                ratings = db.get_user_ratings(st.session_state.user_id)
                render_library_grid(ratings, "library_r")

    else:
        # Hero Section
        st.markdown("""
        <div class="hero-section">
            <h1 style="color: white; margin-bottom: 10px;">🎬 Discover Your Next Favorite Movie</h1>
            <p style="font-size: 1.2rem; color: #a0a0a0;">
                Explore thousands of movies and get personalized recommendations powered by AI.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Featured content / Trending
        st.markdown("### 🔥 Trending Movies")
        
        if not df.empty:
            # Sample 12 random movies for the grid
            if st.session_state.trending_movies is None:
                st.session_state.trending_movies = df.sample(min(12, len(df)))
            
            sample_df = st.session_state.trending_movies
            
            with st.container(border=False):
                st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
                # Grid Layout
                cols = st.columns(4)
                for idx, (_, row) in enumerate(sample_df.iterrows()):
                    with cols[idx % 4]:
                        poster_url = get_poster_url(row.get('poster_path'))
                        title = row['title']
                        vote_average = row.get('vote_average', 0)
                        release_date = row.get('release_date', 'N/A')
                        year = str(release_date).split('-')[0] if '-' in str(release_date) else 'N/A'
                        
                        st.markdown(f"""
                        <div class="movie-card">
                            <img src="{poster_url}" class="movie-poster">
                            <div class="movie-info">
                                <div class="title-text" title="{title}">{title}</div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <span class="subtitle-text">{year}</span>
                                    <span class="rating-badge">★ {format_float(vote_average)}</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Details", key=f"home_btn_{idx}", width="stretch"):
                            st.session_state.selected_movie = title
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)