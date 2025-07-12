from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "request" in response.context

def test_search_found():
    response = client.post("/search", data={"search_movie": "Inception"})
    assert response.status_code == 200
    assert "Inception" in response.text

# def test_search_not_found():
#     response = client.post("/search", data={"search_movie": "asdkfjhasdkjfhakjsdhf"})
#     assert response.status_code == 200

def test_movie_detail_found():
    response = client.get("/movie/Inception")
    assert response.status_code == 200
    assert "Inception" in response.text
    response = client.get("/movie/Furious 7")
    assert response.status_code == 200
    assert "Furious 7" in response.text

def test_movie_detail_not_found():
    response = client.get("/movie/asdkfjhasdkjfhakjsdhf")
    assert response.status_code == 404