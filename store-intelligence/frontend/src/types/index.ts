export interface MetricsResponse {
  store_id: string;
  date: string;
  unique_visitors: number;
  converted_visitors: number;
  conversion_rate: number;
  avg_dwell_by_zone: Record<string, number>;
  current_queue_depth: number;
  queue_abandonment_rate: number;
  total_transactions: number;
  data_as_of: string;
}

export interface FunnelStage {
  name: string;
  label: string;
  count: number;
  drop_off_pct: number;
}

export interface FunnelResponse {
  store_id: string;
  date: string;
  unit: string;
  stages: FunnelStage[];
}

export interface HeatmapZone {
  zone_id: string;
  visit_count: number;
  avg_dwell_sec: number;
  score_0_100: number;
}

export interface HeatmapResponse {
  store_id: string;
  date: string;
  zones: HeatmapZone[];
  data_confidence: string;
}

export interface AnomalyItem {
  anomaly_type: string;
  severity: string;
  zone_id?: string | null;
  description: string;
}

export interface AnomalyResponse {
  store_id: string;
  date: string;
  anomalies: AnomalyItem[];
}

export interface StoreHealth {
  store_id: string;
  last_event_at?: string | null;
  lag_minutes?: number | null;
  warnings: string[];
}

export interface HealthResponse {
  status: string;
  database: string;
  version: string;
  stores: StoreHealth[];
  warnings: string[];
}

export interface EventRecord {
  event_id: string;
  store_id: string;
  camera_id: string;
  visitor_id: string;
  event_type: string;
  timestamp: string;
  zone_id?: string;
  dwell_ms?: number;
  is_staff: boolean;
  confidence: number;
  metadata: Record<string, unknown>;
}
