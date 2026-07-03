"""
Task 1.2: Anomaly Engine
- Trains an IsolationForest on numerical baseline data.
- Exposes predict_anomaly() -> 1 (normal) / -1 (anomaly)
- Computes PSI (Population Stability Index) for drift detection.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import IsolationForest

MODEL_DIR = Path(__file__).resolve().parent.parent / "data"
FEATURES = ["age", "transaction_amount"]


class AnomalyEngine:
    def __init__(self, contamination: float = 0.08, random_state: int = 42):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
        )
        self.is_fitted = False

    def fit(self, baseline_df: pd.DataFrame):
        X = baseline_df[FEATURES].values
        self.model.fit(X)
        self.is_fitted = True
        return self

    def predict(self, record: dict) -> dict:
        """record: {'age': .., 'transaction_amount': ..} -> flag + score"""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() or load() first.")
        X = np.array([[record["age"], record["transaction_amount"]]])
        flag = int(self.model.predict(X)[0])           # 1 normal, -1 anomaly
        score = float(self.model.decision_function(X)[0])  # higher = more normal
        return {"is_anomaly": flag == -1, "anomaly_flag": flag, "anomaly_score": round(score, 4)}

    def save(self, path: Path = None):
        path = path or MODEL_DIR / "isolation_forest.joblib"
        joblib.dump(self.model, path)

    def load(self, path: Path = None):
        path = path or MODEL_DIR / "isolation_forest.joblib"
        self.model = joblib.load(path)
        self.is_fitted = True
        return self


def calculate_psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """
    Population Stability Index between baseline (expected) and
    production (actual) distributions for a single numeric feature.

    Rule of thumb:
      PSI < 0.1  -> no significant drift
      0.1 - 0.25 -> moderate drift, monitor
      > 0.25     -> significant drift, retrain/investigate
    """
    breakpoints = np.linspace(0, 100, buckets + 1)
    bucket_edges = np.percentile(expected, breakpoints)
    bucket_edges[0] = -np.inf
    bucket_edges[-1] = np.inf

    expected_pct = np.histogram(expected, bins=bucket_edges)[0] / len(expected)
    actual_pct = np.histogram(actual, bins=bucket_edges)[0] / len(actual)

    # avoid div-by-zero / log(0)
    expected_pct = np.where(expected_pct == 0, 1e-6, expected_pct)
    actual_pct = np.where(actual_pct == 0, 1e-6, actual_pct)

    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return round(float(psi), 4)


def drift_report(baseline_df: pd.DataFrame, production_df: pd.DataFrame) -> dict:
    report = {}
    for feature in FEATURES:
        report[feature] = calculate_psi(
            baseline_df[feature].values, production_df[feature].values
        )
    return report


if __name__ == "__main__":
    DATA_DIR = Path(__file__).resolve().parent.parent / "data"
    baseline = pd.read_csv(DATA_DIR / "baseline.csv")
    drift_df = pd.read_csv(DATA_DIR / "production_drift.csv")

    engine = AnomalyEngine().fit(baseline)
    engine.save()

    sample_normal = {"age": 34, "transaction_amount": 900}
    sample_anomaly = {"age": 95, "transaction_amount": 50000}

    print("Normal-looking record :", engine.predict(sample_normal))
    print("Anomalous record       :", engine.predict(sample_anomaly))
    print("\nPSI drift report (baseline vs production_drift):")
    for feat, psi in drift_report(baseline, drift_df).items():
        print(f"  {feat:22s} PSI = {psi}")
