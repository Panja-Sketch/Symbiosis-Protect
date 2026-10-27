import Link from "next/link";
import { ProofMix } from "@/components/client-card";
import { Provenance } from "@/components/provenance";
import { ExportButton, IssueForm } from "@/components/role-widgets";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import { roleOnly } from "@/lib/session";
import { fmtDate, usd } from "@/lib/utils";
import type { ClientDetail } from "@/lib/role-types";

export default async function ClientPage({ params }: { params: { id: string } }) {
  const { role } = roleOnly("agent", "underwriter");
  const d = await apiGet<ClientDetail>(`/underwriting/accounts/${params.id}`, role);
  const back = role === "agent" ? "/agent" : "/underwriter";
  return (
    <div className="space-y-5">
      <div>
        <Link prefetch={false} href={back} className="inline-flex min-h-[44px] items-center text-sm font-semibold text-accent-text underline underline-offset-2">
          ← Back
        </Link>
        <h1 className="font-display text-2xl font-semibold md:text-3xl">{d.account.display_name}</h1>
        <p className="flex flex-wrap items-center gap-2 text-sm text-muted">
          {d.row.headline} · {d.policy.product_label} <Provenance kind="SYNTHETIC" />
        </p>
        <p className="mt-2 rounded-lg bg-surface-2 p-3 text-sm">Showing only items this policyholder shared, plus items issued by the insurer or agent.</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Evidence package</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3 text-sm">
            <p>ZIP with a manifest listing every file and its SHA-256. Contains shared items only.</p>
            <ExportButton policyId={d.policy.id} role={role} />
            {d.packages.length > 0 && (
              <ul className="space-y-1 text-xs text-muted" data-testid="package-list">
                {d.packages.map((p) => (
                  <li key={p.id}>
                    {fmtDate(p.created_at, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })} · {p.created_by_role} · {p.scope.replace("_", " ")} ·{" "}
                    <code className="break-all">{p.manifest_sha256.slice(0, 16)}…</code>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Issue a recommendation</CardTitle>
            <Provenance kind="SYNTHETIC" />
          </CardHeader>
          <CardBody>
            <IssueForm accountId={d.account.id} role={role} />
          </CardBody>
        </Card>
      </div>

      <section aria-labelledby="t-h" className="space-y-2">
        <h2 id="t-h" className="font-display text-xl font-semibold">
          Shared tasks
        </h2>
        {d.tasks.length === 0 ? (
          <p className="rounded-card border border-dashed border-line p-4 text-sm text-muted" data-testid="no-shared-tasks">
            Nothing shared yet. This policyholder keeps their tasks private.
          </p>
        ) : (
          <ul className="space-y-2">
            {d.tasks.map((t) => (
              <li key={t.id} className="rounded-card border border-line bg-surface p-3 text-sm" data-testid="shared-task">
                <p className="font-semibold">
                  {t.title} <span className="text-xs font-normal uppercase text-muted">{t.status}{t.source !== "rule" ? ` · ${t.source}-issued` : ""}</span>
                </p>
                <p className="text-muted">{t.why}</p>
              </li>
            ))}
          </ul>
        )}
        {d.history.length > 0 && (
          <ul className="divide-y divide-line rounded-card border border-line bg-surface text-sm">
            {d.history.map((h) => (
              <li key={h.id} className="p-3">
                {h.title} <span className="text-xs text-muted">· {h.status} {fmtDate(h.closed_at)} · proof {h.proof_level ?? "none"}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="p-h" className="space-y-2">
        <h2 id="p-h" className="font-display text-xl font-semibold">
          Proof on file
        </h2>
        <ProofMix mix={d.row.proof_mix} />
        {d.proofs.length > 0 && (
          <ul className="space-y-2">
            {d.proofs.map((p) => (
              <li key={p.id} className="rounded-card border border-line bg-surface p-3 text-sm">
                {p.task_title} · {p.level} {p.type} · {fmtDate(p.captured_at, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
                <code className="mt-1 block break-all text-xs">{p.sha256}</code>
              </li>
            ))}
          </ul>
        )}
      </section>

      {d.cases.length > 0 && (
        <section aria-labelledby="c-h" className="space-y-2">
          <h2 id="c-h" className="font-display text-xl font-semibold">
            Sense cases <Provenance kind="SIMULATED" />
          </h2>
          <ul className="space-y-1 text-sm">
            {d.cases.map((c) => (
              <li key={c.id}>
                {c.kind.replace("_", " ")} {c.unit_label ? `(unit ${c.unit_label})` : ""} — <strong>{c.state.replace("_", " ")}</strong>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section aria-labelledby="cl-h" className="space-y-2">
        <h2 id="cl-h" className="font-display text-xl font-semibold">
          Claims <Provenance kind="SYNTHETIC" />
        </h2>
        {d.claims.length === 0 ? (
          <p className="text-sm text-muted">No claims on file.</p>
        ) : (
          <ul className="text-sm">
            {d.claims.map((c) => (
              <li key={c.id}>
                {fmtDate(c.date, { month: "short", year: "numeric" })} · {c.peril} · {usd(c.paid_usd)} — {c.cause}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
