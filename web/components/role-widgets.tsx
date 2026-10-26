"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Download, Send, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

const BASE = "/backend/api/v1";

export function ExportButton({ policyId, role }: { policyId: string; role: string }) {
  const [state, setState] = useState<{ hash: string; pkg: string; scope: string } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function run() {
    setBusy(true);
    setErr(null);
    const r = await fetch(`${BASE}/evidence/${policyId}/export`, { method: "POST", headers: { "X-Demo-Role": role } });
    setBusy(false);
    if (!r.ok) {
      setErr("Export failed.");
      return;
    }
    const blob = await r.blob();
    const hash = r.headers.get("x-manifest-sha256") ?? "";
    const pkg = r.headers.get("x-package-id") ?? "";
    setState({ hash, pkg, scope: r.headers.get("x-package-scope") ?? "" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `evidence_${policyId}_${pkg}.zip`;
    a.click();
    URL.revokeObjectURL(a.href);
    router.refresh();
  }

  return (
    <div className="space-y-2">
      <Button onClick={run} disabled={busy} data-testid="export-zip">
        <Download className="h-4 w-4" aria-hidden /> {busy ? "Building…" : "Export evidence package (ZIP)"}
      </Button>
      {err && (
        <p role="alert" className="text-sm text-clay-text">
          {err}
        </p>
      )}
      {state && (
        <p className="text-sm" data-testid="export-result">
          <ShieldCheck className="mr-1 inline h-4 w-4 text-saguaro-text" aria-hidden />
          Package {state.pkg} ({state.scope.replace("_", " ")}). Manifest SHA-256 <code className="break-all text-xs" data-testid="export-hash">{state.hash}</code>
        </p>
      )}
    </div>
  );
}

export function IssueForm({ accountId, role }: { accountId: string; role: string }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const field = "min-h-[44px] w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm";

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const steps = String(f.get("steps")).split("\n").map((s) => s.trim()).filter(Boolean);
    const r = await fetch(`${BASE}/tasks/issue`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Demo-Role": role },
      body: JSON.stringify({ account_id: accountId, title: f.get("title"), why: f.get("why"), steps, priority: f.get("priority"), due_in_days: Number(f.get("due")) }),
    });
    if (r.ok) {
      setMsg({ ok: true, text: "Issued. It now shows on the policyholder's Do-now list as coming from you, and cannot be hidden by them." });
      (e.target as HTMLFormElement).reset();
      start(() => router.refresh());
    } else {
      const body = await r.json().catch(() => ({}));
      setMsg({ ok: false, text: typeof body.detail === "string" ? body.detail : "Check the fields: title 5+ characters, reason 10+, at least one step." });
    }
  }

  return (
    <form onSubmit={submit} className="grid gap-3" data-testid="issue-form">
      <label className="text-sm">
        <span className="mb-1 block font-medium">Recommendation title</span>
        <input name="title" required minLength={5} maxLength={140} className={field} placeholder="Install a leak sensor at the water heater" />
      </label>
      <label className="text-sm">
        <span className="mb-1 block font-medium">Why (shown to the policyholder)</span>
        <textarea name="why" required minLength={10} maxLength={600} rows={2} className={field} />
      </label>
      <label className="text-sm">
        <span className="mb-1 block font-medium">Steps (one per line)</span>
        <textarea name="steps" required rows={3} className={field} />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="text-sm">
          <span className="mb-1 block font-medium">Priority</span>
          <select name="priority" defaultValue="medium" className={field}>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium">Due in (days)</span>
          <input name="due" type="number" min={1} max={120} defaultValue={14} className={field} />
        </label>
      </div>
      <Button type="submit" disabled={pending}>
        <Send className="h-4 w-4" aria-hidden /> Issue recommendation
      </Button>
      {msg && (
        <p role={msg.ok ? "status" : "alert"} className={msg.ok ? "text-sm text-saguaro-text" : "text-sm text-clay-text"}>
          {msg.text}
        </p>
      )}
    </form>
  );
}
