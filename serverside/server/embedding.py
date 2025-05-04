import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import logging

# Get logger
logger = logging.getLogger(__name__)

# Model and tokenizer
MODEL_NAME = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"

# Initialize device, tokenizer and model
def initialize_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    model = AutoModel.from_pretrained(MODEL_NAME).to(device).half()
    model.eval()
    
    return device, tokenizer, model

device, tokenizer, model = initialize_model()

# Embedding function
def embed(text: str) -> np.ndarray:
    with torch.no_grad():
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding="longest",
            max_length=512
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.cuda.amp.autocast(enabled=(device.type == 'cuda')):
            outputs = model(**inputs)
        emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()
    return emb.squeeze()

# Cosine similarity
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
