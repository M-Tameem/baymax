import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

def parse_fhir_file(file_path):
    """
    Parse a single FHIR JSON file and return a structured patient summary.
    
    Args:
        file_path (str): Path to the FHIR JSON file
        
    Returns:
        dict: Structured patient summary
    """
    # Clinical resource types
    relevant_types = {
        "Condition", "MedicationRequest", "MedicationStatement",
        "Observation", "AllergyIntolerance", "Patient"
    }

    # Helper for date parsing
    def safe_parse_date(date_str):
        try:
            return datetime.fromisoformat(date_str)
        except Exception:
            return datetime.min

    try:
        with open(file_path) as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None

    entries = [e["resource"] for e in raw_data.get("entry", []) if e.get("resource", {}).get("resourceType") in relevant_types]
    if not entries:
        print(f"No relevant clinical data found in {file_path}")
        return None  # skip non-clinical or malformed files

    seen_conditions = {}
    med_status_map = {}  # Track best status per medication
    allergies = []
    demographics = {}
    recent_vitals = defaultdict(lambda: {'date': None, 'value': None})
    recent_labs = defaultdict(lambda: {'date': None, 'value': None})
    exclude_conditions = {"education", "employment", "social contact", "violence", "situation"}

    for res in entries:
        rtype = res.get("resourceType")

        if rtype == "Condition":
            code_text = res.get("code", {}).get("text", "Unknown")
            onset = res.get("onsetDateTime", "Unknown")
            if any(word in code_text.lower() for word in exclude_conditions):
                continue
            onset_dt = safe_parse_date(onset)
            if (code_text not in seen_conditions) or (onset_dt > seen_conditions[code_text]["_onset_dt"]):
                seen_conditions[code_text] = {'code': code_text, 'onset': onset, '_onset_dt': onset_dt}

        elif rtype in {"MedicationRequest", "MedicationStatement"}:
            med_text = res.get("medicationCodeableConcept", {}).get("text", "Unknown")
            status = res.get("status", "unknown").lower()

            # Upgrade status if necessary (active > completed > stopped)
            prev_status = med_status_map.get(med_text)
            if prev_status != "active":
                if status == "active":
                    med_status_map[med_text] = "active"
                elif status == "completed" and prev_status != "completed":
                    med_status_map[med_text] = "completed"
                elif status == "stopped" and not prev_status:
                    med_status_map[med_text] = "stopped"

        elif rtype == "Observation":
            code = res.get("code", {}).get("text", "Unknown")
            val = res.get("valueQuantity", {}).get("value")
            date = res.get("effectiveDateTime")
            cat = res.get("category", [{}])[0].get("coding", [{}])[0].get("code", "")
            if date and cat == "vital-signs":
                if not recent_vitals[code]['date'] or date > recent_vitals[code]['date']:
                    recent_vitals[code] = {'date': date, 'value': val}
            elif date and cat == "laboratory":
                if not recent_labs[code]['date'] or date > recent_labs[code]['date']:
                    recent_labs[code] = {'date': date, 'value': val}

        elif rtype == "AllergyIntolerance":
            reaction = res.get("code", {}).get("text")
            if reaction:
                allergies.append(reaction)

        elif rtype == "Patient":
            name = res.get("name", [{}])[0]
            full_name = " ".join(filter(None, [name.get("given", [None])[0], name.get("family")]))
            demographics = {
                "name": full_name,
                "gender": res.get("gender"),
                "birthDate": res.get("birthDate")
            }

    # Prepare structured output
    conditions = sorted((v for v in seen_conditions.values()), key=lambda x: x['_onset_dt'])
    for c in conditions:
        del c['_onset_dt']

    medications = [{"medication": k, "status": v} for k, v in med_status_map.items()]
    has_active = any(v == "active" for v in med_status_map.values())

    filename = Path(file_path).name
    
    summary = {
        "file": filename,
        "conditions_all_time": conditions or None,
        "medications_all_time": medications or None,
        "recent_vitals": dict(recent_vitals) or None,
        "recent_labs": dict(recent_labs) or None,
        "allergies": allergies or None,
        "demographics": demographics,
        "has_active_medications": has_active
    }

    return summary

if __name__ == "__main__":
    exit