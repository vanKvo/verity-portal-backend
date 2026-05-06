import pytest
from app.domain.services.mapper import suggest_mappings

def test_suggest_mappings_exact_match():
    headers = ["first_name", "last_name"]
    target_schema = ["first_name", "last_name", "email"]
    
    suggestions = suggest_mappings(headers, target_schema)
    
    # Exact matches should have 100 confidence
    assert suggestions[0] == {"header": "first_name", "target": "first_name", "confidence": 100}
    assert suggestions[1] == {"header": "last_name", "target": "last_name", "confidence": 100}

def test_suggest_mappings_fuzzy_match():
    headers = ["FName", "LName"]
    target_schema = ["first_name", "last_name"]
    
    suggestions = suggest_mappings(headers, target_schema)
    
    # Should suggest target fields with confidence > 70
    assert suggestions[0]["header"] == "FName"
    assert suggestions[0]["target"] == "first_name"
    assert suggestions[0]["confidence"] > 70
    
    assert suggestions[1]["header"] == "LName"
    assert suggestions[1]["target"] == "last_name"
    assert suggestions[1]["confidence"] > 70

def test_suggest_mappings_no_match():
    headers = ["Something Random 123"]
    target_schema = ["first_name", "last_name"]
    
    suggestions = suggest_mappings(headers, target_schema)
    
    # Low confidence matches should not be suggested (or returned as None/empty)
    assert suggestions == []
