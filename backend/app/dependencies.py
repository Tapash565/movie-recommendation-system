from fastapi import Request
from fastapi.templating import Jinja2Templates
import services

# Centralized Template Engine
templates = Jinja2Templates(directory="templates")

def jinja_format_number(value):
    """Jinja2 filter to format numbers with commas."""
    if value is None:
        return "N/A"
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return str(value)

def jinja_format_float(value, decimals=1):
    """Jinja2 filter to format floats with specified decimals."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)

# Register Custom Filters
templates.env.filters["format_number"] = jinja_format_number
templates.env.filters["format_float"] = jinja_format_float

def get_df(request: Request):
    """Dependency to get the movie dataframe from app state."""
    return request.app.state.df

def get_retriever(request: Request):
    """Dependency to get the lazy-loaded retriever from app state."""
    if request.app.state.retriever is None:
        request.app.state.retriever = services.load_retriever()
    return request.app.state.retriever

