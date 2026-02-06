import pytest
import joblib
from app import recommend, search, get_movie_details, format_number, format_float

# Load the dataframe for testing
@pytest.fixture
def df():
    try:
        return joblib.load('movie_list.pkl')
    except Exception as e:
        pytest.skip(f"Failed to load movie data: {e}")

@pytest.fixture
def retriever():
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_huggingface import HuggingFaceInferenceAPIEmbeddings
        embedding = HuggingFaceInferenceAPIEmbeddings(model_name='all-MiniLM-L6-v2')
        vectorstore = FAISS.load_local('movie_recommendation_faiss', embedding, allow_dangerous_deserialization=True)
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"fetch_k": 30}
        )
    except Exception as e:
        pytest.skip(f"Failed to load model: {e}")

def test_search_found(df):
    """Test searching for a movie that exists"""
    results = search("Inception", df)
    assert len(results) > 0
    assert any("Inception" in str(result) for result in results)

def test_search_not_found(df):
    """Test searching for a movie that doesn't exist"""
    results = search("asdkfjhasdkjfhakjsdhf", df)
    assert len(results) == 0

def test_recommend_found(df, retriever):
    """Test getting recommendations for a movie that exists"""
    # Get a movie that definitely exists
    test_movie = df['title'].iloc[0]
    recommendations = recommend(test_movie, df, retriever)
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0

def test_recommend_not_found(df, retriever):
    """Test getting recommendations for a movie that doesn't exist"""
    recommendations = recommend("NonExistentMovie12345", df, retriever)
    assert isinstance(recommendations, list)
    assert len(recommendations) == 0

def test_get_movie_details_found(df):
    """Test getting details for a movie that exists"""
    test_movie = df['title'].iloc[0]
    details = get_movie_details(test_movie, df)
    assert details is not None
    assert 'title' in details
    assert 'overview' in details

def test_get_movie_details_not_found(df):
    """Test getting details for a movie that doesn't exist"""
    details = get_movie_details("NonExistentMovie12345", df)
    assert details is None

def test_format_number():
    """Test number formatting function"""
    assert format_number(1000) == "1,000"
    assert format_number(1000000) == "1,000,000"
    assert format_number(None) == "N/A"

def test_format_float():
    """Test float formatting function"""
    assert format_float(3.14159, 2) == "3.14"
    assert format_float(10.0, 1) == "10.0"
    assert format_float(None) == "N/A"

def test_dataframe_not_empty(df):
    """Test that the dataframe loads and is not empty"""
    assert df is not None
    assert not df.empty
    assert 'title' in df.columns

