import { useEffect, useState } from "react";

import { getCollectionSchedules, runCollectionSchedule } from "../api/client";
import type { CollectionSchedule, ScheduleRunResult } from "../types";

export function CollectionPage() {
  const [schedules, setSchedules] = useState<CollectionSchedule[]>([]);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [lastResult, setLastResult] = useState<ScheduleRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSchedules = () => {
    getCollectionSchedules().then(setSchedules).catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadSchedules();
  }, []);

  const runSchedule = async (id: number) => {
    setRunningId(id);
    setError(null);
    try {
      const result = await runCollectionSchedule(id);
      setLastResult(result);
      loadSchedules();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось запустить сбор");
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div>
      <div className="page-title">
        <h2>Сбор событий из веб-интерфейса</h2>
        <p>Несколько расписаний имитируют регулярный сбор логов из разных источников</p>
      </div>

      {error && <div className="error">Ошибка: {error}</div>}

      <div className="card-grid">
        {schedules.map((schedule) => (
          <article className="info-card" key={schedule.id}>
            <div className="card-header-row">
              <span className="small-label">{schedule.interval_label}</span>
              <span className={schedule.enabled ? "status-dot ok" : "status-dot muted-dot"} />
            </div>
            <h3>{schedule.name}</h3>
            <p>{schedule.description}</p>
            <dl className="meta-list">
              <div><dt>Источник</dt><dd>{schedule.source_name}</dd></div>
              <div><dt>Профиль</dt><dd>{schedule.event_profile}</dd></div>
              <div><dt>Пачка</dt><dd>{schedule.batch_size} событий</dd></div>
              <div><dt>Последний запуск</dt><dd>{schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString() : "еще не запускалось"}</dd></div>
            </dl>
            <button className="primary-button full" disabled={runningId === schedule.id} onClick={() => runSchedule(schedule.id)}>
              {runningId === schedule.id ? "Собираю события..." : "Запустить сейчас"}
            </button>
          </article>
        ))}
      </div>

      {lastResult && (
        <section className="panel result-panel">
          <h3>Результат последнего запуска</h3>
          <div className="cards cards-3 compact-cards">
            <div className="card"><span>Создано событий</span><strong>{lastResult.run.events_created}</strong></div>
            <div className="card"><span>Создано алертов</span><strong>{lastResult.run.alerts_created}</strong></div>
            <div className="card"><span>Создано инцидентов</span><strong>{lastResult.run.incidents_created}</strong></div>
          </div>
          <h4>События из пачки</h4>
          <div className="stack-list">
            {lastResult.events.slice(0, 8).map((event) => (
              <div className="compact-card" key={event.id}>
                <span className="small-label">{event.event_type}</span>
                <strong>{event.host} · риск {event.risk_score.toFixed(3)}</strong>
                <small>{event.message}</small>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
