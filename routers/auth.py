from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import database as db
from dependencies import templates
from logger import get_logger

# Initialize logger for auth
logger = get_logger("auth")

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"active_page": "login"})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user_id = db.verify_user(username, password)
    if user_id:
        logger.info(f"User {username} logged in successfully.")
        request.session["user"] = username
        request.session["user_id"] = user_id
        return RedirectResponse(url="/", status_code=303)
    else:
        logger.warning(f"Failed login attempt for username: {username}")
        return templates.TemplateResponse(request=request, name="login.html", context={
        "error": "Invalid username or password"
    })

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html", context={"active_page": "signup"})

@router.post("/signup")
def signup(request: Request, username: str = Form(...), password: str = Form(...)):
    existing_id = db.get_user_id(username)
    if existing_id:
        logger.warning(f"Signup failed: Username {username} already exists.")
        return templates.TemplateResponse(request=request, name="signup.html", context={
            "error": "Username already exists"
        })
    
    if len(password) < 4:
        return templates.TemplateResponse(request=request, name="signup.html", context={
            "error": "Password must be at least 4 characters"
        })
        
    if db.add_user(username, password):
        logger.info(f"New user created: {username}")
        user_id = db.get_user_id(username)
        request.session["user"] = username
        request.session["user_id"] = user_id
        return RedirectResponse(url="/", status_code=303)
    else:
        logger.error(f"Error creating account for username: {username}")
        return templates.TemplateResponse(request=request, name="signup.html", context={
            "error": "Error creating account"
        })

@router.get("/logout")
def logout(request: Request):
    username = request.session.get("user")
    logger.info(f"User {username} logged out.")
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
