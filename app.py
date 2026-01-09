from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import joblib
from urllib.parse import unquote
import hashlib
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(model='all-MiniLM-L6-v2')

vectorstore = FAISS.load_local('movie_recommendation_faiss', embedding, allow_dangerous_deserialization=True)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"fetch_k": 30}
)


def recommend(movie, df, k=5):
    movie = movie.strip()
    if movie not in df['title'].values:
        return f"'{movie}' not found in the database!"
    
    results = retriever.invoke(movie, k=k+1)
    # Filter out the exact match (the movie itself) and return top k
    recommendations = [doc.metadata['title'] for doc in results if doc.metadata['title'] != movie][:k]
    return recommendations

def search(query, df):
    query = query.strip().lower().replace(" ", "")
    matches = []

    for title in df['title']:
        cleaned_title = str(title).lower().replace(" ", "")
        if query in cleaned_title:
            matches.append(title)

    return matches if matches else [f"'{query}' not found in the database!"]

try:
    df = joblib.load('movie_list.pkl')
except Exception as e:
    print("Failed to load joblib files:", e)


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")
app.mount("/static", StaticFiles(directory="static"), name='static')
templates = Jinja2Templates(directory="templates")

users = {"admin": hashlib.sha256("admin".encode()).hexdigest()}


@app.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})


@app.post("/signup", response_class=HTMLResponse)
async def signup_post(request: Request, username: str = Form(...), password: str = Form(...)):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    if username in users:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username already exists."})
    users[username] = hashed_pw
    request.session['user'] = username
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)

@app.post("/api/recommend")
async def api_recommend(movie: str = Form(...)):
    recs = recommend(movie, df.reset_index())
    return JSONResponse({"recommendations": recs})


@app.post("/api/search")
async def api_search(search_movie: str = Form(...)):
    result = search(search_movie, df)
    return JSONResponse({"search_result": result, "not_found": not bool(result)})


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    if username in users and users[username] == hashed_pw:
        request.session['user'] = username
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password."})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/authenticate")
async def api_authenticate(username: str = Form(...), password: str = Form(...)):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    if username in users and users[username] == hashed_pw:
        return JSONResponse({"authenticated": True})
    else:
        return JSONResponse({"authenticated": False})


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get('user')
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.post("/search", response_class=HTMLResponse)
async def search_movie(request: Request, search_movie: str = Form(...)):
    result = search(search_movie, df)
    not_found = not bool(result) or (len(result) == 1 and "not found" in str(result[0]).lower())
    return templates.TemplateResponse("search.html", {
        "request": request,
        "search_result": result if not not_found else [],
        "not_found": not_found,
        "user": request.session.get('user')
    })

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse("movie_not_found.html", {"request": request}, status_code=404)


@app.get("/api/movie/{title}")
async def api_movie_detail(request: Request, title: str):
    """JSON API endpoint for movie details"""
    decoded_title = unquote(title).strip().lower()
    match = df[df['title'].str.lower() == decoded_title]
    if not match.empty:
        details = match.iloc[0].to_dict()
        original_title = str(details.get('title', title))
        for field in ['cast', 'crew', 'genres']:
            if not isinstance(details.get(field), list):
                details[field] = []
        # Ensure overview is a string, default to empty string if missing or None
        overview_value = details.get('overview')
        if overview_value is None:
            details['overview'] = ""
        else:
            details['overview'] = str(overview_value)
    else:
        raise HTTPException(status_code=404, detail="Movie not found")
    recommended_movies = recommend(original_title, df)
    return JSONResponse({
        "title": original_title,
        "details": details,
        "recommended": recommended_movies,
    })

@app.get("/movie/{title}", response_class=HTMLResponse)
async def movie_detail(request: Request, title: str):
    decoded_title = unquote(title).strip().lower()
    match = df[df['title'].str.lower() == decoded_title]
    if not match.empty:
        details = match.iloc[0].to_dict()
        original_title = str(details.get('title', title))
        for field in ['cast', 'crew', 'genres']:
            if not isinstance(details.get(field), list):
                details[field] = []
        # Ensure overview is a string, default to empty string if missing or None
        overview_value = details.get('overview')
        if overview_value is None:
            details['overview'] = ""
        else:
            details['overview'] = str(overview_value)
    else:
        raise HTTPException(status_code=404, detail="Movie not found")
    recommended_movies = recommend(original_title, df)
    return templates.TemplateResponse("movie.html", {
        "request": request,
        "title": original_title,
        "details": details,
        "recommended": recommended_movies,
        "user": request.session.get('user')
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)