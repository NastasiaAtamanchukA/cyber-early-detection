from __future__ import annotations

from datetime import UTC, datetime, timedelta
from random import choice, randint, random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import verify_api_key
from app.models import Alert, CollectionRun, CollectionSchedule, Event
from app.schemas import CollectionScheduleOut, EventIn, ScheduleRunResult
from app.services.event_ingestion import create_event_from_payload

router = APIRouter(prefix="/collectors", tags=["Сбор событий"], dependencies=[Depends(verify_api_key)])

DEFAULT_SCHEDULES = [
    {
        "code": "auth-every-5-min",
        "name": "Аутентификация каждые 5 минут",
        "description": "Собирает события входа пользователей, SSH/RDP-подключения и ошибки авторизации",
        "interval_label": "каждые 5 минут",
        "source_name": "web-auth-schedule",
        "source_kind": "web-schedule",
        "event_profile": "auth",
        "batch_size": 14,
    },
    {
        "code": "web-every-10-min",
        "name": "Веб-журналы каждые 10 минут",
        "description": "Имитирует сбор access/error логов веб-приложения, включая обращения к административным URL",
        "interval_label": "каждые 10 минут",
        "source_name": "web-nginx-schedule",
        "source_kind": "web-schedule",
        "event_profile": "web",
        "batch_size": 12,
    },
    {
        "code": "night-privileged-hourly",
        "name": "Ночная проверка привилегий",
        "description": "Собирает редкие ночные события sudo, PowerShell, запуска скриптов и административных действий",
        "interval_label": "каждый час ночью",
        "source_name": "web-privileged-schedule",
        "source_kind": "web-schedule",
        "event_profile": "privileged",
        "batch_size": 10,
    },
    {
        "code": "database-hourly",
        "name": "База данных каждый час",
        "description": "Имитирует сбор событий PostgreSQL: отказы доступа, подозрительные запросы и выгрузку данных",
        "interval_label": "каждый час",
        "source_name": "web-db-schedule",
        "source_kind": "web-schedule",
        "event_profile": "database",
        "batch_size": 9,
    },
]


def ensure_default_schedules(db: Session) -> None:
    existing_codes = set(db.scalars(select(CollectionSchedule.code)).all())
    for item in DEFAULT_SCHEDULES:
        if item["code"] in existing_codes:
            continue
        db.add(CollectionSchedule(enabled=True, **item))
    db.commit()


def _timestamp(index: int) -> datetime:
    return datetime.now(UTC) - timedelta(minutes=index * randint(1, 4))


def _auth_event(index: int, schedule: CollectionSchedule) -> EventIn:
    suspicious = random() > 0.55
    host = choice(["srv-auth-01", "vpn-gw-01", "dc-01", "jump-host-01"])
    user = choice(["ivanov", "petrova", "svc-backup", "admin", "unknown"])
    if suspicious:
        event_type = choice(["login_failed", "login_failed", "login_success"])
        message = choice([
            f"Failed SSH login for {user} from 185.22.{randint(1, 254)}.{randint(1, 254)}",
            f"Multiple invalid password attempts for {user} via RDP",
            f"Successful login after many failed attempts for {user}",
        ])
    else:
        event_type = "login_success"
        message = f"Successful interactive login for {user}"
    return EventIn(
        timestamp=_timestamp(index),
        host=host,
        user=None if user == "unknown" else user,
        event_type=event_type,
        message=message,
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"collector": schedule.code, "ip": f"10.10.{randint(1, 10)}.{randint(1, 254)}"},
    )


def _web_event(index: int, schedule: CollectionSchedule) -> EventIn:
    attack = random() > 0.45
    host = choice(["web-01", "web-02", "api-gateway-01"])
    if attack:
        event_type = "web_attack"
        message = choice([
            "HTTP 401 GET /admin from suspicious IP, unauthorized access attempt",
            "HTTP 500 POST /login contains SQL injection pattern ' OR 1=1",
            "HTTP 403 GET /.env blocked, possible reconnaissance",
            "HTTP 404 GET /wp-admin from external scanner",
        ])
        user = None
    else:
        event_type = "network_connection"
        message = choice([
            "HTTP 200 GET /api/health from internal monitor",
            "HTTP 200 GET /dashboard normal user request",
            "HTTP 302 POST /login successful redirect",
        ])
        user = choice(["ivanov", "petrova", "analyst"])
    return EventIn(
        timestamp=_timestamp(index),
        host=host,
        user=user,
        event_type=event_type,
        message=message,
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"collector": schedule.code, "method": choice(["GET", "POST"]), "status": choice([200, 302, 401, 403, 500])},
    )


