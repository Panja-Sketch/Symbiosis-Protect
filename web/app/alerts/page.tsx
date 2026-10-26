import { AlertList } from "@/components/alert-list";
import { apiGet } from "@/lib/api";
import { getSession } from "@/lib/session";
import type { AlertRow } from "@/lib/types";

export default async function AlertsPage() {
  const { account_id } = getSession();
  const alerts = await apiGet<AlertRow[]>(`/alerts?account_id=${account_id}`);
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold md:text-3xl">Alerts</h1>
      <p className="text-sm text-muted">In-app alerts. E-mail goes to a console log in demo mode; nothing is sent to a real inbox.</p>
      <AlertList alerts={alerts} />
    </div>
  );
}
