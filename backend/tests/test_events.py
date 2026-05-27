def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_event_creates_alert(client, sample_event_payload):
    response = client.post("/api/v1/events/ingest", json=sample_event_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["host"] == "srv-01"
    assert body["is_anomaly"] is True
    assert body["risk_score"] == 0.91

    alerts = client.get("/api/v1/alerts").json()
    assert alerts["total"] == 1
    assert len(alerts["items"]) == 1
    assert alerts["items"][0]["severity"] == "critical"


def test_events_filter_by_anomaly(client, sample_event_payload):
    client.post("/api/v1/events/ingest", json=sample_event_payload)
    response = client.get("/api/v1/events?only_anomalies=true")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_dashboard_contains_new_chart_data(client, sample_event_payload):
    client.post("/api/v1/events/ingest", json=sample_event_payload)
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["events_total"] == 1
    assert "risk_distribution" in body
    assert "events_timeline" in body


def test_create_and_update_collection_schedule(client):
    payload = {
        "code": "custom-mixed",
        "name": "Пользовательское расписание",
        "description": "Проверка пользовательского создания расписания",
        "interval_label": "каждые 15 минут",
        "source_name": "custom-source",
        "source_kind": "web-schedule",
        "event_profile": "mixed",
        "batch_size": 3,
        "enabled": True,
    }
    created = client.post("/api/v1/collectors/schedules", json=payload)
    assert created.status_code == 201
    schedule_id = created.json()["id"]

    updated = client.patch(f"/api/v1/collectors/schedules/{schedule_id}", json={"enabled": False, "batch_size": 5})
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["batch_size"] == 5
