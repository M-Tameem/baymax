import logging
import re

def setup_logging():
    """
    Configure and return a logger
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def extract_drug_names(medications):
    drug_names = []
    for med in medications:
        # Remove dosage units and routes/forms
        med = re.sub(r'\b\d+(\.\d+)?\s*(MG|MCG|G|IU|ML)(/[A-Z]+)?\b', '', med, flags=re.IGNORECASE)
        med = re.sub(r'\b\d+\s*HR\b', '', med, flags=re.IGNORECASE)
        med = re.sub(r'\b(Oral|Tablet|Capsule|Patch|Solution|Injection|Suspension|Transdermal System|Syrup|IV|IM|Subcutaneous)\b', '', med, flags=re.IGNORECASE)

        # Remove extra symbols
        med = med.replace("(", "").replace(")", "")
        med = med.replace(",", "")  # remove commas

        # Split on " / " or just "/" if spacing is inconsistent
        parts = re.split(r'\s*/\s*', med)

        # Strip and add clean names
        for part in parts:
            cleaned = ' '.join(part.split())  # remove extra spaces
            if cleaned:
                drug_names.append(cleaned)
    return drug_names


def normalize_string(input_string):
    """
    Normalizes a string by capitalizing the first character and converting 
    everything else to lowercase, including first characters after spaces.
    
    Args:
        input_string (str): The input string to normalize
        
    Returns:
        str: The normalized string
    """
    if not input_string:
        return ""
    
    # Convert everything to lowercase first
    normalized = input_string.lower()
    
    # Capitalize only the first character of the entire string
    normalized = normalized[0].upper() + normalized[1:] if normalized else ""
    
    return normalized

def format_contraindication(contra):
    """Helper function to normalize contraindication format"""
    if not isinstance(contra, dict):
        return {"text": str(contra), "similarity": 0.0}
    
    # Handle different formats observed in logs
    if "patient_text" in contra and "contraindication_text" in contra:
        return {
            "text": f"Patient condition: {contra.get('patient_text', '')}\nContraindication: {contra.get('contraindication_text', '')}",
            "similarity": contra.get("similarity_score", 0.0)
        }
    elif "text" in contra:
        return {
            "text": contra.get("text", ""),
            "similarity": contra.get("similarity", 0.0)
        }
    else:
        # Convert any unexpected format to a standard one
        return {
            "text": str(contra),
            "similarity": 0.0
        }