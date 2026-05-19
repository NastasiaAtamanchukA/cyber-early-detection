import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getIncidents } from "../api/client";
import { Pagination } from "../components/Pagination";
import type { IncidentItem } from "../types";

const PAGE_SIZE = 10;

const severityLabels: Record<string, string> = {
  critical: "критический",
  high: "высокий",
  medium: "средний",
  low: "низкий",
};

const statusLabels: Record<string, string> = {
  open: "открыт",
  investigating: "в расследовании",
  closed: "закрыт",
};

export function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [status, setStatus] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    getIncidents().then(setIncidents).catch(console.error);
  }, []);

  useEffect(() => {
    setPage(1);
  }, [status, severity, query]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return incidents.filter((incident) => {
      if (status !== "all" && incident.status !== status) return false;
      if (severity !== "all" && incident.severity !== severity) return false;
      if (!normalizedQuery) return true;
      return [
        incident.title,
        incident.description,
        incident.affected_host ?? "",
        incident.affected_user ?? "",
        `#${incident.id}`,
      ].join(" ").toLowerCase().includes(normalizedQuery);
    });
  }, [incidents, status, severity, query]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageItems = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  return (
    <div>
      <div className="page-title page-title-row">
        <div>
          <h2>Инциденты</h2>
          <p>Общий список карточек расследования: статус, критичность, хосты, пользователи и временная линия</p>
        </div>
        <div className="page-actions">
          <input
            className="search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Поиск по названию, хосту, пользователю"
          />
          <select className="search-input select" value={severity} onChange={(event) => setSeverity(event.target.value)}>
            <option value="all">Все уровни</option>
            <option value="critical">Критические</option>
            <option value="high">Высокие</option>
            <option value="medium">Средние</option>
            <option value="low">Низкие</option>
          </select>
        </div>
      </div>

      <div className="filter-tabs">
        <button className={status === "all" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("all")}>Все инциденты</button>
        <button className={status === "open" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("open")}>Открытые</button>
        <button className={status === "investigating" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("investigating")}>В расследовании</button>
        <button className={status === "closed" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("closed")}>Закрытые</button>
      </div>

      <div className="event-card-list">
        {pageItems.length === 0 && <div className="empty-state">Инциденты по выбранным фильтрам не найдены</div>}
        {pageItems.map((incident) => (
          <article className="event-card incident-card" key={incident.id}>
            <div className="event-card-top">
              <div>
                <div className="inline-badges">
                  <span className={`badge ${incident.severity}`}>{severityLabels[incident.severity] ?? incident.severity}</span>
                  <span className="small-label">{statusLabels[incident.status] ?? incident.status}</span>
                </div>
                <h3>#{incident.id} · {incident.title}</h3>
              </div>
              <Link className="secondary-button" to={`/incidents/${incident.id}`}>Открыть</Link>
            </div>
            <p>{incident.description}</p>
            <dl className="meta-list horizontal">
              <div><dt>Хост</dt><dd>{incident.affected_host ?? "не указан"}</dd></div>
              <div><dt>Пользователь</dt><dd>{incident.affected_user ?? "не указан"}</dd></div>
              <div><dt>Событий</dt><dd>{incident.event_count}</dd></div>
              <div><dt>Алертов</dt><dd>{incident.alert_count}</dd></div>
              <div><dt>Последнее событие</dt><dd>{new Date(incident.last_seen).toLocaleString()}</dd></div>
            </dl>
          </article>
        ))}
      </div>

      <Pagination page={safePage} pageSize={PAGE_SIZE} total={filtered.length} onPageChange={setPage} />
    </div>
  );
}
