from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


class LogSource(Base):
    __tablename__ = "log_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(50), default="json")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    events: Mapped[list["Event"]] = relationship(back_populates="source")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("log_sources.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    host: Mapped[str] = mapped_column(String(255), index=True)
    user: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    message: Mapped[str] = mapped_column(Text)
    raw_log: Mapped[dict] = mapped_column(JSONType)
    normalized_log: Mapped[dict] = mapped_column(JSONType)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped["LogSource"] = relationship(back_populates="events")
    alert: Mapped["Alert | None"] = relationship(back_populates="event", uselist=False)

    @property
    def alert_id(self) -> int | None:
        return self.alert.id if self.alert else None

    @property
    def source_name(self) -> str | None:
        return self.source.name if self.source else None


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    description: Mapped[str] = mapped_column(Text)
    affected_host: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    affected_user: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    event_count: Mapped[int] = mapped_column(Integer, default=1)
    alert_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    alerts: Mapped[list["Alert"]] = relationship(back_populates="incident")

    @property
    def recommended_actions(self) -> list[str]:
        actions_by_severity = {
            "critical": [
                "Немедленно проверить затронутый хост и пользователя",
                "Изолировать рабочую станцию или сервер при подтверждении компрометации",
                "Сбросить пароль пользователя и проверить активные сессии",
                "Собрать артефакты: процессы, сетевые соединения, последние команды, файлы во временных каталогах",
            ],
            "high": [
                "Взять инцидент в расследование",
                "Проверить связанные алерты и временную линию события",
                "Сопоставить активность пользователя с рабочим графиком",
                "Проверить хост на признаки вредоносных процессов и внешних соединений",
            ],
            "medium": [
                "Проверить событие по журналам источника",
                "Оценить повторяемость похожих событий по пользователю и хосту",
                "При подтверждении риска повысить критичность инцидента",
            ],
            "low": [
                "Проверить корректность нормализации события",
                "Оставить инцидент под наблюдением при отсутствии повторов",
            ],
        }
        return actions_by_severity.get(self.severity, actions_by_severity["medium"])

    @property
    def attack_stage(self) -> str:
        title = self.title.lower()
        description = self.description.lower()
        text = f"{title} {description}"
        if "вход" in text or "login" in text or "auth" in text:
            return "Начальный доступ / подбор учетных данных"
        if "привил" in text or "sudo" in text or "admin" in text:
            return "Повышение привилегий"
        if "web" in text or "http" in text or "sql" in text:
            return "Атака на веб-приложение"
        if "powershell" in text or "процесс" in text or "malware" in text:
            return "Выполнение подозрительного кода"
        if "выгруз" in text or "data" in text or "copy" in text:
            return "Сбор или выгрузка данных"
        return "Аномальная активность"

    @property
    def detection_logic(self) -> str:
        return (
            "Инцидент создан автоматически: связанное событие получило высокий риск или было отнесено "
            "к одному из критичных типов активности. Учитываются риск-скор ML-модуля, тип события, "
            "источник лога, хост, пользователь и текст сообщения."
        )

    @property
    def response_sla(self) -> str:
        return {
            "critical": "до 15 минут",
            "high": "до 1 часа",
            "medium": "до 4 часов",
            "low": "до 1 рабочего дня",
        }.get(self.severity, "до 4 часов")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("event_id", name="uq_alerts_event_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    event: Mapped["Event"] = relationship(back_populates="alert")
    incident: Mapped["Incident | None"] = relationship(back_populates="alerts")


class CollectionSchedule(Base):
    __tablename__ = "collection_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    interval_label: Mapped[str] = mapped_column(String(80))
    source_name: Mapped[str] = mapped_column(String(100))
    source_kind: Mapped[str] = mapped_column(String(50), default="web-schedule")
    event_profile: Mapped[str] = mapped_column(String(80), default="mixed")
    batch_size: Mapped[int] = mapped_column(Integer, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    runs: Mapped[list["CollectionRun"]] = relationship(back_populates="schedule")


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("collection_schedules.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="success", index=True)
    events_created: Mapped[int] = mapped_column(Integer, default=0)
    alerts_created: Mapped[int] = mapped_column(Integer, default=0)
    incidents_created: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict] = mapped_column(JSONType, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    schedule: Mapped["CollectionSchedule"] = relationship(back_populates="runs")
