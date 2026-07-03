<div align="center">

# 🛡️ GuardAI
### Enterprise AI Guardrail & Anomaly Detection Pipeline

**Catches bad data before it breaks your models. Redacts PII before it leaks into your logs.**

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-Isolation%20Forest-F7931E?logo=scikitlearn&logoColor=white)
![spaCy](https://img.shields.io/badge/spaCy-NER-09A3D5?logo=spacy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-9%20passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

[Overview](#-overview) • [Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API](#-api-usage) • [Tests](#-testing) • [Skills](#-skills-demonstrated)

</div>

---

## 📌 Overview

Enterprises ingest constant streams of user-generated data — transactions, support tickets, form submissions. Two things silently go wrong with that data if nobody's watching:

- 📉 **Statistical drift** — incoming data quietly shifts away from what a downstream ML model was trained on, degrading predictions until someone notices too late.
- 🔓 **PII leakage** — free-text fields (bios, comments, notes) routinely contain names, emails, and phone numbers that should never reach raw logs, analytics warehouses, or third-party tools.

**GuardAI** is a guardrail service that sits at the point of ingestion and solves both problems in a single API call: every record is scored for anomaly risk *and* sanitized for PII before it moves downstream.

## ✨ Key Features

| | |
|---|---|
| 🎯 **Unsupervised anomaly detection** | Isolation Forest — no labeled fraud/anomaly data required |
| 📊 **Statistical drift monitoring** | Population Stability Index (PSI) — the same metric real MLOps teams use to trigger retraining |
| 🕵️ **Context-aware PII masking** | spaCy NER understands *"Alice Smith is a person"* from sentence context, not a hardcoded list |
| 🛟 **Regex safety net** | Catches emails & phone numbers NER models often miss |
| ✅ **Schema validation** | Pydantic rejects malformed requests before they touch any model |
| 🐳 **Fully containerized** | Docker image trains the model at build time — ready to serve immediately |
| 🧪 **Unit-tested** | 9 passing pytest tests, with mocked external dependencies |

## 🏗️ Architecture

```
                     ┌─────────────────────────┐
   Incoming JSON  →  │   FastAPI  /v1/scan      │
   (age, amount,     │   (Pydantic validation)  │
    bio text)        └─────────────┬────────────┘
                                    │
                 ┌──────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌─────────────────────────┐            ┌───────────────────────────┐
    │  🎯 Anomaly Engine        │            │  🕵️ AI Masking Unit        │
    │  IsolationForest          │            │  spaCy NER (PERSON/ORG/   │
    │  trained on baseline.csv  │            │  GPE) + regex (email/phone)│
    │  + PSI drift metric       │            │  → generic tags            │
    └─────────────┬─────────────┘            └──────────────┬─────────────┘
                 anomaly_score,                          sanitized_bio
                 is_anomaly                         (raw PII never logged)
                 └────────────────────┬──────────────────────┘
                                       ▼
                          ✅ Sanitized JSON response
```

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10 |
| Classical ML | scikit-learn (Isolation Forest), NumPy, Pandas |
| NLP / AI | spaCy (Named Entity Recognition) |
| Backend API | FastAPI, Pydantic, Uvicorn |
| Testing | Pytest (with mocking) |
| Deployment | Docker |

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/Sachin2400/guardai-anomaly-detection-pipeline.git
cd guardai-anomaly-detection-pipeline

# 2. Create environment & install dependencies
conda create -n guardai python=3.10 -y
conda activate guardai
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Generate data + train the anomaly model
python src/data_generation.py
python src/anomaly_engine.py

# 4. Run tests
pytest -v

# 5. Launch the API
uvicorn src.api:app --reload --port 8000
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger UI.

### 🐳 Or run it with Docker

```bash
docker build -t guardai:latest .
docker run -p 8000:8000 guardai:latest
```

## 📡 API Usage

**`POST /v1/scan`**

<table>
<tr><th>Request</th><th>Response</th></tr>
<tr valign="top">
<td>

```json
{
  "user_data": {
    "age": 45,
    "amount": 95000,
    "bio": "My name is Alice Smith and my email is alice@example.com."
  }
}
```

</td>
<td>

```json
{
  "is_anomaly": true,
  "anomaly_score": -0.1945,
  "sanitized_bio": "My name is [PERSON] and my email is [EMAIL].",
  "entities_masked": 2
}
```

</td>
</tr>
</table>

**`GET /v1/health`**
```json
{"status": "ok", "model_loaded": true}
```

## 🧪 Testing

```bash
pytest -v
```

| Test Area | Coverage |
|---|---|
| Anomaly Engine | Normal vs. extreme record classification |
| PSI Drift Metric | Identical & shifted distribution scenarios |
| PII Masking | Entity + regex merge logic (mocked NER) |
| API | `/v1/health`, `/v1/scan` happy path & validation errors |

**Result: 9/9 tests passing ✅**

## 📁 Project Structure

```
GuardAI/
├── src/
│   ├── data_generation.py   # Synthetic baseline + drift datasets
│   ├── anomaly_engine.py    # Isolation Forest + PSI
│   ├── ner_masking.py       # spaCy NER + PII masking
│   └── api.py                # FastAPI app
├── tests/
│   └── test_pipeline.py      # 9 passing pytest tests
├── data/                      # generated CSVs + trained model (gitignored)
├── requirements.txt
├── Dockerfile
└── README.md
```

## 💡 Skills Demonstrated

| Area | Evidence |
|---|---|
| Machine Learning | Trained & tuned Isolation Forest; implemented PSI from first principles |
| Applied NLP | Entity-recognition pipeline with span-merging for overlapping matches |
| Backend Engineering | Validated REST API with clean request/response contracts |
| MLOps | Drift monitoring — the metric that triggers real retraining pipelines |
| Testing | Pytest suite mocking external dependencies |
| DevOps | Dockerfile that trains the model at build time — a deployment-ready image |
| Privacy Engineering | Raw PII never logged, by architecture — not just by policy |

## 🛣️ Roadmap

- [ ] Swap batch Isolation Forest for a streaming/online anomaly detector
- [ ] Add Prometheus metrics for live anomaly-rate dashboards
- [ ] Swap spaCy for a transformer-based NER model for higher recall on messy text
- [ ] Add a compliance-friendly audit log (entity type + count only, never raw PII)

## 📄 License

MIT — free to use, modify, and learn from.

---

<div align="center">
Built as an end-to-end demonstration of applied ML, NLP, and backend engineering.
</div>
