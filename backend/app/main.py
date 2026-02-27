import os
import warnings
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials

from . import database as db
from . import services
from .logger import get_logger
from .routers import auth, movies, users, recommendations
from .rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Suppress unnecessary logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Initialize logger
logger = get_logger("main")

# Load environment variables
load_dotenv()
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    # Database initialization
    logger.info("Initializing Database...")
    db.init_db()

    # Firebase initialization
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if not service_account_path:
        logger.critical("FIREBASE_SERVICE_ACCOUNT_PATH not found in environment variables!")
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_PATH must be set in .env")
    
    try:
        try:
            firebase_admin.get_app()
            logger.info("Firebase Admin already initialized.")
        except ValueError:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize Firebase Admin: {e}")
        raise RuntimeError(f"Firebase initialization failed: {e}") from e

    # Load basic data on startup
    logger.info("Initializing Movie Recommendation System...")
    app.state.df = services.load_movie_data()
    
    if app.state.df.empty:
        logger.critical("CRITICAL: Movie data failed to load!")
        raise RuntimeError("CRITICAL: Application cannot start without movie data.")
    
    logger.info(f"Successfully loaded {len(app.state.df)} movies.")
    
    app.state.retriever = None
    yield
    logger.info("Shutting down Movie Recommendation System...")

# CORS Middleware
cors_origins_raw = os.getenv("CORS_ORIGINS")
if cors_origins_raw and cors_origins_raw != "*":
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
else:
    # Default to production domains and localhost for development
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://movie-recommendation-system-phi-lac.vercel.app",
        "https://movie-recommendation-system-deployment.vercel.app",
    ]

app = FastAPI(title="Movie Recommendation System", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Restrict methods
    allow_headers=["Authorization", "Content-Type"],  # Restrict headers
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src *; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'"
    return response

# Health check endpoint
@app.get("/api/health")
async def health_check(request: Request):
    """Check if the API, database, and data are healthy."""
    db_status = db.check_db_health()
    data_loaded = hasattr(request.app.state, 'df') and not request.app.state.df.empty
    
    is_healthy = db_status and data_loaded
    
    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "data": "loaded" if data_loaded else "missing",
            "environment": ENVIRONMENT
        }
    )

# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(movies.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on 0.0.0.0:{port} (Environment: {ENVIRONMENT})")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=(ENVIRONMENT == "development")
    )

