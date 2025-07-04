import numpy as np
from fastapi import FastAPI, File, UploadFile, Request, Form, Query
from typing import Dict
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import pickle
from typing import Optional
from pathlib import Path
import pandas as pd
from difflib import SequenceMatcher
import re
from rapidfuzz import fuzz
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from urllib.parse import unquote


df = pickle.load(open('movie_list.pkl', 'rb'))
top_indices = pickle.load(open('top_indices.pkl', 'rb'))
distances = pickle.load(open('top_distances.pkl', 'rb'))

df['title_cleaned'] = df['title'].str.strip().str.lower()

app = FastAPI()

app.mount("/static",StaticFiles(directory="static"),name='static')
templates = Jinja2Templates(directory="templates")

def recommend(movie, df, top_indices, top_distances, threshold=0):
    movie = movie.strip()
    if movie not in df['title'].values:
        return f"'{movie}' not found in the database!"

    movie_index = df[df['title'] == movie].index[0]
    similar_ids = top_indices[movie_index][1:]  # skip the movie itself
    scores = 1 - top_distances[movie_index][1:]  # convert distance to similarity

    recommendations = [
        df.iloc[i].title
        for i, score in zip(similar_ids, scores)
        if score >= threshold
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


def search(query, df, max_results=50):
    query = query.strip().lower()
    query_tokens = tokenize_and_lemmatize(query)

    # Collect all synonyms for each token in the query
    synonym_sets = [get_synonyms(token) | {token} for token in query_tokens]

    matches = []

    for title in df['title']:
        title_lower = str(title).lower()
        title_tokens = tokenize_and_lemmatize(title_lower)

        word_matches = sum(any(t in syn_set for t in title_tokens) for syn_set in synonym_sets)
        substring_matches = sum(title_lower.count(token) for token in query_tokens)
        fuzzy_score = max(fuzz.partial_ratio(token, title_lower) for token in query_tokens)
        sequence_similarity = SequenceMatcher(None, query, title_lower).ratio()

        # Token match ratio
        token_match_ratio = len(set(query_tokens) & set(title_tokens)) / max(len(set(query_tokens)), 1)

        # Combine scores
        score = (
            word_matches * 10 +
            substring_matches * 2 +
            (fuzzy_score / 100) * 5 +
            sequence_similarity * 5 +
            token_match_ratio * 10
        )

        if score > 0:
            matches.append((title, score))

    if not matches:
        return [f"'{query}' not found in the database!"]

    matches.sort(key=lambda x: x[1], reverse=True)
    return [title for title, score in matches][:max_results]



@app.get('/',response_class=HTMLResponse)
async def home(request : Request):
    return templates.TemplateResponse('index.html',{'request': request})

@app.post('/search', response_class=HTMLResponse)
async def search_movie(request: Request, search_movie: str = Form(...)):
    result = search(search_movie,df)
    return templates.TemplateResponse('search.html',{
        'request': request,
        'search_result': result
    })

@app.get('/movie/{title}', response_class=HTMLResponse)
async def movie_detail(request: Request, title: str):
    decoded_title = unquote(title).strip().lower()
    match = df[df['title_cleaned'] == decoded_title]
    
    if not match.empty:
        details = match.iloc[0].to_dict()

        # Ensure fields that must be lists are lists, not floats (NaN)
        for field in ['cast', 'crew', 'genres']:
            if not isinstance(details.get(field), list):
                details[field] = []

        if not isinstance(details.get('overview'), list):
            details['overview'] = ""

    else:
        details = None

    recommended_movies = recommend(title,df,top_indices,distances)    
    return templates.TemplateResponse('movie.html', {
        'request': request,
        'title': decoded_title,
        'details': details,
        'recommended': recommended_movies
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)