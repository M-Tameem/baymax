# Baymax — Clinical AI Assistant

Baymax is a full-stack clinical decision support system that combines biomedical embedding models (SapBERT, SciBERT) and LLM reasoning (Gemini, Ollama) to detect drug interactions, contraindications, and unsafe dosages from FHIR R4 patient records in real time.

It demonstrates how biomedical NLP pipelines and LLM-based reasoning can be integrated into a deployable, containerized system for safe and efficient clinical decision support.

---

## Key Engineering Highlights

- Pre-computed biomedical embedding index (~100k vectors) enabling millisecond-latency similarity search  
- Parallel safety pipeline combining embedding-based retrieval and LLM reasoning  
- Fully containerized full-stack deployment (React + FastAPI + Nginx + Docker)  
- Custom FHIR R4 parser for structured clinical data normalization  
- Separation of offline embedding computation and runtime inference for scalability  
- Persistent embedding cache eliminating expensive recomputation at runtime  

---

## System Architecture

```
FHIR Upload → FastAPI backend
            → SapBERT similarity search (DDI detection)
            → SciBERT contraindication similarity search
            → Ollama dosage safety gate (local LLM)
            → Gemini clinical reasoning and discharge assessment
            → React dashboard visualization
```
---

## What it does

| Feature | How |
|--------|-----|
| Patient dashboard | Parses a FHIR R4 JSON bundle into structured conditions, medications, labs, vitals, and allergies |
| AI clinical narrative | Uses Google Gemini to generate a concise clinical summary |
| Drug-drug interaction check | Embeds drug name using SapBERT and performs cosine similarity search against pre-computed DDInter vectors |
| Contraindication check | Uses SciBERT to embed patient clinical text and compare against contraindication embedding index |
| Dosage safety gate | Uses local LLM (Ollama) to evaluate dosage safety |
| Discharge assessment | Uses Gemini to evaluate discharge readiness |

---

## Running locally

Requires Docker and Docker Compose.

```bash
git clone https://github.com/M-Tameem/baymax.git
cd baymax

# create environment files, make sure to modify them with the requisite information
cp serverside/.env.example serverside/.env
cp baymax-app/.env.example baymax-app/.env

# download embedding caches
./serverside/data/pkl/download_models.sh

# start system
docker compose up --build
```

Access:

- Frontend: http://localhost:3000  
- Backend API: http://localhost:8000/docs  

---

## Machine Learning Pipeline

### Data sources

- **DDInter**  
  ~40k drug interaction pairs with severity labels  
  Normalized and converted into natural-language phrases prior to embedding  

- **FDA Contraindication dataset**  
  1,179 drugs with sentence-level contraindication descriptions  
  Stored as serialized embedding vectors  

---

### Embedding models

**SapBERT**  
`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`  
- Biomedical entity embedding model  
- Used for drug-drug interaction similarity search  

**SciBERT**  
`allenai/scibert_scivocab_uncased`  
- Scientific language embedding model  
- Used for contraindication similarity matching  

---

### Embedding cache architecture

All embeddings are computed offline and stored as `.pkl` files.
Only the query drug and patient text are embedded at runtime.

---

### Custom FHIR parser

The FHIR parser (`fhir_summary.py`) extracts structured patient state from FHIR R4 bundles - which is Ontario's current Patient Data Standard.

Handles:

- Condition deduplication
- Medication status resolution
- Lab and vital normalization
- Removal of irrelevant social data

---

## Tech stack

| Layer | Technology |
|------|------------|
| Frontend | React 19, Tailwind CSS, Framer Motion, Firebase Auth |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| Biomedical NLP | SapBERT, SciBERT, PyTorch, Hugging Face Transformers |
| LLM (cloud) | Google Gemini |
| LLM (local) | Ollama (Phi, Mistral) |
| Data | DDInter CSV, FHIR R4 JSON, pre-computed embedding caches |
| Infrastructure | Docker, Docker Compose, Nginx |

---

## Project structure

```
baymax/
├── baymax-app/
│   ├── src/
│   └── nginx.conf
│
└── serverside/
    ├── server/
    ├── scripts/
    └── data/
        ├── ddinter/
        ├── fhir/
        └── pkl/
```

---

## License

MIT
