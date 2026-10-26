import { ClientCard } from "@/components/client-card";
import { Provenance } from "@/components/provenance";
import { apiGet } from "@/lib/api";
import { roleOnly } from "@/lib/session";
import type { ClientRow } from "@/lib/role-types";

export default async function AgentPage() {
  roleOnly("agent");
  const book = await apiGet<{ clients: ClientRow[]; visibility_note: string }>("/agent/book", "agent");
  const clients = [...book.clients].sort((a, b) => b.exposure.active_alerts.length - a.exposure.active_alerts.length || a.persona_id.localeCompare(b.persona_id));
  const alerted = clients.filter((c) => c.exposure.active_alerts.length > 0).length;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="font-display text-2xl font-semibold md:text-3xl">My book</h1>
          <p className="text-sm text-muted">
            {clients.length} clients · <strong data-testid="alerted-count">{alerted}</strong> under an active weather alert
          </p>
        </div>
        <Provenance kind="SYNTHETIC" detail="Synthetic independent agency and clients." />
      </div>
      <p className="rounded-lg bg-surface-2 p-3 text-sm">{book.visibility_note}</p>
      <div className="grid gap-4 xl:grid-cols-2">
        {clients.map((c) => (
          <ClientCard key={c.account_id} c={c} />
        ))}
      </div>
    </div>
  );
}
