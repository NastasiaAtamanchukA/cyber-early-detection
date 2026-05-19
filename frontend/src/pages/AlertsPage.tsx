import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getAlerts } from "../api/client";
import { Pagination } from "../components/Pagination";
import type { AlertItem } from "../types";

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

export function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [status, setStatus] = useState("all");
  const [severity, setSeverity] = useState("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    getAlerts().then(setAlerts).catch(console.error);
  }, []);

  useEffect(() => {
    setPage(1);
  }, [status, severity, query]);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return alerts.filter((alert) => {
      if (status !== "all" && alert.status !== status) return false;
      if (severity !== "all" && alert.severity !== severity) return false;
      if (!normalizedQuery) return true;
      return [
        alert.title,
        alert.description,
        alert.event?.host ?? "",
        alert.event?.user ?? "",
        alert.event?.event_type ?? "",
        alert.incident_id ? `#${alert.incident_id}` : "",
      ].join(" ").toLowerCase().includes(normalizedQuery);
    });
  }, [alerts, status, severity, query]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageItems = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  return (
    <div>
      <div className="page-title page-title-row">
        <div>
          <h2>Алерты</h2>
          <p>Подозрительные события, сформированные ML-модулем и правилами риска</p>
        </div>
        <div className="page-actions">
          <input
            className="search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Поиск по хосту, пользователю, описанию"
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
        <button className={status === "all" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("all")}>Все алерты</button>
        <button className={status === "open" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("open")}>Открытые</button>
        <button className={status === "investigating" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("investigating")}>В расследовании</button>
        <button className={status === "closed" ? "filter-tab active" : "filter-tab"} onClick={() => setStatus("closed")}>Закрытые</button>
      </div>

      <div className="event-card-list">
        {pageItems.length === 0 && <div className="empty-state">Алерты по выбранным фильтрам не найдены</div>}
        {pageItems.map((alert) => (
          <article className="event-card" key={alert.id}>
            <div className="event-card-top">
              <div>
                <div className="inline-badges">
                  <span className={`badge ${alert.severity}`}>{severityLabels[alert.severity] ?? alert.severity}</span>
                  <span className="small-label">{statusLabels[alert.status] ?? alert.status}</span>
                </div>
                <h3>{alert.title}</h3>
              </div>
              <Link className="secondary-button" to={`/alerts/${alert.id}`}>Открыть</Link>
            </div>
            <p>{alert.description}</p>
            <dl className="meta-list horizontal">
              <div><dt>Хост</dt><dd>{alert.event?.host ?? "не указан"}</dd></div>
              <div><dt>Пользователь</dt><dd>{alert.event?.user ?? "не указан"}</dd></div>
              <div><dt>Тип события</dt><dd>{alert.event?.event_type ?? "не указан"}</dd></div>
              <div><dt>Риск</dt><dd>{alert.event ? alert.event.risk_score.toFixed(3) : "-"}</dd></div>
              <div><dt>Инцидент</dt><dd>{alert.incident_id ? `#${alert.incident_id}` : "не создан"}</dd></div>
            </dl>
          </article>
        ))}
      </div>

      <Pagination page={safePage} pageSize={PAGE_SIZE} total={filtered.length} onPageChange={setPage} />
    </div>
  );
}
