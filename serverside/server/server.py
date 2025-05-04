import logging
import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import shutil
import datetime
from typing import Dict, List, Any, Optional

# Add scripts/ directory to path for importing fhir_summary
scripts_path = Path(__file__).resolve().parent.parent / "scripts"
sys.path.append(str(scripts_path))
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("API_KEY")

from contraindication_checker import ContraindicationChecker
from fhir_summary import parse_fhir_file  # now importable
from extract_active_medications import get_active_medications
from extract_labs_vitals import get_clinical_data
from models import FreeformSummary, SummaryRequest, MatchRequest
from models import FreeformSummary, SummaryRequest, MatchRequest
from embedding import embed, cosine_similarity
from data_processing import load_ddinter_data
from utils import setup_logging, extract_drug_names, normalize_string, format_contraindication
from gemini_client import configure, build_prompt, call_gemini, summarize_patient
from safety_gate import safety_check


def download_model():
    url = "https://drive.google.com/file/d/1K4fFZaHMtJZvhlJLveILIWiUjgFB-frC/view?usp=sharing"
    dest_path = "data/pkl/contraindication_embeddings_final.pkl"

    if not os.path.exists(dest_path):
        print("Downloading model...")
        r = requests.get(url, stream=True)
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")


# Setup logging
logger = setup_logging()

# Load DDInter data once at startup
ddinter_df = load_ddinter_data()

checker = ContraindicationChecker(contraindications_path="../data/pkl/contraindication_embeddings_final.pkl")

def create_full_summary(file_path):
    patient_summary = parse_fhir_file(file_path)
    vitals_data = get_clinical_data(file_path)
    meds_data = get_active_medications(file_path)
    if not patient_summary or not vitals_data or not meds_data:
        raise ValueError("Failed to extract data from the FHIR file.")
    
    return patient_summary, meds_data, vitals_data

