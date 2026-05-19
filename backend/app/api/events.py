from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import verify_api_key
from app.models import Alert, Event
from app.schemas import EventIn, EventListItem, EventOut
from app.services.event_ingestion import create_event_from_payload

router = APIRouter(prefix="/events", tags=["События"], dependencies=[Depends(verify_api_key)])


@router.post("/ingest", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def ingest_event(payload: EventIn, db: Session = Depends(get_db)) -> Event:
    try:
        return await create_event_from_payload(payload, db)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=list[EventListItem])
@router.get("/", response_model=list[EventListItem], include_in_schema=False)
def list_events(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    only_anomalies: bool = False,
    event_type: str | None = None,
    host: str | None = None,
    db: Session = Depends(get_db),
) -> list[Event]:
    stmt = (
        select(Event)
        .options(selectinload(Event.alert), selectinload(Event.source))
        .order_by(desc(Event.timestamp))
        .limit(limit)
        .offset(offset)
    )
    if only_anomalies:
        stmt = stmt.where(Event.is_anomaly.is_(True))
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
    if host:
        stmt = stmt.where(Event.host == host)
    return list(db.scalars(stmt).all())


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    event = db.scalar(
        select(Event)
        .options(selectinload(Event.alert).selectinload(Alert.incident), selectinload(Event.source))
        .where(Event.id == event_id)
    )
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event
