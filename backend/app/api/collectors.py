from __future__ import annotations

from datetime import UTC, datetime
from random import choice, randint

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CollectionRun, CollectionSchedule
from app.schemas import (
    CollectionScheduleCreate,
    CollectionScheduleOut,
    CollectionSchedulePage,
    CollectionScheduleUpdate,
    EventIn,
    ScheduleRunResult,
)
from app.services.event_ingestion import create_event_from_payload

router = APIRouter(prefix="/collectors", tags=["collectors"])


DEFAULT_SCHEDULES = [
    {
        "code": "auth-5min",
        "name": "Проверка событий аутентификации",
        "description": "Имитирует поток успешных и неуспешных входов пользователей.",
        "interval_label": "каждые 5 минут",
        "source_name": "auth-simulator",
        "source_kind": "web-schedule",
        "event_profile": "auth",
        "batch_size": 8,
        "enabled": True,
    },
    {
        "code": "web-10min",
        "name": "Проверка веб-журналов",
        "description": "Генерирует запросы к web-приложению, включая подозрительные обращения.",
        "interval_label": "каждые 10 минут",
        "source_name": "web-gateway",
        "source_kind": "web-schedule",
        "event_profile": "web",
        "batch_size": 10,
        "enabled": True,
    },
    {
        "code": "privileged-manual",
        "name": "Контроль привилегированных действий",
        "description": "Показывает события sudo/admin/powershell для демонстрации реагирования.",
        "interval_label": "по запросу",
        "source_name": "endpoint-agent",
        "source_kind": "web-schedule",
        "event_profile": "privileged",
        "batch_size": 5,
        "enabled": True,
    },
]


def ensure_default_schedules(db: Session) -> None:
    existing_count = db.scalar(select(CollectionSchedule).limit(1))
    if existing_count:
        return
    for item in DEFAULT_SCHEDULES:
        db.add(CollectionSchedule(**item))
    db.commit()


def _auth_event(index: int, schedule: CollectionSchedule) -> EventIn:
    failed = index % 3 == 0
    user = choice(["alice", "bob", "svc-backup", "admin", "olga"])
    return EventIn(
        timestamp=datetime.now(UTC),
        host=choice(["srv-auth-01", "srv-vpn-01", "dc-01"]),
        user=user,
        event_type="login_failed" if failed else "login_success",
        message=(
            f"Failed SSH login for {user} from 10.0.0.{randint(10, 250)}"
            if failed
            else f"Successful login for {user} from corporate network"
        ),
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"profile": "auth", "batch_index": index, "ip": f"10.0.0.{randint(10, 250)}", "force_risk": 0.79 if failed else 0.32},
    )


def _web_event(index: int, schedule: CollectionSchedule) -> EventIn:
    suspicious = index % 4 == 0
    url = choice(["/login", "/api/orders", "/admin", "/.env", "/search?q=' or 1=1--"])
    return EventIn(
        timestamp=datetime.now(UTC),
        host=choice(["web-01", "web-02", "api-gateway"]),
        user=None if suspicious else choice(["web-user", "service-web"]),
        event_type="web_attack" if suspicious else "web_request",
        message=f"HTTP GET {url} status={500 if suspicious else 200} user-agent=curl",
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"profile": "web", "url": url, "status": 500 if suspicious else 200, "force_risk": 0.84 if suspicious else 0.36},
    )


def _privileged_event(index: int, schedule: CollectionSchedule) -> EventIn:
    user = choice(["root", "admin", "devops", "svc-deploy"])
    command = choice(["sudo su", "powershell -enc", "usermod -aG sudo", "cat /etc/shadow"])
    return EventIn(
        timestamp=datetime.now(UTC),
        host=choice(["srv-app-01", "srv-db-01", "linux-jump-01"]),
        user=user,
        event_type="privilege_escalation",
        message=f"Privileged command detected: {command} by {user}",
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"profile": "privileged", "command": command, "force_risk": 0.92},
    )


def _database_event(index: int, schedule: CollectionSchedule) -> EventIn:
    export = index % 2 == 0
    return EventIn(
        timestamp=datetime.now(UTC),
        host=choice(["db-01", "db-report-01"]),
        user=choice(["analyst", "dba", "svc-report"]),
        event_type="data_export" if export else "database_query",
        message=(
            "Large data export from customer table to external path"
            if export
            else "SELECT query from report dashboard"
        ),
        source_name=schedule.source_name,
        source_kind=schedule.source_kind,
        metadata={"profile": "database", "rows": randint(10, 100000), "force_risk": 0.85 if export else 0.38},
    )


