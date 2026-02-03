import pytest
from fastapi.testclient import TestClient
from main import app
import services
import joblib

client = TestClient(app)

# Fixtures for Data Loading (copied concept from old test, but adapted)
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
    # Results is list of dicts now
    assert len(results) > 0
    assert any(r['title'] == "Inception" for r in results)

def test_get_movie_details(df):
    if df.empty:
        pytest.skip("DataFrame is empty")
    title = df.iloc[0]['title']
    details = services.get_movie_details(title, df)
    assert details is not None
    assert details['title'] == title

# API Tests
def test_home_page():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Trending" in response.text

def test_search_endpoint():
    with TestClient(app) as client:
        response = client.get("/search?q=Batman")
        assert response.status_code == 200
        assert "Batman" in response.text

def test_login_page():
    with TestClient(app) as client:
        response = client.get("/login")
        assert response.status_code == 200
        assert "Login" in response.text

def test_movie_details_404():
    with TestClient(app) as client:
        response = client.get("/movie/999999999") 
        assert response.status_code == 404
