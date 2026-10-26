import type { Provenance, Task } from "./types";

export interface ClientRow {
  account_id: string;
  display_name: string;
  headline: string;
  persona_id: string;
  lob: string;
  product_label: string;
  preview_flag: boolean;
  city: string;
  county: string;
  agent_id: string;
  agent?: { name: string; agency_name: string };
  shares_by_default: boolean;
  open_high_priority: { id: string; title: string; source: string; provenance: Provenance }[];
  completion: { done: number; applicable: number; pct: number | null };
  proof_mix: Record<string, number>;
  last_activity: string | null;
  sense: { connected: number; available: number; active_cases: string[]; verified_cases: number };
  exposure: {
    active_alerts: { event: string; provenance: Provenance; ends: string | null }[];
    high_risk_days: string[];
    forecast_provenance: Provenance | null;
    error: string | null;
  };
  renewal_points: string[];
}

export interface Portfolio {
  tiles: {
    participation: { participating: number; total: number; pct: number | null };
    task_completion: { done: number; applicable: number; pct: number | null };
    proof_mix: Record<string, number>;
    alerts_by_county: Record<string, string[]>;
    sense_cases: { total: number; active: number; verified: number };
  };
  accounts: ClientRow[];
  visibility_note: string;
}

export interface ClientDetail {
  row: ClientRow;
  policy: { id: string; lob: string; product_label: string };
  tasks: Task[];
  history: { id: string; title: string; status: string; closed_at: string; proof_level: string | null }[];
  proofs: { id: string; task_title: string; level: string; type: string; captured_at: string; sha256: string; file_url: string | null; lat?: number | null }[];
  cases: { id: string; kind: string; state: string; unit_label: string | null; manifest_sha256: string | null }[];
  claims: { id: string; date: string; peril: string; cause: string; paid_usd: number }[];
  packages: { id: string; scope: string; manifest_sha256: string; created_at: string; created_by_role: string }[];
  account: { id: string; display_name: string; persona_id: string };
}
