import os
import warnings
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from starlette.middleware.sessions import SessionMiddleware

from . import database as db
from . import services
from .logger import get_logger
from .routers import auth, movies, users, recommendations

# Suppress unnecessary logs but don't ignore warnings globally
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Initialize logger for main
logger = get_logger("main")

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    if not SECRET_KEY:
        logger.critical("SECRET_KEY not found in environment variables!")
        raise RuntimeError("SECRET_KEY must be set in .env")

    # Database initialization
    logger.info("Initializing Database...")
    db.init_db()

    # Load basic data on startup
    logger.info("Initializing Movie Recommendation System...")
    app.state.df = services.load_movie_data()
    
    # Validate data loaded successfully
    if app.state.df.empty:
        logger.critical("CRITICAL: Movie data failed to load! Application will have limited functionality.")
        logger.critical("Please ensure backend/data/movie_list.pkl exists and is accessible.")
    else:
        logger.info(f"Successfully loaded {len(app.state.df)} movies.")
    
    # Lazy load retriever later
    app.state.retriever = None
    
    yield
    
    # Clean up resources if needed
    logger.info("Shutting down Movie Recommendation System...")

app = FastAPI(title="Movie Recommendation System", lifespan=lifespan)

# Middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY, 
    https_only=False,  # Important for localhost (http)
    same_site="lax"    # Allows cookies to be sent in top-level navigations (and typically Ajax on same site/localhost)
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Include Routers
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(users.router)
app.include_router(recommendations.router)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

