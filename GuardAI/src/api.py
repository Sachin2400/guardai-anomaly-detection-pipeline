"""
Task 3.1: FastAPI Backend
Exposes:
  POST /v1/scan   -> runs anomaly detection + PII masking on incoming data
  GET  /v1/health -> liveness probe

Run locally:
    uvicorn src.api:app --reload --port 8000
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
import pandas as pd

from src.anomaly_engine import AnomalyEngine
from src.ner_masking import mask_pii

app = FastAPI(
    title="GuardAI",
    description="Enterprise AI Guardrail & Anomaly Detection Pipeline",
    version="1.0.0",
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MODEL_PATH = DATA_DIR / "isolation_forest.joblib"

_engine: AnomalyEngine | None = None


def get_engine() -> AnomalyEngine:
    """Lazy-load the trained model once, on first request."""
    global _engine
    if _engine is None:
        if not MODEL_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail="Model not trained yet. Run `python src/anomaly_engine.py` first.",
            )
        _engine = AnomalyEngine().load(MODEL_PATH)
    return _engine


# ---------- Pydantic Schemas ----------

class UserData(BaseModel):
    age: float = Field(..., ge=0, le=130, description="User age")
    amount: float = Field(..., ge=0, description="Transaction amount")
    bio: str = Field(..., min_length=1, max_length=2000, description="Free-text user bio")


class ScanRequest(BaseModel):
    user_data: UserData


class ScanResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    sanitized_bio: str
    entities_masked: int


# ---------- Endpoints ----------

@app.get("/v1/health")
def health():
    return {"status": "ok", "model_loaded": MODEL_PATH.exists()}


@app.post("/v1/scan", response_model=ScanResponse)
def scan(payload: ScanRequest):
    engine = get_engine()
    data = payload.user_data

    anomaly_result = engine.predict({"age": data.age, "transaction_amount": data.amount})
    mask_result = mask_pii(data.bio)  # original bio never logged/persisted

    return ScanResponse(
        is_anomaly=anomaly_result["is_anomaly"],
        anomaly_score=anomaly_result["anomaly_score"],
        sanitized_bio=mask_result["sanitized_text"],
        entities_masked=mask_result["entity_count"],
    )
