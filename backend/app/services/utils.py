import math
import pandas as pd

def sanitize_for_json(data):
    """
    Recursively clean data to ensure it is JSON compliant.
    """
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(i) for i in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif pd.isna(data):
        return None
    return data

def get_poster_url(poster_path):
    """Construct full TMDB image URL"""
    if poster_path and isinstance(poster_path, str):
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    return "https://via.placeholder.com/500x750?text=No+Poster"

def format_number(value):
    """Format number with commas"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    try:
        return "{:,}".format(int(value))
    except:
        return str(value)

def format_float(value, decimals=1):
    """Format float with specified decimals"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}"
    except:
        return str(value)
