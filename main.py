import os
import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import joblib
import services

# Suppress Warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey") # Should be in .env

# Database initialization
import database as db
db.init_db()

# Routers
from routers import auth, movies, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load basic data on startup
    print("Initializing Movie Recommendation System...")
    app.state.df = services.load_movie_data()
    
    # Lazy load retriever later
    app.state.retriever = None
    
    yield
    # Clean up resources if needed

def get_retriever(app: FastAPI):
    if app.state.retriever is None:
        app.state.retriever = services.load_retriever()
    return app.state.retriever

app = FastAPI(title="Movie Recommendation System", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
