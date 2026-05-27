from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


JSONType = JSON().with_variant(JSONB, "postgresql")


class LogSource(Base):
    __tablename__ = "log_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(50), default="json")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    events: Mapped[list[Event]] = relationship(back_populates="source")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("log_sources.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    host: Mapped[str] = mapped_column(String(255), index=True)
    user: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    message: Mapped[str] = mapped_column(Text)
    raw_log: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONType), default=dict)
    normalized_log: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONType), default=dict)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    source: Mapped[LogSource] = relationship(back_populates="events")
    alert: Mapped[Alert | None] = relationship(back_populates="event", uselist=False)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    affected_host: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    affected_user: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    alerts: Mapped[list[Alert]] = relationship(back_populates="incident")

    @property
    def recommended_actions(self) -> list[str]:
        event_types = {
            alert.event.event_type
            for alert in self.alerts
            if alert.event is not None
        }

        text_parts = [self.title, self.description, self.severity]
        for alert in self.alerts:
            text_parts.append(alert.title)
            text_parts.append(alert.description)
            if alert.event is not None:
                text_parts.append(alert.event.message)
                text_parts.append(alert.event.event_type)

        text = " ".join(part.lower() for part in text_parts if part)

        actions = [
            "Зафиксировать инцидент в журнале расследования: время обнаружения, критичность, затронутый хост, пользователя и связанные алерты.",
            "Проверить временную линию: сопоставить первое и последнее событие, повторяемость алертов и наличие похожих событий по тому же пользователю или хосту.",
            "Проверить исходный лог и нормализованные поля события, чтобы исключить ошибку парсинга, некорректный источник или тестовую активность.",
        ]

        if self.severity in {"critical", "high"}:
            actions.extend(
                [
                    "Перевести инцидент в активное расследование и назначить ответственного SOC-аналитика.",
                    "Проверить, есть ли признаки продолжающейся активности: новые входы, новые процессы, сетевые соединения, повторные ошибки авторизации.",
                    "При подтверждении риска временно ограничить доступ затронутой учетной записи или изолировать хост от критичных сегментов сети.",
                ]
            )

        if "login" in text or "auth" in text or "failed" in text or "login_failed" in event_types:
            actions.extend(
                [
                    "Проверить историю входов пользователя за последние 24 часа: успешные входы после серии ошибок, необычные IP-адреса, нетипичное время активности.",
                    "Сопоставить активность с рабочим графиком пользователя и известными административными работами.",
                    "При признаках подбора пароля сбросить пароль пользователя, завершить активные сессии и проверить необходимость включения MFA.",
                ]
            )

        if "sudo" in text or "privilege" in text or "admin" in text or "powershell" in text:
            actions.extend(
                [
                    "Проверить команды и процессы с повышенными привилегиями: sudo, PowerShell, cmd, bash, скрипты из временных каталогов.",
                    "Собрать артефакты с хоста: список процессов, автозагрузку, последние команды, новые файлы, сетевые соединения и изменения локальных групп.",
                    "Проверить, не добавлялся ли пользователь в административные группы и не создавались ли новые служебные учетные записи.",
                ]
            )

        if "web" in text or "http" in text or "sql" in text or "admin" in text:
            actions.extend(
                [
                    "Проверить access/error логи веб-сервера: URL, метод, HTTP-статус, user-agent, IP-адрес и повторяемость запросов.",
                    "Отдельно проверить обращения к административным URL, попытки доступа к .env, wp-admin, SQL injection-паттерны и частые 401/403/500.",
                    "При подтверждении атаки ограничить источник на уровне WAF/firewall и сохранить сырые HTTP-запросы для дальнейшего анализа.",
                ]
            )

        if "data" in text or "copy" in text or "export" in text or "exfiltration" in text:
            actions.extend(
                [
                    "Проверить объем выгруженных данных, целевые таблицы/файлы и направление передачи.",
                    "Сопоставить действие с легитимными задачами: резервное копирование, регламентный экспорт, отчетность.",
                    "При подозрении на утечку ограничить доступ учетной записи к данным и инициировать процедуру реагирования на инцидент ИБ.",
                ]
            )

        actions.extend(
            [
                "После первичной проверки классифицировать результат: подтвержденный инцидент, ложноположительное срабатывание или событие под наблюдением.",
                "Если инцидент подтвержден, подготовить краткое заключение: причина, затронутые активы, выполненные действия, остаточные риски и рекомендации по предотвращению повторения.",
            ]
        )

        return actions


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), unique=True, index=True)
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    event: Mapped[Event] = relationship(back_populates="alert")
    incident: Mapped[Incident | None] = relationship(back_populates="alerts")


class CollectionSchedule(Base):
    __tablename__ = "collection_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    interval_label: Mapped[str] = mapped_column(String(80), default="по запросу")
    source_name: Mapped[str] = mapped_column(String(100), default="demo")
    source_kind: Mapped[str] = mapped_column(String(50), default="web-schedule")
    event_profile: Mapped[str] = mapped_column(String(50), default="mixed")
    batch_size: Mapped[int] = mapped_column(Integer, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    runs: Mapped[list[CollectionRun]] = relationship(back_populates="schedule")


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("collection_schedules.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="success")
    events_created: Mapped[int] = mapped_column(Integer, default=0)
    alerts_created: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    schedule: Mapped[CollectionSchedule] = relationship(back_populates="runs")
