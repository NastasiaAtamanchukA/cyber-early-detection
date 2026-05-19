from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import verify_api_key
from app.models import Alert, Event
from app.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["Алерты"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=list[AlertOut])
@router.get("/", response_model=list[AlertOut], include_in_schema=False)
def list_alerts(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = None,
    severity: str | None = None,
    host: str | None = None,
    db: Session = Depends(get_db),
) -> list[Alert]:
    stmt = (
        select(Alert)
        .options(
            selectinload(Alert.event).selectinload(Event.source),
            selectinload(Alert.incident),
        )
        .order_by(desc(Alert.created_at))
        .limit(limit)
        .offset(offset)
    )
    if status_filter:
        stmt = stmt.where(Alert.status == status_filter)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if host:
        stmt = stmt.join(Alert.event).where(Event.host == host)
    return list(db.scalars(stmt).all())


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    alert = db.scalar(
        select(Alert)
        .options(
            selectinload(Alert.event).selectinload(Event.source),
            selectinload(Alert.incident),
        )
        .where(Alert.id == alert_id)
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Алерт не найден")
    return alert
