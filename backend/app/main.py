import asyncio
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import firebase_admin.auth as firebase_auth

from .config import get_settings
from .database import check_db_health, init_db
from .services.firebase_service import init_firebase
from . import services
from .logger import get_logger
from .rate_limit import limiter
from .routers import movies, recommendations, users, auth

# Initialize settings and logger
settings = get_settings()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting application in {settings.ENVIRONMENT} environment...")

    logger.info("Initializing Database...")
    init_db()

    logger.info("Initializing Firebase...")
    await asyncio.to_thread(init_firebase)

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

# CORS Configuration - use settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SlowAPI Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Middleware to extract Firebase UID for per-user rate limiting
@app.middleware("http")
async def extract_firebase_uid_for_rate_limiting(request: Request, call_next):
    """Extract Firebase UID from Authorization header for rate limiting."""
    auth_header = request.headers.get("authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            try:
                # Verify token and extract UID (lightweight, just decode)
                # Run in thread to avoid blocking the event loop
                decoded = await asyncio.to_thread(
                    firebase_auth.verify_id_token, token, check_revoked=False
                )
                request.state.firebase_uid = decoded.get("uid")
            except Exception as err:
                # Token invalid or expired - rate limit by IP only
                logger.debug(f"Token verification failed: {err}")

    response = await call_next(request)
    return response


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

    # Skip strict CSP for docs pages (Swagger UI loads from cdn.jsdelivr.net)
    docs_paths = ("/api/docs", "/api/redoc", "/api/openapi.json")
    if not request.url.path.startswith(docs_paths):
        # CSP without unsafe-inline for better security
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
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


@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Simple health check for platform infrastructure (no /api prefix)."""
    return {
        "status": "ok",
        "service": "movie-recommendation-api",
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/health")
@limiter.limit("100/minute")
async def deep_health_check(request: Request):
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
            "environment": settings.ENVIRONMENT
        }
    )


# Include Routers
# Using prefix="/api" for recommendations to support /api/discover
app.include_router(movies.router, prefix="/api", tags=["Movies"])
app.include_router(recommendations.router, prefix="/api", tags=["Recommendations"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.is_development)
