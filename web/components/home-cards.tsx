import Link from "next/link";
import { AlertTriangle, ArrowRight, Droplets, Snowflake, Thermometer } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, fmtDate } from "@/lib/utils";
import type { HistoryResponse, WeatherAlert, WeatherResponse } from "@/lib/types";

export function ReadinessRing({ done, applicable }: { done: number; applicable: number }) {
  const pct = applicable ? done / applicable : 1;
  const r = 40;
  const c = 2 * Math.PI * r;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Readiness</CardTitle>
        <Provenance kind="SYNTHETIC" detail="Counts tasks completed in this demo." />
      </CardHeader>
      <CardBody className="flex items-center gap-4">
        <svg width="96" height="96" viewBox="0 0 100 100" role="img" aria-label={`${done} of ${applicable} tasks done`}>
          <circle cx="50" cy="50" r={r} fill="none" stroke="var(--surface-2)" strokeWidth="10" />
          <circle
            cx="50" cy="50" r={r} fill="none" stroke="var(--accent)" strokeWidth="10" strokeLinecap="round"
            strokeDasharray={c} strokeDashoffset={c * (1 - pct)} transform="rotate(-90 50 50)"
            style={{ transition: "stroke-dashoffset 400ms ease" }}
          />
          <text x="50" y="56" textAnchor="middle" className="fill-ink text-[22px] font-bold">
            {Math.round(pct * 100)}%
          </text>
        </svg>
        <p className="text-sm">
          <strong data-testid="readiness-count">
            {done} of {applicable}
          </strong>{" "}
          applicable tasks done. Each finished task lowers the chance of a preventable loss.
        </p>
      </CardBody>
    </Card>
  );
}

const SEV: Record<string, string> = {
  Extreme: "border-clay bg-clay-soft",
  Severe: "border-clay bg-clay-soft",
  Moderate: "border-amber bg-amber-soft",
};

export function WeatherCard({ weather, alerts, alertsError }: { weather: WeatherResponse; alerts: WeatherAlert[]; alertsError: string | null }) {
  const today = weather.daily[0];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Weather &amp; alerts</CardTitle>
        {weather.provenance && <Provenance kind={weather.provenance} detail={(weather.sources ?? []).join(" + ")} />}
      </CardHeader>
      <CardBody className="space-y-3">
        {weather.error || !today ? (
          <p role="status" className="rounded-lg bg-surface-2 p-3 text-sm">
            Weather is temporarily unavailable. We never show a made-up forecast — check weather.gov and try again soon.
          </p>
        ) : (
          <p className="text-sm">
            <span className="text-3xl font-semibold tabular-nums" data-testid="today-high">
              {today.max_f != null ? Math.round(today.max_f) : "—"}°F
            </span>{" "}
            <span className="text-muted">
              high today · low {today.min_f != null ? Math.round(today.min_f) : "—"}°F
              {today.precip_in ? ` · ${today.precip_in.toFixed(2)} in rain` : ""}
            </span>
          </p>
        )}
        {alertsError && <p className="text-sm text-muted">Official alerts could not be checked right now.</p>}
        {alerts.length === 0 && !alertsError ? (
          <p className="text-sm text-muted" data-testid="no-alerts">
            No active weather alerts for your location.
          </p>
        ) : (
          <ul className="space-y-2">
            {alerts.map((a) => (
              <li key={a.id} className={cn("rounded-lg border-l-4 p-3 text-sm", SEV[a.severity ?? ""] ?? "border-line bg-surface-2")} data-testid="alert-item">
                <p className="flex flex-wrap items-center gap-2 font-semibold">
                  <AlertTriangle className="h-4 w-4" aria-hidden /> {a.event} <Provenance kind={a.provenance} />
                </p>
                <p className="mt-1">{a.headline}</p>
                {a.ends && <p className="mt-1 text-xs text-muted">Until {fmtDate(a.ends, { weekday: "short", hour: "numeric", minute: "2-digit" })}</p>}
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

export function HistoryTeaser({ history, city }: { history: HistoryResponse; city: string }) {
  const a = history.weather.avg_per_year;
  const items = [
    { icon: Thermometer, label: "days at 110°F or higher", value: a.days_ge_110f },
    { icon: Snowflake, label: "nights at 28°F or lower", value: a.nights_le_28f },
    { icon: Droplets, label: "inches of monsoon rain", value: a.monsoon_precip_in },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>{city} history</CardTitle>
        <Provenance kind="HISTORIC" detail={`${history.weather.source}`} />
      </CardHeader>
      <CardBody>
        <p className="mb-2 text-xs text-muted">Average per year, {history.weather.years[0]}–{history.weather.years.at(-1)}</p>
        <ul className="grid grid-cols-3 gap-2 text-center">
          {items.map(({ icon: Icon, label, value }) => (
            <li key={label} className="rounded-lg bg-surface-2 p-2">
              <Icon className="mx-auto h-4 w-4 text-muted" aria-hidden />
              <span className="block text-xl font-semibold tabular-nums">{value ?? "—"}</span>
              <span className="block text-[11px] leading-tight text-muted">{label}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-sm">
          FEMA National Risk Index for your area: <strong>{history.risk_index.risk_rating}</strong>.
        </p>
        <Link href="/place" className="mt-2 inline-flex min-h-[44px] items-center gap-1 text-sm font-semibold text-accent-text underline underline-offset-2">
          See local history <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </CardBody>
    </Card>
  );
}
