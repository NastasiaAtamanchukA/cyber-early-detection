from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MLPredictionResponse(BaseModel):
    anomaly: bool
    anomaly_score: float
    risk_score: float
    model_version: str = "unknown"


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
    created_at: datetime


class EventOut(EventListItem):
    raw_log: dict[str, Any]
    normalized_log: dict[str, Any]


class AlertListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    incident_id: int | None
    title: str
    severity: str
    status: str
    description: str
    created_at: datetime


class AlertOut(AlertListItem):
    event: EventOut | None = None


class IncidentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: str
    status: str
    affected_host: str | None
    affected_user: str | None
    description: str
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    recommended_actions: list[str] = []


class IncidentOut(IncidentListItem):
    alerts: list[AlertListItem] = []


class StatItem(BaseModel):
    name: str
    count: int


class HostStatItem(BaseModel):
    host: str
    event_count: int
    alert_count: int
    max_risk: float


class RiskBucketItem(BaseModel):
    name: str
    count: int
    min_risk: float
    max_risk: float


class TimelineItem(BaseModel):
    label: str
    count: int
    max_risk: float


class DashboardOut(BaseModel):
    events_total: int
    alerts_total: int
    incidents_total: int
    anomalies_total: int
    average_risk: float
    critical_alerts: int
    high_risk_events: int
    alerts_by_severity: list[StatItem]
    events_by_type: list[StatItem]
    incidents_by_status: list[StatItem]
    top_hosts: list[HostStatItem]
    risk_distribution: list[RiskBucketItem]
    events_timeline: list[TimelineItem]
    recent_events: list[EventListItem]
    recent_alerts: list[AlertListItem]
    recent_incidents: list[IncidentListItem]


class CollectionScheduleBase(BaseModel):
    code: str = Field(min_length=3, max_length=80)
    name: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=1, max_length=2000)
    interval_label: str = Field(min_length=2, max_length=80)
    source_name: str = Field(min_length=2, max_length=100)
    source_kind: str = Field(default="web-schedule", min_length=2, max_length=50)
    event_profile: Literal["auth", "web", "privileged", "database", "mixed"] = "mixed"
    batch_size: int = Field(default=10, ge=1, le=100)
    enabled: bool = True


class CollectionScheduleCreate(CollectionScheduleBase):
    pass


class CollectionScheduleUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=80)
    name: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    interval_label: str | None = Field(default=None, min_length=2, max_length=80)
    source_name: str | None = Field(default=None, min_length=2, max_length=100)
    source_kind: str | None = Field(default=None, min_length=2, max_length=50)
    event_profile: Literal["auth", "web", "privileged", "database", "mixed"] | None = None
    batch_size: int | None = Field(default=None, ge=1, le=100)
    enabled: bool | None = None


class CollectionScheduleOut(CollectionScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ScheduleRunResult(BaseModel):
    schedule_id: int
    run_id: int
    events_created: int
    alerts_created: int
    message: str


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class EventPage(PaginationMeta):
    items: list[EventListItem]


class AlertPage(PaginationMeta):
    items: list[AlertListItem]


class IncidentPage(PaginationMeta):
    items: list[IncidentListItem]


class CollectionSchedulePage(PaginationMeta):
    items: list[CollectionScheduleOut]
