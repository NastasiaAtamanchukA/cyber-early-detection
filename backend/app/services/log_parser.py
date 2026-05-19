from __future__ import annotations

import hashlib
from typing import Any

from app.schemas import EventIn

EVENT_TYPE_MAP = {
    "login_success": 0,
    "login_failed": 1,
    "process_start": 2,
    "sudo": 3,
    "network_connection": 4,
    "file_access": 5,
}

FEATURE_ORDER = [
    "hour",
    "is_night",
    "message_length",
    "user_missing",
    "event_type_code",
    "host_bucket",
    "user_bucket",
    "contains_error",
    "contains_privilege",
    "contains_network",
    "contains_process",
    "metadata_size",
]


def _stable_bucket(value: str, modulo: int = 1000) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def _contains_any(text: str, keywords: list[str]) -> int:
    return int(any(keyword in text for keyword in keywords))


def normalize_log(payload: EventIn) -> dict[str, Any]:
    lowered = f"{payload.event_type} {payload.message}".lower()
    hour = payload.timestamp.hour
    event_type_key = payload.event_type.lower().strip()
    event_type_code = EVENT_TYPE_MAP.get(event_type_key, 50 + _stable_bucket(event_type_key, 50))

    return {
        "timestamp": payload.timestamp.isoformat(),
        "hour": hour,
        "is_night": int(hour < 6 or hour >= 22),
        "message_length": len(payload.message),
        "user_missing": int(not payload.user),
        "event_type_code": event_type_code,
        "host_bucket": _stable_bucket(payload.host),
        "user_bucket": _stable_bucket(payload.user or "unknown"),
        "contains_error": _contains_any(lowered, ["fail", "failed", "error", "denied", "invalid", "unauthorized"]),
        "contains_privilege": _contains_any(lowered, ["sudo", "root", "admin", "privilege", "elevat"]),
        "contains_network": _contains_any(lowered, ["ssh", "rdp", "tcp", "udp", "port", "connection", "ip"]),
        "contains_process": _contains_any(lowered, ["powershell", "cmd.exe", "bash", "python", "curl", "wget"]),
        "metadata_size": len(payload.metadata or {}),
    }


def build_feature_vector(normalized: dict[str, Any]) -> list[float]:
    return [float(normalized[key]) for key in FEATURE_ORDER]
