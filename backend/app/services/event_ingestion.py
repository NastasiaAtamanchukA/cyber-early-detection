from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models import Alert, Event, Incident, LogSource
from app.schemas import EventIn
from app.services.detector import score_event
from app.services.log_parser import normalize_log


HIGH_RISK_EVENT_TYPES = {"sudo", "privilege_escalation", "malware_detected", "web_attack", "data_exfiltration"}


def get_or_create_source(db: Session, name: str, kind: str) -> LogSource:
    source = db.scalar(select(LogSource).where(LogSource.name == name))
    if source:
        return source
    source = LogSource(name=name, kind=kind)
    db.add(source)
    db.flush()
    return source


def severity_from_risk(risk: float) -> str:
    if risk >= 0.90:
        return "critical"
    if risk >= 0.75:
        return "high"
    if risk >= 0.50:
        return "medium"
    return "low"


def russian_severity(severity: str) -> str:
    return {
        "critical": "критическая",
        "high": "высокая",
        "medium": "средняя",
        "low": "низкая",
    }.get(severity, severity)


def build_alert_title(event: Event, severity: str) -> str:
    titles = {
        "login_failed": "Подозрительные неуспешные входы",
        "login_success": "Нетипичный успешный вход",
        "sudo": "Повышение привилегий",
        "process_start": "Подозрительный запуск процесса",
        "network_connection": "Нетипичное сетевое соединение",
        "web_attack": "Возможная атака на веб-приложение",
        "db_access_denied": "Подозрительный отказ доступа к БД",
        "malware_detected": "Возможная вредоносная активность",
        "data_exfiltration": "Возможная выгрузка данных",
    }
    base = titles.get(event.event_type, "Подозрительное событие")
    return f"{base}: {event.host}"


def build_alert_description(event: Event, severity: str) -> str:
    return (
        f"Событие получило риск {event.risk_score:.3f} и уровень {russian_severity(severity)}. "
        f"Источник: {event.source.name if event.source else 'неизвестно'}. "
        f"Тип события: {event.event_type}. Сообщение: {event.message}"
    )


def should_create_incident(event: Event, severity: str) -> bool:
    return severity in {"critical", "high"} or event.event_type in HIGH_RISK_EVENT_TYPES


def create_incident_for_alert(db: Session, event: Event, alert: Alert, severity: str) -> Incident:
    title = f"Инцидент: {alert.title}"
    description = (
        "Автоматически сформированный инцидент по результатам анализа события. "
        f"Затронутый хост: {event.host}. "
        f"Пользователь: {event.user or 'не указан'}. "
        f"Основание: {alert.description}"
    )
    incident = Incident(
        title=title,
        severity=severity,
        status="open",
        description=description,
        affected_host=event.host,
        affected_user=event.user,
        event_count=1,
        alert_count=1,
        first_seen=event.timestamp,
        last_seen=event.timestamp,
    )
    db.add(incident)
    db.flush()
    alert.incident_id = incident.id
    return incident


async def create_event_from_payload(payload: EventIn, db: Session) -> Event:
    source = get_or_create_source(db, payload.source_name, payload.source_kind)
    normalized = normalize_log(payload)
    prediction = await score_event(normalized)
    should_alert = prediction.anomaly or prediction.risk_score >= settings.alert_threshold

    event = Event(
        source_id=source.id,
        timestamp=payload.timestamp,
        host=payload.host,
        user=payload.user,
        event_type=payload.event_type,
        message=payload.message,
        raw_log=payload.model_dump(mode="json"),
        normalized_log=normalized,
        is_anomaly=should_alert,
        anomaly_score=prediction.anomaly_score,
        risk_score=prediction.risk_score,
    )
    db.add(event)
    db.flush()

    if should_alert:
        severity = severity_from_risk(event.risk_score)
        alert = Alert(
            event_id=event.id,
            title=build_alert_title(event, severity),
            severity=severity,
            status="open",
            description=build_alert_description(event, severity),
        )
        db.add(alert)
        db.flush()
        if should_create_incident(event, severity):
            create_incident_for_alert(db, event, alert, severity)

    db.commit()
    hydrated = db.scalar(
        select(Event)
        .options(selectinload(Event.alert).selectinload(Alert.incident), selectinload(Event.source))
        .where(Event.id == event.id)
    )
    if hydrated is None:
        raise RuntimeError("Event was not saved")
    return hydrated
