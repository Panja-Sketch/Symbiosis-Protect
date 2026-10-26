"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Pencil } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { Button } from "@/components/ui/button";
import { fmtDate } from "@/lib/utils";
import type { Asset } from "@/lib/types";

const THIS_YEAR = 2026;

function AssetRow({ a }: { a: Asset }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [editing, setEditing] = useState(false);
  const [year, setYear] = useState(a.install_year?.toString() ?? "");
  const [service, setService] = useState(a.last_service_date ?? "");
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    setErr(null);
    const r = await fetch(`/backend/api/v1/assets/${a.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ install_year: year ? Number(year) : null, last_service_date: service || null }),
    });
    if (!r.ok) {
      setErr("Could not save. Check the year and date.");
      return;
    }
    setEditing(false);
    start(() => router.refresh());
  }

  const age = a.install_year ? THIS_YEAR - a.install_year : null;
  const inputCls = "min-h-[44px] w-full rounded-lg border border-line bg-surface px-3 text-sm";
  return (
    <li className="rounded-card border border-line bg-surface p-4" data-testid="asset-row">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold">{a.label}</p>
          <p className="text-sm text-muted">
            {a.install_year ? `Installed ${a.install_year} (${age} yr)` : "Age unknown"}
            {a.material ? ` · ${a.material}` : ""}
            {a.last_service_date ? ` · serviced ${fmtDate(a.last_service_date, { month: "short", year: "numeric" })}` : ""}
          </p>
          {a.notes && <p className="mt-1 text-xs text-muted">{a.notes}</p>}
        </div>
        <div className="flex items-center gap-2">
          <Provenance kind="SYNTHETIC" />
          {a.type !== "main_shutoff" && (
            <Button variant="secondary" size="sm" onClick={() => setEditing((e) => !e)} aria-expanded={editing} aria-label={`Edit ${a.label}`}>
              <Pencil className="h-4 w-4" aria-hidden /> Edit
            </Button>
          )}
        </div>
      </div>
      {editing && (
        <form
          className="mt-3 grid gap-3 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            void save();
          }}
        >
          <label className="text-sm">
            <span className="mb-1 block font-medium">Install year</span>
            <input className={inputCls} inputMode="numeric" pattern="[0-9]{4}" value={year} onChange={(e) => setYear(e.target.value)} placeholder="Unknown" />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium">Last service date</span>
            <input className={inputCls} type="date" value={service} onChange={(e) => setService(e.target.value)} />
          </label>
          {err && (
            <p role="alert" className="text-sm text-clay-text sm:col-span-2">
              {err}
            </p>
          )}
          <div className="flex gap-2 sm:col-span-2">
            <Button type="submit" disabled={pending}>
              Save
            </Button>
            <Button type="button" variant="ghost" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        </form>
      )}
    </li>
  );
}

export function AssetList({ assets }: { assets: Asset[] }) {
  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {assets.map((a) => (
        <AssetRow key={a.id} a={a} />
      ))}
    </ul>
  );
}
