import { CheckCircle2, CircleDashed, Mail, Phone } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import { policyholderOnly } from "@/lib/session";
import { fmtDate, usd } from "@/lib/utils";
import type { AccountResponse, Policy } from "@/lib/types";

export default async function CoveragePage() {
  const { account_id } = policyholderOnly();
  const [acct, list] = await Promise.all([apiGet<AccountResponse>(`/accounts/${account_id}`), apiGet<Policy[]>(`/accounts/${account_id}/policies`)]);
  const policy = await apiGet<Policy>(`/policies/${list[0].id}`);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-semibold md:text-3xl">What&apos;s insured</h1>
        <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted">
          {policy.product_label} · {fmtDate(policy.term_start, { month: "short", day: "numeric", year: "numeric" })} –{" "}
          {fmtDate(policy.term_end, { month: "short", day: "numeric", year: "numeric" })}
          <Provenance kind="SYNTHETIC" detail="Original plain-language summary written for this demo; not an insurer's policy wording." />
        </p>
        <p className="mt-2 rounded-lg bg-surface-2 p-3 text-sm">{policy.summary_disclaimer}</p>
      </div>

      <section aria-labelledby="cov-h" className="space-y-3">
        <h2 id="cov-h" className="font-display text-xl font-semibold">
          Coverages
        </h2>
        <ul className="grid gap-3 md:grid-cols-2">
          {policy.coverages.map((c) => (
            <li key={c.code} id={c.code} className="scroll-mt-20">
              <Card className="h-full" data-testid="coverage-card">
                <CardHeader>
                  <CardTitle>{c.name_plain}</CardTitle>
                </CardHeader>
                <CardBody className="space-y-3 text-sm">
                  <dl className="grid grid-cols-2 gap-2 rounded-lg bg-surface-2 p-3">
                    <div>
                      <dt className="text-xs text-muted">Limit</dt>
                      <dd className="font-semibold">{c.limit_usd ? usd(c.limit_usd) : c.limit_note ?? "—"}</dd>
                      {c.limit_usd && c.limit_note && <dd className="text-xs text-muted">{c.limit_note}</dd>}
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Deductible</dt>
                      <dd className="font-semibold">{c.deductible_usd ? usd(c.deductible_usd) : c.deductible_note ?? "None listed"}</dd>
                    </div>
                  </dl>
                  <div>
                    <p className="font-semibold">Generally covers</p>
                    <p>{c.what_it_covers_plain}</p>
                  </div>
                  <div>
                    <p className="font-semibold">Generally does not cover</p>
                    <p>{c.what_it_does_not_plain}</p>
                  </div>
                  {c.examples.length > 0 && (
                    <div>
                      <p className="font-semibold">For example</p>
                      <ul className="list-disc pl-5 text-muted">
                        {c.examples.map((e) => (
                          <li key={e}>{e}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardBody>
              </Card>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="end-h" className="space-y-3">
        <h2 id="end-h" className="font-display text-xl font-semibold">
          Add-ons (endorsements)
        </h2>
        <ul className="grid gap-3 md:grid-cols-2">
          {policy.endorsements.map((e) => (
            <li key={e.code} id={e.code} className="scroll-mt-20 rounded-card border border-line bg-surface p-4 text-sm" data-testid="endorsement">
              <p className="flex items-center gap-2 font-semibold">
                {e.present ? <CheckCircle2 className="h-5 w-5 text-saguaro-text" aria-hidden /> : <CircleDashed className="h-5 w-5 text-clay-text" aria-hidden />}
                {e.name_plain}
                <span className={e.present ? "text-saguaro-text" : "text-clay-text"}>{e.present ? "On your policy" : "Not on your policy"}</span>
              </p>
              <p className="mt-1 text-muted">{e.why_it_matters_plain}</p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="ex-h" className="space-y-3">
        <h2 id="ex-h" className="font-display text-xl font-semibold">
          Things usually left out
        </h2>
        <ul className="space-y-2">
          {policy.exclusions_plain.map((x) => (
            <li key={x.code} id={x.code} className="scroll-mt-20 rounded-card border border-line bg-surface p-4 text-sm">
              <p className="font-semibold">{x.title}</p>
              <p className="text-muted">{x.plain}</p>
            </li>
          ))}
        </ul>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Your agent</CardTitle>
          <Provenance kind="SYNTHETIC" detail="Synthetic independent agency." />
        </CardHeader>
        <CardBody className="text-sm">
          <p className="font-semibold">
            {acct.agent.name} · {acct.agent.agency_name}
          </p>
          <p className="mt-1 text-muted">Your agent confirms final coverage decisions.</p>
          <p className="mt-2 flex flex-wrap gap-4">
            <span className="inline-flex items-center gap-1">
              <Mail className="h-4 w-4" aria-hidden /> {acct.agent.email}
            </span>
            {acct.agent.phone && (
              <span className="inline-flex items-center gap-1">
                <Phone className="h-4 w-4" aria-hidden /> {acct.agent.phone}
              </span>
            )}
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
