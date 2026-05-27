from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models import Alert, Event, Incident
from app.schemas import DashboardOut, HostStatItem, RiskBucketItem, StatItem, TimelineItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _stat_rows(db: Session, stmt) -> list[StatItem]:
    return [StatItem(name=str(name), count=int(count)) for name, count in db.execute(stmt).all()]


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    events_total = db.scalar(select(func.count(Event.id))) or 0
    alerts_total = db.scalar(select(func.count(Alert.id))) or 0
    incidents_total = db.scalar(select(func.count(Incident.id))) or 0
    anomalies_total = db.scalar(select(func.count(Event.id)).where(Event.is_anomaly.is_(True))) or 0
    average_risk = db.scalar(select(func.avg(Event.risk_score))) or 0.0
    critical_alerts = db.scalar(select(func.count(Alert.id)).where(Alert.severity == "critical")) or 0
    high_risk_events = db.scalar(select(func.count(Event.id)).where(Event.risk_score >= 0.75)) or 0

    alerts_by_severity = _stat_rows(
        db,
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).order_by(desc(func.count(Alert.id))),
    )
    events_by_type = _stat_rows(
        db,
        select(Event.event_type, func.count(Event.id)).group_by(Event.event_type).order_by(desc(func.count(Event.id))).limit(10),
    )
    incidents_by_status = _stat_rows(
        db,
        select(Incident.status, func.count(Incident.id)).group_by(Incident.status).order_by(desc(func.count(Incident.id))),
    )

    top_hosts = [
        HostStatItem(host=host, event_count=int(event_count), alert_count=int(alert_count or 0), max_risk=float(max_risk or 0.0))
        for host, event_count, alert_count, max_risk in db.execute(
            select(
                Event.host,
                func.count(Event.id).label("event_count"),
                func.count(Alert.id).label("alert_count"),
                func.max(Event.risk_score).label("max_risk"),
            )
            .outerjoin(Alert, Alert.event_id == Event.id)
            .group_by(Event.host)
            .order_by(desc("max_risk"), desc("event_count"))
            .limit(10)
        ).all()
    ]

    risk_distribution = [
        RiskBucketItem(name="low", count=db.scalar(select(func.count(Event.id)).where(Event.risk_score < 0.5)) or 0, min_risk=0.0, max_risk=0.49),
        RiskBucketItem(name="medium", count=db.scalar(select(func.count(Event.id)).where(Event.risk_score >= 0.5, Event.risk_score < 0.75)) or 0, min_risk=0.5, max_risk=0.74),
        RiskBucketItem(name="high", count=db.scalar(select(func.count(Event.id)).where(Event.risk_score >= 0.75, Event.risk_score < 0.9)) or 0, min_risk=0.75, max_risk=0.89),
        RiskBucketItem(name="critical", count=db.scalar(select(func.count(Event.id)).where(Event.risk_score >= 0.9)) or 0, min_risk=0.9, max_risk=1.0),
    ]

    timeline_events = list(db.scalars(select(Event).order_by(desc(Event.timestamp)).limit(200)).all())
    timeline_map: dict[str, dict[str, float | int]] = {}
    for event in reversed(timeline_events):
        label = event.timestamp.strftime("%H:%M")
        bucket = timeline_map.setdefault(label, {"count": 0, "max_risk": 0.0})
        bucket["count"] = int(bucket["count"]) + 1
        bucket["max_risk"] = max(float(bucket["max_risk"]), float(event.risk_score or 0.0))

    events_timeline = [
        TimelineItem(label=label, count=int(values["count"]), max_risk=float(values["max_risk"]))
        for label, values in list(timeline_map.items())[-12:]
    ]

    recent_events = list(db.scalars(select(Event).order_by(desc(Event.timestamp), desc(Event.id)).limit(5)).all())
    recent_alerts = list(db.scalars(select(Alert).order_by(desc(Alert.created_at), desc(Alert.id)).limit(5)).all())
    recent_incidents = list(
        db.scalars(
            select(Incident)
            .options(selectinload(Incident.alerts))
            .order_by(desc(Incident.created_at), desc(Incident.id))
            .limit(5)
        ).all()
    )

    return DashboardOut(
        events_total=int(events_total),
        alerts_total=int(alerts_total),
        incidents_total=int(incidents_total),
        anomalies_total=int(anomalies_total),
        average_risk=float(round(average_risk, 4)),
        critical_alerts=int(critical_alerts),
        high_risk_events=int(high_risk_events),
        alerts_by_severity=alerts_by_severity,
        events_by_type=events_by_type,
        incidents_by_status=incidents_by_status,
        top_hosts=top_hosts,
        risk_distribution=risk_distribution,
        events_timeline=events_timeline,
        recent_events=recent_events,
        recent_alerts=recent_alerts,
        recent_incidents=recent_incidents,
    )
