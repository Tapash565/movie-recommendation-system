import math
import pandas as pd
from typing import Any


def sanitize_for_json(data: Any) -> Any:
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


def get_poster_url(poster_path: str | None) -> str:
    """Construct full TMDB image URL"""
    if poster_path and isinstance(poster_path, str):
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    # Use inline SVG data URI as fallback (no external dependencies)
    return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'%3E%3Crect fill='%23374151' width='500' height='750'/%3E%3Ctext fill='%239ca3af' font-family='system-ui' font-size='24' x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle'%3ENo%20Poster%3C/text%3E%3C/svg%3E"


def format_number(value: Any) -> str:
    """Format number with commas"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return str(value)


def format_float(value: Any, decimals: int = 1) -> str:
    """Format float with specified decimals"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)
