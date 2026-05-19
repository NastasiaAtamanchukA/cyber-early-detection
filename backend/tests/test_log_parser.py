from app.schemas import EventIn
from app.services.log_parser import build_feature_vector, normalize_log


def test_normalize_log_extracts_expected_flags():
    payload = EventIn(
        timestamp="2026-05-17T23:10:00Z",
        host="srv-99",
        user=None,
        event_type="sudo",
        message="Denied privilege escalation via sudo",
        metadata={"k": "v"},
    )
    normalized = normalize_log(payload)
    assert normalized["is_night"] == 1
    assert normalized["user_missing"] == 1
    assert normalized["contains_privilege"] == 1
    assert normalized["metadata_size"] == 1


def test_build_feature_vector_has_stable_length():
    normalized = {
        "hour": 10,
        "is_night": 0,
        "message_length": 20,
        "user_missing": 0,
        "event_type_code": 1,
        "host_bucket": 10,
        "user_bucket": 20,
        "contains_error": 1,
        "contains_privilege": 0,
        "contains_network": 1,
        "contains_process": 0,
        "metadata_size": 2,
    }
    vector = build_feature_vector(normalized)
    assert len(vector) == 12
