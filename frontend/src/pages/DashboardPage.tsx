import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { getDashboard } from "../api/client";
import type { DashboardData, HostStatItem, StatItem, TimelineItem } from "../types";

const severityLabels: Record<string, string> = {
  low: "Низкие",
  medium: "Средние",
  high: "Высокие",
  critical: "Критические",
};

const statusLabels: Record<string, string> = {
  new: "Новые",
  open: "Новые",
  investigating: "В работе",
  closed: "Закрытые",
};

function countOf(items: StatItem[], name: string) {
  return items.find((item) => item.name === name)?.count ?? 0;
}

function statusClass(status: string) {
  return `status-pill status-${status === "open" ? "new" : status}`;
}

function DonutChart({ items }: { items: StatItem[] }) {
  const rawTotal = items.reduce((sum, item) => sum + item.count, 0);
  const total = Math.max(1, rawTotal);
  const critical = countOf(items, "critical");
  const high = countOf(items, "high");
  const medium = countOf(items, "medium");
  const low = countOf(items, "low");
  const criticalPct = Math.round((critical / total) * 100);
  const highPct = Math.round((high / total) * 100);
  const mediumPct = Math.round((medium / total) * 100);

  return (
    <div className="donut-widget">
      <div className="donut-widget-visual">
        <div
          className="donut"
          style={{
            background: `conic-gradient(#ef4444 0 ${criticalPct}%, #f97316 ${criticalPct}% ${criticalPct + highPct}%, #eab308 ${criticalPct + highPct}% ${criticalPct + highPct + mediumPct}%, #22c55e ${criticalPct + highPct + mediumPct}% 100%)`,
          }}
        >
          <div>
            <strong>{rawTotal}</strong>
            <span>алертов</span>
          </div>
        </div>
      </div>
      <div className="donut-widget-meta">
        <div className="chart-legend">
          <span><i className="legend-dot critical-dot" /> critical: {critical}</span>
          <span><i className="legend-dot high-dot" /> high: {high}</span>
          <span><i className="legend-dot medium-dot" /> medium: {medium}</span>
          <span><i className="legend-dot low-dot" /> low: {low}</span>
        </div>
      </div>
    </div>
  );
}

