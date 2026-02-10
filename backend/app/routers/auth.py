from fastapi import APIRouter, Request, HTTPException, Depends
from ..schemas import UserLogin, UserCreate

from .. import database as db
from ..logger import get_logger

# Initialize logger for auth
logger = get_logger("auth")

router = APIRouter()

@router.post("/api/auth/login")
async def login(request: Request, user_data: UserLogin):
    """Handle user login via API."""
    user_id = db.verify_user(user_data.username, user_data.password)
    if user_id:
        logger.info(f"User '{user_data.username}' logged in successfully.")
        request.session["user"] = user_data.username
        request.session["user_id"] = user_id
        return {"success": True, "user": user_data.username, "user_id": user_id}
    
    logger.warning(f"Failed login attempt for username: '{user_data.username}'")
    raise HTTPException(status_code=401, detail="Invalid username or password")

@router.post("/api/auth/signup")
async def signup(request: Request, user_data: UserCreate):
    """Handle user registration and login via API."""
    existing_id = db.get_user_id(user_data.username)
    if existing_id:
        logger.warning(f"Signup failed: Username '{user_data.username}' already exists.")
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if len(user_data.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
        
    if db.add_user(user_data.username, user_data.password):
        logger.info(f"New user created: '{user_data.username}'")
        user_id = db.get_user_id(user_data.username)
        request.session["user"] = user_data.username
        request.session["user_id"] = user_id
        return {"success": True, "user": user_data.username, "user_id": user_id}
    
    logger.error(f"Error creating account for username: '{user_data.username}'")
    raise HTTPException(status_code=500, detail="Error creating account")

@router.post("/api/auth/logout")
def logout(request: Request):
    """Handle user logout."""
    username = request.session.get("user")
    logger.info(f"User '{username}' logged out.")
    request.session.clear()
    return {"success": True}

@router.get("/api/auth/me")
def get_current_user(request: Request):
    """Check current session."""
    user = request.session.get("user")
    user_id = request.session.get("user_id")
    if user:
        return {"user": user, "user_id": user_id, "authenticated": True}
    return {"authenticated": False}

