import { AskChat } from "@/components/ask-chat";
import { apiGet } from "@/lib/api";
import { policyholderOnly } from "@/lib/session";
import type { AccountResponse } from "@/lib/types";

export default async function AskPage() {
  const { account_id } = policyholderOnly();
  const [{ starters }, acct] = await Promise.all([
    apiGet<{ starters: string[] }>(`/assistant/starters?account_id=${account_id}`),
    apiGet<AccountResponse>(`/accounts/${account_id}`),
  ]);
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="font-display text-2xl font-semibold md:text-3xl">Ask about my coverage</h1>
        <p className="mt-1 text-sm text-muted">
          Answers come only from your policy summary and show which coverage they are based on. Advice on claims, pricing or legal questions goes
          to your agent.
        </p>
      </div>
      <AskChat accountId={account_id} starters={starters} agentPhone={acct.agent.phone} />
    </div>
  );
}
