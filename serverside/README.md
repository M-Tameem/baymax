# Baymax — Backend

FastAPI backend for the Baymax clinical AI assistant.
See the [root README](../README.md) for full setup and deployment instructions.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in GOOGLE_API_KEY
python server/server.py
```

Server runs on `http://localhost:8000` — interactive docs at `/docs`.

## Data files

Large binary files (`.pkl`, DDInter CSV) are **not** committed to the repo.
Place them at:

```
data/
  ddinter/ddinter_combined.csv
  pkl/ddinter_embeddings_final.pkl
  pkl/contraindication_embeddings_final.pkl
  fhir/              ← FHIR R4 patient JSON files go here
```
