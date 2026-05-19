#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1/events/ingest}"

post_event() {
  curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$1" | python -m json.tool
}

post_event '{
  "timestamp": "2026-05-17T09:10:00Z",
  "host": "workstation-12",
  "user": "ivan.petrov",
  "event_type": "login_success",
  "message": "Successful interactive login",
  "source_name": "windows-security",
  "source_kind": "json",
  "metadata": {"event_id": 4624}
}'

post_event '{
  "timestamp": "2026-05-17T23:45:00Z",
  "host": "srv-linux-01",
  "user": "root",
  "event_type": "sudo",
  "message": "Denied privilege escalation via sudo after failed ssh login",
  "source_name": "linux-auth",
  "source_kind": "json",
  "metadata": {"ip": "10.0.0.44"}
}'

post_event '{
  "timestamp": "2026-05-17T02:15:00Z",
  "host": "dc-01",
  "user": "administrator",
  "event_type": "process_start",
  "message": "Suspicious powershell command with encoded payload",
  "source_name": "sysmon",
  "source_kind": "json",
  "metadata": {"process": "powershell.exe", "event_id": 1}
}'

post_event '{
  "timestamp": "2026-05-17T10:20:00Z",
  "host": "web-01",
  "user": null,
  "event_type": "network_connection",
  "message": "Outbound TCP connection to external IP port 4444",
  "source_name": "nginx-netflow",
  "source_kind": "json",
  "metadata": {"dst_ip": "185.10.10.10", "dst_port": 4444}
}'
