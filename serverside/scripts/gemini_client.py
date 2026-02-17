import os
import re
import json
import random
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def configure(api_key=None):
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing Google API key. Set GOOGLE_API_KEY in your .env file.")
    genai.configure(api_key=api_key)


def call_gemini(prompt, model_name=None, temperature=0.2):
    model_name = model_name or GEMINI_MODEL
    model = genai.GenerativeModel(model_name)
    time.sleep(random.uniform(1.0, 2.0))  # basic rate-limit buffer
    response = model.generate_content(prompt)
    return response.text.strip()


def _extract_section(text: str, header: str) -> str:
    pattern = rf"\*\*{header}:\*\*\s*(.+?)(?=\n\*\*|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def summarize_patient(
    general_summary: dict,
    recent_labs_vitals: dict,
    active_medications: dict,
    model_name: str = None,
    temperature: float = 0.2,
) -> dict:
    """
    Generate a structured clinical summary via Gemini.

    Returns a dict with keys:
      "Medical Summary", "Abnormal Labs/Vitals", "Clinical Implications"
    """
    model_name = model_name or GEMINI_MODEL

    prompt = (
        "You are a clinical AI assistant. Provide a structured clinical summary in the following exact format:\n\n"
        "**Medical Summary:**  \n<text>\n\n"
        "**Abnormal Labs/Vitals:**  \n<text>\n\n"
        "**Clinical Implications:**  \n<text>\n\n"
        "Only output those three sections. Do not include file names, disclaimers, or follow-up instructions.\n\n"
        f"Patient general summary: {json.dumps(general_summary, indent=2)}\n"
        f"Recent Labs and Vitals: {json.dumps(recent_labs_vitals, indent=2)}\n"
        f"Active Medications: {json.dumps(active_medications, indent=2)}"
    )

    raw = call_gemini(prompt, model_name=model_name, temperature=temperature)

    return {
        "Medical Summary": _extract_section(raw, "Medical Summary"),
        "Abnormal Labs/Vitals": _extract_section(raw, "Abnormal Labs/Vitals"),
        "Clinical Implications": _extract_section(raw, "Clinical Implications"),
    }
