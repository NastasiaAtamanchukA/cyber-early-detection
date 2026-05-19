import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { applyIncidentAction, getIncident } from "../api/client";
import type { IncidentAction, IncidentDetails } from "../types";

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

const actionLabels: Record<IncidentAction, string> = {
  take_in_work: "Взять в работу",
  close: "Закрыть",
  reopen: "Переоткрыть",
  escalate: "Повысить критичность",
  downgrade: "Понизить критичность",
};

export function IncidentDetailsPage() {
  const { id } = useParams();
  const [incident, setIncident] = useState<IncidentDetails | null>(null);
  const [actionLoading, setActionLoading] = useState<IncidentAction | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getIncident(id).then(setIncident).catch(console.error);
  }, [id]);

  async function runAction(action: IncidentAction) {
    if (!incident) return;
    setActionError(null);
    setActionLoading(action);
    try {
      const updated = await applyIncidentAction(incident.id, action);
      setIncident(updated);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Не удалось выполнить действие");
    } finally {
      setActionLoading(null);
    }
  }

  if (!incident) return <p>Загружаю карточку инцидента...</p>;

  return (
    <div>
      <Link className="back-link" to="/incidents">← Вернуться к инцидентам</Link>
      <div className="page-title page-title-row">
        <div>
          <h2>Карточка инцидента #{incident.id}</h2>
          <p>{incident.title}</p>
        </div>
        <div className="incident-actions">
          <button className="secondary-button" disabled={actionLoading !== null} onClick={() => runAction("take_in_work")}>{actionLoading === "take_in_work" ? "Выполняю..." : actionLabels.take_in_work}</button>
          <button className="secondary-button" disabled={actionLoading !== null} onClick={() => runAction("escalate")}>{actionLabels.escalate}</button>
          <button className="secondary-button" disabled={actionLoading !== null} onClick={() => runAction("downgrade")}>{actionLabels.downgrade}</button>
          {incident.status === "closed" ? (
            <button className="primary-button" disabled={actionLoading !== null} onClick={() => runAction("reopen")}>{actionLabels.reopen}</button>
          ) : (
            <button className="danger-button" disabled={actionLoading !== null} onClick={() => runAction("close")}>{actionLabels.close}</button>
          )}
        </div>
      </div>

      {actionError && <div className="error">Ошибка действия: {actionError}</div>}

      <div className="cards cards-4 compact-cards">
        <div className="card"><span>Статус</span><strong className="text-fit">{statusLabels[incident.status] ?? incident.status}</strong><small>текущее состояние</small></div>
        <div className="card"><span>Критичность</span><strong className="text-fit">{severityLabels[incident.severity] ?? incident.severity}</strong><small>уровень реагирования</small></div>
        <div className="card"><span>SLA реакции</span><strong className="text-fit">{incident.response_sla}</strong><small>рекомендуемый срок</small></div>
        <div className="card"><span>Связанные алерты</span><strong>{incident.alert_count}</strong><small>{incident.event_count} событий</small></div>
      </div>

      <div className="details-grid">
        <section className="panel detail-panel">
          <h3>Сводка расследования</h3>
          <p><strong>Критичность:</strong> <span className={`badge ${incident.severity}`}>{severityLabels[incident.severity] ?? incident.severity}</span></p>
          <p><strong>Статус:</strong> {statusLabels[incident.status] ?? incident.status}</p>
          <p><strong>Стадия атаки:</strong> {incident.attack_stage}</p>
          <p><strong>Описание:</strong> {incident.description}</p>
        </section>

        <section className="panel detail-panel">
          <h3>Затронутые объекты</h3>
          <p><strong>Хост:</strong> {incident.affected_host ?? "не указан"}</p>
          <p><strong>Пользователь:</strong> {incident.affected_user ?? "не указан"}</p>
          <p><strong>Количество событий:</strong> {incident.event_count}</p>
          <p><strong>Количество алертов:</strong> {incident.alert_count}</p>
        </section>

        <section className="panel detail-panel wide-panel">
          <h3>Логика обнаружения</h3>
          <p>{incident.detection_logic}</p>
        </section>

        <section className="panel detail-panel">
          <h3>Рекомендуемые действия аналитика</h3>
          <ol className="action-list">
            {incident.recommended_actions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ol>
        </section>

        <section className="panel detail-panel">
          <h3>Временная линия</h3>
          <div className="timeline-line">
            <div>
              <span>Первое событие</span>
              <strong>{new Date(incident.first_seen).toLocaleString()}</strong>
            </div>
            <div>
              <span>Последнее событие</span>
              <strong>{new Date(incident.last_seen).toLocaleString()}</strong>
            </div>
            <div>
              <span>Карточка обновлена</span>
              <strong>{new Date(incident.updated_at).toLocaleString()}</strong>
            </div>
          </div>
        </section>
      </div>

      <section className="panel result-panel">
        <h3>Связанные алерты</h3>
        <div className="event-card-list compact-list">
          {incident.related_alerts.length === 0 && <div className="empty-state">Связанных алертов нет</div>}
          {incident.related_alerts.map((alert) => (
            <article className="event-card" key={alert.id}>
              <div className="event-card-top">
                <div>
                  <span className={`badge ${alert.severity}`}>{severityLabels[alert.severity] ?? alert.severity}</span>
                  <h3>{alert.title}</h3>
                </div>
                <Link className="secondary-button" to={`/alerts/${alert.id}`}>Открыть</Link>
              </div>
              <p>{alert.description}</p>
              <dl className="meta-list horizontal">
                <div><dt>Статус</dt><dd>{statusLabels[alert.status] ?? alert.status}</dd></div>
                <div><dt>Хост</dt><dd>{alert.event?.host ?? "не указан"}</dd></div>
                <div><dt>Пользователь</dt><dd>{alert.event?.user ?? "не указан"}</dd></div>
                <div><dt>Тип события</dt><dd>{alert.event?.event_type ?? "не указан"}</dd></div>
                <div><dt>Риск</dt><dd>{alert.event ? alert.event.risk_score.toFixed(3) : "-"}</dd></div>
              </dl>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
