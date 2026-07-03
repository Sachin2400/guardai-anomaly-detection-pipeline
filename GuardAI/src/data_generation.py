"""
Task 1.1: Dataset Generation
Generates a baseline (normal) dataset and a production_drift dataset
containing statistical anomalies, with realistic PII embedded in a
free-text `bio` column so Phase 2 (NER masking) has something to detect.
"""

import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path

np.random.seed(42)
fake = Faker()
Faker.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _make_bio(name: str, email: str, city: str) -> str:
    templates = [
        f"My name is {name} and my email is {email}. I live in {city}.",
        f"Hi, I'm {name}, based in {city}. Reach me at {email}.",
        f"{name} here, contact: {email}. Currently residing in {city}.",
    ]
    return np.random.choice(templates)


def generate_dataset(n_rows: int, drift: bool = False) -> pd.DataFrame:
    """
    drift=False -> baseline/normal distribution
    drift=True  -> injects statistical anomalies (age, amount, location skew)
    """
    ages = np.random.normal(loc=35, scale=10, size=n_rows).clip(18, 75)
    amounts = np.random.lognormal(mean=6.5, sigma=0.6, size=n_rows)  # ~ INR 500-3000 typical
    cities = np.random.choice(
        ["Patna", "Delhi", "Mumbai", "Bengaluru", "Kolkata", "Gaya", "Ranchi"],
        size=n_rows,
        p=[0.30, 0.20, 0.15, 0.15, 0.10, 0.05, 0.05],
    )

    if drift:
        # Inject anomalies: fatter tails on age & amount, a skewed location shift
        n_anom = max(1, int(0.08 * n_rows))
        anom_idx = np.random.choice(n_rows, n_anom, replace=False)
        ages[anom_idx] = np.random.choice([16, 17, 90, 95, 99], size=n_anom)
        amounts[anom_idx] = amounts[anom_idx] * np.random.uniform(15, 40, size=n_anom)
        cities = np.random.choice(
            ["Patna", "Delhi", "Mumbai", "Bengaluru", "Kolkata", "Gaya", "Ranchi", "Unknown"],
            size=n_rows,
            p=[0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.65],
        )

    rows = []
    for i in range(n_rows):
        name = fake.name()
        email = fake.email()
        rows.append(
            {
                "user_id": f"U{i:05d}",
                "age": round(float(ages[i]), 1),
                "transaction_amount": round(float(amounts[i]), 2),
                "location": cities[i],
                "bio": _make_bio(name, email, cities[i]),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    baseline = generate_dataset(n_rows=2000, drift=False)
    production_drift = generate_dataset(n_rows=500, drift=True)

    baseline.to_csv(DATA_DIR / "baseline.csv", index=False)
    production_drift.to_csv(DATA_DIR / "production_drift.csv", index=False)

    print(f"baseline.csv          -> {baseline.shape}")
    print(f"production_drift.csv  -> {production_drift.shape}")
    print("\nSample bio field:\n", baseline["bio"].iloc[0])
