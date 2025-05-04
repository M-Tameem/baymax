import json
import torch
import pickle
import re
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- Configuration ----------------
SCIBERT_MODEL_NAME = "allenai/scibert_scivocab_uncased"
DEFAULT_THRESHOLD = 0.729  # Using the threshold from the class-based version

# ---------------- Setup ----------------
tokenizer = None
scibert_model = None
device = None
contra_embeddings = None

def init_model():
    """Initialize the SciBERT model."""
    global tokenizer, scibert_model, device
    
    tokenizer = AutoTokenizer.from_pretrained(SCIBERT_MODEL_NAME)
    scibert_model = AutoModel.from_pretrained(SCIBERT_MODEL_NAME).eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    scibert_model.to(device)
    print(f"Device set to use {device}")

def load_embeddings(path):
    """Load pre-computed drug contraindication embeddings."""
    global contra_embeddings
    
    with open(path, "rb") as f:
        contra_embeddings = pickle.load(f)
    print(f"Loaded contraindication embeddings for {len(contra_embeddings)} drugs")
    return contra_embeddings

def embed(text):
    """Create an embedding vector for the given text using SciBERT."""
    if tokenizer is None or scibert_model is None:
        init_model()
        
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(device)
    with torch.no_grad():
        output = scibert_model(**inputs)
    return output.last_hidden_state[:, 0, :].squeeze().cpu().numpy()

def split_sentences(text):
    """Split text into sentences for individual analysis using regex pattern."""
    return [s.strip() for s in re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text) if s.strip()]

def check_contraindications(patient_summary, drug, threshold=None):
    """
    Check contraindications between a patient summary and a specific drug.
    
    Args:
        patient_summary: Dictionary with keys like 'medical_summary'/'Medical Summary', etc.
        drug: Name of the drug to check
        threshold: Optional similarity threshold (defaults to DEFAULT_THRESHOLD)
        
    Returns:
        List of top 5 contraindication matches with similarity scores
    """
    if contra_embeddings is None:
        raise ValueError("Drug contraindication embeddings not loaded. Call load_embeddings first.")
        
    # Use provided threshold or default
    threshold = threshold or DEFAULT_THRESHOLD
    
    # Normalize keys to handle different case formats
    normalized_summary = {}
    for key in patient_summary:
        if key.lower() == "medical summary":
            normalized_summary["medical_summary"] = patient_summary[key]
        elif key.lower() == "abnormal labs/vitals":
            normalized_summary["abnormal_labs_vitals"] = patient_summary[key]
        elif key.lower() == "clinical implications":
            normalized_summary["clinical_implications"] = patient_summary[key]
        else:
            normalized_summary[key.lower().replace(" ", "_")] = patient_summary[key]
    
    # Get all text from the patient summary
    all_sentences = []
    for key in ["medical_summary", "abnormal_labs_vitals", "clinical_implications"]:
        if key in normalized_summary and normalized_summary[key]:
            all_sentences.extend(split_sentences(normalized_summary[key]))
    
    # Normalize drug name (lowercase)
    drug_name = drug.strip()
    
    # Check if we have contraindications for this drug
    if drug_name not in contra_embeddings:
        print(f"No contraindications found for drug: {drug_name}")
        return [{"warning": f"No contraindication data available for {drug_name}"}]
    
    # Embed each sentence
    sentence_vectors = [(s, embed(s)) for s in all_sentences]
    
    # Compare patient sentences with drug contraindications
    scores = []
    for patient_sent, patient_vec in sentence_vectors:
        for contra_sent, contra_vec in contra_embeddings[drug_name]:
            sim = cosine_similarity([patient_vec], [contra_vec])[0][0]
            if sim >= threshold:
                scores.append({
                    "patient_text": patient_sent,
                    "contraindication_text": contra_sent,
                    "similarity_score": float(sim)
                })
    
    # Sort by similarity score and return top 5
    top_matches = sorted(scores, key=lambda x: x["similarity_score"], reverse=True)[:5]
    
    # For console output similar to original script
    print(f"\nPatient vs. '{drug_name}' contraindications:")
    for match in top_matches:
        print(f"- [{match['similarity_score']:.3f}] Patient: \"{match['patient_text']}\"\n           ↳ Drug:    \"{match['contraindication_text']}\"\n")
    
    return top_matches

# For compatibility with the server.py code that currently uses both implementations
class ContraindicationChecker:
    def __init__(self, contraindications_path):
        load_embeddings(contraindications_path)
        init_model()
        
    def check_contraindications(self, patient_summary, drug_name):
        return check_contraindications(patient_summary, drug_name)

# ---------------- Entry Point ----------------
if __name__ == "__main__":
    exit