from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event
from app.schemas import EventIn, EventOut, EventPage
from app.services.event_ingestion import create_event_from_payload

router = APIRouter(prefix="/events", tags=["events"])


def _pages(total: int, page_size: int) -> int:
    return max(1, (total + page_size - 1) // page_size)


@router.post("/ingest", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def ingest_event(payload: EventIn, db: Session = Depends(get_db)) -> Event:
    try:
        return await create_event_from_payload(payload, db)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=EventPage)
def list_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    only_anomalies: bool = False,
    event_type: str | None = None,
    host: str | None = None,
    user: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> EventPage:
    stmt = select(Event)
    count_stmt = select(func.count(Event.id))

    filters = []
    if only_anomalies:
        filters.append(Event.is_anomaly.is_(True))
    if event_type:
        filters.append(Event.event_type == event_type)
    if host:
        filters.append(Event.host.ilike(f"%{host}%"))
    if user:
        filters.append(Event.user.ilike(f"%{user}%"))
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Event.message.ilike(pattern), Event.host.ilike(pattern), Event.event_type.ilike(pattern)))

    for item_filter in filters:
        stmt = stmt.where(item_filter)
        count_stmt = count_stmt.where(item_filter)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(
            stmt.order_by(desc(Event.timestamp), desc(Event.id))
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
    )
    return EventPage(items=items, total=total, page=page, page_size=page_size, pages=_pages(total, page_size))


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    event = db.scalar(select(Event).where(Event.id == event_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event
