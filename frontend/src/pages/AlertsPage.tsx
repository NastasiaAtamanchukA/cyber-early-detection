import { useEffect, useState } from "react";
import { getAlert, getAlerts } from "../api/client";
import { DetailModal } from "../components/DetailModal";
import { JsonBlock } from "../components/JsonBlock";
import { Pagination } from "../components/Pagination";
import type { AlertDetails, AlertFilters, AlertItem, PaginatedResponse } from "../types";

const severityLabels: Record<string, string> = { low: "Низкий", medium: "Средний", high: "Высокий", critical: "Критический" };
const statusLabels: Record<string, string> = { new: "Новый", open: "Новый", investigating: "В работе", closed: "Закрыт" };
const initialFilters: AlertFilters = { page: 1, page_size: 10, search: "", host: "", status: "", severity: "" };

function normalizedStatus(status: string) {
  return status === "open" ? "new" : status;
}

function statusClass(status: string) {
  return `status-pill status-${normalizedStatus(status)}`;
}

export function AlertsPage() {
  const [filters, setFilters] = useState<AlertFilters>(initialFilters);
  const [data, setData] = useState<PaginatedResponse<AlertItem> | null>(null);
  const [selected, setSelected] = useState<AlertDetails | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load(nextFilters = filters) {
    getAlerts(nextFilters).then(setData).catch((err) => setError(err.message));
  }

  useEffect(() => {
    load(filters);
  }, [filters.page]);

  function applyFilters() {
    const next = { ...filters, page: 1 };
    setFilters(next);
    load(next);
  }

  function resetFilters() {
    setFilters(initialFilters);
    load(initialFilters);
  }

  async function openDetails(item: AlertItem) {
    setError(null);
    try {
      setSelected(await getAlert(item.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось открыть алерт");
    }
  }

  return (
    <>
      <header className="page-header"><div><p>Prioritized alerts</p><h1>Алерты</h1></div></header>
      {error && <div className="panel error-panel">{error}</div>}

      <section className="panel filters-panel">
        <label>Поиск<input value={filters.search as string} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="заголовок, описание" /></label>
        <label>Хост<input value={filters.host as string} onChange={(e) => setFilters({ ...filters, host: e.target.value })} placeholder="api-gateway" /></label>
        <label>Критичность<select value={filters.severity as string} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}><option value="">Все</option><option value="low">low</option><option value="medium">medium</option><option value="high">high</option><option value="critical">critical</option></select></label>
        <label>Статус<select value={filters.status as string} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><option value="">Все</option><option value="new">new</option><option value="open">open</option><option value="investigating">investigating</option><option value="closed">closed</option></select></label>
        <div className="filter-actions"><button className="primary-button" onClick={applyFilters}>Применить</button><button className="secondary-button" onClick={resetFilters}>Сбросить</button></div>
      </section>

      <div className="alert-list-grid">
        {data?.items.map((alert) => (
          <article className={`panel alert-row-card ${alert.severity} clickable-card`} key={alert.id} onClick={() => openDetails(alert)}>
            <div className="alert-row-main">
              <div className="alert-row-header">
                <span className={`severity-pill ${alert.severity}`}>{severityLabels[alert.severity] ?? alert.severity}</span>
                <span className={statusClass(alert.status)}>{statusLabels[alert.status] ?? alert.status}</span>
              </div>
              <h3>{alert.title}</h3>
              <p>{alert.description}</p>
            </div>
            <div className="alert-row-side">
              <span>event #{alert.event_id}</span>
              <span>{alert.incident_id ? `incident #${alert.incident_id}` : "без incident"}</span>
              <small>{new Date(alert.created_at).toLocaleString()}</small>
            </div>
          </article>
        ))}
      </div>
      {data?.items.length === 0 && <div className="panel empty-state">Алерты не найдены</div>}
      <Pagination data={data} onPageChange={(page) => setFilters({ ...filters, page })} />

      {selected && (
        <DetailModal title={`Алерт #${selected.id}`} subtitle={selected.title} onClose={() => setSelected(null)}>
          <div className="details-grid">
            <div><span>Критичность</span><strong>{selected.severity}</strong></div>
            <div><span>Статус</span><strong>{statusLabels[selected.status] ?? selected.status}</strong></div>
            <div><span>Event</span><strong>#{selected.event_id}</strong></div>
            <div><span>Incident</span><strong>{selected.incident_id ? `#${selected.incident_id}` : "—"}</strong></div>
            <div><span>Создан</span><strong>{new Date(selected.created_at).toLocaleString()}</strong></div>
          </div>
          <h3>Описание</h3><p className="detail-text">{selected.description}</p>
          {selected.event && (<><h3>Связанное событие</h3><JsonBlock value={selected.event} /></>)}
        </DetailModal>
      )}
    </>
  );
}
