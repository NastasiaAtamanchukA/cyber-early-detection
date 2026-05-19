import { useEffect, useMemo, useState } from "react";

import { getEvents } from "../api/client";
import { Pagination } from "../components/Pagination";
import type { EventItem } from "../types";

const PAGE_SIZE = 10;

const eventTypeLabels: Record<string, string> = {
  login_failed: "Ошибка входа",
  login_success: "Успешный вход",
  sudo: "Sudo-команда",
  process_start: "Запуск процесса",
  network_connection: "Сетевое соединение",
  web_attack: "Веб-атака",
  db_access_denied: "Отказ доступа к БД",
  malware_detected: "Вредоносная активность",
  data_exfiltration: "Выгрузка данных",
  file_access: "Доступ к файлам",
  privilege_escalation: "Повышение привилегий",
};

export function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [activeTab, setActiveTab] = useState("all");
  const [eventType, setEventType] = useState("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    getEvents().then(setEvents).catch(console.error);
  }, []);

  useEffect(() => {
    setPage(1);
  }, [activeTab, eventType, query]);

  const eventTypes = useMemo(() => Array.from(new Set(events.map((event) => event.event_type))).sort(), [events]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return events.filter((event) => {
      if (activeTab === "anomalies" && !event.is_anomaly) return false;
      if (activeTab === "with-alert" && !event.alert_id) return false;
      if (activeTab === "high-risk" && event.risk_score < 0.75) return false;
      if (eventType !== "all" && event.event_type !== eventType) return false;
      if (!normalizedQuery) return true;
      return [event.host, event.user ?? "", event.event_type, event.message, event.source_name ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [events, activeTab, eventType, query]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageItems = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  return (
    <div>
      <div className="page-title page-title-row">
        <div>
          <h2>События безопасности</h2>
          <p>Нормализованные записи из источников логов с оценкой риска</p>
        </div>
        <div className="page-actions">
          <input
            className="search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Поиск по хосту, пользователю, типу"
          />
          <select className="search-input select" value={eventType} onChange={(event) => setEventType(event.target.value)}>
            <option value="all">Все типы</option>
            {eventTypes.map((type) => (
              <option value={type} key={type}>{eventTypeLabels[type] ?? type}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="filter-tabs">
        <button className={activeTab === "all" ? "filter-tab active" : "filter-tab"} onClick={() => setActiveTab("all")}>Все события</button>
        <button className={activeTab === "anomalies" ? "filter-tab active" : "filter-tab"} onClick={() => setActiveTab("anomalies")}>Только аномалии</button>
        <button className={activeTab === "with-alert" ? "filter-tab active" : "filter-tab"} onClick={() => setActiveTab("with-alert")}>С алертами</button>
        <button className={activeTab === "high-risk" ? "filter-tab active" : "filter-tab"} onClick={() => setActiveTab("high-risk")}>Высокий риск</button>
      </div>

      <div className="event-card-list">
        {pageItems.length === 0 && <div className="empty-state">События по выбранным фильтрам не найдены</div>}
        {pageItems.map((event) => (
          <article className={event.is_anomaly ? "event-card anomaly" : "event-card"} key={event.id}>
            <div className="event-card-top">
              <div>
                <span className="small-label">{eventTypeLabels[event.event_type] ?? event.event_type}</span>
                <h3>{event.host}</h3>
              </div>
              <span className="risk-pill">Риск {event.risk_score.toFixed(3)}</span>
            </div>
            <p>{event.message}</p>
            <dl className="meta-list horizontal">
              <div><dt>Время</dt><dd>{new Date(event.timestamp).toLocaleString()}</dd></div>
              <div><dt>Пользователь</dt><dd>{event.user ?? "не указан"}</dd></div>
              <div><dt>Источник</dt><dd>{event.source_name ?? "не указан"}</dd></div>
              <div><dt>Аномалия</dt><dd>{event.is_anomaly ? "да" : "нет"}</dd></div>
              <div><dt>Алерт</dt><dd>{event.alert_id ? `#${event.alert_id}` : "нет"}</dd></div>
            </dl>
          </article>
        ))}
      </div>

      <Pagination page={safePage} pageSize={PAGE_SIZE} total={filtered.length} onPageChange={setPage} />
    </div>
  );
}
