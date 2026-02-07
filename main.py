import os
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import services
from logger import get_logger

# Initialize logger for main
logger = get_logger("main")

# Suppress unnecessary logs but don't ignore warnings globally
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.critical("SECRET_KEY not found in environment variables!")
    raise RuntimeError("SECRET_KEY must be set in .env")

# Database initialization
import database as db
db.init_db()

# Routers
from routers import auth, movies, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load basic data on startup
    logger.info("Initializing Movie Recommendation System...")
    app.state.df = services.load_movie_data()
    
    # Lazy load retriever later
    app.state.retriever = None
    
    yield
    # Clean up resources if needed
    logger.info("Shutting down Movie Recommendation System...")

from dependencies import get_df, get_retriever

app = FastAPI(title="Movie Recommendation System", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

from dependencies import get_df, get_retriever, templates

# Middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on 0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