def build_demo_event(index: int, schedule: CollectionSchedule) -> EventIn:
    builders = {
        "auth": _auth_event,
        "web": _web_event,
        "privileged": _privileged_event,
        "database": _database_event,
    }

    if schedule.event_profile == "mixed":
        builder = choice(list(builders.values()))
        return builder(index, schedule)

    return builders.get(schedule.event_profile, _auth_event)(index, schedule)


def _pages(total: int, page_size: int) -> int:
    return max(1, (total + page_size - 1) // page_size)


@router.get("/schedules", response_model=CollectionSchedulePage)
def list_schedules(
    page: int = 1,
    page_size: int = 10,
    enabled: bool | None = None,
    event_profile: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> CollectionSchedulePage:
    ensure_default_schedules(db)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    stmt = select(CollectionSchedule)
    count_stmt = select(func.count(CollectionSchedule.id))

    filters = []
    if enabled is not None:
        filters.append(CollectionSchedule.enabled.is_(enabled))
    if event_profile:
        filters.append(CollectionSchedule.event_profile == event_profile)
    if search:
        pattern = f"%{search}%"
        filters.append(or_(CollectionSchedule.name.ilike(pattern), CollectionSchedule.code.ilike(pattern), CollectionSchedule.description.ilike(pattern), CollectionSchedule.source_name.ilike(pattern)))

    for item_filter in filters:
        stmt = stmt.where(item_filter)
        count_stmt = count_stmt.where(item_filter)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(
            stmt.order_by(CollectionSchedule.id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
    )
    return CollectionSchedulePage(items=items, total=total, page=page, page_size=page_size, pages=_pages(total, page_size))


@router.post("/schedules", response_model=CollectionScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: CollectionScheduleCreate, db: Session = Depends(get_db)) -> CollectionSchedule:
    ensure_default_schedules(db)
    existing = db.scalar(select(CollectionSchedule).where(CollectionSchedule.code == payload.code))
    if existing:
        raise HTTPException(status_code=409, detail="Расписание с таким code уже существует")

    schedule = CollectionSchedule(**payload.model_dump(), updated_at=datetime.now(UTC))
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.patch("/schedules/{schedule_id}", response_model=CollectionScheduleOut)
def update_schedule(
    schedule_id: int,
    payload: CollectionScheduleUpdate,
    db: Session = Depends(get_db),
) -> CollectionSchedule:
    ensure_default_schedules(db)
    schedule = db.scalar(select(CollectionSchedule).where(CollectionSchedule.id == schedule_id))
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание сбора не найдено")

    update_data = payload.model_dump(exclude_unset=True)
    new_code = update_data.get("code")
    if new_code and new_code != schedule.code:
        duplicate = db.scalar(select(CollectionSchedule).where(CollectionSchedule.code == new_code))
        if duplicate:
            raise HTTPException(status_code=409, detail="Расписание с таким code уже существует")

    for field, value in update_data.items():
        setattr(schedule, field, value)
    schedule.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(schedule)
    return schedule


@router.post("/schedules/{schedule_id}/run", response_model=ScheduleRunResult)
async def run_schedule(schedule_id: int, db: Session = Depends(get_db)) -> ScheduleRunResult:
    ensure_default_schedules(db)
    schedule = db.scalar(select(CollectionSchedule).where(CollectionSchedule.id == schedule_id))
    if schedule is None:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    if not schedule.enabled:
        raise HTTPException(status_code=400, detail="Расписание отключено")

    run = CollectionRun(schedule_id=schedule.id, status="running", message="Запуск сбора событий")
    db.add(run)
    db.commit()
    db.refresh(run)

    created_events = 0
    created_alerts = 0
    try:
        for index in range(schedule.batch_size):
            event = await create_event_from_payload(build_demo_event(index, schedule), db)
            created_events += 1
            if event.is_anomaly:
                created_alerts += 1
        run.status = "success"
        run.events_created = created_events
        run.alerts_created = created_alerts
        run.message = f"Создано событий: {created_events}; алертов: {created_alerts}"
    except Exception as exc:
        run.status = "failed"
        run.message = str(exc)
    finally:
        run.finished_at = datetime.now(UTC)
        db.commit()
        db.refresh(run)

    return ScheduleRunResult(
        schedule_id=schedule.id,
        run_id=run.id,
        events_created=run.events_created,
        alerts_created=run.alerts_created,
        message=run.message,
    )
