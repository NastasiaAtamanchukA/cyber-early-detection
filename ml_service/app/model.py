from __future__ import annotations

import math
import os
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

FEATURE_ORDER = [
    "hour",
    "is_night",
    "message_length",
    "user_missing",
    "event_type_code",
    "host_bucket",
    "user_bucket",
    "contains_error",
    "contains_privilege",
    "contains_network",
    "contains_process",
    "metadata_size",
]

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"


def make_synthetic_training_frame(rows: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "hour": rng.integers(8, 19, size=rows),
            "is_night": np.zeros(rows, dtype=int),
            "message_length": rng.normal(70, 20, size=rows).clip(10, 300).astype(int),
            "user_missing": rng.choice([0, 1], size=rows, p=[0.95, 0.05]),
            "event_type_code": rng.choice([0, 2, 4, 5], size=rows, p=[0.35, 0.25, 0.25, 0.15]),
            "host_bucket": rng.integers(0, 1000, size=rows),
            "user_bucket": rng.integers(0, 1000, size=rows),
            "contains_error": rng.choice([0, 1], size=rows, p=[0.95, 0.05]),
            "contains_privilege": rng.choice([0, 1], size=rows, p=[0.96, 0.04]),
            "contains_network": rng.choice([0, 1], size=rows, p=[0.85, 0.15]),
            "contains_process": rng.choice([0, 1], size=rows, p=[0.92, 0.08]),
            "metadata_size": rng.integers(0, 4, size=rows),
        }
    )


def train_model(csv_path: str | None = None) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if csv_path:
        df = pd.read_csv(csv_path)
        missing = [col for col in FEATURE_ORDER if col not in df.columns]
        if missing:
            raise ValueError(f"CSV is missing feature columns: {missing}")
        df = df[FEATURE_ORDER]
    else:
        df = make_synthetic_training_frame()

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(df[FEATURE_ORDER])
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    model.fit(x_scaled)

    version = datetime.now(UTC).isoformat()
    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_order": FEATURE_ORDER,
        "model_version": version,
        "trained_on_rows": int(len(df)),
    }
    joblib.dump(bundle, MODEL_PATH)
    return bundle


def load_or_bootstrap_model() -> dict:
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return train_model()


def predict(features: list[float]) -> dict:
    bundle = load_or_bootstrap_model()
    if len(features) != len(bundle["feature_order"]):
        raise ValueError(f"Expected {len(bundle['feature_order'])} features, got {len(features)}")

    x = pd.DataFrame([features], columns=bundle["feature_order"])
    x_scaled = bundle["scaler"].transform(x)
    pred = int(bundle["model"].predict(x_scaled)[0])
    decision = float(bundle["model"].decision_function(x_scaled)[0])
    risk = float(1 / (1 + math.exp(6 * decision)))
    risk = round(risk, 6)

    return {
        "anomaly": pred == -1,
        "anomaly_score": risk,
        "risk_score": risk,
        "model_version": bundle["model_version"],
    }
