import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getAlert } from "../api/client";
import type { AlertItem } from "../types";

const severityLabels: Record<string, string> = {
  critical: "критический",
  high: "высокий",
  medium: "средний",
  low: "низкий",
};

export function AlertDetailsPage() {
  const { id } = useParams();
  const [alert, setAlert] = useState<AlertItem | null>(null);

  useEffect(() => {
    if (!id) return;
    getAlert(id).then(setAlert).catch(console.error);
  }, [id]);

  if (!alert) return <p>Загружаю карточку алерта...</p>;

  return (
    <div>
      <Link className="back-link" to="/alerts">← Вернуться к алертам</Link>
      <div className="page-title">
        <h2>Карточка алерта #{alert.id}</h2>
        <p>{alert.title}</p>
      </div>

      <div className="details-grid">
        <section className="panel detail-panel">
          <h3>Основная информация</h3>
          <p><strong>Критичность:</strong> <span className={`badge ${alert.severity}`}>{severityLabels[alert.severity] ?? alert.severity}</span></p>
          <p><strong>Статус:</strong> {alert.status}</p>
          <p><strong>Описание:</strong> {alert.description}</p>
          <p><strong>Создан:</strong> {new Date(alert.created_at).toLocaleString()}</p>
          <p><strong>Обновлен:</strong> {new Date(alert.updated_at).toLocaleString()}</p>
        </section>

        {alert.event && (
          <section className="panel detail-panel">
            <h3>Связанное событие</h3>
            <p><strong>Хост:</strong> {alert.event.host}</p>
            <p><strong>Пользователь:</strong> {alert.event.user ?? "не указан"}</p>
            <p><strong>Тип:</strong> {alert.event.event_type}</p>
            <p><strong>Источник:</strong> {alert.event.source_name ?? "не указан"}</p>
            <p><strong>Риск:</strong> {alert.event.risk_score.toFixed(3)}</p>
            <p><strong>Оценка аномальности:</strong> {alert.event.anomaly_score.toFixed(3)}</p>
            <p><strong>Сообщение:</strong> {alert.event.message}</p>
          </section>
        )}

        {alert.incident && (
          <section className="panel detail-panel wide-panel">
            <h3>Связанный инцидент</h3>
            <p><strong>Название:</strong> {alert.incident.title}</p>
            <p><strong>Затронутый хост:</strong> {alert.incident.affected_host ?? "не указан"}</p>
            <p><strong>Затронутый пользователь:</strong> {alert.incident.affected_user ?? "не указан"}</p>
            <p><strong>Событий:</strong> {alert.incident.event_count}</p>
            <p><strong>Алертов:</strong> {alert.incident.alert_count}</p>
            <Link className="secondary-button" to={`/incidents/${alert.incident.id}`}>Открыть инцидент</Link>
          </section>
        )}
      </div>
    </div>
  );
}
