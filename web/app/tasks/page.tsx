import Link from "next/link";
import { Provenance } from "@/components/provenance";
import { TaskList } from "@/components/task-list";
import { apiGet } from "@/lib/api";
import { policyholderOnly } from "@/lib/session";
import { cn, fmtDate } from "@/lib/utils";
import type { EvidenceResponse, Policy, TasksResponse } from "@/lib/types";
import { EvidenceTab } from "@/components/evidence-tab";

const TABS = [
  { key: "do_now", label: "Do now" },
  { key: "coming_up", label: "Coming up" },
  { key: "done", label: "Done" },
  { key: "evidence", label: "Evidence" },
] as const;

export default async function TasksPage({ searchParams }: { searchParams: { tab?: string; open?: string } }) {
  const { account_id } = policyholderOnly();
  const tab = TABS.find((t) => t.key === searchParams.tab)?.key ?? "do_now";
  const [res, counts, policies] = await Promise.all([
    apiGet<TasksResponse>(`/accounts/${account_id}/tasks?status=${tab === "evidence" ? "done" : tab}`),
    apiGet<TasksResponse>(`/accounts/${account_id}/tasks?status=open`),
    apiGet<Policy[]>(`/accounts/${account_id}/policies`),
  ]);
  const evidence = tab === "evidence" ? await apiGet<EvidenceResponse>(`/accounts/${account_id}/evidence`) : null;
  const policy = await apiGet<Policy>(`/policies/${policies[0].id}`);
  const n = { do_now: counts.tasks.filter((t) => t.bucket === "do_now").length, coming_up: counts.tasks.filter((t) => t.bucket === "coming_up").length };
  const openId = searchParams.open && [...res.tasks, ...counts.tasks].some((t) => t.id === searchParams.open) ? searchParams.open : undefined;

  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold md:text-3xl">Tasks</h1>
      <nav aria-label="Task lists" className="flex gap-1 rounded-xl bg-surface-2 p-1">
        {TABS.map((t) => (
          <Link
            key={t.key}
            href={`/tasks?tab=${t.key}`}
            aria-current={tab === t.key ? "page" : undefined}
            className={cn(
              "flex min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-lg px-3 text-sm font-semibold",
              tab === t.key ? "bg-surface shadow-sm" : "text-muted hover:text-ink",
            )}
          >
            {t.label}
            {(t.key === "do_now" || t.key === "coming_up") && <span className="rounded-full bg-surface-2 px-1.5 text-xs">{n[t.key]}</span>}
          </Link>
        ))}
      </nav>

      {tab === "evidence" ? (
        <EvidenceTab evidence={evidence} />
      ) : (
      <TaskList
        tasks={res.tasks}
        policy={policy}
        openId={openId}
        empty={tab === "done" ? "Nothing completed yet in this session." : "Nothing here right now."}
      />
      )}

      {tab === "done" && res.history.length > 0 && (
        <section aria-labelledby="past-h" className="space-y-2">
          <h2 id="past-h" className="font-display text-lg font-semibold">
            Earlier this year
          </h2>
          <ul className="divide-y divide-line rounded-card border border-line bg-surface">
            {res.history.map((h) => (
              <li key={h.id} className="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
                <span>
                  <span className="font-medium">{h.title}</span>
                  <span className="block text-xs text-muted">
                    {h.status} · {fmtDate(h.closed_at)} {h.proof_level ? `· proof ${h.proof_level}` : ""}
                  </span>
                </span>
                <Provenance kind={h.provenance} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
