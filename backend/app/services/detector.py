from __future__ import annotations

import httpx

from app.config import settings
from app.schemas import MLPredictionResponse
from app.services.log_parser import build_feature_vector


def _heuristic_risk(normalized: dict) -> float:
    risk = 0.05
    risk += 0.20 * normalized["is_night"]
    risk += 0.25 * normalized["contains_error"]
    risk += 0.20 * normalized["contains_privilege"]
    risk += 0.15 * normalized["contains_network"]
    risk += 0.10 * normalized["contains_process"]
    risk += 0.05 * normalized["user_missing"]
    if normalized["event_type_code"] in {1, 3}:
        risk += 0.10
    return min(round(risk, 6), 0.99)


async def score_event(normalized: dict) -> MLPredictionResponse:
    payload = {"features": build_feature_vector(normalized)}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(settings.ml_predict_url, json=payload)
            response.raise_for_status()
            return MLPredictionResponse(**response.json())
    except Exception:
        fallback_risk = _heuristic_risk(normalized)
        return MLPredictionResponse(
            anomaly=fallback_risk >= settings.alert_threshold,
            anomaly_score=fallback_risk,
            risk_score=fallback_risk,
            model_version="heuristic-fallback",
        )
