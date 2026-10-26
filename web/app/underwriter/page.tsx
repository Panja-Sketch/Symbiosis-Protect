import Link from "next/link";
import { ProofMix } from "@/components/client-card";
import { Provenance } from "@/components/provenance";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import { roleOnly } from "@/lib/session";
import type { Portfolio } from "@/lib/role-types";

function Tile({ label, value, sub, testid }: { label: string; value: string; sub?: string; testid: string }) {
  return (
    <Card>
      <CardBody className="pt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
        <p className="mt-1 font-display text-3xl font-semibold" data-testid={testid}>
          {value}
        </p>
        {sub && <p className="text-sm text-muted">{sub}</p>}
      </CardBody>
    </Card>
  );
}

export default async function UnderwriterPage() {
  roleOnly("underwriter");
  const p = await apiGet<Portfolio>("/underwriting/portfolio", "underwriter");
  const t = p.tiles;
  const counties = Object.entries(t.alerts_by_county);
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="font-display text-2xl font-semibold md:text-3xl">Portfolio</h1>
          <p className="text-sm text-muted">Risk-control view of the Arizona demo book</p>
        </div>
        <Provenance kind="SYNTHETIC" detail="Synthetic accounts and tasks; alerts are LIVE or SIMULATED as labelled." />
      </div>
      <p className="rounded-lg bg-surface-2 p-3 text-sm" data-testid="visibility-note">
        {p.visibility_note}
      </p>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Tile testid="tile-participation" label="Participation" value={t.participation.pct != null ? `${t.participation.pct}%` : "—"} sub={`${t.participation.participating} of ${t.participation.total} accounts share by default`} />
        <Tile testid="tile-completion" label="Task completion" value={t.task_completion.pct != null ? `${t.task_completion.pct}%` : "—"} sub={`${t.task_completion.done} of ${t.task_completion.applicable} shared tasks`} />
        <Tile testid="tile-sense" label="Sense cases" value={String(t.sense_cases.total)} sub={`${t.sense_cases.active} active · ${t.sense_cases.verified} verified`} />
        <Card>
          <CardBody className="pt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted">Proof-level mix</p>
            <div className="mt-2" data-testid="tile-proof-mix">
              <ProofMix mix={t.proof_mix} />
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active alerts by county</CardTitle>
        </CardHeader>
        <CardBody>
          {counties.length === 0 ? (
            <p className="text-sm text-muted" data-testid="no-county-alerts">
              No active weather alerts for any insured county.
            </p>
          ) : (
            <ul className="space-y-1 text-sm" data-testid="county-alerts">
              {counties.map(([county, events]) => (
                <li key={county}>
                  <strong>{county}</strong>: {events.join(", ")}
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <section aria-labelledby="accts-h">
        <h2 id="accts-h" className="mb-2 font-display text-xl font-semibold">
          Accounts
        </h2>
        <div className="overflow-x-auto rounded-card border border-line bg-surface">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Accounts with shared completion and proof mix</caption>
            <thead>
              <tr className="border-b border-line text-xs text-muted">
                <th scope="col" className="p-3">Account</th>
                <th scope="col" className="p-3">Line</th>
                <th scope="col" className="p-3">Sharing</th>
                <th scope="col" className="p-3">Completion</th>
                <th scope="col" className="p-3">Open high priority</th>
              </tr>
            </thead>
            <tbody>
              {p.accounts.map((a) => (
                <tr key={a.account_id} className="border-b border-line/60" data-testid="portfolio-row">
                  <th scope="row" className="p-3 font-medium">
                    <Link href={`/client/${a.account_id}`} className="text-accent-text underline underline-offset-2">
                      {a.display_name}
                    </Link>
                    <span className="block text-xs font-normal text-muted">{a.city}</span>
                  </th>
                  <td className="p-3">{a.lob.replace(/_/g, " ")}</td>
                  <td className="p-3">{a.shares_by_default ? "Shares" : "Private"}</td>
                  <td className="p-3">{a.completion.pct != null ? `${a.completion.pct}%` : "—"}</td>
                  <td className="p-3">{a.open_high_priority.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
