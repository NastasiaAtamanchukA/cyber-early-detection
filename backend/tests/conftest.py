from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.schemas import MLPredictionResponse


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    async def fake_score_event(_normalized: dict) -> MLPredictionResponse:
        return MLPredictionResponse(
            anomaly=True,
            anomaly_score=0.91,
            risk_score=0.91,
            model_version="test",
        )

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.services.event_ingestion.score_event", fake_score_event)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def sample_event_payload() -> dict:
    return {
        "timestamp": datetime(2026, 5, 17, 12, 0, tzinfo=UTC).isoformat(),
        "host": "srv-01",
        "user": "alice",
        "event_type": "login_failed",
        "message": "Failed SSH login for alice from 10.0.0.15",
        "source_name": "ssh-gateway",
        "source_kind": "json",
        "metadata": {"ip": "10.0.0.15", "port": 22},
    }