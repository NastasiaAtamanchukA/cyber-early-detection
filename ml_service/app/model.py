from __future__ import annotations

import math
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_DIR = Path("/data/models")
MODEL_PATH = MODEL_DIR / "isolation_forest.joblib"

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


def _synthetic_training_frame() -> pd.DataFrame:
    rows: list[list[float]] = []
    for hour in range(24):
        for event_type_code in [10, 11, 20, 40, 50]:
            rows.append([
                hour,
                int(hour < 7 or hour > 22),
                60 + event_type_code,
                0,
                event_type_code,
                (hour * 17) % 500,
                (event_type_code * 13) % 500,
                int(event_type_code == 10),
                0,
                1,
                int(event_type_code == 20),
                2,
            ])
    return pd.DataFrame(rows, columns=FEATURE_ORDER)


def train_model(training_data: list[list[float]] | None = None) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    x = pd.DataFrame(training_data, columns=FEATURE_ORDER) if training_data else _synthetic_training_frame()
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    model.fit(x_scaled)
    bundle = {
        "feature_order": FEATURE_ORDER,
        "scaler": scaler,
        "model": model,
        "model_version": "iforest-demo-v0.2.0",
    }
    joblib.dump(bundle, MODEL_PATH)
    return bundle


def load_or_bootstrap_model() -> dict:
    if not MODEL_PATH.exists():
        return train_model()
    return joblib.load(MODEL_PATH)


def predict(features: list[float]) -> dict:
    bundle = load_or_bootstrap_model()
    if len(features) != len(bundle["feature_order"]):
        raise ValueError(f"Expected {len(bundle['feature_order'])} features, got {len(features)}")

    x = pd.DataFrame([features], columns=bundle["feature_order"])
    x_scaled = bundle["scaler"].transform(x)
    pred = int(bundle["model"].predict(x_scaled)[0])
    decision = float(bundle["model"].decision_function(x_scaled)[0])
    risk = float(1 / (1 + math.exp(6 * decision)))
    return {
        "anomaly": pred == -1 or risk >= 0.72,
        "anomaly_score": round(risk, 6),
        "risk_score": round(risk, 6),
        "model_version": bundle["model_version"],
    }
