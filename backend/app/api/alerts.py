from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Alert, Event
from app.schemas import AlertOut, AlertPage

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _pages(total: int, page_size: int) -> int:
    return max(1, (total + page_size - 1) // page_size)


@router.get("", response_model=AlertPage)
def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = None,
    severity: str | None = None,
    host: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
) -> AlertPage:
    stmt = select(Alert).join(Alert.event)
    count_stmt = select(func.count(Alert.id)).join(Alert.event)

    filters = []
    if status:
        filters.append(Alert.status == status)
    if severity:
        filters.append(Alert.severity == severity)
    if host:
        filters.append(Event.host.ilike(f"%{host}%"))
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Alert.title.ilike(pattern), Alert.description.ilike(pattern), Event.message.ilike(pattern), Event.host.ilike(pattern)))

    for item_filter in filters:
        stmt = stmt.where(item_filter)
        count_stmt = count_stmt.where(item_filter)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(
            stmt.order_by(desc(Alert.created_at), desc(Alert.id))
            .limit(page_size)
            .offset((page - 1) * page_size)
        ).all()
    )
    return AlertPage(items=items, total=total, page=page, page_size=page_size, pages=_pages(total, page_size))


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    alert = db.scalar(
        select(Alert)
        .options(joinedload(Alert.event))
        .where(Alert.id == alert_id)
    )
    if alert is None:
        raise HTTPException(status_code=404, detail="Алерт не найден")
    return alert
