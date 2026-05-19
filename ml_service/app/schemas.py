from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: list[float] = Field(min_length=12, max_length=12)


class PredictResponse(BaseModel):
    anomaly: bool
    anomaly_score: float
    risk_score: float
    model_version: str


class TrainRequest(BaseModel):
    csv_path: str | None = None


class TrainResponse(BaseModel):
    model_version: str
    trained_on_rows: int
