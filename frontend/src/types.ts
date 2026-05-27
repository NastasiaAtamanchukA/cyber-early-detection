export type Severity = "low" | "medium" | "high" | "critical";
export type IncidentStatus = "new" | "open" | "investigating" | "closed" | string;

export type EventItem = {
  id: number;
  timestamp: string;
  host: string;
  user: string | null;
  event_type: string;
  message: string;
  is_anomaly: boolean;
  anomaly_score: number;
  risk_score: number;
  created_at: string;
};

export type EventDetails = EventItem & {
  raw_log: Record<string, unknown>;
  normalized_log: Record<string, unknown>;
};

export type AlertItem = {
  id: number;
  event_id: number;
  incident_id: number | null;
  title: string;
  severity: Severity | string;
  status: string;
  description: string;
  created_at: string;
};

export type AlertDetails = AlertItem & {
  event: EventDetails | null;
};

export type IncidentItem = {
  id: number;
  title: string;
  severity: Severity | string;
  status: IncidentStatus;
  affected_host: string | null;
  affected_user: string | null;
  description: string;
  first_seen: string;
  last_seen: string;
  created_at: string;
  recommended_actions: string[];
};

export type IncidentDetails = IncidentItem & {
  alerts: AlertItem[];
};

export type StatItem = {
  name: string;
  count: number;
};

export type HostStatItem = {
  host: string;
  event_count: number;
  alert_count: number;
  max_risk: number;
};

export type RiskBucketItem = {
  name: string;
  count: number;
  min_risk: number;
  max_risk: number;
};

export type TimelineItem = {
  label: string;
  count: number;
  max_risk: number;
};

export type DashboardData = {
  events_total: number;
  alerts_total: number;
  incidents_total: number;
  anomalies_total: number;
  average_risk: number;
  critical_alerts: number;
  high_risk_events: number;
  alerts_by_severity: StatItem[];
  events_by_type: StatItem[];
  incidents_by_status: StatItem[];
  top_hosts: HostStatItem[];
  risk_distribution: RiskBucketItem[];
  events_timeline: TimelineItem[];
  recent_events: EventItem[];
  recent_alerts: AlertItem[];
  recent_incidents: IncidentItem[];
};

export type CollectionSchedule = {
  id: number;
  code: string;
  name: string;
  description: string;
  interval_label: string;
  source_name: string;
  source_kind: string;
  event_profile: "auth" | "web" | "privileged" | "database" | "mixed" | string;
  batch_size: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type CollectionSchedulePayload = {
  code: string;
  name: string;
  description: string;
  interval_label: string;
  source_name: string;
  source_kind: string;
  event_profile: "auth" | "web" | "privileged" | "database" | "mixed";
  batch_size: number;
  enabled: boolean;
};

export type ScheduleRunResult = {
  schedule_id: number;
  run_id: number;
  events_created: number;
  alerts_created: number;
  message: string;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type EventFilters = {
  page?: number;
  page_size?: number;
  search?: string;
  host?: string;
  user?: string;
  event_type?: string;
  only_anomalies?: boolean;
};

export type AlertFilters = {
  page?: number;
  page_size?: number;
  search?: string;
  host?: string;
  status?: string;
  severity?: string;
};

export type IncidentFilters = {
  page?: number;
  page_size?: number;
  search?: string;
  host?: string;
  status?: string;
  severity?: string;
};

export type ScheduleFilters = {
  page?: number;
  page_size?: number;
  search?: string;
  enabled?: boolean | "";
  event_profile?: string;
};
