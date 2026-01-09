import os
import warnings

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

import streamlit as st
import joblib
import hashlib
import math
import ast
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Page configuration
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .movie-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .movie-title {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .movie-detail {
        margin: 5px 0;
    }
    .recommendation-item {
        padding: 10px;
        margin: 5px 0;
        background-color: #e8eaf6;
        border-radius: 5px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'users' not in st.session_state:
    st.session_state.users = {"admin": hashlib.sha256("admin".encode()).hexdigest()}
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None

# Load data and model
@st.cache_resource
def load_model():
    embedding = HuggingFaceEmbeddings(model='all-MiniLM-L6-v2')
    vectorstore = FAISS.load_local('movie_recommendation_faiss', embedding, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"fetch_k": 30}
    )
    return retriever

@st.cache_data
def load_data():
    try:
        df = joblib.load('movie_list.pkl')
        return df
    except Exception as e:
        st.error(f"Failed to load movie data: {e}")
        return None

# Helper functions
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
    movie = movie.strip()
    if movie not in df['title'].values:
        return []
    
    results = retriever.invoke(movie, k=k+1)
    recommendations = [doc.metadata['title'] for doc in results if doc.metadata['title'] != movie][:k]
    return recommendations

def search(query, df):
    query = query.strip().lower().replace(" ", "")
    matches = []
    for title in df['title']:
        cleaned_title = str(title).lower().replace(" ", "")
        if query in cleaned_title:
            matches.append(title)
    return matches

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
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.selected_movie = None
            st.rerun()
    else:
        auth_choice = st.radio("Choose action:", ["Login", "Sign Up"])
        
        if auth_choice == "Login":
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
                    if username in st.session_state.users and st.session_state.users[username] == hashed_pw:
                        st.session_state.user = username
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        else:  # Sign Up
            with st.form("signup_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign Up")
                
                if submit:
                    if username in st.session_state.users:
                        st.error("Username already exists")
                    else:
                        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
                        st.session_state.users[username] = hashed_pw
                        st.session_state.user = username
                        st.success("Account created successfully!")
                        st.rerun()

# Main content
if df is None:
    st.error("Failed to load movie database. Please check the data files.")
else:
    st.title("🎬 Movie Recommendation System")
    
    # Search bar
    search_query = st.text_input("Search for a movie:", placeholder="Enter movie title...")
    
    if search_query:
        results = search(search_query, df)
        
        if results:
            st.subheader(f"Found {len(results)} movie(s)")
            
            # Display search results
            cols = st.columns(3)
            for idx, movie_title in enumerate(results[:12]):  # Limit to 12 results
                with cols[idx % 3]:
                    if st.button(movie_title, key=f"search_{idx}"):
                        st.session_state.selected_movie = movie_title
                        st.rerun()
        else:
            st.warning(f"No movies found matching '{search_query}'")
    
    # Display selected movie details
    if st.session_state.selected_movie:
        st.markdown("---")
        movie_details = get_movie_details(st.session_state.selected_movie, df)
        print(movie_details)
        
        if movie_details:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### {movie_details.get('title', 'N/A')}")
                st.markdown(f"**Overview:** {movie_details.get('overview', 'No overview available.')}")
                
                # Movie information
                st.markdown("#### Movie Information")
                info_col1, info_col2 = st.columns(2)
                
                with info_col1:
                    st.markdown(f"**Release Date:** {movie_details.get('release_date', 'N/A')}")
                    st.markdown(f"**Runtime:** {format_number(movie_details.get('runtime'))} minutes")
                    st.markdown(f"**Budget:** ${format_number(movie_details.get('budget'))}")
                    st.markdown(f"**Revenue:** ${format_number(movie_details.get('revenue'))}")
                
                with info_col2:
                    st.markdown(f"**Rating:** {format_float(movie_details.get('vote_average'))} / 10")
                    st.markdown(f"**Vote Count:** {format_number(movie_details.get('vote_count'))}")
                    st.markdown(f"**Popularity:** {format_float(movie_details.get('popularity'))}")
                    st.markdown(f"**Status:** {movie_details.get('status', 'N/A')}")
                
                # Additional details
                if movie_details.get('genres'):
                    st.markdown(f"**Genres:** {', '.join(movie_details['genres'])}")
                
                if movie_details.get('cast'):
                    cast_display = movie_details['cast'] if isinstance(movie_details['cast'], str) else ', '.join(movie_details['cast'][:10])
                    st.markdown(f"**Cast:** {cast_display}")
                
                if movie_details.get('crew'):
                    crew_display = movie_details['crew'] if isinstance(movie_details['crew'], str) else ', '.join(movie_details['crew'][:10])
                    st.markdown(f"**Crew:** {crew_display}")
                
                if movie_details.get('keywords'):
                    st.markdown(f"**Keywords:** {', '.join(movie_details['keywords'][:5])}")
                
                if movie_details.get('production_companies'):
                    st.markdown(f"**Production Companies:** {', '.join(movie_details['production_companies'][:3])}")
            
            with col2:
                st.markdown("#### Recommendations")
                recommendations = recommend(st.session_state.selected_movie, df, retriever)
                
                if recommendations:
                    for rec in recommendations:
                        if st.button(rec, key=f"rec_{rec}"):
                            st.session_state.selected_movie = rec
                            st.rerun()
                else:
                    st.info("No recommendations available")
        
        if st.button("Clear Selection"):
            st.session_state.selected_movie = None
            st.rerun()
    
    else:
        # Home page with random movies or popular movies
        st.markdown("### Welcome to the Movie Recommendation System!")
        st.markdown("Search for a movie above to get personalized recommendations.")
        
        if not df.empty:
            st.markdown("### Sample Movies")
            sample_movies = df['title'].sample(min(9, len(df))).tolist()
            
            cols = st.columns(3)
            for idx, movie in enumerate(sample_movies):
                with cols[idx % 3]:
                    if st.button(movie, key=f"sample_{idx}"):
                        st.session_state.selected_movie = movie
                        st.rerun()