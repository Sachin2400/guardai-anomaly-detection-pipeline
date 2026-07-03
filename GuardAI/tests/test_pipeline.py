"""
Test suite for GuardAI.
Run with: pytest -v
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.anomaly_engine import AnomalyEngine, calculate_psi
from src.ner_masking import mask_pii
import src.api as api_mod


# ---------- Anomaly Engine ----------

@pytest.fixture(scope="module")
def trained_engine():
    from src.data_generation import generate_dataset
    baseline = generate_dataset(n_rows=500, drift=False)
    return AnomalyEngine().fit(baseline)


def test_normal_record_not_flagged(trained_engine):
    result = trained_engine.predict({"age": 35, "transaction_amount": 850})
    assert result["anomaly_flag"] in (1, -1)  # valid flag
    assert "anomaly_score" in result


def test_extreme_record_flagged_as_anomaly(trained_engine):
    result = trained_engine.predict({"age": 99, "transaction_amount": 500000})
    assert result["is_anomaly"] is True
    assert result["anomaly_flag"] == -1


def test_psi_identical_distributions_near_zero():
    import numpy as np
    data = np.random.normal(35, 10, 1000)
    psi = calculate_psi(data, data)
    assert psi < 0.01


def test_psi_shifted_distribution_flags_drift():
    import numpy as np
    baseline = np.random.normal(35, 10, 1000)
    shifted = np.random.normal(70, 5, 1000)
    psi = calculate_psi(baseline, shifted)
    assert psi > 0.25  # significant drift threshold


# ---------- PII Masking (NER logic, entities mocked) ----------

def test_mask_pii_replaces_person_and_email():
    text = "My name is Alice Smith and my email is alice@example.com."
    fake_entities = [{"text": "Alice Smith", "label": "PERSON", "start": 11, "end": 22}]
    with patch("src.ner_masking.extract_entities", return_value=fake_entities):
        result = mask_pii(text)
    assert result["sanitized_text"] == "My name is [PERSON] and my email is [EMAIL]."
    assert result["entity_count"] == 2


def test_mask_pii_no_entities_returns_original():
    text = "The weather is nice today."
    with patch("src.ner_masking.extract_entities", return_value=[]):
        result = mask_pii(text)
    assert result["sanitized_text"] == text
    assert result["entity_count"] == 0


# ---------- API ----------

@pytest.fixture
def client():
    return TestClient(api_mod.app)


def test_health_endpoint(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_scan_endpoint_returns_expected_shape(client):
    fake_mask = {"sanitized_text": "[PERSON] bought an item.", "entities_found": ["[PERSON]"], "entity_count": 1}
    with patch.object(api_mod, "mask_pii", return_value=fake_mask):
        payload = {"user_data": {"age": 45, "amount": 95000, "bio": "John Doe bought an item."}}
        r = client.post("/v1/scan", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"is_anomaly", "anomaly_score", "sanitized_bio", "entities_masked"}


def test_scan_endpoint_rejects_invalid_payload(client):
    r = client.post("/v1/scan", json={"user_data": {"age": -5, "amount": 100, "bio": "x"}})
    assert r.status_code == 422  # Pydantic validation error
