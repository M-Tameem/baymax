import os
import google.generativeai as genai
import re 
import json
import random
import time

from dotenv import load_dotenv
load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-1.5-pro-latest")


# ---------- Step 1: Configuration ----------
def configure(api_key=None):
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing Google API key. Set GOOGLE_API_KEY env variable or pass it in.")
    genai.configure(api_key=api_key)


# ---------- Step 3: Call Gemini ----------
def call_gemini(prompt, model_name=None, temperature=0.2):
    model_name = model_name or GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    time.sleep(random.uniform(1.0, 2.0))  # 1–2 seconds between calls
    response = model.generate_content(prompt)
    return response.text.strip()


def build_prompt(data):
    return f"""
You are a clinical AI assistant. Provide a structured clinical summary in the following exact format:

**Medical Summary:**  
<text>

**Abnormal Labs/Vitals:**  
<text>

**Clinical Implications:**  
<text>

Only output those three sections. Do not include file names, disclaimers, or follow-up instructions.

Patient general summary: {json.dumps(data['diagnoses'], indent=2)}  
Recent Labs: {json.dumps(data['recent_labs'], indent=2)}  
Recent Vitals: {json.dumps(data['recent_vitals'], indent=2)}  
Active Medications: {json.dumps(data['active_medications'], indent=2)}
"""

def _extract_section(text: str, header: str) -> str:
    pattern = rf"\*\*{header}:\*\*\s*(.+?)(?=\n\*\*|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def summarize_patient(
    general_summary: dict,
    recent_labs_vitals: dict,
    active_medications: dict,
    model_name: str = None,
    temperature: float = 0.2
) -> dict:
    """
    Returns a dict with keys "Medical Summary", "Abnormal Labs/Vitals", "Clinical Implications".
    
    All inputs should be standard Python dicts or lists. We serialize them with json.dumps
    so the LLM sees structured JSON in the prompt.
    """
    model_name = model_name or GEMINI_MODEL

    # Build the prompt, embedding each dict as formatted JSON
    prompt = (
        "You are a clinical AI assistant. Provide a structured clinical summary in the following exact format:\n\n"
        "**Medical Summary:**  \n<text>\n\n"
        "**Abnormal Labs/Vitals:**  \n<text>\n\n"
        "**Clinical Implications:**  \n<text>\n\n"
        "Only output those three sections. Do not include file names, disclaimers, or follow-up instructions.\n\n"
        f"Patient general summary: {json.dumps(general_summary, indent=2)}  \n"
        f"Recent Labs and Vitals: {json.dumps(recent_labs_vitals, indent=2)}  \n"
        f"Active Medications: {json.dumps(active_medications, indent=2)}"
    )

    # Call the model
    raw = call_gemini(prompt, model_name=model_name, temperature=temperature)

    # Parse out each section
    return {
        "Medical Summary": _extract_section(raw, "Medical Summary"),
        "Abnormal Labs/Vitals": _extract_section(raw, "Abnormal Labs/Vitals"),
        "Clinical Implications": _extract_section(raw, "Clinical Implications"),
    }

if __name__ == "__main__":
    exit