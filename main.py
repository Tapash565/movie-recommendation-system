import os
import warnings
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import database as db
import services
from logger import get_logger
from routers import auth, movies, users

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
    
    # Lazy load retriever later
    app.state.retriever = None
    
    yield
    
    # Clean up resources if needed
    logger.info("Shutting down Movie Recommendation System...")

app = FastAPI(title="Movie Recommendation System", lifespan=lifespan)

# Middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(users.router)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