function TimelineLineChart({ items }: { items: TimelineItem[] }) {
  const normalized = items.length
    ? items.slice(-8)
    : [{ label: "—", count: 0, max_risk: 0 }];
  const width = 620;
  const height = 220;
  const padding = 26;
  const maxValue = Math.max(...normalized.map((item) => item.count), 1);
  const stepX = normalized.length > 1 ? (width - padding * 2) / (normalized.length - 1) : 0;

  const points = normalized.map((item, index) => {
    const x = padding + index * stepX;
    const y = height - padding - (item.count / maxValue) * (height - padding * 2);
    return { ...item, x, y };
  });

  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  const area = [
    `${padding},${height - padding}`,
    ...points.map((point) => `${point.x},${point.y}`),
    `${padding + stepX * (points.length - 1)},${height - padding}`,
  ].join(" ");

  return (
    <div className="line-chart-widget">
      <div className="line-chart-head">
        <strong>{normalized.reduce((sum, item) => sum + item.count, 0)}</strong>
        <span>событий на последних точках таймлайна</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="line-chart-svg" role="img" aria-label="Динамика событий">
        <defs>
          <linearGradient id="lineAreaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(37, 99, 235, 0.28)" />
            <stop offset="100%" stopColor="rgba(37, 99, 235, 0.03)" />
          </linearGradient>
          <linearGradient id="lineStrokeGradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#2563eb" />
            <stop offset="100%" stopColor="#0ea5e9" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3].map((line) => {
          const y = padding + ((height - padding * 2) / 3) * line;
          return <line key={line} x1={padding} x2={width - padding} y1={y} y2={y} className="line-grid" />;
        })}
        <polygon points={area} fill="url(#lineAreaGradient)" />
        <polyline points={polyline} fill="none" stroke="url(#lineStrokeGradient)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
        {points.map((point) => (
          <g key={`${point.label}-${point.x}`}>
            <circle cx={point.x} cy={point.y} r="5" className={point.max_risk >= 0.75 ? "line-point danger" : "line-point"} />
            <text x={point.x} y={height - 8} textAnchor="middle" className="line-label">{point.label}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function Bars({ items }: { items: StatItem[] }) {
  const max = Math.max(...items.map((item) => item.count), 1);
  return (
    <div className="type-bars">
      {items.length === 0 && <div className="empty-state">Данных пока нет</div>}
      {items.map((item) => (
        <div className="type-bar-row" key={item.name}>
          <span>{statusLabels[item.name] ?? item.name}</span>
          <div><b style={{ width: `${Math.max(4, (item.count / max) * 100)}%` }} /></div>
          <strong>{item.count}</strong>
        </div>
      ))}
    </div>
  );
}

function HostList({ items }: { items: HostStatItem[] }) {
  const [page, setPage] = useState(1);
  const pageSize = 3;
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  const safePage = Math.min(page, pages);
  const visible = items.slice((safePage - 1) * pageSize, safePage * pageSize);

  return (
    <div className="host-widget">
      <div className="host-list dashboard-hosts compact-hosts">
        {visible.length === 0 && <div className="empty-state">Рисковые хосты пока не выявлены</div>}
        {visible.map((host) => (
          <div className="host-card" key={host.host}>
            <strong>{host.host}</strong>
            <span>{host.event_count} событий · {host.alert_count} алертов</span>
            <em>max risk: {host.max_risk.toFixed(3)}</em>
          </div>
        ))}
      </div>
      {items.length > pageSize && (
        <div className="mini-pagination">
          <button className="secondary-button" type="button" disabled={safePage === 1} onClick={() => setPage(safePage - 1)}>Назад</button>
          <span>{safePage} / {pages}</span>
          <button className="secondary-button" type="button" disabled={safePage === pages} onClick={() => setPage(safePage + 1)}>Вперёд</button>
        </div>
      )}
    </div>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard().then(setData).catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="panel error-panel">{error}</div>;
  if (!data) return <div className="panel">Загружаю дашборд...</div>;

  return (
    <>
      <header className="hero-header">
        <div>
          <p>Security Operations Dashboard</p>
          <h1>Дашборд безопасности</h1>
          <span>Общая картина событий, алертов, инцидентов и рисковых хостов</span>
        </div>
        <Link className="primary-button hero-action" to="/collectors">Запустить сбор событий</Link>
      </header>

      <section className="stats-grid kpi-grid">
        <div className="stat-card accent clean"><span>Всего событий</span><strong>{data.events_total}</strong><small>записей в журнале</small></div>
        <div className="stat-card clean"><span>Всего алертов</span><strong>{data.alerts_total}</strong><small>подозрительных сработок</small></div>
        <div className="stat-card clean"><span>Инциденты</span><strong>{data.incidents_total}</strong><small>расследования</small></div>
        <div className="stat-card danger-soft clean"><span>Критические алерты</span><strong>{data.critical_alerts}</strong><small>требуют внимания</small></div>
        <div className="stat-card warning-soft clean"><span>Высокий риск</span><strong>{data.high_risk_events}</strong><small>события risk ≥ 0.75</small></div>
        <div className="stat-card clean"><span>Средний риск</span><strong>{data.average_risk.toFixed(3)}</strong><small>по всем событиям</small></div>
      </section>

      <section className="dashboard-layout refined">
        <div className="panel chart-panel chart-donut">
          <h3>Алерты по критичности</h3>
          <DonutChart items={data.alerts_by_severity} />
        </div>
        <div className="panel chart-panel chart-line">
          <h3>Динамика событий</h3>
          <TimelineLineChart items={data.events_timeline} />
        </div>
        <div className="panel">
          <h3>События по типам</h3>
          <Bars items={data.events_by_type} />
        </div>
        <div className="panel">
          <h3>Статусы инцидентов</h3>
          <Bars items={data.incidents_by_status} />
        </div>
        <div className="panel">
          <h3>Рисковые хосты</h3>
          <HostList items={data.top_hosts} />
        </div>
      </section>

      <section className="dashboard-bottom-grid">
        <div className="panel feed-panel">
          <h3>Последние инциденты</h3>
          {data.recent_incidents.map((incident) => (
            <Link className="feed-card" to="/incidents" key={incident.id}>
              <span className={`severity-pill ${incident.severity}`}>{severityLabels[incident.severity] ?? incident.severity}</span>
              <strong>{incident.title}</strong>
              <small>{incident.affected_host ?? "—"} · <span className={statusClass(incident.status)}>{statusLabels[incident.status] ?? incident.status}</span></small>
            </Link>
          ))}
          {data.recent_incidents.length === 0 && <div className="empty-state">Инцидентов пока нет</div>}
        </div>
        <div className="panel feed-panel">
          <h3>Последние алерты</h3>
          {data.recent_alerts.map((alert) => (
            <Link className="feed-card" to="/alerts" key={alert.id}>
              <span className={`severity-pill ${alert.severity}`}>{severityLabels[alert.severity] ?? alert.severity}</span>
              <strong>{alert.title}</strong>
              <small>event #{alert.event_id} · <span className={statusClass(alert.status)}>{statusLabels[alert.status] ?? alert.status}</span></small>
            </Link>
          ))}
          {data.recent_alerts.length === 0 && <div className="empty-state">Алертов пока нет</div>}
        </div>
        <div className="panel feed-panel">
          <h3>Последние события</h3>
          {data.recent_events.map((event) => (
            <Link className="feed-card" to="/events" key={event.id}>
              <span>{event.event_type}</span>
              <strong>{event.host}</strong>
              <small>{event.message}</small>
            </Link>
          ))}
          {data.recent_events.length === 0 && <div className="empty-state">Событий пока нет</div>}
        </div>
      </section>
    </>
  );
}
