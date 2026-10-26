"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { CheckCircle2, Clock, MapPin, Wallet } from "lucide-react";
import { ProofCapture } from "@/components/proof-capture";
import { Provenance } from "@/components/provenance";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { cn, usd } from "@/lib/utils";
import type { Policy, Task } from "@/lib/types";

const PRIORITY: Record<Task["priority"], string> = {
  high: "bg-clay-soft text-clay-text border-clay/50",
  medium: "bg-amber-soft text-amber-text border-amber/50",
  low: "bg-surface-2 text-ink border-line",
};

function Pills({ t }: { t: Task }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className={cn("rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase", PRIORITY[t.priority])}>{t.priority}</span>
      <Provenance kind={t.provenance} detail={`Inputs: ${t.inputs_snapshot.input_provenance.join(", ")}.`} />
      {t.source !== "rule" && <span className="rounded-full border border-line px-2 py-0.5 text-[11px] font-semibold uppercase">From {t.source}</span>}
    </div>
  );
}

function ShareToggle({ task }: { task: Task }) {
  const router = useRouter();
  const [shared, setShared] = useState(task.visibility === "shared");
  const [err, setErr] = useState<string | null>(null);
  if (task.source !== "rule") {
    return <p className="mt-3 text-xs text-muted">Issued by your {task.source}; it is visible to them.</p>;
  }
  if (task.status === "declined") return null;
  async function change(next: boolean) {
    setErr(null);
    const r = await fetch(`/backend/api/v1/tasks/${task.id}/visibility`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ visibility: next ? "shared" : "private" }),
    });
    if (r.ok) {
      setShared(next);
      router.refresh();
    } else setErr("Could not change sharing.");
  }
  return (
    <div className="mt-4 rounded-lg bg-surface-2 p-3 text-sm">
      <label className="flex min-h-[44px] items-start gap-3">
        <input type="checkbox" checked={shared} onChange={(e) => change(e.target.checked)} className="mt-1 h-5 w-5" data-testid="share-task" />
        <span>
          <strong>Share this task and its proof with my insurer and agent</strong>
          <span className="block text-muted">{shared ? "They can see this task and any proof you add." : "Private: only you can see this task."}</span>
        </span>
      </label>
      {err && (
        <p role="alert" className="text-clay-text">
          {err}
        </p>
      )}
    </div>
  );
}