def _privileged_event(index: int, schedule: CollectionSchedule) -> EventIn:
    host = choice(["srv-core-01", "linux-admin-01", "win-admin-01"])
    user = choice(["root", "admin", "svc-deploy", "petrova"])
    event_type = choice(["sudo", "process_start", "privilege_escalation"])
    message = choice([
        f"sudo command executed by {user}: cat /etc/shadow",
        "PowerShell encoded command started with administrative privileges",
        "bash script started from /tmp with root privileges",
        "User added to local administrators group",
    ])
    return EventIn(
        timestamp=_timestamp(index),
        host=host,
        user=user,
        event_type=event_type,
        message=message,
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"collector": schedule.code, "process": choice(["powershell.exe", "bash", "sudo", "cmd.exe"])},
    )


def _database_event(index: int, schedule: CollectionSchedule) -> EventIn:
    host = choice(["db-01", "db-02", "analytics-db-01"])
    user = choice(["app_user", "report_user", "postgres", "unknown"])
    risky = random() > 0.5
    event_type = choice(["db_access_denied", "data_exfiltration"]) if risky else "file_access"
    message = choice([
        "PostgreSQL denied connection for invalid password from external IP",
        "Large SELECT export detected from sensitive table customers",
        "COPY command executed for table payments to external file",
        "Routine SELECT query completed successfully",
    ])
    return EventIn(
        timestamp=_timestamp(index),
        host=host,
        user=None if user == "unknown" else user,
        event_type=event_type,
        message=message,
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"collector": schedule.code, "database": choice(["main", "billing", "analytics"])},
    )


def build_demo_event(index: int, schedule: CollectionSchedule) -> EventIn:
    builders = {
        "auth": _auth_event,
        "web": _web_event,
        "privileged": _privileged_event,
        "database": _database_event,
    }
    return builders.get(schedule.event_profile, _auth_event)(index, schedule)


@router.get("/schedules", response_model=list[CollectionScheduleOut])
def list_schedules(db: Session = Depends(get_db)) -> list[CollectionSchedule]:
    ensure_default_schedules(db)
    return list(db.scalars(select(CollectionSchedule).order_by(CollectionSchedule.id)).all())


@router.post("/schedules/{schedule_id}/run", response_model=ScheduleRunResult)
async def run_schedule(schedule_id: int, db: Session = Depends(get_db)) -> ScheduleRunResult:
    ensure_default_schedules(db)
    schedule = db.scalar(select(CollectionSchedule).where(CollectionSchedule.id == schedule_id))
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание сбора не найдено")
    if not schedule.enabled:
        raise HTTPException(status_code=400, detail="Расписание отключено")

    started_at = datetime.now(UTC)
    created_events: list[Event] = []
    alerts_before = db.scalar(select(func_count_alerts()))
    incidents_before = db.scalar(select(func_count_incidents()))

    for index in range(schedule.batch_size):
        created_events.append(await create_event_from_payload(build_demo_event(index, schedule), db))

    alerts_after = db.scalar(select(func_count_alerts()))
    incidents_after = db.scalar(select(func_count_incidents()))
    schedule.last_run_at = datetime.now(UTC)

    run = CollectionRun(
        schedule_id=schedule.id,
        status="success",
        events_created=len(created_events),
        alerts_created=int((alerts_after or 0) - (alerts_before or 0)),
        incidents_created=int((incidents_after or 0) - (incidents_before or 0)),
        details={"profile": schedule.event_profile, "source": schedule.source_name},
        started_at=started_at,
        finished_at=datetime.now(UTC),
    )
    db.add(run)
    db.commit()
    db.refresh(schedule)
    db.refresh(run)

    hydrated_events = list(
        db.scalars(
            select(Event)
            .options(selectinload(Event.alert).selectinload(Alert.incident), selectinload(Event.source))
            .where(Event.id.in_([event.id for event in created_events]))
            .order_by(Event.id)
        ).all()
    )
    return ScheduleRunResult(schedule=schedule, run=run, events=hydrated_events)


def func_count_alerts():
    from sqlalchemy import func

    return func.count(Alert.id)


def func_count_incidents():
    from sqlalchemy import func

    from app.models import Incident

    return func.count(Incident.id)
