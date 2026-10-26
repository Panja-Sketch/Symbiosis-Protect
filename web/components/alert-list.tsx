"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Bell, CloudLightning, ListChecks, Radio, UserRound } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { cn, fmtDate } from "@/lib/utils";
import type { AlertRow } from "@/lib/types";

const FILTERS = ["all", "weather", "task", "device", "agent"] as const;
const ICON = { weather: CloudLightning, task: ListChecks, device: Radio, agent: UserRound } as const;
const SEV: Record<string, string> = { critical: "border-clay", warning: "border-clay", watch: "border-amber", info: "border-line" };

export function AlertList({ alerts }: { alerts: AlertRow[] }) {
  const router = useRouter();
  const [, start] = useTransition();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const rows = alerts.filter((a) => filter === "all" || a.kind === filter);

  async function read(id: string) {
    await fetch(`/backend/api/v1/alerts/${id}/read`, { method: "POST" });
    start(() => router.refresh());
  }

  return (
    <div className="space-y-3">
      <div role="group" aria-label="Filter alerts" className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            aria-pressed={filter === f}
            onClick={() => setFilter(f)}
            className={cn(
              "min-h-[44px] rounded-full border px-4 text-sm font-semibold capitalize",
              filter === f ? "border-accent-strong bg-accent-soft text-accent-text" : "border-line bg-surface",
            )}
          >
            {f}
          </button>
        ))}
      </div>
      {rows.length === 0 ? (
        <p className="rounded-card border border-dashed border-line p-6 text-center text-sm text-muted" data-testid="no-alert-rows">
          <Bell className="mx-auto mb-2 h-6 w-6" aria-hidden />
          No alerts here yet. Official weather alerts and new high-priority tasks appear in this list.
        </p>
      ) : (
        <ul className="space-y-2">
          {rows.map((a) => {
            const Icon = ICON[a.kind as keyof typeof ICON] ?? Bell;
            return (
              <li key={a.id} className={cn("rounded-card border border-l-4 bg-surface p-4", SEV[a.severity] ?? "border-line")} data-testid="alert-row">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="flex items-center gap-2 font-semibold">
                    <Icon className="h-4 w-4" aria-hidden /> {a.title}
                    {!a.read_at && <span className="rounded-full bg-clay-text px-2 text-[11px] font-bold text-white dark:text-[#2a1008]">NEW</span>}
                  </p>
                  <Provenance kind={a.provenance} />
                </div>
                <p className="mt-1 text-sm">{a.body}</p>
                <p className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted">
                  <span>{fmtDate(a.created_at, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</span>
                  <span>Sent via {a.sent_channels.length ? a.sent_channels.map((c) => c.replace("_", " ")).join(", ") : "—"}</span>
                  {a.deep_link && (
                    <Link href={a.deep_link} className="inline-flex min-h-[44px] items-center font-semibold text-accent-text underline underline-offset-2">
                      Open
                    </Link>
                  )}
                  {!a.read_at && (
                    <button type="button" onClick={() => read(a.id)} className="min-h-[44px] font-semibold text-accent-text underline underline-offset-2">
                      Mark read
                    </button>
                  )}
                </p>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
