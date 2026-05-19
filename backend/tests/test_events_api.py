def test_ingest_event_creates_event_and_alert(client):
    payload = {
        "timestamp": "2026-05-17T12:00:00Z",
        "host": "srv-01",
        "user": "alice",
        "event_type": "login_failed",
        "message": "Failed SSH login for alice from 10.0.0.15",
        "source_name": "ssh-gateway",
        "source_kind": "json",
        "metadata": {"ip": "10.0.0.15", "port": 22},
    }

    response = client.post("/api/v1/events/ingest", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["host"] == "srv-01"
    assert body["is_anomaly"] is True
    assert body["alert_id"] is not None


def test_list_events_returns_array(client):
    payload = {
        "timestamp": "2026-05-17T12:00:00Z",
        "host": "srv-02",
        "user": "bob",
        "event_type": "network_connection",
        "message": "Outbound TCP connection to 10.10.10.10",
        "metadata": {},
    }
    client.post("/api/v1/events/ingest", json=payload)

    response = client.get("/api/v1/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
