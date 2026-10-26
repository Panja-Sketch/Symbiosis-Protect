"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";

interface Prefs {
  channels: string[];
  quiet_hours: [string, string] | null;
  share_default: boolean;
}

export function SettingsForm({ accountId, prefs, agentName }: { accountId: string; prefs: Prefs; agentName: string }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [p, setP] = useState<Prefs>({ ...prefs, quiet_hours: prefs.quiet_hours ?? ["21:00", "07:00"] });
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function save() {
    setMsg(null);
    const r = await fetch(`/backend/api/v1/accounts/${accountId}/preferences`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ share_default: p.share_default, channels: p.channels, quiet_hours: p.quiet_hours }),
    });
    if (r.ok) {
      setMsg({ ok: true, text: "Saved. New tasks follow these settings." });
      start(() => router.refresh());
    } else setMsg({ ok: false, text: "Choose at least one notification channel." });
  }

  const toggleChannel = (c: string) => setP((s) => ({ ...s, channels: s.channels.includes(c) ? s.channels.filter((x) => x !== c) : [...s.channels, c] }));
  const box = "flex min-h-[44px] items-start gap-3 rounded-lg border border-line bg-surface p-3 text-sm";
  const time = "min-h-[44px] rounded-lg border border-line bg-surface px-3 text-sm";

  return (
    <form
      className="max-w-2xl space-y-6"
      onSubmit={(e) => {
        e.preventDefault();
        void save();
      }}
    >
      <fieldset className="space-y-2">
        <legend className="font-display text-lg font-semibold">Notifications</legend>
        <label className={box}>
          <input type="checkbox" checked={p.channels.includes("in_app")} onChange={() => toggleChannel("in_app")} className="mt-1 h-5 w-5" />
          <span>
            <strong>In the app</strong>
            <span className="block text-muted">Always shown in your Alerts list.</span>
          </span>
        </label>
        <label className={box}>
          <input type="checkbox" checked={p.channels.includes("email")} onChange={() => toggleChannel("email")} className="mt-1 h-5 w-5" />
          <span>
            <strong>E-mail</strong>
            <span className="block text-muted">Demo mode writes e-mails to a console log; nothing reaches a real inbox.</span>
          </span>
        </label>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <label>
            Quiet hours from <input type="time" className={time} value={p.quiet_hours?.[0] ?? "21:00"} onChange={(e) => setP({ ...p, quiet_hours: [e.target.value, p.quiet_hours?.[1] ?? "07:00"] })} />
          </label>
          <label>
            to <input type="time" className={time} value={p.quiet_hours?.[1] ?? "07:00"} onChange={(e) => setP({ ...p, quiet_hours: [p.quiet_hours?.[0] ?? "21:00", e.target.value] })} />
          </label>
        </div>
        <p className="text-xs text-muted">Critical alerts (such as a sensor-detected leak) are still delivered during quiet hours.</p>
      </fieldset>

      <fieldset className="space-y-2">
        <legend className="font-display text-lg font-semibold">What your insurer and agent can see</legend>
        <label className={box}>
          <input type="checkbox" checked={p.share_default} onChange={(e) => setP({ ...p, share_default: e.target.checked })} className="mt-1 h-5 w-5" data-testid="share-default" />
          <span>
            <strong>Share my tasks and proof with my insurer and {agentName}</strong>
            <span className="block text-muted">
              Applies to new tasks. You can change any single task from its details. Tasks you decline are always private. Recommendations
              your insurer or agent send you are visible to them.
            </span>
          </span>
        </label>
      </fieldset>

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={pending}>
          Save settings
        </Button>
        {msg && (
          <p role={msg.ok ? "status" : "alert"} className={msg.ok ? "text-sm text-saguaro-text" : "text-sm text-clay-text"}>
            {msg.text}
          </p>
        )}
      </div>
    </form>
  );
}
