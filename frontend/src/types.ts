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
  source_name?: string | null;
  alert_id?: number | null;
};

export type EventDetails = EventItem & {
  source_id: number;
  raw_log: Record<string, unknown>;
  normalized_log: Record<string, unknown>;
  created_at: string;
};

export type IncidentItem = {
  id: number;
  title: string;
  severity: string;
  status: string;
  description: string;
  affected_host: string | null;
  affected_user: string | null;
  event_count: number;
  alert_count: number;
  first_seen: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
};

export type AlertItem = {
  id: number;
  event_id: number;
  incident_id?: number | null;
  title: string;
  severity: string;
  status: string;
  description: string;
  created_at: string;
  updated_at: string;
  event?: EventItem | null;
  incident?: IncidentItem | null;
};

export type AlertSummary = Omit<AlertItem, "incident">;

export type IncidentDetails = IncidentItem & {
  recommended_actions: string[];
  attack_stage: string;
  detection_logic: string;
  response_sla: string;
  related_alerts: AlertSummary[];
  related_events: EventItem[];
};

export type IncidentAction = "take_in_work" | "close" | "reopen" | "escalate" | "downgrade";

export type StatItem = {
  name: string;
  count: number;
};

export type HostStatItem = {
  host: string;
  count: number;
  max_risk: number;
};

export type DashboardData = {
  total_events: number;
  total_alerts: number;
  total_incidents: number;
  open_incidents: number;
  critical_alerts: number;
  high_alerts: number;
  anomalies: number;
  avg_risk: number;
  events_by_type: StatItem[];
  alerts_by_severity: StatItem[];
  incidents_by_status: StatItem[];
  top_hosts: HostStatItem[];
  latest_events: EventItem[];
  latest_alerts: AlertItem[];
  latest_incidents: IncidentItem[];
};

export type CollectionSchedule = {
  id: number;
  code: string;
  name: string;
  description: string;
  interval_label: string;
  source_name: string;
  source_kind: string;
  event_profile: string;
  batch_size: number;
  enabled: boolean;
  last_run_at: string | null;
  created_at: string;
};

export type CollectionRun = {
  id: number;
  schedule_id: number;
  status: string;
  events_created: number;
  alerts_created: number;
  incidents_created: number;
  details: Record<string, unknown>;
  started_at: string;
  finished_at: string | null;
};

export type ScheduleRunResult = {
  schedule: CollectionSchedule;
  run: CollectionRun;
  events: EventItem[];
};
