"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { CheckCircle2, Clock, Wallet } from "lucide-react";
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

function CoverageLens({ task, policy, onClose }: { task: Task; policy: Policy; onClose: () => void }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [err, setErr] = useState<string | null>(null);
  const note = task.coverage_note_key ? policy.coverage_notes[task.coverage_note_key] : null;
  const covs = task.coverage_codes
    .map((c) => ({ code: c, cov: policy.coverages.find((x) => x.code === c), end: policy.endorsements.find((x) => x.code === c), ex: policy.exclusions_plain.find((x) => x.code === c) }))
    .filter((x) => x.cov || x.end || x.ex);
  const canAttest = task.proof_accepted.includes("E0");

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

      <h3 className={h}>Proof</h3>
      {task.status === "done" ? (
        <p className="mt-1 text-sm text-saguaro-text">
          <CheckCircle2 className="mr-1 inline h-4 w-4" aria-hidden />
          Done. Proof level {task.proof[0]?.level}; SHA-256 <code className="break-all text-xs">{task.proof[0]?.sha256}</code>
        </p>
      ) : (
        <>
          <p className="mt-1 text-sm text-muted">
            Accepted: {task.proof_accepted.join(", ")} (E0 one tap · E1 photo · E2 document). Photo and document capture arrive in the
            proof update; one-tap confirmation works now where accepted.
          </p>
          {err && (
            <p role="alert" className="mt-2 rounded-lg bg-clay-soft p-2 text-sm text-clay-text">
              {err}
            </p>
          )}
          <div className="sticky bottom-0 -mx-4 mt-4 flex flex-wrap gap-2 border-t border-line bg-surface p-4">
            <Button disabled={!canAttest || pending} onClick={() => act("complete", { level: "E0" })} className="flex-1">
              <CheckCircle2 className="h-4 w-4" aria-hidden /> I did this
            </Button>
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
