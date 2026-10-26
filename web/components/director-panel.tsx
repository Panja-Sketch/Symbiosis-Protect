"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { CalendarClock, CloudLightning, Flame, Snowflake, Undo2, Waves, Wind } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { Button } from "@/components/ui/button";

const API = "/backend/api/v1";

interface DirState {
  fake_now: string | null;
  now: string;
  injections: { kind: string; label: string; created_at: string }[];
}
interface Evaluated {
  account_id: string;
  created: string[];
  alerts: string[];
}

const WEATHER = [
  { kind: "freeze_flagstaff", label: "Freeze Warning – Flagstaff", icon: Snowflake },
  { kind: "heat_phoenix", label: "Extreme Heat Warning – Phoenix metro", icon: Flame },
  { kind: "storm_flood_valley", label: "Severe Thunderstorm + Flash Flood Warning – Tempe/Mesa", icon: CloudLightning },
  { kind: "dust_i10", label: "Dust Storm Warning – I-10", icon: Wind },
];
const DEVICES = [
  { device_id: "dev-p5-3b", scenario: "slow_leak", label: "Slow leak – Mesa Palms Unit 3B" },
  { device_id: "dev-p1-main", scenario: "burst", label: "Burst – Maya's laundry" },
  { device_id: "dev-p6-cooler1", scenario: "cooler_drift", label: "Cooler temperature drift – Desert Bloom" },
  { device_id: "dev-p4-riser", scenario: "freeze_drop", label: "Stockroom cold – Ponderosa riser" },
];
const PRESETS = [
  { label: "Pretend it's July 18 (monsoon)", iso: "2026-07-18T19:00:00+00:00" },
  { label: "Pretend it's Dec 22 (holiday closure)", iso: "2026-12-22T19:00:00+00:00" },
];

function dayOfYear(d: Date) {
  return Math.round((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - Date.UTC(d.getUTCFullYear(), 0, 0)) / 86400000);
}
function fromDay(n: number) {
  return new Date(Date.UTC(2026, 0, n, 19, 0, 0));
}

