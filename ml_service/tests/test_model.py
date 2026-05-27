from app import model


def test_feature_order_has_12_features():
    assert len(model.FEATURE_ORDER) == 12


def test_predict_returns_bounded_risk(tmp_path, monkeypatch):
    monkeypatch.setattr(model, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(model, "MODEL_PATH", tmp_path / "isolation_forest.joblib")
    model.train_model()

    result = model.predict([12, 0, 64, 0, 0, 100, 200, 0, 0, 1, 0, 1])

    assert 0.0 <= result["risk_score"] <= 1.0
    assert "model_version" in result
