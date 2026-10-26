"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Droplets, Hand, Plug, ShieldCheck, Thermometer, Waves, Wrench } from "lucide-react";
import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts";
import { Provenance } from "@/components/provenance";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Reading { ts: string; flow_lpm: number | null; leak: number | null; temp_f: number | null; humidity: number | null }
interface CaseEvent { ts: string; state: string; note: string; source: string }
interface Case {
  id: string; state: string; kind: string; unit_label: string | null; timeline: CaseEvent[]; reopen_count: number;
  manifest_sha256: string | null;
}
interface Device {
  id: string; label: string; model: string; kind: "water" | "stockroom" | "cooler"; status: string; supports_shutoff: boolean;
  unit_label: string | null; latest: Reading | null; recent: Reading[]; case: Case | null; scenarios: string[];
  state: { valve: string; scenario: string } | null;
}

const API = "/backend/api/v1";
const STATE_STYLE: Record<string, string> = {
  detected: "bg-clay-soft text-clay-text", alerted: "bg-clay-soft text-clay-text", reopened: "bg-clay-soft text-clay-text",
  acting: "bg-amber-soft text-amber-text", verifying: "bg-accent-soft text-accent-text", verified: "bg-saguaro-soft text-saguaro-text",
  not_improving: "bg-clay-soft text-clay-text", inconclusive: "bg-amber-soft text-amber-text",
};
const STATE_HELP: Record<string, string> = {
  alerted: "Act now: shut the water off and fix the source.",
  reopened: "The problem came back after it was verified. Act again.",
  acting: "Working on it. Tap I fixed it when the repair is done.",
  verifying: "Checking readings. The case closes only after the sensor shows normal readings several times in a row.",
  verified: "Verified by the sensor. The sensor keeps watching for 24 hours and reopens this case if the problem returns.",
  not_improving: "The sensor still shows a problem after the fix. Try again.",
  inconclusive: "We could not verify the fix (missing or stale sensor data). Never counted as verified.",
};

function Tile({ icon: Icon, label, value, bad }: { icon: typeof Droplets; label: string; value: string; bad?: boolean }) {
  return (
    <div className={cn("rounded-lg p-3", bad ? "bg-clay-soft" : "bg-surface-2")}>
      <p className="flex items-center gap-1 text-xs text-muted">
        <Icon className="h-3.5 w-3.5" aria-hidden /> {label}
      </p>
      <p className={cn("text-xl font-semibold tabular-nums", bad && "text-clay-text")}>{value}</p>
    </div>
  );
}

