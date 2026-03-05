import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.services as services
import joblib

client = TestClient(app)

# Fixtures for Data Loading
@pytest.fixture(scope="module")
def df():
    try:
        return joblib.load('movie_list.pkl')
    except Exception as e:
        pytest.skip(f"Failed to load movie data: {e}")

# Service Level Tests
def test_format_number():
    assert services.format_number(1000) == "1,000"
    assert services.format_number(None) == "N/A"

def test_format_float():
    assert services.format_float(3.14159) == "3.1"
    assert services.format_float(None) == "N/A"

def test_search_services(df):
    results = services.search_movies("Inception", df)
    assert len(results) > 0
    assert any(r['title'] == "Inception" for r in results)

def test_get_movie_details(df):
    if df.empty:
        pytest.skip("DataFrame is empty")
    # Get a movie ID that exists
    movie_id = df.iloc[0]['id']
    details = services.get_movie_details(movie_id, df)
    assert details is not None
    assert details['id'] == movie_id

# API Tests
def test_health_check():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_search_endpoint():
    with TestClient(app) as client:
        # Use common movie that is likely to be in any dataset
        response = client.get("/api/movies/search?q=Batman")
        assert response.status_code == 200
        assert "movies" in response.json()

def test_trending_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/movies/trending")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

def test_movie_details_404():
    with TestClient(app) as client:
        response = client.get("/api/movies/999999999") 
        assert response.status_code == 404
