from __future__ import annotations

import math

import httpx

from app.config import settings
from app.schemas import MLPredictionResponse


async def score_event(normalized: dict) -> MLPredictionResponse:
    features = normalized.get("features", [])
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.ml_service_url}/predict",
                json={"features": features},
            )
            response.raise_for_status()
            return MLPredictionResponse(**response.json())
    except Exception:
        # Демонстрационный fallback: позволяет backend не падать, если ML-сервис временно недоступен.
        text = " ".join(str(normalized.get(key, "")) for key in ("message", "event_type"))
        text = text.lower()
        suspicious = sum(
            token in text
            for token in ["failed", "sudo", "admin", "sql", "error", "powershell", "denied"]
        )
        base = min(0.95, 0.25 + suspicious * 0.18 + len(text) / 2500)
        risk = 1 / (1 + math.exp(-6 * (base - 0.55)))
        return MLPredictionResponse(
            anomaly=risk >= settings.alert_threshold,
            anomaly_score=round(risk, 6),
            risk_score=round(risk, 6),
            model_version="fallback-rule-score",
        )
