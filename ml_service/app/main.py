from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.model import FEATURE_ORDER, predict, train_model

app = FastAPI(title="Cyber Early Detection ML Service", version="0.2.0")


class PredictRequest(BaseModel):
    features: list[float] = Field(min_length=len(FEATURE_ORDER), max_length=len(FEATURE_ORDER))


class PredictResponse(BaseModel):
    anomaly: bool
    anomaly_score: float
    risk_score: float
    model_version: str


class TrainRequest(BaseModel):
    training_data: list[list[float]] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ml-service", "healthy": "true"}


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(payload: PredictRequest) -> PredictResponse:
    try:
        result = predict(payload.features)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PredictResponse(**result)


@app.post("/train")
def train_endpoint(payload: TrainRequest) -> dict:
    bundle = train_model(payload.training_data)
    return {"status": "trained", "model_version": bundle["model_version"]}


@app.get("/feature-order")
def feature_order() -> dict:
    return {"feature_order": FEATURE_ORDER}
