from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import verify_api_key
from app.models import Alert, Event, Incident
from app.schemas import DashboardOut, HostStatItem, StatItem

router = APIRouter(prefix="/dashboard", tags=["Дашборд"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=DashboardOut)
@router.get("/", response_model=DashboardOut, include_in_schema=False)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    total_events = db.scalar(select(func.count(Event.id))) or 0
    total_alerts = db.scalar(select(func.count(Alert.id))) or 0
    total_incidents = db.scalar(select(func.count(Incident.id))) or 0
    open_incidents = db.scalar(select(func.count(Incident.id)).where(Incident.status == "open")) or 0
    critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "critical")) or 0
    high_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "high")) or 0
    anomalies = db.scalar(select(func.count(Event.id)).where(Event.is_anomaly.is_(True))) or 0
    avg_risk = float(db.scalar(select(func.coalesce(func.avg(Event.risk_score), 0.0))) or 0.0)

    events_by_type = [
        StatItem(name=name, count=count)
        for name, count in db.execute(
            select(Event.event_type, func.count(Event.id)).group_by(Event.event_type).order_by(desc(func.count(Event.id))).limit(8)
        )
    ]
    alerts_by_severity = [
        StatItem(name=name, count=count)
        for name, count in db.execute(
            select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).order_by(desc(func.count(Alert.id)))
        )
    ]
    incidents_by_status = [
        StatItem(name=name, count=count)
        for name, count in db.execute(
            select(Incident.status, func.count(Incident.id)).group_by(Incident.status).order_by(desc(func.count(Incident.id)))
        )
    ]
    top_hosts = [
        HostStatItem(host=host, count=count, max_risk=float(max_risk or 0.0))
        for host, count, max_risk in db.execute(
            select(Event.host, func.count(Event.id), func.max(Event.risk_score))
            .group_by(Event.host)
            .order_by(desc(func.max(Event.risk_score)), desc(func.count(Event.id)))
            .limit(6)
        )
    ]
    latest_events = list(
        db.scalars(
            select(Event)
            .options(selectinload(Event.alert), selectinload(Event.source))
            .order_by(desc(Event.timestamp))
            .limit(8)
        ).all()
    )
    latest_alerts = list(
        db.scalars(
            select(Alert)
            .options(selectinload(Alert.event), selectinload(Alert.incident))
            .order_by(desc(Alert.created_at))
            .limit(6)
        ).all()
    )
    latest_incidents = list(
        db.scalars(select(Incident).order_by(desc(Incident.last_seen)).limit(6)).all()
    )

    return DashboardOut(
        total_events=total_events,
        total_alerts=total_alerts,
        total_incidents=total_incidents,
        open_incidents=open_incidents,
        critical_alerts=critical_alerts,
        high_alerts=high_alerts,
        anomalies=anomalies,
        avg_risk=round(avg_risk, 3),
        events_by_type=events_by_type,
        alerts_by_severity=alerts_by_severity,
        incidents_by_status=incidents_by_status,
        top_hosts=top_hosts,
        latest_events=latest_events,
        latest_alerts=latest_alerts,
        latest_incidents=latest_incidents,
    )
