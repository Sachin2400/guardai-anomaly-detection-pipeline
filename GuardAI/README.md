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
│   ├── data_generation.py   
│   ├── anomaly_engine.py    
│   ├── ner_masking.py       
│   └── api.py                
├── tests/
│   └── test_pipeline.py      
├── data/                      
├── requirements.txt
├── Dockerfile                
└── README.md
```




