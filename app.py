from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import joblib
from difflib import SequenceMatcher
import re
from rapidfuzz import fuzz
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from urllib.parse import unquote

def recommend(movie, df, top_indices, top_distances, threshold=0):
    movie = movie.strip()
    
    match = df[df['title'].str.lower() == movie.lower()]
    if match.empty:
        return f"'{movie}' not found in the database!"

    movie_index = match.index[0]  # this is now integer index

    similar_ids = top_indices[movie_index][1:]
    scores = 1 - top_distances[movie_index][1:]

    recommendations = [
        df.iloc[i]['title']
        for i, score in zip(similar_ids, scores)
        if i < len(df) and score >= threshold
    ]
    return recommendations

lemmatizer = WordNetLemmatizer()


def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower())
    return synonyms

def tokenize_and_lemmatize(text):
    tokens = re.findall(r'\w+', text.lower())
    return [lemmatizer.lemmatize(token) for token in tokens]

def get_popularity(title):
    try:
        return float(df[df['title'] == title]['popularity'].values[0])
    except Exception:
        return 0

def search(query, df, max_results=20):
    query = query.strip().lower()
    query_tokens = tokenize_and_lemmatize(query)
    synonym_sets = [get_synonyms(token) | {token} for token in query_tokens]
    matches = []
    input_length = len(query.replace(' ', ''))
    for idx, row in df.iterrows():
        title = row['title']
        title_tokens = row['tokens_lemmas']
        title_lower = str(title).lower()
        is_short_query = len(query) <= 5
        prefix_match_bonus = 0
        prefix_matched = False

        # Prefix match logic: boost score if any title token starts with any query token
        for token in title_tokens:
            for q in query_tokens:
                if q and token.startswith(q):
                    prefix_match_bonus += 15
                    prefix_matched = True

        # Only consider titles with at least one query token in their tokens or a prefix match
        if not (set(query_tokens) & set(title_tokens) or prefix_matched):
            continue

        word_matches = sum(any(t in syn_set for t in title_tokens) for syn_set in synonym_sets)
        substring_matches = sum(title_lower.count(token) for token in query_tokens)
        fuzzy_score = max(fuzz.partial_ratio(token, title_lower) for token in query_tokens)
        sequence_similarity = SequenceMatcher(None, query, title_lower).ratio()
        token_match_ratio = len(set(query_tokens) & set(title_tokens)) / max(len(set(query_tokens)), 1)
        # Weighted scoring: more weight to prefix, sequence, and token match
        score = (
            word_matches * 8 +
            substring_matches * 2 +
            (fuzzy_score / 100) * 5 +
            sequence_similarity * 30 +
            token_match_ratio * 20 +
            prefix_match_bonus
        )
        min_fuzzy = max(fuzz.partial_ratio(token, title_lower) for token in query_tokens)
        # Allow prefix matches or strong overall matches
        if (score > 30 and sequence_similarity > 0.5) or prefix_matched:
            matches.append((title, score))

    if not matches:
        return []
    matches.sort(key=lambda x: x[1], reverse=True)
    top_matches = matches[:max_results]
    top_matches.sort(key=lambda x: get_popularity(x[0]), reverse=True)
    return [title for title, score in top_matches]

try:
    df = joblib.load('movie_list.pkl')
    top_indices = joblib.load('top_indices.pkl')
    distances = joblib.load('top_distances.pkl')
except Exception as e:
    print("Failed to load joblib files:", e)


# Clean and index for fast lookup
df['title_cleaned'] = df['title'].str.strip().str.lower()
df.set_index('title_cleaned', inplace=True)
df.drop_duplicates(subset='title', inplace=True)

# Precompute tokenized/lemmatized titles for search optimization
def _precompute_tokens_lemmas(title):
    return tokenize_and_lemmatize(str(title))

df['tokens_lemmas'] = df['title'].str.lower().apply(_precompute_tokens_lemmas)

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"),name='static')
templates = Jinja2Templates(directory="templates")

@app.get('/',response_class=HTMLResponse)
async def home(request : Request):
    return templates.TemplateResponse(request,'index.html',{'request': request})

@app.post('/search', response_class=HTMLResponse)
async def search_movie(request: Request, search_movie: str = Form(...)):
    result = search(search_movie,df)
    not_found = False
    if not result:
        not_found = True
    return templates.TemplateResponse(request,'search.html', {
        'request': request,
        'search_result': result,
        'not_found': not_found
    })

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(request,"movie_not_found.html", {"request": request}, status_code=404)

@app.get('/movie/{title}', response_class=HTMLResponse)
async def movie_detail(request: Request, title: str):
    decoded_title = unquote(title).strip().lower()
    if decoded_title in df.index:
        details = df.loc[decoded_title].to_dict()
        # Ensure fields that must be lists are lists, not floats (NaN)
        for field in ['cast', 'crew', 'genres']:
            if not isinstance(details.get(field), list):
                details[field] = []
        if not isinstance(details.get('overview'), list):
            details['overview'] = ""
        # Use the original title for recommendations
        original_title = str(df.loc[decoded_title, 'title'])


    else:
        raise HTTPException(status_code=404, detail="Movie not found")
    recommended_movies = recommend(original_title, df.reset_index(), top_indices, distances)
    return templates.TemplateResponse(request, 'movie.html', {
        'request': request,
        'title': original_title,
        'details': details,
        'recommended': recommended_movies
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)