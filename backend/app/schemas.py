from pydantic import BaseModel
from typing import List, Optional, Any
from enum import Enum

class Movie(BaseModel):
    id: int
    title: str
    year: str
    poster_url: str
    vote_average: float
    vote_count: int
    popularity: float
    overview: str
    genres: List[str]
    cast: List[str]
    crew: List[str]
    keywords: List[str]
    production_companies: List[str]
    runtime: Optional[float] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    adult: Optional[bool] = False

class MovieDetail(Movie):
    recommendations: List[Movie] = []
    bookmark_status: Optional[str] = None
    user_rating: Optional[float] = None

class MovieListResponse(BaseModel):
    movies: List[Movie]
    
class SearchResponse(BaseModel):
    search_query: str
    movies: List[Movie]
    result_count: int = 0
    total_results: int = 0
    page: int = 1
    page_size: int = 24
    order_by: str = ""

class BookmarkStatus(str, Enum):
    TO_WATCH = "to_watch"
    WATCHED = "watched"

class BookmarkRequest(BaseModel):
    movie_id: int
    movie_title: str
    status: BookmarkStatus

class RatingRequest(BaseModel):
    movie_id: int
    movie_title: str
    rating: float

class RemoveBookmarkRequest(BaseModel):
    movie_id: int

class UserPreferences(BaseModel):
    filter_adult: bool = False

class UserPreferencesUpdate(BaseModel):
    filter_adult: bool