export function DirectorPanel({ names }: { names: Record<string, string> }) {
  const [st, setSt] = useState<DirState | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [day, setDay] = useState(dayOfYear(new Date("2026-10-25T12:00:00Z")));

  const refresh = useCallback(async () => {
    const r = await fetch(`${API}/director/state`, { cache: "no-store" });
    if (r.ok) setSt(await r.json());
  }, []);
  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function run(label: string, path: string, body?: object) {
    setBusy(true);
    const r = await fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : "{}" });
    setBusy(false);
    if (!r.ok) {
      setLog((l) => [`${label}: failed (${r.status})`, ...l]);
      return;
    }
    const data = await r.json();
    const ev: Evaluated[] = data.evaluated ?? [];
    const changed = ev.filter((e) => e.created.length || e.alerts.length).map((e) => `${names[e.account_id] ?? e.account_id}: +${e.created.length} task(s), +${e.alerts.length} alert(s)`);
    setLog((l) => [`${label} → ${changed.length ? changed.join(" · ") : "applied"}`, ...l].slice(0, 12));
    await refresh();
  }

  const btn = "justify-start text-left whitespace-normal py-2 h-auto";
  const travelDate = fromDay(day);
  return (
    <div className="space-y-6">
      <section className="rounded-card border border-line bg-surface p-4" aria-labelledby="clock-h">
        <h2 id="clock-h" className="font-display text-lg font-semibold">
          Demo clock
        </h2>
        <p className="mt-1 text-sm" data-testid="director-clock">
          {st?.fake_now ? (
            <>
              Pretending it is <strong>{new Date(st.fake_now).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "America/Phoenix" })}</strong>. Weather is
              built from 1991–2020 normals and labelled SIMULATED.
            </>
          ) : (
            <>Real time. Weather is LIVE unless a scenario below is injected.</>
          )}
        </p>
        {st && st.injections.length > 0 && (
          <ul className="mt-2 flex flex-wrap gap-2 text-xs" data-testid="active-injections">
            {st.injections.map((i) => (
              <li key={i.kind} className="rounded-full border border-clay/50 bg-clay-soft px-2 py-1 text-clay-text">
                {i.label} <Provenance kind="SIMULATED" />
              </li>
            ))}
          </ul>
        )}
        <div className="mt-3 flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <Button key={p.iso} variant="secondary" disabled={busy} onClick={() => run(p.label, "/director/time-travel", { to: p.iso })}>
              <CalendarClock className="h-4 w-4" aria-hidden /> {p.label}
            </Button>
          ))}
          <Button variant="ghost" disabled={busy} onClick={() => run("Back to today", "/director/time-travel", { to: null })}>
            <Undo2 className="h-4 w-4" aria-hidden /> Back to today
          </Button>
        </div>
        <div className="mt-4">
          <label htmlFor="travel" className="block text-sm font-medium">
            Travel to any day in 2026: <strong>{travelDate.toLocaleDateString("en-US", { month: "long", day: "numeric", timeZone: "UTC" })}</strong>
          </label>
          <div className="flex items-center gap-3">
            <input
              id="travel"
              type="range"
              min={1}
              max={365}
              value={day}
              onChange={(e) => setDay(Number(e.target.value))}
              aria-valuetext={travelDate.toLocaleDateString("en-US", { month: "long", day: "numeric", timeZone: "UTC" })}
              className="h-11 w-full"
            />
            <Button disabled={busy} onClick={() => run(`Time travel to ${travelDate.toISOString().slice(0, 10)}`, "/director/time-travel", { to: travelDate.toISOString() })} data-testid="travel-go">
              Go
            </Button>
          </div>
        </div>
      </section>

      <section aria-labelledby="wx-h" className="space-y-2">
        <h2 id="wx-h" className="font-display text-lg font-semibold">
          Weather events <Provenance kind="SIMULATED" />
        </h2>
        <div className="grid gap-2 md:grid-cols-2">
          {WEATHER.map(({ kind, label, icon: Icon }) => (
            <Button key={kind} variant="secondary" className={btn} disabled={busy} onClick={() => run(label, "/director/inject", { kind })} data-testid={`inject-${kind}`}>
              <Icon className="h-5 w-5 shrink-0" aria-hidden /> {label}
            </Button>
          ))}
        </div>
      </section>

      <section aria-labelledby="dev-h" className="space-y-2">
        <h2 id="dev-h" className="font-display text-lg font-semibold">
          Device events <Provenance kind="SIMULATED" />
        </h2>
        <div className="grid gap-2 md:grid-cols-2">
          {DEVICES.map((d) => (
            <Button key={d.device_id} variant="secondary" className={btn} disabled={busy} onClick={() => run(d.label, "/director/device", { device_id: d.device_id, scenario: d.scenario })} data-testid={`device-${d.device_id}`}>
              <Waves className="h-5 w-5 shrink-0" aria-hidden /> {d.label}
            </Button>
          ))}
        </div>
        <p className="text-sm text-muted">
          After a device event, open the <Link href="/sense" className="font-semibold text-accent-text underline">Sense</Link> screen as that persona.
        </p>
      </section>

      <section aria-labelledby="reset-h" className="space-y-2">
        <h2 id="reset-h" className="font-display text-lg font-semibold">
          Reset
        </h2>
        <Button variant="danger" disabled={busy} onClick={() => run("Reset demo", "/director/reset")} data-testid="director-reset">
          Reset demo
        </Button>
        <p className="text-sm text-muted">Clears injected events, time travel, tasks, alerts, proofs, cases and owner edits, then re-evaluates every account.</p>
      </section>

      {log.length > 0 && (
        <section aria-labelledby="log-h">
          <h2 id="log-h" className="font-display text-lg font-semibold">
            What just happened
          </h2>
          <ul className="mt-2 space-y-1 text-sm" aria-live="polite" data-testid="director-log">
            {log.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
