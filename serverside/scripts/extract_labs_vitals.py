"""
FHIR Clinical Data Parser

This module extracts clinical data (diagnoses, vitals, labs) from FHIR JSON files.
"""
import json
from datetime import datetime
from collections import defaultdict

# Phrases to exclude from diagnoses (social determinants, not clinical diagnoses)
EXCLUDE_PHRASES = [
    "employment", "education", "school", "labor force", "income",
    "environment", "social determinant", "housing", "insurance",
    "received education", "reports of violence", "works in"
]

def safe_parse_date(date_str):
    """
    Safely parse a date string to datetime object.
    
    Args:
        date_str (str): ISO format date string
        
    Returns:
        datetime: Parsed datetime or datetime.min if parsing fails
    """
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.min

def is_valid_diagnosis(code_data):
    """
    Check if a condition code represents a valid clinical diagnosis.
    
    Args:
        code_data (dict): The FHIR code data for a condition
        
    Returns:
        bool: True if the condition is a valid clinical diagnosis
    """
    text = code_data.get("text", "").lower()
    if any(phrase in text for phrase in EXCLUDE_PHRASES):
        return False
    codings = code_data.get("coding", [])
    return any(
        c.get("system", "").startswith("http://snomed.info") or
        "icd" in c.get("system", "")
        for c in codings
    )

def get_clinical_data(file_path):
    """
    Extract clinical data from a single FHIR JSON file.
    
    Args:
        file_path (str): Path to the FHIR JSON file
        
    Returns:
        dict: Dictionary containing diagnoses, recent vitals, and recent labs
    """
    try:
        with open(file_path) as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {
            "diagnoses": None,
            "recent_vitals": None,
            "recent_labs": None
        }
        
    conditions = {}
    recent_vitals = defaultdict(lambda: {'date': None, 'value': None})
    recent_labs = defaultdict(lambda: {'date': None, 'value': None})
    
    for e in raw_data.get("entry", []):
        r = e.get("resource", {})
        rtype = r.get("resourceType")
        
        if rtype == "Condition":
            code_data = r.get("code", {})
            if not is_valid_diagnosis(code_data):
                continue
            code = code_data.get("text", "Unknown")
            onset = safe_parse_date(r.get("onsetDateTime", "1900"))
            if code not in conditions or onset > conditions[code]["_onset"]:
                conditions[code] = {
                    "diagnosis": code,
                    "onset": r.get("onsetDateTime"),
                    "_onset": onset
                }
                
        elif rtype == "Observation":
            cat = r.get("category", [{}])[0].get("coding", [{}])[0].get("code", "")
            test = r.get("code", {}).get("text", "Unknown")
            value = r.get("valueQuantity", {}).get("value")
            date = r.get("effectiveDateTime")
            if date and cat == "vital-signs":
                if not recent_vitals[test]['date'] or date > recent_vitals[test]['date']:
                    recent_vitals[test] = {'date': date, 'value': value}
            elif date and cat == "laboratory":
                if not recent_labs[test]['date'] or date > recent_labs[test]['date']:
                    recent_labs[test] = {'date': date, 'value': value}
    
    # Clean up internal tracking data
    for c in conditions.values():
        if '_onset' in c:
            del c['_onset']
    
    return {
        "diagnoses": list(conditions.values()) if conditions else None,
        "recent_vitals": dict(recent_vitals) if recent_vitals else None,
        "recent_labs": dict(recent_labs) if recent_labs else None
    }