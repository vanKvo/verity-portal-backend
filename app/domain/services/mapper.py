from typing import List, Dict
from thefuzz import process, fuzz

def suggest_mappings(headers: List[str], target_schema: List[str]) -> List[Dict]:
    """
    Suggests mappings between input headers and a target schema using fuzzy logic.
    Only returns suggestions with a confidence score > 70.
    """
    suggestions = []
    
    # Pre-calculate normalized target schema for better matching
    # Map normalized names back to original names
    normalized_targets = {t.lower().replace("_", "").replace(" ", ""): t for t in target_schema}
    target_keys = list(normalized_targets.keys())
    
    for header in headers:
        normalized_header = header.lower().replace("_", "").replace(" ", "")
        
        # If we have an exact normalized match, use it immediately with 100 confidence
        if normalized_header in normalized_targets:
            suggestions.append({
                "header": header,
                "target": normalized_targets[normalized_header],
                "confidence": 100
            })
            continue

        # Otherwise, use fuzzy matching on the normalized strings
        # fuzz.ratio is more strict and better for short header names
        match_key, score = process.extractOne(normalized_header, target_keys, scorer=fuzz.ratio)
        
        if score > 70:
            suggestions.append({
                "header": header,
                "target": normalized_targets[match_key],
                "confidence": score
            })
            
    return suggestions
