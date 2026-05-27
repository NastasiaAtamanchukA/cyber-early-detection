import { useEffect, useState } from "react";
import { closeIncident, getIncident, getIncidents, reopenIncident, takeIncident } from "../api/client";
import { DetailModal } from "../components/DetailModal";
import { Pagination } from "../components/Pagination";
import type { IncidentDetails, IncidentFilters, IncidentItem, PaginatedResponse } from "../types";

const severityLabels: Record<string, string> = { low: "Низкий", medium: "Средний", high: "Высокий", critical: "Критический" };
const statusLabels: Record<string, string> = { new: "Новый", open: "Новый", investigating: "В работе", closed: "Закрыт" };
const initialFilters: IncidentFilters = { page: 1, page_size: 10, search: "", host: "", status: "", severity: "" };

const responseActions = [
  "Изолировать хост",
  "Заблокировать УЗ",
  "Запросить логи",
  "Создать задачу SOC",
  "Отправить уведомление администратору",
];

function normalizedStatus(status: string) {
  return status === "open" ? "new" : status;
}

function statusClass(status: string) {
  return `status-pill status-${normalizedStatus(status)}`;
}

export function IncidentsPage() {
  const [filters, setFilters] = useState<IncidentFilters>(initialFilters);
  const [data, setData] = useState<PaginatedResponse<IncidentItem> | null>(null);
  const [selected, setSelected] = useState<IncidentDetails | null>(null);
  const [busyAction, setBusyAction] = useState(false);
  const [responseLog, setResponseLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  function load(nextFilters = filters) {
    getIncidents(nextFilters).then(setData).catch((err) => setError(err.message));
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

  async function openDetails(item: IncidentItem) {
    setError(null);
    setResponseLog([]);
    try {
      setSelected(await getIncident(item.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось открыть инцидент");
    }
  }

  async function runAction(action: "take" | "close" | "reopen") {
    if (!selected) return;
    setBusyAction(true);
    setError(null);
    try {
      const updated = action === "take"
        ? await takeIncident(selected.id)
        : action === "close"
          ? await closeIncident(selected.id)
          : await reopenIncident(selected.id);
      setSelected(updated);
      setResponseLog([]);
      load(filters);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось изменить статус инцидента");
    } finally {
      setBusyAction(false);
    }
  }

  function addResponseAction(action: string) {
    const time = new Date().toLocaleTimeString();
    setResponseLog((items) => [`${time} — ${action}: действие добавлено в план реагирования`, ...items]);
  }

  const selectedStatus = selected ? normalizedStatus(selected.status) : "";

  return (
    <>
      <header className="page-header"><div><p>Investigation queue</p><h1>Инциденты и рекомендации</h1></div></header>
      {error && <div className="panel error-panel">{error}</div>}

      <section className="panel filters-panel">
        <label>Поиск<input value={filters.search as string} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="название, описание" /></label>
        <label>Хост<input value={filters.host as string} onChange={(e) => setFilters({ ...filters, host: e.target.value })} placeholder="web-01" /></label>
        <label>Критичность<select value={filters.severity as string} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}><option value="">Все</option><option value="medium">medium</option><option value="high">high</option><option value="critical">critical</option></select></label>
        <label>Статус<select value={filters.status as string} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><option value="">Все</option><option value="new">new</option><option value="investigating">investigating</option><option value="closed">closed</option></select></label>
        <div className="filter-actions"><button className="primary-button" onClick={applyFilters}>Применить</button><button className="secondary-button" onClick={resetFilters}>Сбросить</button></div>
      </section>

      <div className="incident-list">
        {data?.items.map((incident) => (
          <section className="panel incident-card clickable-card" key={incident.id} onClick={() => openDetails(incident)}>
            <div className="incident-head">
              <div>
                <span className={`severity-pill ${incident.severity}`}>{severityLabels[incident.severity] ?? incident.severity}</span>
                <h3>{incident.title}</h3>
              </div>
              <span className={statusClass(incident.status)}>{statusLabels[incident.status] ?? incident.status}</span>
            </div>
            <p>{incident.description}</p>
            <div className="incident-meta"><span>Хост: {incident.affected_host ?? "—"}</span><span>Пользователь: {incident.affected_user ?? "—"}</span><span>Алертов: {incident.recommended_actions.length ? "есть" : "—"}</span></div>
            <h4>Ключевые рекомендации</h4>
            <ol className="recommendations compact-list">
              {incident.recommended_actions.slice(0, 3).map((action) => <li key={action}>{action}</li>)}
            </ol>
          </section>
        ))}
      </div>
      {data?.items.length === 0 && <div className="panel empty-state">Инциденты не найдены</div>}
      <Pagination data={data} onPageChange={(page) => setFilters({ ...filters, page })} />

      {selected && (
        <DetailModal
          title={`Инцидент #${selected.id}`}
          subtitle={selected.title}
          onClose={() => setSelected(null)}
          footer={
            <div className="modal-actions">
              {selectedStatus === "new" && <button disabled={busyAction} className="primary-button" onClick={() => runAction("take")}>Взять в работу</button>}
              {selectedStatus === "investigating" && <button disabled={busyAction} className="danger-button" onClick={() => runAction("close")}>Закрыть</button>}
              {selectedStatus === "closed" && <button disabled={busyAction} className="primary-button" onClick={() => runAction("reopen")}>Переоткрыть</button>}
            </div>
          }
        >
          <div className="details-grid">
            <div><span>Критичность</span><strong>{selected.severity}</strong></div>
            <div><span>Статус</span><strong>{statusLabels[selected.status] ?? selected.status}</strong></div>
            <div><span>Хост</span><strong>{selected.affected_host ?? "—"}</strong></div>
            <div><span>Пользователь</span><strong>{selected.affected_user ?? "—"}</strong></div>
            <div><span>Первое событие</span><strong>{new Date(selected.first_seen).toLocaleString()}</strong></div>
            <div><span>Последнее событие</span><strong>{new Date(selected.last_seen).toLocaleString()}</strong></div>
          </div>
          <h3>Описание</h3><p className="detail-text">{selected.description}</p>

          {selectedStatus === "investigating" && (
            <section className="response-actions-panel">
              <h3>Быстрое реагирование</h3>
              <p>Кнопки доступны только для инцидента, который взят в работу.</p>
              <div className="response-actions-grid">
                {responseActions.map((action) => (
                  <button className="secondary-button response-action-button" type="button" key={action} onClick={() => addResponseAction(action)}>
                    {action}
                  </button>
                ))}
              </div>
              {responseLog.length > 0 && (
                <div className="response-log">
                  {responseLog.map((item) => <span key={item}>{item}</span>)}
                </div>
              )}
            </section>
          )}

          <h3>Связанные алерты</h3>
          <div className="nested-list">
            {selected.alerts.map((alert) => <div key={alert.id}><strong>#{alert.id} {alert.title}</strong><span>{alert.severity} · {statusLabels[alert.status] ?? alert.status} · event #{alert.event_id}</span></div>)}
            {selected.alerts.length === 0 && <div className="empty-state">Связанных алертов нет</div>}
          </div>
          <h3>Подробные рекомендации по действиям</h3>
          <ol className="recommendations detailed">
            {selected.recommended_actions.map((action) => <li key={action}>{action}</li>)}
          </ol>
        </DetailModal>
      )}
    </>
  );
}
