import { SenseConsole } from "@/components/sense-console";
import { apiGet } from "@/lib/api";
import { getSession } from "@/lib/session";

export default async function SensePage() {
  const { account_id } = getSession();
  const { devices } = await apiGet<{ devices: never[] }>(`/devices?account_id=${account_id}`);
  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-display text-2xl font-semibold md:text-3xl">Sense</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Optional. Connect a water or temperature device and a problem opens a case: alert, action, then a fix that the sensor itself verifies.
          Devices here are <strong>simulated</strong>; no real device vendor is connected in this demo.
        </p>
      </div>
      <SenseConsole accountId={account_id} initial={devices} demo />
    </div>
  );
}