function DeviceCard({ d, demo, act }: { d: Device; demo: boolean; act: (path: string, body?: object) => Promise<void> }) {
  const r = d.latest;
  const water = d.kind === "water";
  const series = d.recent.map((x) => ({ t: x.ts, v: water ? x.flow_lpm : x.temp_f }));
  const c = d.case;
  const open = c && c.state !== "verified";
  const age = r ? Math.max(0, Math.round((Date.now() - new Date(r.ts).getTime()) / 1000)) : null;

  return (
    <article className="space-y-3 rounded-card border border-line bg-surface p-4" data-testid="device-card" data-device={d.id}>
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="font-display text-lg font-semibold">{d.label}</h2>
          <p className="text-xs text-muted">{d.model}</p>
        </div>
        <div className="flex items-center gap-2">
          <Provenance kind="SIMULATED" detail="Simulated device readings, not a real sensor." />
          <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase", d.status === "connected" ? "bg-saguaro-soft text-saguaro-text" : "bg-surface-2")}>
            {d.status}
          </span>
        </div>
      </header>

      {d.status !== "connected" ? (
        <Button onClick={() => act("/devices/connect", { device_id: d.id })} data-testid="connect">
          <Plug className="h-4 w-4" aria-hidden /> Connect (simulated)
        </Button>
      ) : (
        <>
          {r ? (
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4" data-testid="tiles">
              {water ? (
                <>
                  <Tile icon={Waves} label="Flow" value={`${r.flow_lpm?.toFixed(1)} L/min`} bad={(r.flow_lpm ?? 0) > 0.3} />
                  <Tile icon={Droplets} label="Leak sensor" value={r.leak ? "WET" : "Dry"} bad={!!r.leak} />
                  <Tile icon={Thermometer} label="Temperature" value={`${r.temp_f?.toFixed(0)}°F`} />
                  <Tile icon={Droplets} label="Humidity" value={`${r.humidity?.toFixed(0)}%`} />
                </>
              ) : (
                <Tile icon={Thermometer} label="Temperature" value={`${r.temp_f?.toFixed(1)}°F`} bad={d.kind === "cooler" ? (r.temp_f ?? 0) >= 41 : (r.temp_f ?? 99) <= 40} />
              )}
              <p className="col-span-2 self-end text-xs text-muted sm:col-span-4">
                Updated {age}s ago · valve {d.state?.valve ?? "n/a"}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted">Waiting for the first reading…</p>
          )}
          {series.length > 1 && (
            <div role="img" aria-label={`Recent ${water ? "flow" : "temperature"} readings`} className="h-20 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={series}>
                  <YAxis hide domain={["auto", "auto"]} />
                  <Line type="monotone" dataKey="v" stroke="var(--accent)" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {c && (
            <section aria-label="Case" className="space-y-3 rounded-lg border border-line p-3" data-testid="case" data-state={c.state}>
              <div className="flex flex-wrap items-center gap-2">
                <span className={cn("rounded-full px-2.5 py-1 text-xs font-bold uppercase", STATE_STYLE[c.state])} data-testid="case-state">
                  {c.state.replace("_", " ")}
                </span>
                {c.reopen_count > 0 && <span className="text-xs text-muted">Reopened {c.reopen_count}×</span>}
              </div>
              <p className="text-sm">{STATE_HELP[c.state]}</p>
              {open && (
                <div className="flex flex-wrap gap-2">
                  {water && d.supports_shutoff && ["alerted", "reopened", "not_improving", "inconclusive", "acting"].includes(c.state) && (
                    <Button variant="danger" onClick={() => act(`/cases/${c.id}/shutoff`)} data-testid="shutoff">
                      <Hand className="h-4 w-4" aria-hidden /> Shut off water
                    </Button>
                  )}
                  {["alerted", "reopened", "not_improving", "inconclusive"].includes(c.state) && (
                    <Button variant="secondary" onClick={() => act(`/cases/${c.id}/acting`)}>
                      <Wrench className="h-4 w-4" aria-hidden /> I&apos;m on it
                    </Button>
                  )}
                  {["alerted", "reopened", "acting", "not_improving", "inconclusive"].includes(c.state) && (
                    <Button onClick={() => act(`/cases/${c.id}/report-fix`)} data-testid="report-fix">
                      <CheckCircle2 className="h-4 w-4" aria-hidden /> I fixed it
                    </Button>
                  )}
                </div>
              )}
              {c.state === "verified" && c.manifest_sha256 && (
                <p className="text-xs">
                  <ShieldCheck className="mr-1 inline h-4 w-4 text-saguaro-text" aria-hidden />
                  Evidence hash <code className="break-all" data-testid="manifest-hash">{c.manifest_sha256}</code>
                </p>
              )}
              <ol className="space-y-1 border-l-2 border-line pl-3 text-xs" aria-label="Case timeline">
                {c.timeline.map((e, i) => (
                  <li key={i} data-testid="timeline-item">
                    <span className="font-semibold uppercase">{e.state.replace("_", " ")}</span> · {new Date(e.ts).toLocaleTimeString("en-US", { timeZone: "America/Phoenix" })} ·{" "}
                    <span className="text-muted">{e.source}</span>
                    <span className="block">{e.note}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {demo && (
            <details className="rounded-lg bg-surface-2 p-3 text-sm">
              <summary className="min-h-[44px] cursor-pointer font-semibold">Demo controls (SIMULATED)</summary>
              <div className="mt-2 flex flex-wrap gap-2">
                {d.scenarios.map((s) => (
                  <Button key={s} variant="secondary" size="sm" onClick={() => act("/director/device", { device_id: d.id, scenario: s })} data-testid={`scenario-${s}`}>
                    {s.replace("_", " ")}
                  </Button>
                ))}
                {water && (
                  <Button variant="ghost" size="sm" onClick={() => act("/director/device", { device_id: d.id, scenario: d.state?.scenario ?? "normal", fix_works: false })}>
                    Make the next fix fail
                  </Button>
                )}
              </div>
            </details>
          )}
        </>
      )}
    </article>
  );
}

export function SenseConsole({ accountId, initial, demo }: { accountId: string; initial: Device[]; demo: boolean }) {
  const [devices, setDevices] = useState<Device[]>(initial);
  const [err, setErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const r = await fetch(`${API}/devices?account_id=${accountId}`, { cache: "no-store" });
      if (r.ok) setDevices((await r.json()).devices);
    } catch {
      /* keep the last known state; the next poll will retry */
    }
  }, [accountId]);

  useEffect(() => {
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  async function act(path: string, body?: object) {
    setErr(null);
    const r = await fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
    if (!r.ok) setErr((await r.json().catch(() => ({}))).detail ?? "That did not work.");
    await refresh();
  }

  if (devices.length === 0) return <p className="rounded-card border border-dashed border-line p-6 text-sm text-muted">No devices are available for this property in the demo.</p>;
  return (
    <div className="space-y-4">
      {err && (
        <p role="alert" className="rounded-lg bg-clay-soft p-3 text-sm text-clay-text">
          {err}
        </p>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        {devices.map((d) => (
          <DeviceCard key={d.id} d={d} demo={demo} act={act} />
        ))}
      </div>
    </div>
  );
}
