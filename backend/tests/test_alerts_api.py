def test_get_alerts_returns_created_alert(client):
    payload = {
        "timestamp": "2026-05-17T12:00:00Z",
        "host": "srv-03",
        "user": "root",
        "event_type": "sudo",
        "message": "Privilege escalation with sudo by root",
        "metadata": {},
    }
    client.post("/api/v1/events/ingest", json=payload)

    alerts_resp = client.get("/api/v1/alerts")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) == 1

    alert_id = alerts[0]["id"]
    detail_resp = client.get(f"/api/v1/alerts/{alert_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["event"]["host"] == "srv-03"