GEMINI_MODEL = configure(api_key)
#build_prompt("Gemini", "Gemini is a large language model that can assist with drug-drug interaction analysis.")
#response = call_gemini("What is the drug-drug interaction between aspirin and ibuprofen?")
#print(response)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/match")
def match_summary_input(request: MatchRequest):
    print(f"Received request: {request}")
    file_path = Path("../data/fhir/" + request.file_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    active_meds = get_active_medications(str(file_path))
    print(f"Active medications before extracted: {active_meds}")
    active_meds = extract_drug_names(active_meds)
    print(f"Active medications: {active_meds}")

    new_med = request.new_medication.strip().lower()
    active_meds = [m.strip().lower() for m in active_meds if m.strip()]
    

    # 1) Exact‐match lookup (score = 1.0)
    exact = []
    seen_pairs = set()
    for med in active_meds:
        mask = (
            (ddinter_df["A_norm"] == med) & (ddinter_df["B_norm"] == new_med)
        ) | (
            (ddinter_df["B_norm"] == med) & (ddinter_df["A_norm"] == new_med)
        )
        for _, row in ddinter_df[mask].iterrows():
            combo_key = tuple(sorted([row["A_norm"], row["B_norm"]]))
            if combo_key not in seen_pairs:
                seen_pairs.add(combo_key)
                exact.append({
                    "interaction": f"{row['Drug_A'].lower()} and {row['Drug_B'].lower()} interaction ({row['Level']})",
                    "score": 1.0
                })

    # 2) Fallback to embeddings up to 5 total, but only if sim >= 0.9
    results = exact.copy()
    THRESHOLD = 0.9
    if len(results) < 5:
        for med in active_meds:
            pair_text = f"{med} and {new_med} interaction"
            emb = embed(pair_text)

            # narrow candidates to any row involving either term
            cand = ddinter_df[
                (ddinter_df["A_norm"].isin([med, new_med])) |
                (ddinter_df["B_norm"].isin([med, new_med]))
            ].copy()
            if cand.empty:
                continue

            # compute similarity and filter by threshold
            cand["sim"] = cand["embedding"].apply(lambda e: cosine_similarity(emb, e))
            cand = cand[cand["sim"] >= THRESHOLD]
            if cand.empty:
                continue

            # pick the best remaining candidate
            best = cand.sort_values("sim", ascending=False).iloc[0]
            combo_key = tuple(sorted([best["A_norm"], best["B_norm"]]))
            if combo_key in seen_pairs:
                continue

            seen_pairs.add(combo_key)
            results.append({
                "interaction": best["combo"],
                "score": float(best["sim"])
            })

            if len(results) >= 5:
                break

    return {"top_5_ddi_matches": results[:5]}

@app.post("/summary")
def get_summary(request: SummaryRequest):
    # Check if the file exists
    file_path = Path(request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
    
    # Proceed with summarization if file exists
    summary = parse_fhir_file(request.file_path)
    return summary


@app.post("/discharge")
def discharge_decision(request: SummaryRequest):
    print(f"Received request: {request}")
    file_path = Path("../data/fhir/" + request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    patient_summary = parse_fhir_file(file_path)

    try:
        if not patient_summary:
            raise ValueError("Empty patient summary")

        prompt = (
            f"You are a hospital discharge safety assistant. Given the following patient summary, decide if it is safe "
            f"to discharge the patient. Your response must start with exactly one of the following: "
            f"'Yes', 'With manual review', 'No', or 'Absolutely not'. Then provide a short explanation.\n\n"
            f"Patient summary:\n{patient_summary}\n\nDecision:"
        )
        gemini_response = call_gemini(prompt)

        if not gemini_response:
            raise ValueError("No response from Gemini")

        lines = gemini_response.strip().splitlines()
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        first_line = non_empty_lines[0] if non_empty_lines else ""
        rest_of_response = "\n".join(non_empty_lines[1:]) if len(non_empty_lines) > 1 else ""

        decision_prefixes = ["With manual review", "Absolutely not", "Yes", "No"]
        matched_prefix = next((prefix for prefix in decision_prefixes if first_line.startswith(prefix)), None)

        if not matched_prefix:
            raise ValueError(f"Unexpected Gemini response format: '{first_line}'")

        decision = matched_prefix
        first_line_remainder = first_line[len(matched_prefix):].strip(" .:")
        justification = f"{first_line_remainder} {rest_of_response}".strip()

        print(f"Prompt sent to Gemini: {prompt}")
        print(f"Gemini response: {gemini_response}")
        print(f"Decision: {decision}")
        print(f"Justification: {justification}")

        return {
            "decision": decision,
            "justification": justification
        }

    except Exception as e:
        logger.error(f"Discharge endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-active-medications")
def extract_active_medications(request: SummaryRequest):
    file_path = Path("../data/fhir/" + request.file_path)
    medications = get_active_medications(file_path)
    if medications is None:
        return {"message": "Failed to parse file or no active medications found."}
    return {"active_medications": medications}

@app.post("/extract-labs-vitals")
def extract_labs_vitals(request: SummaryRequest):
    file_path = Path("../data/fhir/" + request.file_path)
    clinical_data = get_clinical_data(file_path)
    if clinical_data is None:
        return {"message": "Failed to parse file or no clinical data found."}
    return {"clinical_data": clinical_data}

@app.get("/list-all-patients")
def list_all_patients():
    """
    Lists all FHIR patient files found in the ../data/fhir/ directory
    
    Returns:
        A list of available patient file names
    """
    try:
        # Get the path to the FHIR data directory
        fhir_data_path = Path(__file__).resolve().parent.parent / "data" / "fhir"
        
        # Check if directory exists
        if not fhir_data_path.exists() or not fhir_data_path.is_dir():
            return {"error": f"Directory {fhir_data_path} not found"}
        
        # List all files in the directory (only include files, not subdirectories)
        patient_files = [file.name for file in fhir_data_path.iterdir() if file.is_file()]
        
        # Sort the files alphabetically for consistent output
        patient_files.sort()
        
        return {"patient_files": patient_files}
    
    except Exception as e:
        logger.error(f"Error listing patient files: {str(e)}")
        return {"error": f"Failed to list patient files: {str(e)}"}

@app.post("/upload-fhir")
async def upload_fhir_file(file: UploadFile = File(...)):
    """
    Uploads a FHIR R4 .json file and stores it in the ../data/fhir/ directory.
    """
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are allowed.")

    fhir_dir = Path(__file__).resolve().parent.parent / "data" / "fhir"
    fhir_dir.mkdir(parents=True, exist_ok=True)

    destination = fhir_dir / file.filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        attempt_to_parse = parse_fhir_file(destination)  # Call the function to parse the file
        if attempt_to_parse is None:
            raise ValueError("Uploaded file is empty or not a valid FHIR file.")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save the file.")

    return {"message": f"File '{file.filename}' uploaded successfully."}

@app.post("/ai-summary")
def ai_summary(request: SummaryRequest):
    file_path = Path("../data/fhir/" + request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
    
    try:
        patient_summary, active_meds, labs_vitals = create_full_summary(file_path)
        full_summary = summarize_patient(patient_summary, labs_vitals, active_meds)
        print(f"Full summary: {full_summary}")
        return {"summary": full_summary}
        
    except Exception as e:
        logger.error(f"AI Summary generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate AI summary.")


@app.post("/contraindication-checker")
def contra_checker(request: MatchRequest):
    # 1) Locate the file
    file_path = Path("../data/fhir/") / request.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    # 2) Extract structured data
    patient_summary, active_meds, labs_vitals = create_full_summary(file_path)
    full_summary = summarize_patient(patient_summary, labs_vitals, active_meds)

    # 3) Optionally normalize drug name
    drug_name = request.new_medication.strip()
    drug_name = normalize_string(drug_name)

    # 4) Build the dict the checker expects - note the key capitalization update!
    checker_input = {
        "medical_summary": full_summary.get("Medical Summary", ""),
        "abnormal_labs_vitals": full_summary.get("Abnormal Labs/Vitals", ""),
        "clinical_implications": full_summary.get("Clinical Implications", ""),
    }

    print(f"Checker input: {checker_input}")

    # 5) Run the checker
    matches = checker.check_contraindications(checker_input, drug_name)
    print(f"Matches found: {matches}")

    # 6) Return them in your response
    return {"contraindications": matches}

#@app.post("/submit-drug-order")
# """
# first thing, parse the JSON file,
# and extract the active medications, store in a variable
# and extract lab vitals, store in a variable
# and extract diagnoses, store in a variable
# then, check for any drug-drug interactions with the new medication with the active medications
# then check for any drug-lab interactions with the new medication with the lab vitals (THIS IS NOT IMPLEMENTED YET)
# then also use the summary used from the AI summary endpoint to return
# then check if either checks returned anything, if they did, have the results sent to gemini to make a readable summary of alerts
# """

@app.post("/submit-drug-order")
def submit_drug_order(request: MatchRequest):
    """
    Comprehensive endpoint for submitting a new drug order that:
    1. Checks for drug-drug interactions with active medications
    2. Checks for contraindications based on patient data
    3. Generates a summary of any alerts found
    4. Returns a complete assessment of the order
    """
    logger.info(f"Processing drug order for medication: {request.new_medication} and file: {request.file_path}")
    
    # 1) Locate the file
    file_path = Path("../data/fhir/") / request.file_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    try:
        # 2) Extract all required data
        patient_summary, active_meds, labs_vitals = create_full_summary(file_path)
        
        # Extract drug names for DDI checking
        drug_names = extract_drug_names(active_meds)
        new_med = request.new_medication.strip()        
        new_med = extract_drug_names([new_med])[0]  # Normalize the new medication name
        new_med = normalize_string(new_med)

        
        # 3) Check for drug-drug interactions
        ddi_results = []
        try:
            ddi_request = {
                "file_path": request.file_path,
                "new_medication": new_med
            }
            # Convert dict to MatchRequest object
            match_req = MatchRequest(**ddi_request)
            ddi_result = match_summary_input(match_req)
            ddi_results = ddi_result.get("top_5_ddi_matches", [])
        except Exception as e:
            logger.error(f"Error checking drug-drug interactions: {str(e)}")
            ddi_results = []
        
        # 4) Check for contraindications
        contraindications = []
        try:
            # Generate AI summary for context (needed for contraindication checker)
            full_summary = summarize_patient(patient_summary, labs_vitals, active_meds)
            
            checker_input = {
                "medical_summary": full_summary.get("Medical Summary", ""),
                "abnormal_labs_vitals": full_summary.get("Abnormal Labs/Vitals", ""),
                "clinical_implications": full_summary.get("Clinical Implications", "")
            }
            
            contra_results = checker.check_contraindications(checker_input, new_med)
            contraindications = contra_results if isinstance(contra_results, list) else []
            
            # Filter out "no contraindication data available" messages
            contraindications = [c for c in contraindications if not (
                isinstance(c, dict) and 
                c.get("warning", "").startswith("No contraindication data available")
            )]
            
        except Exception as e:
            logger.error(f"Error checking contraindications: {str(e)}")
            contraindications = []
        
        # 5) Determine if there are any alerts to summarize
        has_alerts = len(ddi_results) > 0 or len(contraindications) > 0
        
        # 6) If alerts exist, generate a summary with Gemini
        alert_summary = ""
        if has_alerts:
            try:
                prompt = (
                    f"You are a medication safety expert. A healthcare provider is attempting to "
                    f"prescribe {new_med} to a patient with the following profile:\n\n"
                    f"Patient Summary: {full_summary.get('Medical Summary', '')}\n\n"
                    f"Active Medications: {', '.join(drug_names)}\n\n"
                    f"Abnormal Labs/Vitals: {full_summary.get('Abnormal Labs/Vitals', '')}\n\n"
                )
                
                if ddi_results:
                    prompt += f"Drug-Drug Interactions Found:\n"
                    for idx, interaction in enumerate(ddi_results, 1):
                        interaction_text = interaction.get('interaction', 'Unknown interaction')
                        score = interaction.get('score', 0.0)
                        prompt += f"{idx}. {interaction_text} (confidence: {score:.2f})\n"
                
                if contraindications:
                    prompt += f"\nContraindications Found:\n"
                    for idx, contra in enumerate(contraindications, 1):
                        if isinstance(contra, dict):
                            if 'text' in contra:
                                prompt += f"{idx}. {contra.get('text', '')} (similarity: {contra.get('similarity', 0.0):.2f})\n"
                            elif 'patient_text' in contra and 'contraindication_text' in contra:
                                prompt += (f"{idx}. Patient condition: {contra.get('patient_text', '')}\n"
                                           f"    Contraindication: {contra.get('contraindication_text', '')}\n"
                                           f"    (similarity: {contra.get('similarity_score', 0.0):.2f})\n")
                
                prompt += (
                    f"\nProvide a concise clinical assessment of these alerts. "
                    f"Summarize key concerns in 2-3 short sentences, and provide one overall recommendation "
                    f"on whether to proceed with this medication, modify the order, or avoid it."
                )
                
                alert_summary = call_gemini(prompt)
            except Exception as e:
                logger.error(f"Error generating alert summary: {str(e)}")
                alert_summary = "Unable to generate AI assessment due to an error. Please review the raw alerts manually."
        
        # 7) Compile and return the complete assessment
        response = {
            "safety_assessment": {
                "drug_interactions": ddi_results,
                "contraindications": [format_contraindication(c) for c in contraindications],
                "has_alerts": has_alerts,
                "ai_assessment": alert_summary
            },
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Drug order submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process drug order: {str(e)}")
    
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",  # Changed from "info" to "debug" for more details
        access_log=True     # Changed from False to True to log all requests
    )
