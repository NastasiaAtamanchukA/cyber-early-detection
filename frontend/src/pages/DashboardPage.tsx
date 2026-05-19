import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getDashboard } from "../api/client";
import type { DashboardData, StatItem } from "../types";

const severityLabels: Record<string, string> = {
  critical: "Критические",
  high: "Высокие",
  medium: "Средние",
  low: "Низкие",
};

function BarList({ items, labelMap = {} }: { items: StatItem[]; labelMap?: Record<string, string> }) {
  const max = Math.max(...items.map((item) => item.count), 1);

  return (
    <div className="bar-list">
      {items.length === 0 && <p className="muted">Данных пока нет</p>}
      {items.map((item) => (
        <div className="bar-row" key={item.name}>
          <div className="bar-label">
            <span>{labelMap[item.name] ?? item.name}</span>
            <strong>{item.count}</strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.max(8, (item.count / max) * 100)}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard().then(setData).catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="error">Ошибка API: {error}</div>;
  if (!data) return <p>Загружаю дашборд...</p>;

  return (
    <div>
      <div className="page-title page-title-row">
        <div>
          <h2>Дашборд безопасности</h2>
          <p>Общая картина событий, алертов, инцидентов и рисковых хостов</p>
        </div>
        <Link className="primary-button" to="/collection">Запустить сбор событий</Link>
      </div>

      <div className="cards cards-6">
        <div className="card accent"><span>Всего событий</span><strong>{data.total_events}</strong><small>записей в журнале</small></div>
        <div className="card"><span>Всего алертов</span><strong>{data.total_alerts}</strong><small>подозрительных сработок</small></div>
        <div className="card"><span>Инциденты</span><strong>{data.total_incidents}</strong><small>{data.open_incidents} открытых</small></div>
        <div className="card danger"><span>Критические алерты</span><strong>{data.critical_alerts}</strong><small>требуют внимания</small></div>
        <div className="card warn"><span>Высокий риск</span><strong>{data.high_alerts}</strong><small>алерты high</small></div>
        <div className="card"><span>Средний риск</span><strong>{data.avg_risk.toFixed(3)}</strong><small>по всем событиям</small></div>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <h3>События по типам</h3>
          <BarList items={data.events_by_type} />
        </section>

        <section className="panel">
          <h3>Алерты по критичности</h3>
          <BarList items={data.alerts_by_severity} labelMap={severityLabels} />
        </section>

        <section className="panel">
          <h3>Рисковые хосты</h3>
          <div className="mini-list">
            {data.top_hosts.length === 0 && <p className="muted">Данных пока нет</p>}
            {data.top_hosts.map((host) => (
              <div className="mini-row" key={host.host}>
                <div>
                  <strong>{host.host}</strong>
                  <span>{host.count} событий</span>
                </div>
                <span className="risk-pill">{host.max_risk.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <h3>Статусы инцидентов</h3>
          <BarList items={data.incidents_by_status} labelMap={{ open: "Открытые", closed: "Закрытые", investigating: "В расследовании" }} />
        </section>
      </div>

      <div className="details-grid three">
        <section className="panel">
          <h3>Последние инциденты</h3>
          <div className="stack-list">
            {data.latest_incidents.length === 0 && <p className="muted">Инцидентов пока нет</p>}
            {data.latest_incidents.map((incident) => (
              <Link className="compact-card" to={`/incidents/${incident.id}`} key={incident.id}>
                <span className={`badge ${incident.severity}`}>{severityLabels[incident.severity] ?? incident.severity}</span>
                <strong>{incident.title}</strong>
                <small>{incident.affected_host ?? "хост не указан"} · {incident.status}</small>
              </Link>
            ))}
          </div>
        </section>

        <section className="panel">
          <h3>Последние алерты</h3>
          <div className="stack-list">
            {data.latest_alerts.length === 0 && <p className="muted">Алертов пока нет</p>}
            {data.latest_alerts.map((alert) => (
              <Link className="compact-card" to={`/alerts/${alert.id}`} key={alert.id}>
                <span className={`badge ${alert.severity}`}>{severityLabels[alert.severity] ?? alert.severity}</span>
                <strong>{alert.title}</strong>
                <small>{alert.event?.host ?? "хост не указан"} · риск {alert.event?.risk_score.toFixed(3) ?? "-"}</small>
              </Link>
            ))}
          </div>
        </section>

        <section className="panel">
          <h3>Последние события</h3>
          <div className="stack-list">
            {data.latest_events.length === 0 && <p className="muted">Событий пока нет</p>}
            {data.latest_events.map((event) => (
              <div className="compact-card" key={event.id}>
                <span className="small-label">{event.event_type}</span>
                <strong>{event.host}</strong>
                <small>{event.message}</small>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
