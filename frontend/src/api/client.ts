import type {
  AlertItem,
  CollectionSchedule,
  DashboardData,
  EventItem,
  IncidentAction,
  IncidentDetails,
  IncidentItem,
  ScheduleRunResult,
} from "../types";

const isDirectFrontendPort =
  window.location.port === "3000" ||
  window.location.port === "5173";

const API_BASE =
  import.meta.env.VITE_API_URL ||
  (isDirectFrontendPort
    ? `${window.location.protocol}//${window.location.hostname}:8000/api/v1`
    : "/api/v1");

function buildQuery(params?: Record<string, string | number | boolean | null | undefined>) {
  if (!params) return "";

  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });

  const query = search.toString();
  return query ? `?${query}` : "";
}

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Ошибка API ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const getDashboard = () => api<DashboardData>("/dashboard");

export const getEvents = (params?: Record<string, string | number | boolean | null | undefined>) =>
  api<EventItem[]>(`/events${buildQuery({ limit: 500, ...params })}`);

export const getAlerts = (params?: Record<string, string | number | boolean | null | undefined>) =>
  api<AlertItem[]>(`/alerts${buildQuery({ limit: 500, ...params })}`);

export const getAlert = (id: string) => api<AlertItem>(`/alerts/${id}`);

export const getIncidents = (params?: Record<string, string | number | boolean | null | undefined>) =>
  api<IncidentItem[]>(`/incidents${buildQuery({ limit: 500, ...params })}`);

export const getIncident = (id: string) => api<IncidentDetails>(`/incidents/${id}`);

export const applyIncidentAction = (id: number, action: IncidentAction, comment?: string) =>
  api<IncidentDetails>(`/incidents/${id}/actions`, {
    method: "POST",
    body: JSON.stringify({ action, comment }),
  });

export const getCollectionSchedules = () => api<CollectionSchedule[]>("/collectors/schedules");

export const runCollectionSchedule = (id: number) =>
  api<ScheduleRunResult>(`/collectors/schedules/${id}/run`, {
    method: "POST",
  });
