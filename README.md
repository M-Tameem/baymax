# Baymax — Clinical AI Assistant

A full-stack healthcare AI app that helps clinical staff make safer, faster decisions around medication orders and patient discharge. Upload a FHIR R4 patient record and Baymax runs a multi-model ML pipeline to surface drug interactions, contraindications, and discharge readiness — all in one dashboard.

---

## What it does

| Feature | How |
|---------|-----|
| Patient dashboard | Parses a FHIR R4 JSON bundle into structured conditions, medications, labs, vitals, and allergies |
| AI clinical narrative | Feeds the parsed summary to Google Gemini to generate a concise plain-English clinical note |
| Drug-drug interaction check | Embeds the new drug name with SapBERT and runs cosine similarity against a pre-vectorised DDInter dataset |
| Contraindication check | Embeds each sentence of the patient's clinical text with SciBERT and compares against pre-computed drug contraindication vectors |
| Dosage safety gate | Asks a local LLM (Ollama) for a binary SAFE / UNSAFE verdict on the ordered dose before submission |
| Discharge assessment | Sends current patient state to Gemini for a discharge recommendation with clinical reasoning |

All three safety checks (DDI + contraindication + dosage) run in parallel on drug order submission.

---

## Running locally

Requires Docker and Docker Compose.

```bash
git clone https://github.com/baymaxey/baymax.git
cd baymax

# create .env files populated with the information from .env.example in serverside/ and baymax-app/
# run download_models.sh in serverside/data/pkl

docker compose up --build
```

- App: http://localhost:3000
- API + interactive docs: http://localhost:8000/docs

---
## The ML in detail

### Data sources
- **DDInter** — a published drug-drug interaction database (~40k pairs, severity-labelled). Drug pairs are filtered to remove "unknown" severity entries, normalised for spelling variants (British/US), and combined into natural-language phrases (e.g. `"aspirin and warfarin interaction (major)"`) before embedding.
- **Drug contraindication data** — sourced and pre-processed into sentence-level contraindication statements per drug, covering 1,179 drugs. Stored as a serialised dict mapping drug name → list of (sentence, vector) pairs.

### Embedding models
Both models are loaded at server startup and run on CPU (GPU if available):

- **SapBERT** (`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`) — biomedical entity embedding model fine-tuned on PubMed. Used for DDI search: the query drug's name is embedded and compared against every pre-vectorised DDInter combo to retrieve the top-k most similar interactions.
- **SciBERT** (`allenai/scibert_scivocab_uncased`) — scientific language model from AllenAI. Used for contraindication matching: each sentence in the patient summary is embedded and scored against every contraindication sentence for the target drug; matches above a cosine similarity threshold (0.729, tuned empirically) are flagged.

### Embedding caches
All DDInter combo embeddings and contraindication embeddings are pre-computed offline and stored as `.pkl` files. At runtime, the server loads these caches into memory — no re-embedding of the database on each request, only the query drug/patient text is embedded live.

### Custom FHIR parser
The FHIR parser (`fhir_summary.py`) is hand-written against the FHIR R4 bundle format. It walks the `entry` array, filters to clinically relevant resource types (`Condition`, `MedicationRequest`, `MedicationStatement`, `Observation`, `AllergyIntolerance`, `Patient`), deduplicates conditions by most-recent onset, resolves medication status conflicts (active > completed > stopped), and keeps only the most recent value per lab/vital. Social and non-clinical observations (employment, education, etc.) are excluded by keyword.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Tailwind CSS, Framer Motion, Firebase Auth |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| Biomedical NLP | SapBERT + SciBERT via PyTorch + Hugging Face Transformers |
| LLM (cloud) | Google Gemini (`google-generativeai`) |
| LLM (local) | Ollama — Phi / Mistral for dosage safety gate |
| Data | DDInter CSV, FHIR R4 JSON, pre-computed `.pkl` embedding caches |
| Infrastructure | Docker, Docker Compose, Nginx |

---

## Project structure

```
baymax/
├── baymax-app/                    # React frontend
│   ├── src/
│   │   ├── DashboardPage.js       # Patient view, drug orders, discharge UI
│   │   └── contexts/              # Firebase auth context
│   └── nginx.conf
│
└── serverside/                    # Python FastAPI backend
    ├── server/
    │   ├── server.py              # All API endpoints
    │   ├── embedding.py           # SapBERT embed + cosine similarity
    │   ├── data_processing.py     # DDInter CSV loader + embedding cache
    │   └── models.py              # Pydantic request/response models
    ├── scripts/
    │   ├── fhir_summary.py        # Custom FHIR R4 bundle parser
    │   ├── contraindication_checker.py   # SciBERT similarity pipeline
    │   ├── safety_gate.py         # Ollama dosage safety check
    │   └── gemini_client.py       # Gemini API wrapper
    └── data/
        ├── ddinter/               # DDInter interaction CSV
        ├── fhir/                  # Uploaded patient files
        └── pkl/                   # Pre-computed embedding caches
```

---

## License

MIT
