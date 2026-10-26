"use client";

import Link from "next/link";
import { useState } from "react";
import { Cloud, CloudLightning, CloudRain, Pin, Snowflake, Sun, Thermometer } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { cn, fmtDate } from "@/lib/utils";
import type { Ribbon, RibbonDay } from "@/lib/types";

const ICONS: Record<string, typeof Sun> = { sun: Sun, heat: Thermometer, freeze: Snowflake, rain: CloudRain, storm: CloudLightning, unknown: Cloud };
const RISK_LABEL = { none: "Calm", elevated: "Watch", high: "High risk" } as const;
const RISK_STYLE = {
  none: "border-line bg-surface",
  elevated: "border-amber bg-amber-soft",
  high: "border-clay bg-clay-soft",
} as const;

function Tile({ day, selected, onSelect }: { day: RibbonDay; selected: boolean; onSelect: () => void }) {
  const Icon = ICONS[day.icon] ?? Cloud;
  const label = new Date(day.date + "T12:00:00").toLocaleDateString("en-US", { weekday: "short", day: "numeric" });
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      data-testid="ribbon-day"
      data-risk={day.risk}
      className={cn(
        "relative flex min-h-[128px] w-[84px] shrink-0 snap-start flex-col items-center justify-between rounded-card border-2 p-2 text-center transition-shadow",
        RISK_STYLE[day.risk],
        selected && "shadow-lift ring-2 ring-accent-strong ring-offset-2 ring-offset-bg",
      )}
    >
      <span className="text-xs font-semibold">{label}</span>
      <Icon className="h-6 w-6" aria-hidden />
      <span className="text-sm font-semibold">
        {day.max_f != null ? `${Math.round(day.max_f)}°` : "—"}
        <span className="font-normal text-muted"> / {day.min_f != null ? `${Math.round(day.min_f)}°` : "—"}</span>
      </span>
      <span className="text-[11px] font-medium text-ink">{RISK_LABEL[day.risk]}</span>
      {day.task_pins.length > 0 && (
        <span className="mt-1 flex h-5 items-center justify-center gap-0.5 rounded-full bg-accent-strong px-1.5 text-[11px] font-bold text-white dark:text-[#06201f]">
          <Pin className="h-3 w-3" aria-hidden />
          {day.task_pins.length}
          <span className="sr-only"> task{day.task_pins.length > 1 ? "s" : ""}</span>
        </span>
      )}
    </button>
  );
}

/** Signature element: 7 day tiles, task pins dropped on the day they matter. Tap a day for what to do. */
export function RiskRibbon({ ribbon }: { ribbon: Ribbon }) {
  const firstPinned = Math.max(0, ribbon.days.findIndex((d) => d.task_pins.length > 0 || d.risk === "high"));
  const [sel, setSel] = useState(firstPinned);
  const day = ribbon.days[sel];

  return (
    <section aria-labelledby="ribbon-h" className="rounded-card border border-line bg-surface p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 id="ribbon-h" className="font-display text-lg font-semibold">
          Next 7 days
        </h2>
        {ribbon.provenance && <Provenance kind={ribbon.provenance} detail={ribbon.sources.join(" + ")} />}
      </div>
      <div className="-mx-1 flex snap-x gap-2 overflow-x-auto px-1 pb-2 pt-2 scrollbar-none" role="group" aria-label="Seven day forecast">
        {ribbon.days.map((d, i) => (
          <Tile key={d.date} day={d} selected={i === sel} onSelect={() => setSel(i)} />
        ))}
      </div>
      {day && (
        <div className="mt-2 rounded-lg bg-surface-2 p-3 text-sm" aria-live="polite" data-testid="ribbon-detail">
          <p className="font-semibold">
            {fmtDate(day.date, { weekday: "long", month: "short", day: "numeric" })} — {RISK_LABEL[day.risk]}
          </p>
          {day.reasons.length > 0 ? <p className="mt-1 text-muted">{day.reasons.join(" · ")}</p> : <p className="mt-1 text-muted">No weather triggers for your property this day.</p>}
          {day.task_pins.length > 0 ? (
            <ul className="mt-2 space-y-1">
              {day.task_pins.map((t) => (
                <li key={t.task_id}>
                  <Link href={`/tasks?open=${t.task_id}`} className="inline-flex min-h-[44px] items-center gap-2 font-medium text-accent-text underline underline-offset-2">
                    <Pin className="h-4 w-4" aria-hidden /> {t.title}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-muted">Nothing is scheduled for this day.</p>
          )}
        </div>
      )}
    </section>
  );
}
