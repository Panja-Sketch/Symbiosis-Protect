import { Download, FileCheck2, MapPin } from "lucide-react";
import { Provenance } from "@/components/provenance";
import { fmtDate } from "@/lib/utils";
import type { EvidenceResponse } from "@/lib/types";

const LEVEL_NAME: Record<string, string> = { E0: "One tap", E1: "Photo", E2: "Document", E3: "Review", E4: "Sensor" };

export function EvidenceTab({ evidence }: { evidence: EvidenceResponse | null }) {
  if (!evidence) return null;
  const { proofs, history, level_mix } = evidence;
  return (
    <div className="space-y-4" data-testid="evidence-tab">
      <p className="text-sm text-muted">
        Every completed task keeps proof you can show an agent or insurer: when it was recorded, where (only if you allowed location), and a
        SHA-256 fingerprint that changes if the file is altered.
      </p>
      {Object.keys(level_mix).length > 0 && (
        <p className="flex flex-wrap gap-2 text-sm">
          {Object.entries(level_mix).map(([l, n]) => (
            <span key={l} className="rounded-full border border-line bg-surface px-3 py-1">
              {LEVEL_NAME[l] ?? l} ({l}): <strong>{n}</strong>
            </span>
          ))}
        </p>
      )}
      {proofs.length === 0 ? (
        <p className="rounded-card border border-dashed border-line p-6 text-center text-sm text-muted">
          <FileCheck2 className="mx-auto mb-2 h-6 w-6" aria-hidden />
          No proof captured yet. Finish a task with a photo or document and it shows up here.
        </p>
      ) : (
        <ul className="space-y-2">
          {proofs.map((p) => (
            <li key={p.id} className="rounded-card border border-line bg-surface p-4 text-sm" data-testid="evidence-row">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="font-semibold">{p.task_title}</p>
                <span className="rounded-full bg-saguaro-soft px-2 py-0.5 text-[11px] font-semibold uppercase text-saguaro-text">
                  {p.level} · {p.type}
                </span>
              </div>
              <p className="mt-1 text-muted">
                Recorded {fmtDate(p.captured_at, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" })} (server time)
                {p.lat != null ? (
                  <>
                    {" · "}
                    <MapPin className="mr-0.5 inline h-3.5 w-3.5" aria-hidden />
                    {p.lat.toFixed(4)}, {p.lon?.toFixed(4)}
                  </>
                ) : (
                  " · location not shared"
                )}
              </p>
              <p className="mt-1 break-all">
                <span className="text-muted">SHA-256 </span>
                <code className="text-xs" data-testid="evidence-hash">
                  {p.sha256}
                </code>
              </p>
              {p.file_url && (
                <a
                  href={`/backend${p.file_url}?download=true`}
                  className="mt-1 inline-flex min-h-[44px] items-center gap-1 font-semibold text-accent-text underline underline-offset-2"
                >
                  <Download className="h-4 w-4" aria-hidden /> Download {p.filename ?? "file"}
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
      {history.length > 0 && (
        <section aria-labelledby="ev-hist-h">
          <h2 id="ev-hist-h" className="mb-2 font-display text-lg font-semibold">
            Earlier this year
          </h2>
          <ul className="divide-y divide-line rounded-card border border-line bg-surface">
            {history.map((h) => (
              <li key={h.id} className="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
                <span>
                  {h.title}
                  <span className="block text-xs text-muted">
                    {fmtDate(h.closed_at)} · proof {h.proof_level ?? "none"}
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
