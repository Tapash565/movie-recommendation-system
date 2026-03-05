import os
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .database import check_db_health, init_db
from .services.firebase_service import init_firebase
from . import services
from .logger import get_logger
from .rate_limit import limiter
from .routers import movies, recommendations, users, auth

# Initialize logger
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Database...")
    init_db()
    
    logger.info("Initializing Firebase...")
    init_firebase()
    
    logger.info("Initializing Movie Recommendation System...")
    # Pre-load data into app state for dependencies to use
    app.state.df = services.load_movie_data()
    # Lazy-load retriever via dependency or during first request
    app.state.retriever = None
    
    if not app.state.df.empty:
        logger.info(f"Successfully loaded {len(app.state.df)} movies.")
    else:
        logger.error("Failed to load movie data during startup.")
        
    yield
    # Shutdown
    logger.info("Shutting down Movie Recommendation System...")

app = FastAPI(
    title="Movie Recommendation API",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
# We relax this slightly to allow common deployment scenarios if CORS_ORIGINS is not perfectly set
cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
if not cors_origins:
    cors_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SlowAPI Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Skip for preflight
    if request.method == "OPTIONS":
        return await call_next(request)
        
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Enhanced CSP
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https://image.tmdb.org blob:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://vapi-public.s3.amazonaws.com https://api.vapi.ai; "
        "frame-ancestors 'none'; "
        "form-action 'self';"
    )
    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error occurred: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "error_type": type(exc).__name__
        }
    )

@app.get("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def read_root(request: Request):
    return """
    <html>
        <head><title>Movie Recommendation System</title></head>
        <body>
            <h1>Welcome to the Movie Recommendation System API</h1>
            <p>Go to <a href="/api/docs">/api/docs</a> for the API documentation.</p>
        </body>
    </html>
    """

@app.get("/api/health")
@limiter.limit("20/minute") # Increased limit slightly for monitoring
async def health_check(request: Request):
    """Deep health check including database and data readiness."""
    db_healthy = check_db_health()
    data_loaded = not request.app.state.df.empty
    is_fully_functional = db_healthy and data_loaded
    
    status_code = status.HTTP_200_OK if is_fully_functional else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_fully_functional else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "data_loaded": data_loaded,
            "environment": os.getenv("ENVIRONMENT", "production")
        }
    )

# Include Routers
# Note: Changing prefix to /api for recommendations as frontend expects /api/discover
app.include_router(movies.router, prefix="/api", tags=["Movies"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
