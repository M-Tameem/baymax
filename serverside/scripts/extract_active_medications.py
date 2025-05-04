"""
FHIR Active Medication Parser

This module extracts active medications from FHIR JSON files.
"""
import json
import os

def get_active_medications(file_path):
    """
    Extract active medications from a single FHIR JSON file.
    
    Args:
        file_path (str): Path to the FHIR JSON file
        
    Returns:
        list: List of active medication names
    """
    try:
        with open(file_path) as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []
        
    medication_lookup = {}
    active_medications = []
    
    # First pass: build Medication resource lookup
    for e in raw_data.get("entry", []):
        r = e.get("resource", {})
        if r.get("resourceType") == "Medication":
            med_id = r.get("id")
            med_code = r.get("code", {})
            med_text = med_code.get("text") or med_code.get("coding", [{}])[0].get("display")
            if med_id and med_text:
                medication_lookup[f"urn:uuid:{med_id}"] = med_text
    
    # Second pass: collect active medications
    for e in raw_data.get("entry", []):
        r = e.get("resource", {})
        if r.get("resourceType") in {"MedicationRequest", "MedicationStatement"}:
            if r.get("status") != "active":
                continue
            med_text = None
            
            if "medicationCodeableConcept" in r:
                med = r["medicationCodeableConcept"]
                med_text = med.get("text") or med.get("coding", [{}])[0].get("display")
            elif "medicationReference" in r:
                ref = r["medicationReference"].get("reference")
                med_text = medication_lookup.get(ref)
            
            if med_text and med_text != "Unknown":
                active_medications.append(med_text)
    
    return active_medications