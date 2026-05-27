import { useEffect, useState } from "react";
import type { FormEvent, MouseEvent } from "react";
import { createCollectionSchedule, getCollectionSchedules, runCollectionSchedule, updateCollectionSchedule } from "../api/client";
import { DetailModal } from "../components/DetailModal";
import { Pagination } from "../components/Pagination";
import type { CollectionSchedule, CollectionSchedulePayload, PaginatedResponse, ScheduleFilters, ScheduleRunResult } from "../types";

const emptyForm: CollectionSchedulePayload = {
  code: "",
  name: "",
  description: "",
  interval_label: "каждые 10 минут",
  source_name: "custom-web-schedule",
  source_kind: "web-schedule",
  event_profile: "mixed",
  batch_size: 10,
  enabled: true,
};

const initialFilters: ScheduleFilters = { page: 1, page_size: 10, search: "", enabled: "", event_profile: "" };

export function CollectionPage() {
  const [filters, setFilters] = useState<ScheduleFilters>(initialFilters);
  const [data, setData] = useState<PaginatedResponse<CollectionSchedule> | null>(null);
  const [form, setForm] = useState<CollectionSchedulePayload>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selected, setSelected] = useState<CollectionSchedule | null>(null);
  const [saving, setSaving] = useState(false);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [lastRun, setLastRun] = useState<ScheduleRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load(nextFilters = filters) {
    getCollectionSchedules(nextFilters).then(setData).catch((err) => setError(err.message));
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

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setIsFormOpen(true);
  }

  function startEdit(schedule: CollectionSchedule, event?: MouseEvent) {
    event?.stopPropagation();
    setEditingId(schedule.id);
    setForm({
      code: schedule.code,
      name: schedule.name,
      description: schedule.description,
      interval_label: schedule.interval_label,
      source_name: schedule.source_name,
      source_kind: schedule.source_kind,
      event_profile: schedule.event_profile as CollectionSchedulePayload["event_profile"],
      batch_size: schedule.batch_size,
      enabled: schedule.enabled,
    });
    setIsFormOpen(true);
  }

  function closeForm() {
    setIsFormOpen(false);
    setEditingId(null);
    setForm(emptyForm);
  }

  async function submitSchedule(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (editingId) await updateCollectionSchedule(editingId, form);
      else await createCollectionSchedule(form);
      closeForm();
      load(filters);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить расписание");
    } finally {
      setSaving(false);
    }
  }

  async function runSchedule(id: number, event?: MouseEvent) {
    event?.stopPropagation();
    setRunningId(id);
    setError(null);
    try {
      const result = await runCollectionSchedule(id);
      setLastRun(result);
      load(filters);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось запустить расписание");
    } finally {
      setRunningId(null);
    }
  }

  async function toggleSchedule(schedule: CollectionSchedule, event?: MouseEvent) {
    event?.stopPropagation();
    setError(null);
    try {
      await updateCollectionSchedule(schedule.id, { enabled: !schedule.enabled });
      load(filters);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось изменить статус расписания");
    }
  }

  return (
    <>
      <header className="page-header">
        <div><p>Collection schedules</p><h1>Расписания сбора событий</h1></div>
        <button className="primary-button" onClick={openCreate}>Добавить расписание</button>
      </header>

      {error && <div className="panel error-panel">{error}</div>}
      {lastRun && <div className="panel success-panel">{lastRun.message}. Run #{lastRun.run_id}</div>}

      <section className="panel filters-panel">
        <label>Поиск<input value={filters.search as string} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="название, code, источник" /></label>
        <label>Профиль<select value={filters.event_profile as string} onChange={(e) => setFilters({ ...filters, event_profile: e.target.value })}><option value="">Все</option><option value="auth">auth</option><option value="web">web</option><option value="privileged">privileged</option><option value="database">database</option><option value="mixed">mixed</option></select></label>
        <label>Статус<select value={String(filters.enabled)} onChange={(e) => setFilters({ ...filters, enabled: e.target.value === "" ? "" : e.target.value === "true" })}><option value="">Все</option><option value="true">Включено</option><option value="false">Отключено</option></select></label>
        <div className="filter-actions"><button className="primary-button" onClick={applyFilters}>Применить</button><button className="secondary-button" onClick={resetFilters}>Сбросить</button></div>
      </section>

      <div className="schedule-grid">
        {data?.items.map((schedule) => (
          <article className="panel schedule-card clickable-card" key={schedule.id} onClick={() => setSelected(schedule)}>
            <div className="schedule-head"><div><span className="code-pill">{schedule.code}</span><h3>{schedule.name}</h3></div><span className={schedule.enabled ? "enabled-pill" : "disabled-pill"}>{schedule.enabled ? "Включено" : "Отключено"}</span></div>
            <p>{schedule.description}</p>
            <div className="schedule-meta"><span>{schedule.interval_label}</span><span>{schedule.source_name}</span><span>{schedule.event_profile}</span><span>{schedule.batch_size} событий</span></div>
            <div className="schedule-actions">
              <button className="primary-button" disabled={runningId === schedule.id || !schedule.enabled} onClick={(event) => runSchedule(schedule.id, event)}>{runningId === schedule.id ? "Собираю события..." : "Запустить сейчас"}</button>
              <button className="secondary-button" onClick={(event) => startEdit(schedule, event)}>Редактировать</button>
              <button className="secondary-button" onClick={(event) => toggleSchedule(schedule, event)}>{schedule.enabled ? "Отключить" : "Включить"}</button>
            </div>
          </article>
        ))}
      </div>
      {data?.items.length === 0 && <div className="panel empty-state">Расписания не найдены</div>}
      <Pagination data={data} onPageChange={(page) => setFilters({ ...filters, page })} />

      {isFormOpen && (
        <DetailModal title={editingId ? "Редактировать расписание" : "Добавить расписание"} subtitle="Пользовательское расписание сбора событий" onClose={closeForm}>
          <form className="schedule-form modal-form" onSubmit={submitSchedule}>
            <label>Code<input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="custom-auth-10-min" required /></label>
            <label>Название<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Проверка авторизаций" required /></label>
            <label>Интервал<input value={form.interval_label} onChange={(e) => setForm({ ...form, interval_label: e.target.value })} placeholder="каждые 10 минут" required /></label>
            <label>Источник<input value={form.source_name} onChange={(e) => setForm({ ...form, source_name: e.target.value })} placeholder="custom-auth-schedule" required /></label>
            <label>Тип источника<input value={form.source_kind} onChange={(e) => setForm({ ...form, source_kind: e.target.value })} placeholder="web-schedule" required /></label>
            <label>Профиль событий<select value={form.event_profile} onChange={(e) => setForm({ ...form, event_profile: e.target.value as CollectionSchedulePayload["event_profile"] })}><option value="mixed">Смешанный</option><option value="auth">Аутентификация</option><option value="web">Веб-журналы</option><option value="privileged">Привилегии</option><option value="database">База данных</option></select></label>
            <label>Размер пачки<input type="number" min={1} max={100} value={form.batch_size} onChange={(e) => setForm({ ...form, batch_size: Number(e.target.value) })} /></label>
            <label className="checkbox schedule-checkbox"><input type="checkbox" checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} /> Расписание включено</label>
            <label className="schedule-description">Описание<textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Что именно имитирует это расписание" required /></label>
            <div className="form-actions"><button className="primary-button" type="submit" disabled={saving}>{saving ? "Сохраняю..." : "Сохранить"}</button><button className="secondary-button" type="button" onClick={closeForm}>Отмена</button></div>
          </form>
        </DetailModal>
      )}

      {selected && (
        <DetailModal title={selected.name} subtitle={`Расписание #${selected.id}`} onClose={() => setSelected(null)}>
          <div className="details-grid">
            <div><span>Code</span><strong>{selected.code}</strong></div>
            <div><span>Статус</span><strong>{selected.enabled ? "Включено" : "Отключено"}</strong></div>
            <div><span>Интервал</span><strong>{selected.interval_label}</strong></div>
            <div><span>Профиль</span><strong>{selected.event_profile}</strong></div>
            <div><span>Источник</span><strong>{selected.source_name}</strong></div>
            <div><span>Размер пачки</span><strong>{selected.batch_size}</strong></div>
          </div>
          <h3>Описание</h3><p className="detail-text">{selected.description}</p>
          <div className="modal-actions"><button className="primary-button" disabled={runningId === selected.id || !selected.enabled} onClick={(event) => runSchedule(selected.id, event)}>{runningId === selected.id ? "Запускаю..." : "Запустить сейчас"}</button><button className="secondary-button" onClick={(event) => startEdit(selected, event)}>Редактировать</button></div>
        </DetailModal>
      )}
    </>
  );
}
