from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Incident
from app.schemas import IncidentOut, IncidentPage

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _pages(total: int, page_size: int) -> int:
    return max(1, (total + page_size - 1) // page_size)


def _load_incident(db: Session, incident_id: int) -> Incident:
    incident = db.scalar(
        select(Incident)
        .options(selectinload(Incident.alerts))
        .where(Incident.id == incident_id)
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Инцидент не найден")
    return incident


@router.get("", response_model=IncidentPage)
def list_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = None,
    severity: str | None = None,
    host: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> IncidentPage:
    stmt = select(Incident).options(selectinload(Incident.alerts))
    count_stmt = select(func.count(Incident.id))

    filters = []
    if status:
        if status == "new":
            filters.append(Incident.status.in_(["new", "open"]))
        else:
            filters.append(Incident.status == status)
    if severity:
        filters.append(Incident.severity == severity)
    if host:
        filters.append(Incident.affected_host.ilike(f"%{host}%"))
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Incident.title.ilike(pattern), Incident.description.ilike(pattern), Incident.affected_host.ilike(pattern)))

    for item_filter in filters:
        stmt = stmt.where(item_filter)
        count_stmt = count_stmt.where(item_filter)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(
            stmt.order_by(desc(Incident.created_at), desc(Incident.id))
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
    )
    return IncidentPage(items=items, total=total, page=page, page_size=page_size, pages=_pages(total, page_size))


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    return _load_incident(db, incident_id)


@router.post("/{incident_id}/take", response_model=IncidentOut)
def take_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    incident = _load_incident(db, incident_id)
    if incident.status in {"closed"}:
        raise HTTPException(status_code=400, detail="Закрытый инцидент нужно переоткрыть")
    incident.status = "investigating"
    incident.last_seen = datetime.utcnow()
    for alert in incident.alerts:
        alert.status = "investigating"
    db.commit()
    return _load_incident(db, incident_id)


@router.post("/{incident_id}/close", response_model=IncidentOut)
def close_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    incident = _load_incident(db, incident_id)
    if incident.status not in {"investigating"}:
        raise HTTPException(status_code=400, detail="Закрыть можно только инцидент в работе")
    incident.status = "closed"
    incident.last_seen = datetime.utcnow()
    for alert in incident.alerts:
        alert.status = "closed"
    db.commit()
    return _load_incident(db, incident_id)


@router.post("/{incident_id}/reopen", response_model=IncidentOut)
def reopen_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    incident = _load_incident(db, incident_id)
    if incident.status != "closed":
        raise HTTPException(status_code=400, detail="Переоткрыть можно только закрытый инцидент")
    incident.status = "investigating"
    incident.last_seen = datetime.utcnow()
    for alert in incident.alerts:
        alert.status = "investigating"
    db.commit()
    return _load_incident(db, incident_id)
