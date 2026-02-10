from fastapi import Request
from . import services

def get_df(request: Request):
    """Dependency to get the movie dataframe from app state."""
    return request.app.state.df

def get_retriever(request: Request):
    """Dependency to get the lazy-loaded retriever from app state."""
    if request.app.state.retriever is None:
        request.app.state.retriever = services.load_retriever()
    return request.app.state.retriever

