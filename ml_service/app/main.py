from fastapi import FastAPI, HTTPException

from app.model import FEATURE_ORDER, load_or_bootstrap_model, predict, train_model
from app.schemas import PredictRequest, PredictResponse, TrainRequest, TrainResponse

app = FastAPI(title="Cyber ML Service", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    load_or_bootstrap_model()


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict_endpoint(payload: PredictRequest) -> PredictResponse:
    try:
        result = predict(payload.features)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PredictResponse(**result)


@app.post("/train", response_model=TrainResponse)
def train_endpoint(payload: TrainRequest) -> TrainResponse:
    try:
        bundle = train_model(csv_path=payload.csv_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TrainResponse(model_version=bundle["model_version"], trained_on_rows=bundle["trained_on_rows"])


@app.get("/feature-order")
def feature_order() -> dict:
    return {"feature_order": FEATURE_ORDER}
