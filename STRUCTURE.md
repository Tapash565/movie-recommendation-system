# Movie Recommendation System - Project Structure

This document outlines the structure of the Movie Recommendation System deployment project.

## 📁 Directory Structure

```
movie_recommendation_system_deployment/
│
├── app.py                          # Main FastAPI application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
├── test_app.py                    # Test suite
│
├── templates/                      # HTML Templates (Jinja2)
│   ├── index.html                  # Homepage
│   ├── login.html                  # Login page
│   ├── signup.html                 # Signup page
│   ├── search.html                 # Search results page
│   ├── movie.html                  # Movie details page
│   └── movie_not_found.html        # 404 error page
│
├── static/                         # Static Assets
│   ├── style.css                   # Main stylesheet
│   └── api.js                      # JavaScript API client
│
├── Data/                           # Movie datasets
│   ├── tmdb_5000_credits.csv
│   ├── tmdb_5000_movies.csv
│   └── TMDB_movie_dataset_v11.csv
│
├── movie_recommendation_faiss/     # FAISS vector store
│   ├── index.faiss
│   └── index.pkl
│
├── movie_list.pkl                  # Processed movie list
└── Movie_Recommendation_NLP.ipynb  # Jupyter notebook (model training)
```

## 🎯 API Endpoints

### HTML Endpoints (Server-Side Rendered)
- `GET /` - Homepage
- `GET /login` - Login page
- `POST /login` - Login form submission
- `GET /signup` - Signup page
- `POST /signup` - Signup form submission
- `GET /logout` - Logout user
- `POST /search` - Search movies (form submission)
- `GET /movie/{title}` - Movie details page

### JSON API Endpoints
- `POST /api/search` - Search movies (JSON)
- `POST /api/recommend` - Get movie recommendations (JSON)
- `GET /api/movie/{title}` - Get movie details (JSON)
- `POST /api/authenticate` - Authenticate user (JSON)

## 🎨 Frontend Structure

### Templates (`templates/`)
All HTML templates use Jinja2 templating engine and are server-side rendered.

**Key Features:**
- Responsive design with dark theme
- Consistent navigation across all pages
- Form-based interactions with server-side processing
- Error handling and user feedback

### Static Assets (`static/`)

#### `style.css`
Organized CSS with sections:
1. Login & Authentication Styles
2. Hero Section & Homepage
3. Global Styles & Reset
4. Navigation & Header
5. Container & Layout
6. Search Forms
7. Movie Details & Content
8. Recommendations & Lists

**Color Scheme:**
- Primary: `#4f8cff` (Blue)
- Accent: `#a3e635` (Green)
- Background: `#181c24` (Dark)
- Surface: `#23283a` (Dark Gray)
- Text: `#f3f3f3` (Light Gray)

#### `api.js`
JavaScript API client for client-side interactions:
- `searchMovies(query)` - Search for movies
- `getRecommendations(movie)` - Get recommendations
- `getMovieDetails(title)` - Get movie details (JSON)
- `authenticate(username, password)` - Authenticate user
- `logout()` - Logout user

## 🔧 Backend Structure

### `app.py`
FastAPI application with:
- Session-based authentication
- FAISS vector store for recommendations
- Movie search functionality
- Template rendering for HTML pages
- JSON API endpoints

**Key Functions:**
- `recommend(movie, df, k=5)` - Get movie recommendations
- `search(query, df)` - Search movies by title

### Data Flow
1. User submits search/recommendation request
2. FastAPI processes request
3. FAISS vector store retrieves similar movies
4. Results rendered as HTML or returned as JSON

## 🚀 Usage

### Running the Application
```bash
python app.py
```

The application will be available at `http://localhost:8000`

### Using the JSON API
```javascript
// Example: Search for movies
const results = await searchMovies("Inception");
console.log(results.search_result);

// Example: Get recommendations
const recs = await getRecommendations("Inception");
console.log(recs.recommendations);

// Example: Get movie details
const movie = await getMovieDetails("Inception");
console.log(movie.details);
```

## 📝 Notes

- The application uses both server-side rendering (HTML) and JSON API endpoints
- Session management is handled via FastAPI's SessionMiddleware
- Movie data is loaded from `movie_list.pkl` on startup
- FAISS index is loaded from `movie_recommendation_faiss/` directory
- All templates include the API JavaScript client for potential client-side enhancements
