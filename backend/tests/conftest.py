import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.schemas import MLPredictionResponse

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    async def fake_score_event(_normalized):
        return MLPredictionResponse(anomaly=True, anomaly_score=0.91, risk_score=0.91, model_version="test")

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.services.event_ingestion.score_event", fake_score_event)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
