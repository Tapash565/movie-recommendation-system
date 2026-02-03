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
    # Load resources on startup
    print("Loading Movie Database...")
    try:
        app.state.df = joblib.load('movie_list.pkl')
        print("Movie Database loaded.")
    except Exception as e:
        print(f"Error loading movie list: {e}")
        app.state.df = None

    print("Loading Recommendation Model...")
    try:
        embedding = HuggingFaceEmbeddings(model='all-MiniLM-L6-v2')
        vectorstore = FAISS.load_local('movie_recommendation_faiss', embedding, allow_dangerous_deserialization=True)
        app.state.retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"fetch_k": 30}
        )
        print("Recommendation Model loaded.")
    except Exception as e:
        print(f"Error loading FAISS model: {e}")
        app.state.retriever = None
        
    yield
    # Clean up resources if needed

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
