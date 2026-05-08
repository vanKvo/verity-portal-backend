from typing import List, Dict
from thefuzz import process, fuzz

def suggest_mappings(headers: List[str], target_schema: List[str]) -> List[Dict]:
    """
    Suggests mappings between input headers and a target schema using fuzzy logic.
    Only returns suggestions with a confidence score > 70.
    """
    suggestions = []
    
    normalized_targets = {t.lower().replace("_", "").replace(" ", ""): t for t in target_schema}
    target_keys = list(normalized_targets.keys())
    
    for header in headers:
        normalized_header = header.lower().replace("_", "").replace(" ", "")
        
        if normalized_header in normalized_targets:
            suggestions.append({
                "header": header,
                "target": normalized_targets[normalized_header],
                "confidence": 100
            })
            continue

        match_key, score = process.extractOne(normalized_header, target_keys, scorer=fuzz.ratio)
        
        if score > 70:
            suggestions.append({
                "header": header,
                "target": normalized_targets[match_key],
                "confidence": score
            })
            
    return suggestions
