from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import database as db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"active_page": "login"})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user_id = db.verify_user(username, password)
    if user_id:
        request.session["user"] = username
        request.session["user_id"] = user_id
        return RedirectResponse(url="/", status_code=303)
    else:
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
        return templates.TemplateResponse(request=request, name="signup.html", context={
            "error": "Username already exists"
        })
    
    if len(password) < 4:
        return templates.TemplateResponse(request=request, name="signup.html", context={
            "error": "Password must be at least 4 characters"
        })
        
    if db.add_user(username, password):
        user_id = db.get_user_id(username)
        request.session["user"] = username
        request.session["user_id"] = user_id
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse(request=request, name="signup.html", context={
            "error": "Error creating account"
        })

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
