from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import verify_api_key
from app.models import Alert, Event, Incident
from app.schemas import IncidentActionIn, IncidentDetailsOut, IncidentOut

router = APIRouter(prefix="/incidents", tags=["Инциденты"], dependencies=[Depends(verify_api_key)])

SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def _load_incident(db: Session, incident_id: int) -> Incident | None:
    return db.scalar(
        select(Incident)
        .options(
            selectinload(Incident.alerts)
            .selectinload(Alert.event)
            .selectinload(Event.source)
        )
        .where(Incident.id == incident_id)
    )


def _incident_details(incident: Incident) -> IncidentDetailsOut:
    related_alerts = sorted(incident.alerts, key=lambda item: item.created_at, reverse=True)
    related_events = [alert.event for alert in related_alerts if alert.event is not None]
    return IncidentDetailsOut.model_validate(
        {
            "id": incident.id,
            "title": incident.title,
            "severity": incident.severity,
            "status": incident.status,
            "description": incident.description,
            "affected_host": incident.affected_host,
            "affected_user": incident.affected_user,
            "event_count": incident.event_count,
            "alert_count": incident.alert_count,
            "first_seen": incident.first_seen,
            "last_seen": incident.last_seen,
            "created_at": incident.created_at,
            "updated_at": incident.updated_at,
            "recommended_actions": incident.recommended_actions,
            "attack_stage": incident.attack_stage,
            "detection_logic": incident.detection_logic,
            "response_sla": incident.response_sla,
            "related_alerts": related_alerts,
            "related_events": related_events,
        }
    )


def _change_severity(current: str, direction: int) -> str:
    if current not in SEVERITY_ORDER:
        return "medium"
    index = SEVERITY_ORDER.index(current)
    return SEVERITY_ORDER[max(0, min(len(SEVERITY_ORDER) - 1, index + direction))]


@router.get("", response_model=list[IncidentOut])
@router.get("/", response_model=list[IncidentOut], include_in_schema=False)
def list_incidents(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = None,
    severity: str | None = None,
    host: str | None = None,
    user: str | None = None,
    db: Session = Depends(get_db),
) -> list[Incident]:
    stmt = select(Incident).order_by(desc(Incident.last_seen)).limit(limit).offset(offset)
    if status_filter:
        stmt = stmt.where(Incident.status == status_filter)
    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if host:
        stmt = stmt.where(Incident.affected_host == host)
    if user:
        stmt = stmt.where(Incident.affected_user == user)
    return list(db.scalars(stmt).all())


@router.get("/{incident_id}", response_model=IncidentDetailsOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> IncidentDetailsOut:
    incident = _load_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Инцидент не найден")
    return _incident_details(incident)


@router.post("/{incident_id}/actions", response_model=IncidentDetailsOut)
def apply_incident_action(
    incident_id: int,
    payload: IncidentActionIn,
    db: Session = Depends(get_db),
) -> IncidentDetailsOut:
    incident = _load_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Инцидент не найден")

    if payload.action == "take_in_work":
        incident.status = "investigating"
        for alert in incident.alerts:
            if alert.status != "closed":
                alert.status = "investigating"
    elif payload.action == "close":
        incident.status = "closed"
        for alert in incident.alerts:
            alert.status = "closed"
    elif payload.action == "reopen":
        incident.status = "open"
        for alert in incident.alerts:
            alert.status = "open"
    elif payload.action == "escalate":
        incident.severity = _change_severity(incident.severity, 1)
        for alert in incident.alerts:
            alert.severity = _change_severity(alert.severity, 1)
    elif payload.action == "downgrade":
        incident.severity = _change_severity(incident.severity, -1)
        for alert in incident.alerts:
            alert.severity = _change_severity(alert.severity, -1)
    else:
        raise HTTPException(status_code=400, detail="Неизвестное действие")

    # Комментарий пока не сохраняется отдельной таблицей, но действие отражается в updated_at и статусах.
    incident.updated_at = datetime.now(UTC)
    db.commit()

    refreshed = _load_incident(db, incident_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="Инцидент не найден после обновления")
    return _incident_details(refreshed)
