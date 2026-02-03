# Movie Recommendation System - FastAPI Deployment

This project is a movie recommendation web application built with **FastAPI**. It features a modern, responsive UI, robust search capabilities, and personalized recommendations powered by a FAISS vector store.

## 📁 Directory Structure

```
movie_recommendation_system_deployment/
│
├── main.py                          # FastAPI Application Entry Point
├── services.py                      # Core Business Logic (Search, Recommendations)
├── database.py                      # PostgreSQL Database Management
├── requirements.txt                 # Python Dependencies
├── test_main.py                     # API Integration Tests
│
├── routers/                         # API Routers
│   ├── auth.py                      # Authentication (Login/Signup/Logout)
│   ├── movies.py                    # Movie Browsing & Details
│   └── users.py                     # Library Management (Bookmarks/Ratings)
│
├── templates/                       # Jinja2 HTML Templates
│   ├── base.html                    # Layout Template
│   ├── index.html                   # Home & Search Results
│   ├── ...                          # Other pages
│
├── static/                          # Static Assets
│   ├── css/style.css                # Glassmorphism Styles
│   └── js/main.js                   # Client-side Interactions
│
├── movie_recommendation_faiss/      # FAISS Vector Store
├── movie_list.pkl                   # Processed Movie Data
```

## 🎯 Features

### Web Interface
- **Glassmorphism UI**: A modern, dark-themed interface with translucent panels and smooth transitions.
- **Server-Side Rendering (SSR)**: Standard HTML/CSS for better SEO and performance, powered by Jinja2.
- **Interactive**: JavaScript-powered actions for bookmarking and rating without full page reloads.

### User Features
- **Smart Search**: Finds movies by exact title, fuzzy match (typos), or keywords.
- **Recommendations**: Content-based recommendations using vector similarity.
- **Library**: Save movies to "To Watch" or "Watched" and rate them.
- **Authentication**: secure login and signup functionality.

## 🚀 Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*Note: Ensure you have `rapidfuzz` installed if it's not picked up automatically.*

### 2. Run the Application
Start the development server using Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```
The app will be available at [http://localhost:8000](http://localhost:8000).

### 3. Run Tests
Verify the code correctness using `pytest`:
```bash
pytest test_main.py
```

## 🐳 Docker Deployment
(Optional) To run via Docker, ensure your `Dockerfile` exposes port 8000.
```bash
docker build -t movie-recommender .
docker run -p 8000:8000 movie-recommender
```

## 📝 Notes
- **App Architecture**: Moved from Streamlit (single script) to FastAPI (MVC-like pattern) for better scalability and separation of concerns.
- **Database**: Uses PostgreSQL for storing user data. Ensure your `.env` has valid DB credentials.
- **Model Loading**: The ML models (FAISS) are loaded once during application startup for efficiency.
