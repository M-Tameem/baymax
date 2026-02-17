# Baymax — Clinical AI Assistant

A full-stack healthcare AI application that helps clinical staff with medication safety and patient discharge decisions.

**Features:**
- Drug-drug interaction (DDI) detection using SapBERT embeddings + the DDInter database
- Contraindication checking with SciBERT semantic similarity
- AI-generated patient summaries via Google Gemini
- Discharge eligibility assessment
- FHIR R4 patient file upload and parsing
- Firebase authentication (email/password + Google sign-in)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Tailwind CSS, Framer Motion, Firebase Auth |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| ML | PyTorch, Hugging Face Transformers, Scikit-learn |
| LLM | Google Gemini (via `google-generativeai`) |
| Data | FHIR R4 JSON, DDInter CSV, SciBERT embeddings |
| Auth | Firebase Authentication |
| Deploy | Docker / Docker Compose / Render |

---

## Quick Start (Docker — one command)

> **Prerequisites:** Docker and Docker Compose installed.

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/baymax.git
   cd baymax
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cp serverside/.env.example serverside/.env
   # Fill in GOOGLE_API_KEY (required)

   # Frontend — create a root-level .env for Docker Compose
   cp baymax-app/.env.example .env
   # Fill in Firebase values (see Firebase Setup below)
   ```

3. **Launch**
   ```bash
   docker compose up --build
   ```

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API docs: http://localhost:8000/docs

---

## Manual Setup

### Backend

```bash
cd serverside

# Create and activate a virtual environment
python -m venv emr_venv
source emr_venv/bin/activate        # Windows: emr_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in env vars
cp .env.example .env
# Edit .env — at minimum set GOOGLE_API_KEY

# Run the server
python server/server.py
# Server runs on http://localhost:8000
```

### Frontend

```bash
cd baymax-app

# Install dependencies
npm install

# Copy and fill in env vars
cp .env.example src/.env
# Edit src/.env — fill in Firebase values and set:
#   REACT_APP_API_BASE_URL=http://localhost:8000

# Start dev server
npm start
# App runs on http://localhost:3000
```

---

## Environment Variables

### Backend (`serverside/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | **Yes** | Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey)) |
| `GEMINI_MODEL` | No | Gemini model name (default: `models/gemini-1.5-pro-latest`) |
| `API_KEY` | No | Secret key to protect server endpoints |

### Frontend (`baymax-app/src/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `REACT_APP_API_BASE_URL` | **Yes** | URL of the backend (e.g. `http://localhost:8000`) |
| `REACT_APP_FIREBASE_API_KEY` | **Yes** | From Firebase Console |
| `REACT_APP_FIREBASE_AUTH_DOMAIN` | **Yes** | From Firebase Console |
| `REACT_APP_FIREBASE_PROJECT_ID` | **Yes** | From Firebase Console |
| `REACT_APP_FIREBASE_STORAGE_BUCKET` | **Yes** | From Firebase Console |
| `REACT_APP_FIREBASE_MESSAGING_SENDER_ID` | **Yes** | From Firebase Console |
| `REACT_APP_FIREBASE_APP_ID` | **Yes** | From Firebase Console |
| `REACT_APP_FIREBASE_MEASUREMENT_ID` | No | From Firebase Console (Analytics) |

---

## Firebase Setup (Step by Step)

1. **Create a Firebase project**
   - Go to [https://console.firebase.google.com](https://console.firebase.google.com)
   - Click **"Add project"**, give it a name, and follow the prompts.

2. **Enable Authentication**
   - In the left sidebar, click **Build → Authentication**.
   - Click **"Get started"**.
   - Under **Sign-in method**, enable:
     - **Email/Password** (toggle on → Save)
     - **Google** (toggle on → add your support email → Save)

3. **Register a Web App**
   - Click the gear icon next to "Project Overview" → **Project settings**.
   - Scroll to **"Your apps"** → click the web icon (`</>`).
   - Give the app a nickname (e.g. `baymax-web`) and click **"Register app"**.

4. **Copy your config**
   - After registering, Firebase shows a config object like:
     ```js
     const firebaseConfig = {
       apiKey: "AIza...",
       authDomain: "your-project.firebaseapp.com",
       projectId: "your-project",
       storageBucket: "your-project.firebasestorage.app",
       messagingSenderId: "1234567890",
       appId: "1:1234...:web:abc...",
       measurementId: "G-XXXXXXX"
     };
     ```
   - Copy each value into your `baymax-app/src/.env` file as the corresponding `REACT_APP_FIREBASE_*` variable.

5. **Add Authorized Domains** (for Google sign-in)
   - In **Authentication → Settings → Authorized domains**
   - Add `localhost` (already there by default) and your production domain when you deploy.

6. **Firestore / Storage** (optional)
   - Baymax only uses Firebase Authentication — you do not need Firestore or Storage.

---

## Deployment on Render

This repo includes a `render.yaml` blueprint for one-click deployment.

1. Fork this repo on GitHub.
2. Go to [https://dashboard.render.com/blueprints](https://dashboard.render.com/blueprints) → **New Blueprint Instance**.
3. Connect your forked repo.
4. Render will detect `render.yaml` and create two services:
   - `baymax-backend` — Python web service (FastAPI)
   - `baymax-frontend` — Static site (React build)
5. Fill in the required environment variable values in the Render dashboard:
   - `GOOGLE_API_KEY` — your Gemini key
   - All `REACT_APP_FIREBASE_*` variables
   - `REACT_APP_API_BASE_URL` — set this to the URL of your deployed `baymax-backend`

> **Note:** The backend loads large ML models at startup; it may take 2-3 minutes to become healthy on the first deploy.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/list-all-patients` | List all available FHIR patient files |
| `POST` | `/upload-fhir` | Upload a FHIR R4 `.json` file |
| `POST` | `/summary` | Parse a FHIR file and return structured summary |
| `POST` | `/ai-summary` | Generate an AI-written clinical summary (Gemini) |
| `POST` | `/match` | Check drug-drug interactions for a new medication |
| `POST` | `/contraindication-checker` | Check contraindications for a new medication |
| `POST` | `/submit-drug-order` | Full safety check: DDI + contraindications + AI assessment |
| `POST` | `/discharge` | Assess whether the patient is safe to discharge |
| `POST` | `/extract-active-medications` | Extract active medications from a FHIR file |
| `POST` | `/extract-labs-vitals` | Extract lab results and vitals from a FHIR file |

Interactive API docs are available at `http://localhost:8000/docs` when running locally.

---

## Project Structure

```
baymax/
├── baymax-app/          # React frontend
│   ├── src/
│   │   ├── DashboardPage.js
│   │   ├── LoginPage.js
│   │   ├── firebase/    # Firebase init + auth helpers
│   │   └── contexts/    # Auth context
│   ├── .env.example
│   ├── Dockerfile
│   └── nginx.conf
│
├── serverside/          # Python FastAPI backend
│   ├── server/
│   │   ├── server.py    # Main FastAPI app + all endpoints
│   │   ├── models.py    # Pydantic request/response models
│   │   ├── embedding.py # SapBERT embedding helpers
│   │   └── data_processing.py
│   ├── scripts/
│   │   ├── fhir_summary.py
│   │   ├── gemini_client.py
│   │   ├── contraindication_checker.py
│   │   └── safety_gate.py
│   ├── data/
│   │   └── fhir/        # FHIR R4 patient JSON files
│   ├── .env.example
│   └── Dockerfile
│
├── docker-compose.yml   # One-command local stack
├── render.yaml          # One-click Render deployment
└── README.md
```

---

## License

MIT
