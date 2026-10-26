export type Provenance = "LIVE" | "HISTORIC" | "SYNTHETIC" | "SIMULATED" | "AI";
export type Role = "policyholder" | "agent" | "underwriter";

export interface Persona {
  id: string;
  persona_id: string;
  display_name: string;
  type: "person" | "business";
  headline: string;
  agent_id: string;
  program_label: string | null;
  policy_id: string;
  lob: string;
  product_label: string;
  preview_flag: boolean;
  location_id: string;
  city: string;
}

export interface Proof {
  id: string;
  level: string;
  type: string;
  captured_at: string;
  sha256: string;
  lat?: number | null;
  lon?: number | null;
  uri?: string | null;
  filename?: string | null;
  content_type?: string | null;
  size_bytes?: number | null;
  location_source?: string;
  client_captured_at?: string | null;
}

export interface Task {
  id: string;
  rule_id: string;
  account_id: string;
  location_id: string;
  asset_id: string | null;
  source: "rule" | "insurer" | "agent";
  title: string;
  why: string;
  steps: string[];
  priority: "high" | "medium" | "low";
  score: number;
  est_minutes: number | null;
  est_cost_usd: [number, number] | null;
  peril: string;
  coverage_note_key: string | null;
  coverage_codes: string[];
  proof_default_level: string;
  proof_accepted: string[];
  status: "open" | "done" | "deferred" | "declined" | "expired";
  bucket: "do_now" | "coming_up";
  relevant_date: string | null;
  due_at: string | null;
  opened_at: string;
  closed_at: string | null;
  inputs_snapshot: {
    reasons: string[];
    alert_ids: string[];
    input_provenance: Provenance[];
    evaluated_at: string;
    weather: { provenance: Provenance | null; sources: string[] };
    asset_facts: Record<string, unknown>;
  };
  proof: Proof[];
  provenance: Provenance;
  visibility: "private" | "shared";
}

export interface HistoricTask {
  id: string;
  title: string;
  status: string;
  closed_at: string;
  proof_level: string | null;
  provenance: Provenance;
}

export interface TasksResponse {
  tasks: Task[];
  history: HistoricTask[];
  readiness: { done: number; applicable: number; ratio: number };
}

export interface DailyForecast {
  date: string;
  max_f: number | null;
  min_f: number | null;
  precip_in: number | null;
  precip_prob: number | null;
  source: string;
}

export interface WeatherResponse {
  daily: DailyForecast[];
  provenance: Provenance | null;
  sources?: string[];
  fetched_at?: string;
  now_local: string;
  error: string | null;
}

export interface WeatherAlert {
  id: string;
  event: string;
  severity: string | null;
  headline: string;
  onset: string | null;
  ends: string | null;
  provenance: Provenance;
  source: string;
}

export interface RibbonDay {
  date: string;
  max_f: number | null;
  min_f: number | null;
  precip_in: number | null;
  icon: string;
  risk: "none" | "elevated" | "high";
  reasons: string[];
  alerts: string[];
  task_pins: { task_id: string; title: string; priority: string }[];
}
export interface Ribbon {
  days: RibbonDay[];
  provenance: Provenance | null;
  sources: string[];
}

export interface Coverage {
  code: string;
  name_plain: string;
  limit_usd: number | null;
  limit_note: string | null;
  deductible_usd: number | null;
  deductible_note: string | null;
  what_it_covers_plain: string;
  what_it_does_not_plain: string;
  examples: string[];
}

export interface Policy {
  id: string;
  lob: string;
  product_label: string;
  term_start: string;
  term_end: string;
  preview_flag: boolean;
  coverages: Coverage[];
  endorsements: { code: string; name_plain: string; present: boolean; why_it_matters_plain: string }[];
  exclusions_plain: { code: string; title: string; plain: string }[];
  deductibles: Record<string, number | string>;
  summary_disclaimer: string;
  coverage_notes: Record<string, { key: string; title: string; plain: string }>;
}

export interface AccountResponse {
  id: string;
  display_name: string;
  headline: string;
  program_label: string | null;
  type: string;
  agent: { name: string; agency_name: string; email: string; phone: string | null };
  locations: { id: string; label: string; city: string; county: string; elevation_ft: number; nws_zone: string }[];
}

export interface Asset {
  id: string;
  type: string;
  label: string;
  install_year: number | null;
  last_service_date: string | null;
  material: string | null;
  unit_label: string | null;
  floor: number | null;
  notes: string;
  attributes: Record<string, unknown>;
}

export interface AssetsResponse {
  assets: Asset[];
  profiles: Record<string, unknown>[];
}

export interface AlertRow {
  id: string;
  kind: string;
  severity: string;
  title: string;
  body: string;
  deep_link: string | null;
  created_at: string;
  read_at: string | null;
  provenance: Provenance;
  sent_channels: string[];
}

export interface HistoryResponse {
  weather: {
    years: string[];
    per_year: Record<string, Record<string, number | null>>;
    avg_per_year: Record<string, number | null>;
    monthly_normals: { month: number; mean_max_f: number; mean_min_f: number; mean_precip_in: number }[];
    normals_period: string;
    source: string;
  };
  storm_events: {
    county: string;
    summary: { total_events: number; by_type: Record<string, number>; monsoon_season_by_type: Record<string, number>; property_damage_usd: number };
  };
  risk_index: {
    risk_rating: string;
    county_risk_rating: string;
    social_vulnerability: string | null;
    hazards: Record<string, { name: string; eal_rating: string | null; az_tract_percentile: number | null }>;
  };
  provenance: Provenance;
}

export interface EvidenceRow extends Proof {
  task_id: string;
  task_title: string;
  file_url: string | null;
}

export interface EvidenceResponse {
  proofs: EvidenceRow[];
  history: HistoricTask[];
  level_mix: Record<string, number>;
}