function CoverageLens({ task, policy, onClose }: { task: Task; policy: Policy; onClose: () => void }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string | null>(null);
  const note = task.coverage_note_key ? policy.coverage_notes[task.coverage_note_key] : null;
  const covs = task.coverage_codes
    .map((c) => ({ code: c, cov: policy.coverages.find((x) => x.code === c), end: policy.endorsements.find((x) => x.code === c), ex: policy.exclusions_plain.find((x) => x.code === c) }))
    .filter((x) => x.cov || x.end || x.ex);

  async function act(path: string, body?: object) {
    setErr(null);
    const r = await fetch(`/backend/api/v1/tasks/${task.id}/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
    if (!r.ok) {
      setErr((await r.json().catch(() => ({}))).detail ?? "Something went wrong");
      return;
    }
    onClose();
    start(() => router.refresh());
  }

  const h = "mt-5 font-display text-base font-semibold first:mt-0";
  return (
    <div data-testid="coverage-lens">
      <Pills t={task} />
      <h3 className={h}>What could happen</h3>
      <p className="mt-1 text-sm">{task.why}</p>

      <h3 className={h}>What your policy says</h3>
      {note && (
        <div className="mt-1 rounded-lg bg-accent-soft p-3 text-sm text-ink">
          <p className="font-semibold">{note.title}</p>
          <p className="mt-1">{note.plain}</p>
        </div>
      )}
      <ul className="mt-2 flex flex-wrap gap-2">
        {covs.map(({ code, cov, end, ex }) => (
          <li key={code} className="rounded-lg border border-line bg-surface px-3 py-2 text-xs" data-testid="coverage-chip">
            <span className="block font-semibold">{cov?.name_plain ?? end?.name_plain ?? ex?.title}</span>
            <span className="text-muted">
              {cov ? `${cov.limit_usd ? `Limit ${usd(cov.limit_usd)}` : cov.limit_note ?? "See policy"}` : end ? (end.present ? "Included" : "Not on your policy") : "Exclusion"}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-muted">{policy.summary_disclaimer}</p>

      <h3 className={h}>What to do</h3>
      <ol className="mt-2 list-decimal space-y-2 pl-5 text-sm">
        {task.steps.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ol>
      <p className="mt-3 flex flex-wrap gap-4 text-sm text-muted">
        {task.est_minutes != null && (
          <span className="inline-flex items-center gap-1">
            <Clock className="h-4 w-4" aria-hidden /> About {task.est_minutes} min
          </span>
        )}
        {task.est_cost_usd && (
          <span className="inline-flex items-center gap-1">
            <Wallet className="h-4 w-4" aria-hidden /> {task.est_cost_usd[1] === 0 ? "Free" : `${usd(task.est_cost_usd[0])}–${usd(task.est_cost_usd[1])}`}
          </span>
        )}
      </p>

      <h3 className={h}>Why now</h3>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
        {task.inputs_snapshot.reasons.map((r, i) => (
          <li key={i}>{r}</li>
        ))}
      </ul>

      <ShareToggle task={task} />

      <h3 className={h}>Proof</h3>
      {task.status === "done" ? (
        <div className="mt-1 space-y-2 text-sm" data-testid="proof-done">
          <p className="text-saguaro-text">
            <CheckCircle2 className="mr-1 inline h-4 w-4" aria-hidden />
            Done with proof level {task.proof[0]?.level} ({task.proof[0]?.type}).
          </p>
          <p>
            SHA-256 <code className="break-all text-xs" data-testid="proof-hash">{task.proof[0]?.sha256}</code>
          </p>
          {task.proof[0]?.lat != null && (
            <p>
              <MapPin className="mr-1 inline h-4 w-4" aria-hidden />
              Location {task.proof[0].lat?.toFixed(4)}, {task.proof[0].lon?.toFixed(4)} (from your device)
            </p>
          )}
          {task.proof[0]?.uri && (
            <a
              className="inline-flex min-h-[44px] items-center font-semibold text-accent-text underline"
              href={`/backend/api/v1/proofs/${task.proof[0].id}/file?download=true`}
            >
              Download your proof file
            </a>
          )}
        </div>
      ) : (
        <>
          <ProofCapture
            task={task}
            onSubmitted={() => {
              onClose();
              start(() => router.refresh());
            }}
          />
          {err && (
            <p role="alert" className="mt-2 rounded-lg bg-clay-soft p-2 text-sm text-clay-text">
              {err}
            </p>
          )}
          <div className="mt-3 flex flex-wrap gap-2 border-t border-line pt-3">
            <Button variant="secondary" disabled={pending} onClick={() => act("defer", { hours: 24 })}>
              Remind me tomorrow
            </Button>
            <Button variant="ghost" disabled={pending} onClick={() => act("decline")}>
              Not applicable
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

export function TaskList({ tasks, policy, openId, empty }: { tasks: Task[]; policy: Policy; openId?: string; empty: string }) {
  const [openTask, setOpenTask] = useState<string | null>(openId ?? null);
  useEffect(() => setOpenTask(openId ?? null), [openId]);
  const current = tasks.find((t) => t.id === openTask);

  if (tasks.length === 0) return <p className="rounded-card border border-dashed border-line p-6 text-center text-sm text-muted">{empty}</p>;
  return (
    <>
      <ul className="space-y-3">
        {tasks.map((t) => (
          <li key={t.id}>
            <button
              type="button"
              onClick={() => setOpenTask(t.id)}
              data-testid="task-card"
              className="w-full rounded-card border border-line bg-surface p-4 text-left transition-shadow hover:shadow-lift"
            >
              <Pills t={t} />
              <span className="mt-2 block font-display text-base font-semibold leading-snug">{t.title}</span>
              <span className="mt-1 line-clamp-2 block text-sm text-muted">{t.why}</span>
              <span className="mt-2 flex flex-wrap gap-4 text-xs text-muted">
                {t.est_minutes != null && <span>About {t.est_minutes} min</span>}
                {t.status !== "open" && <span className="font-semibold uppercase">{t.status}</span>}
                <span className="font-semibold text-accent-text">Why this, why now →</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      <Sheet open={!!current} onOpenChange={(o) => !o && setOpenTask(null)}>
        {current && (
          <SheetContent title={current.title} description="Coverage Lens: what could happen, what your policy says, what to do.">
            <CoverageLens task={current} policy={policy} onClose={() => setOpenTask(null)} />
          </SheetContent>
        )}
      </Sheet>
    </>
  );
}
