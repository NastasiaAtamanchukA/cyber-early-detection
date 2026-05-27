import type {
  AlertDetails,
  AlertFilters,
  AlertItem,
  CollectionSchedule,
  CollectionSchedulePayload,
  DashboardData,
  EventDetails,
  EventFilters,
  EventItem,
  IncidentDetails,
  IncidentFilters,
  IncidentItem,
  PaginatedResponse,
  ScheduleFilters,
  ScheduleRunResult,
} from "../types";

const API_BASE = "/api/v1";

function toQuery(params: Record<string, string | number | boolean | undefined | null>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  });
  const text = query.toString();
  return text ? `?${text}` : "";
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API error ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const getDashboard = () => api<DashboardData>("/dashboard");

export const getEvents = (filters: EventFilters = {}) =>
  api<PaginatedResponse<EventItem>>(`/events${toQuery({ page: 1, page_size: 10, ...filters })}`);
export const getEvent = (id: number) => api<EventDetails>(`/events/${id}`);

export const getAlerts = (filters: AlertFilters = {}) =>
  api<PaginatedResponse<AlertItem>>(`/alerts${toQuery({ page: 1, page_size: 10, ...filters })}`);
export const getAlert = (id: number) => api<AlertDetails>(`/alerts/${id}`);

export const getIncidents = (filters: IncidentFilters = {}) =>
  api<PaginatedResponse<IncidentItem>>(`/incidents${toQuery({ page: 1, page_size: 10, ...filters })}`);
export const getIncident = (id: number) => api<IncidentDetails>(`/incidents/${id}`);
export const takeIncident = (id: number) => api<IncidentDetails>(`/incidents/${id}/take`, { method: "POST" });
export const closeIncident = (id: number) => api<IncidentDetails>(`/incidents/${id}/close`, { method: "POST" });
export const reopenIncident = (id: number) => api<IncidentDetails>(`/incidents/${id}/reopen`, { method: "POST" });

export const getCollectionSchedules = (filters: ScheduleFilters = {}) =>
  api<PaginatedResponse<CollectionSchedule>>(
    `/collectors/schedules${toQuery({ page: 1, page_size: 10, ...filters })}`,
  );

export const createCollectionSchedule = (payload: CollectionSchedulePayload) =>
  api<CollectionSchedule>("/collectors/schedules", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateCollectionSchedule = (
  id: number,
  payload: Partial<CollectionSchedulePayload>,
) =>
  api<CollectionSchedule>(`/collectors/schedules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const runCollectionSchedule = (id: number) =>
  api<ScheduleRunResult>(`/collectors/schedules/${id}/run`, {
    method: "POST",
  });
