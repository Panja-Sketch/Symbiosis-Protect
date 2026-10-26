import { AssetList } from "@/components/asset-editor";
import { HistoryCharts } from "@/components/history-charts";
import { Provenance } from "@/components/provenance";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import { getSession } from "@/lib/session";
import type { AccountResponse, AssetsResponse, HistoryResponse } from "@/lib/types";

export default async function PlacePage() {
  const { account_id } = getSession();
  const acct = await apiGet<AccountResponse>(`/accounts/${account_id}`);
  const loc = acct.locations[0];
  const [assets, history] = await Promise.all([
    apiGet<AssetsResponse>(`/accounts/${account_id}/assets`),
    apiGet<HistoryResponse>(`/locations/${loc.id}/history`),
  ]);
  const units = assets.assets.filter((a) => a.type === "unit");
  const rest = assets.assets.filter((a) => a.type !== "unit");
  const hz = Object.values(history.risk_index.hazards).filter((h) => h.eal_rating && h.eal_rating !== "No Expected Annual Losses" && h.eal_rating !== "Not Applicable");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold md:text-3xl">My place</h1>
        <p className="text-sm text-muted">
          {loc.label} · {loc.elevation_ft.toLocaleString()} ft · NWS zone {loc.nws_zone}
        </p>
      </div>

      <section aria-labelledby="assets-h" className="space-y-3">
        <h2 id="assets-h" className="font-display text-xl font-semibold">
          Equipment &amp; age
        </h2>
        <p className="text-sm text-muted">Edit an age or service date and your tasks update right away.</p>
        <AssetList assets={rest} />
        {units.length > 0 && (
          <details className="rounded-card border border-line bg-surface p-4">
            <summary className="min-h-[44px] cursor-pointer text-sm font-semibold">Unit register ({units.length} units)</summary>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Unit register</caption>
                <thead>
                  <tr className="border-b border-line text-xs text-muted">
                    <th scope="col" className="py-2 pr-3">Unit</th>
                    <th scope="col" className="pr-3">Water heater</th>
                    <th scope="col" className="pr-3">Last turnover</th>
                    <th scope="col">Supply lines checked</th>
                  </tr>
                </thead>
                <tbody>
                  {units.map((u) => (
                    <tr key={u.id} className="border-b border-line/60">
                      <th scope="row" className="py-1.5 pr-3 font-medium">{u.unit_label}</th>
                      <td className="pr-3">{String(u.attributes.water_heater_year ?? "unknown")}</td>
                      <td className="pr-3">{String(u.attributes.last_turnover_date ?? "—")}</td>
                      <td>{u.attributes.supply_lines_checked_at_turnover ? "Yes" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        )}
      </section>

      <section aria-labelledby="hist-h" className="space-y-3">
        <h2 id="hist-h" className="font-display text-xl font-semibold">
          Local history
        </h2>
        <HistoryCharts history={history} />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>FEMA National Risk Index</CardTitle>
          <Provenance kind="HISTORIC" detail="FEMA NRI v1.20 (Dec 2025), census tract." />
        </CardHeader>
        <CardBody className="text-sm">
          <p>
            Overall tract rating: <strong>{history.risk_index.risk_rating}</strong> (county: {history.risk_index.county_risk_rating}). Higher
            percentile means a larger share of Arizona tracts have lower expected annual loss for that hazard.
          </p>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {hz.map((h) => (
              <li key={h.name} className="flex items-center justify-between rounded-lg bg-surface-2 px-3 py-2">
                <span>{h.name}</span>
                <span className="font-semibold">
                  {h.eal_rating}
                  {h.az_tract_percentile != null && <span className="font-normal text-muted"> · {Math.round(h.az_tract_percentile)}th pct in AZ</span>}
                </span>
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>
    </div>
  );
}
