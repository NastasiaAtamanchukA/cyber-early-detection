from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EventIn(BaseModel):
    timestamp: datetime
    host: str = Field(min_length=1, max_length=255)
    user: str | None = Field(default=None, max_length=255)
    event_type: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    source_name: str = Field(default="api", max_length=100)
    source_kind: str = Field(default="json", max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    host: str
    user: str | None
    event_type: str
    message: str
    is_anomaly: bool
    anomaly_score: float
    risk_score: float
    source_name: str | None = None
    alert_id: int | None = None


class EventOut(EventListItem):
    source_id: int
    raw_log: dict[str, Any]
    normalized_log: dict[str, Any]
    created_at: datetime


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: str
    status: str
    description: str
    affected_host: str | None
    affected_user: str | None
    event_count: int
    alert_count: int
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    incident_id: int | None = None
    title: str
    severity: str
    status: str
    description: str
    created_at: datetime
    updated_at: datetime
    event: EventListItem | None = None
    incident: IncidentOut | None = None


class AlertSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    incident_id: int | None = None
    title: str
    severity: str
    status: str
    description: str
    created_at: datetime
    updated_at: datetime
    event: EventListItem | None = None


class IncidentDetailsOut(IncidentOut):
    recommended_actions: list[str]
    attack_stage: str
    detection_logic: str
    response_sla: str
    related_alerts: list[AlertSummary] = Field(default_factory=list)
    related_events: list[EventListItem] = Field(default_factory=list)


class IncidentActionIn(BaseModel):
    action: Literal["take_in_work", "close", "reopen", "escalate", "downgrade"]
    comment: str | None = Field(default=None, max_length=1000)


class CollectionScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    interval_label: str
    source_name: str
    source_kind: str
    event_profile: str
    batch_size: int
    enabled: bool
    last_run_at: datetime | None
    created_at: datetime


class CollectionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schedule_id: int
    status: str
    events_created: int
    alerts_created: int
    incidents_created: int
    details: dict[str, Any]
    started_at: datetime
    finished_at: datetime | None


class ScheduleRunResult(BaseModel):
    schedule: CollectionScheduleOut
    run: CollectionRunOut
    events: list[EventListItem]


class StatItem(BaseModel):
    name: str
    count: int


class HostStatItem(BaseModel):
    host: str
    count: int
    max_risk: float


class DashboardOut(BaseModel):
    total_events: int
    total_alerts: int
    total_incidents: int
    open_incidents: int
    critical_alerts: int
    high_alerts: int
    anomalies: int
    avg_risk: float
    events_by_type: list[StatItem]
    alerts_by_severity: list[StatItem]
    incidents_by_status: list[StatItem]
    top_hosts: list[HostStatItem]
    latest_events: list[EventListItem]
    latest_alerts: list[AlertOut]
    latest_incidents: list[IncidentOut]


class MLPredictionResponse(BaseModel):
    anomaly: bool
    anomaly_score: float
    risk_score: float
    model_version: str
