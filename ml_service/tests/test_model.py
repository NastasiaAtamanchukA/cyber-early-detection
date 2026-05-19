from pathlib import Path

from app import model


def test_train_model_creates_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(model, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(model, "MODEL_PATH", tmp_path / "isolation_forest.joblib")
    bundle = model.train_model()
    assert bundle["trained_on_rows"] > 0
    assert Path(model.MODEL_PATH).exists()


def test_predict_returns_bounded_risk(tmp_path, monkeypatch):
    monkeypatch.setattr(model, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(model, "MODEL_PATH", tmp_path / "isolation_forest.joblib")
    model.train_model()
    result = model.predict([12, 0, 64, 0, 0, 100, 200, 0, 0, 1, 0, 1])
    assert 0.0 <= result["risk_score"] <= 1.0
    assert "model_version" in result
