# GuardAI — Enterprise AI Guardrail & Anomaly Detection Pipeline

A production-style ML service that scans incoming data streams for **statistical anomalies**
(via Isolation Forest + PSI drift monitoring) and automatically **masks sensitive PII**
in free-text fields (via NER), exposed through a FastAPI backend and shipped in Docker.

## 1. Problem Statement

Enterprises ingest streams of user-generated data (transactions, support tickets, form
submissions) that (a) can silently drift out of the distribution a downstream ML model was
trained on, causing degraded predictions, and (b) frequently contain PII (names, emails,
phone numbers) embedded in free text that must never reach logs or analytics warehouses in
raw form. GuardAI sits as a guardrail layer in front of downstream systems: every record is
scored for anomaly risk and sanitized for PII before it moves further into the pipeline.

## 2. Architecture

```
                     ┌─────────────────────────┐
   Incoming JSON  →  │   FastAPI  /v1/scan      │
   (age, amount,     │   (Pydantic validation)  │
    bio text)        └─────────────┬────────────┘
                                    │
                 ┌──────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌─────────────────────────┐            ┌───────────────────────────┐
    │  Anomaly Engine          │            │  AI Masking Unit          │
    │  IsolationForest         │            │  spaCy NER (PERSON/ORG/   │
    │  trained on baseline.csv │            │  GPE) + regex (email/phone)│
    │  + PSI drift metric      │            │  → generic tags           │
    └─────────────┬────────────┘            └──────────────┬────────────┘
                 anomaly_score,                         sanitized_bio
                 is_anomaly                        (raw PII never logged)
                 └────────────────────┬──────────────────────┘
                                       ▼
                          Sanitized JSON response
```

## 3. Project Structure

```
GuardAI/
├── src/
│   ├── data_generation.py   # Task 1.1 — synthetic baseline + drift datasets
│   ├── anomaly_engine.py    # Task 1.2 — Isolation Forest + PSI
│   ├── ner_masking.py       # Task 2.1/2.2 — spaCy NER + PII masking
│   └── api.py                # Task 3.1 — FastAPI app
├── tests/
│   └── test_pipeline.py      # pytest suite (9 tests, all green)
├── data/                      # generated CSVs + trained model (gitignored)
├── requirements.txt
├── Dockerfile                 # Task 3.2
└── README.md
```

## 4. Setup Instructions (Anaconda)

You mentioned you're using **Anaconda Navigator**. Navigator's GUI is fine for
environment creation, but installing this exact dependency set is easiest through
**Anaconda Prompt** (Navigator → Environments → your env → "Open Terminal", or just
open "Anaconda Prompt" from the Start Menu).

```bash
# 1. Create and activate an environment (Python 3.10 recommended)
conda create -n guardai python=3.10 -y
conda activate guardai

# 2. Install dependencies
cd path\to\GuardAI
pip install -r requirements.txt

# 3. Download the spaCy NER model (one-time)
python -m spacy download en_core_web_sm

# 4. Generate datasets + train the anomaly model
python src/data_generation.py
python src/anomaly_engine.py

# 5. Run the test suite
pytest -v

# 6. Start the API
uvicorn src.api:app --reload --port 8000
```

If you'd rather do all of this from Navigator's GUI: create the `guardai` env in the
**Environments** tab, install `pip` if not already present, then use the **Home** tab
to launch a **Jupyter Notebook** or **VS Code** pointed at that environment — but the
terminal commands above are more reliable for this project.

Open **http://127.0.0.1:8000/docs** for interactive Swagger UI once the server is running.

## 5. Docker

```bash
docker build -t guardai:latest .
docker run -p 8000:8000 guardai:latest
```

## 6. Example API Request & Response

**POST** `/v1/scan`

Request:
```json
{
  "user_data": {
    "age": 45,
    "amount": 95000,
    "bio": "My name is Alice Smith and my email is alice@example.com."
  }
}
```

Response:
```json
{
  "is_anomaly": true,
  "anomaly_score": -0.1945,
  "sanitized_bio": "My name is [PERSON] and my email is [EMAIL].",
  "entities_masked": 2
}
```

**GET** `/v1/health`
```json
{"status": "ok", "model_loaded": true}
```

## 7. What Each Phase Demonstrates (for interview talking points)

| Phase | Skill demonstrated |
|---|---|
| Data generation + Isolation Forest + PSI | Classical ML, unsupervised anomaly detection, statistical drift monitoring (MLOps) |
| spaCy NER + regex masking | Applied NLP, privacy-by-design engineering |
| FastAPI + Pydantic | Backend API design, input validation, production service patterns |
| Docker | Containerization, reproducible deployment |
| pytest suite | Testing discipline, mocking external dependencies (NER model) in unit tests |

## 8. Possible Extensions (mention these in interviews to show depth)
- Swap Isolation Forest for a `River`-based online/streaming detector for true real-time drift.
- Add Prometheus metrics (`/metrics`) for anomaly-rate monitoring in production.
- Swap spaCy for `dslim/bert-base-NER` via HuggingFace when higher recall is needed on
  messier text, at the cost of latency (worth A/B testing).
- Add an audit log table (entity type + count only, never raw PII) for compliance reporting.
