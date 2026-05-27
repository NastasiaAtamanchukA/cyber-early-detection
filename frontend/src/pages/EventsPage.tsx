import { useEffect, useState } from "react";
import { getEvent, getEvents } from "../api/client";
import { DetailModal } from "../components/DetailModal";
import { JsonBlock } from "../components/JsonBlock";
import { Pagination } from "../components/Pagination";
import type { EventDetails, EventFilters, EventItem, PaginatedResponse } from "../types";

const initialFilters: EventFilters = { page: 1, page_size: 10, search: "", host: "", user: "", event_type: "", only_anomalies: false };

export function EventsPage() {
  const [filters, setFilters] = useState<EventFilters>(initialFilters);
  const [data, setData] = useState<PaginatedResponse<EventItem> | null>(null);
  const [selected, setSelected] = useState<EventDetails | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load(nextFilters = filters) {
    getEvents(nextFilters).then(setData).catch((err) => setError(err.message));
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

  async function openDetails(item: EventItem) {
    setError(null);
    try {
      setSelected(await getEvent(item.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось открыть событие");
    }
  }

  return (
    <>
      <header className="page-header">
        <div>
          <p>Event stream</p>
          <h1>События безопасности</h1>
        </div>
      </header>

      {error && <div className="panel error-panel">{error}</div>}

      <section className="panel filters-panel">
        <label>Поиск<input value={filters.search as string} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="сообщение, тип, хост" /></label>
        <label>Тип события<input value={filters.event_type as string} onChange={(e) => setFilters({ ...filters, event_type: e.target.value })} placeholder="web_attack" /></label>
        <label>Хост<input value={filters.host as string} onChange={(e) => setFilters({ ...filters, host: e.target.value })} placeholder="web-01" /></label>
        <label>Пользователь<input value={filters.user as string} onChange={(e) => setFilters({ ...filters, user: e.target.value })} placeholder="admin" /></label>
        <label className="checkbox inline-checkbox"><input type="checkbox" checked={Boolean(filters.only_anomalies)} onChange={(e) => setFilters({ ...filters, only_anomalies: e.target.checked })} /> только аномалии</label>
        <div className="filter-actions"><button className="primary-button" onClick={applyFilters}>Применить</button><button className="secondary-button" onClick={resetFilters}>Сбросить</button></div>
      </section>

      <div className="panel table-panel">
        <table>
          <thead>
            <tr><th>ID</th><th>Время</th><th>Хост</th><th>Пользователь</th><th>Тип</th><th>Риск</th><th>Сообщение</th></tr>
          </thead>
          <tbody>
            {data?.items.map((event) => (
              <tr className="clickable-row" key={event.id} onClick={() => openDetails(event)}>
                <td>{event.id}</td>
                <td>{new Date(event.timestamp).toLocaleString()}</td>
                <td><strong>{event.host}</strong></td>
                <td>{event.user ?? "—"}</td>
                <td><span className="code-pill">{event.event_type}</span></td>
                <td><span className={event.risk_score >= 0.75 ? "risk high" : "risk"}>{event.risk_score.toFixed(3)}</span></td>
                <td>{event.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.items.length === 0 && <div className="empty-state">События не найдены</div>}
      </div>
      <Pagination data={data} onPageChange={(page) => setFilters({ ...filters, page })} />

      {selected && (
        <DetailModal title={`Событие #${selected.id}`} subtitle="Подробная карточка события" onClose={() => setSelected(null)}>
          <div className="details-grid">
            <div><span>Время</span><strong>{new Date(selected.timestamp).toLocaleString()}</strong></div>
            <div><span>Хост</span><strong>{selected.host}</strong></div>
            <div><span>Пользователь</span><strong>{selected.user ?? "—"}</strong></div>
            <div><span>Тип</span><strong>{selected.event_type}</strong></div>
            <div><span>Risk score</span><strong>{selected.risk_score.toFixed(3)}</strong></div>
            <div><span>Anomaly</span><strong>{selected.is_anomaly ? "Да" : "Нет"}</strong></div>
          </div>
          <h3>Сообщение</h3><p className="detail-text">{selected.message}</p>
          <h3>Нормализованные поля</h3><JsonBlock value={selected.normalized_log} />
          <h3>Raw log</h3><JsonBlock value={selected.raw_log} />
        </DetailModal>
      )}
    </>
  );
}
