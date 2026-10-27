import Link from "next/link";
import { AlertTriangle, ArrowRight, Radio } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { fmtDate } from "@/lib/utils";
import type { ClientRow } from "@/lib/role-types";

export function ProofMix({ mix }: { mix: Record<string, number> }) {
  const entries = Object.entries(mix);
  if (entries.length === 0) return <span className="text-xs text-muted">No shared proof yet</span>;
  return (
    <ul className="flex flex-wrap gap-1.5" aria-label="Proof levels">
      {entries.map(([l, n]) => (
        <li key={l} className="rounded-full border border-line bg-surface-2 px-2 py-0.5 text-xs">
          {l}: <strong>{n}</strong>
        </li>
      ))}
    </ul>
  );
}

export function ClientCard({ c }: { c: ClientRow }) {
  const alerted = c.exposure.active_alerts.length > 0;
  return (
    <article className="space-y-3 rounded-card border border-line bg-surface p-4" data-testid="client-card" data-persona={c.persona_id}>
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="font-display text-lg font-semibold">{c.display_name}</h2>
          <p className="text-sm text-muted">
            {c.headline} · {c.product_label}
          </p>
        </div>
        <Provenance kind="SYNTHETIC" detail="Synthetic client. Only shared and insurer/agent-issued items are shown." />
      </header>

      {alerted && (
        <div className="rounded-lg border-l-4 border-clay bg-clay-soft p-3 text-sm" data-testid="exposure-alert">
          <p className="flex flex-wrap items-center gap-2 font-semibold text-clay-text">
            <AlertTriangle className="h-4 w-4" aria-hidden /> Under active alert in {c.county}
          </p>
          <ul className="mt-1 space-y-1">
            {c.exposure.active_alerts.map((a) => (
              <li key={a.event} className="flex items-center gap-2">
                {a.event} <Provenance kind={a.provenance} />
              </li>
            ))}
          </ul>
        </div>
      )}
      {c.exposure.high_risk_days.length > 0 && !alerted && (
        <p className="text-sm text-amber-text">
          High-risk forecast days: {c.exposure.high_risk_days.map((d) => fmtDate(d)).join(", ")}{" "}
          {c.exposure.forecast_provenance && <Provenance kind={c.exposure.forecast_provenance} />}
        </p>
      )}
      {c.exposure.error && <p className="text-xs text-muted">{c.exposure.error}</p>}

      <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-xs text-muted">Shared completion</dt>
          <dd className="font-semibold">{c.completion.pct != null ? `${c.completion.pct}% (${c.completion.done}/${c.completion.applicable})` : "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Last activity</dt>
          <dd className="font-semibold">{fmtDate(c.last_activity)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Sharing</dt>
          <dd className="font-semibold">{c.shares_by_default ? "On by default" : "Off (private)"}</dd>
        </div>
        <div>
          <dt className="flex items-center gap-1 text-xs text-muted">
            <Radio className="h-3 w-3" aria-hidden /> Sense
          </dt>
          <dd className="font-semibold">
            {c.sense.connected}/{c.sense.available} connected
            {c.sense.active_cases.length > 0 && <span className="text-clay-text"> · {c.sense.active_cases.length} active case</span>}
          </dd>
        </div>
      </dl>

      <div>
        <p className="text-xs font-semibold text-muted">Open high-priority (shared)</p>
        {c.open_high_priority.length === 0 ? (
          <p className="text-sm text-muted">None visible to you.</p>
        ) : (
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
            {c.open_high_priority.map((t) => (
              <li key={t.id}>
                {t.title} {t.source !== "rule" && <span className="text-xs font-semibold uppercase text-accent-text">({t.source}-issued)</span>}{" "}
                <Provenance kind={t.provenance} />
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <p className="flex items-center gap-2 text-xs font-semibold text-muted">
          Renewal talking points <Provenance kind="SYNTHETIC" detail="Composed by rules from shared data; no AI used." />
        </p>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm" data-testid="renewal-points">
          {c.renewal_points.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <ProofMix mix={c.proof_mix} />
        <Link prefetch={false} href={`/client/${c.account_id}`} className="inline-flex min-h-[44px] items-center gap-1 text-sm font-semibold text-accent-text underline underline-offset-2">
          Open account <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </div>
    </article>
  );
}
