#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1}"

echo "[seed] health backend"
curl -s "$API_URL/health" | cat
printf '\n'

echo "[seed] create demo events"
for payload in \
'{"timestamp":"2026-05-17T12:00:00Z","host":"srv-01","user":"alice","event_type":"login_failed","message":"Failed SSH login for alice from 10.0.0.15","source_name":"ssh-gateway","source_kind":"json","metadata":{"ip":"10.0.0.15","port":22}}' \
'{"timestamp":"2026-05-17T12:05:00Z","host":"web-01","user":null,"event_type":"web_attack","message":"HTTP GET /.env status=500 user-agent=curl","source_name":"nginx","source_kind":"json","metadata":{"url":"/.env","status":500}}' \
'{"timestamp":"2026-05-17T12:10:00Z","host":"srv-db-01","user":"dba","event_type":"data_export","message":"Large data export from customer table to external path","source_name":"postgres-audit","source_kind":"json","metadata":{"rows":120000}}'
do
  curl -s -X POST "$API_URL/events/ingest" \
    -H "Content-Type: application/json" \
    -d "$payload" | cat
  printf '\n'
done

echo "[seed] done"
