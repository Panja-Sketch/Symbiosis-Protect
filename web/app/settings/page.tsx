import { SettingsForm } from "@/components/settings-form";
import { apiGet } from "@/lib/api";
import { policyholderOnly } from "@/lib/session";
import type { AccountResponse } from "@/lib/types";

export default async function SettingsPage() {
  const { account_id } = policyholderOnly();
  const acct = await apiGet<AccountResponse & { preferences: { channels: string[]; quiet_hours: [string, string] | null; share_default: boolean } }>(`/accounts/${account_id}`);
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-semibold md:text-3xl">Settings</h1>
      <SettingsForm accountId={account_id} prefs={acct.preferences} agentName={acct.agent.name} />
    </div>
  );
}
