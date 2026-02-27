import pytest
from app.services.utils import sanitize_for_json, format_number

def test_sanitize_for_json():
    assert sanitize_for_json("Hello") == "Hello"
    assert sanitize_for_json(float('nan')) is None
    assert sanitize_for_json(float('inf')) is None
    assert sanitize_for_json(123) == 123

def test_format_number():
    assert format_number(1000) == "1,000"
    assert format_number(1000000) == "1,000,000"
    assert format_number(500) == "500"
