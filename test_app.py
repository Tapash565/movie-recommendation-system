from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "MovieRec" in response.text

def test_search_found():
    response = client.post("/search", data={"search_movie": "Inception"})
    assert response.status_code == 200
    assert "Inception" in response.text

def test_search_not_found():
    response = client.post("/search", data={"search_movie": "asdkfjhasdkjfhakjsdhf"})
    assert response.status_code == 200
    assert "not_found" in response.text or "Movie not found" in response.text

def test_movie_detail_found():
    response = client.get("/movie/Inception")
    assert response.status_code == 200
    assert "Inception" in response.text

def test_movie_detail_not_found():
    response = client.get("/movie/asdkfjhasdkjfhakjsdhf")
    assert response.status_code == 404

def test_api_authenticate_success():
    response = client.post("/api/authenticate", data={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    assert response.json()["authenticated"] is True

def test_api_authenticate_fail():
    response = client.post("/api/authenticate", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 200
    assert response.json()["authenticated"] is False

def test_api_search_found():
    response = client.post("/api/search", data={"search_movie": "Inception"})
    assert response.status_code == 200
    assert "Inception" in str(response.json()["search_result"])

def test_api_search_not_found():
    response = client.post("/api/search", data={"search_movie": "asdkfjhasdkjfhakjsdhf"})
    assert response.status_code == 200
    assert response.json()["not_found"] is True

# The logout endpoint is expected to return a 303 status code because it redirects the user after logging out.
def test_logout():
    with TestClient(app) as client:
        # Login first to set session
        client.post("/login", data={"username": "admin", "password": "admin"})

        # Now logout
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 303  # Redirect
