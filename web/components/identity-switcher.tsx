"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import * as DD from "@radix-ui/react-dropdown-menu";
import { Check, ChevronDown, UserRound } from "lucide-react";
import type { Persona, Role } from "@/lib/types";

const ROLE_LABEL: Record<Role, string> = { policyholder: "Policyholder", agent: "Agent", underwriter: "Underwriter" };

export function IdentitySwitcher({ personas, accountId, role }: { personas: Persona[]; accountId: string; role: Role }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const current = personas.find((p) => p.id === accountId);

  async function set(body: { account_id?: string; role?: Role }) {
    await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    start(() => router.refresh());
  }

  const item = "flex min-h-[44px] cursor-pointer items-center justify-between gap-3 rounded-md px-3 py-2 text-sm outline-none data-[highlighted]:bg-surface-2";
  return (
    <DD.Root>
      <DD.Trigger
        className="flex min-h-[44px] items-center gap-2 rounded-lg border border-line bg-surface px-3 text-sm font-medium hover:bg-surface-2"
        data-testid="identity-switcher"
      >
        <UserRound className="h-4 w-4" aria-hidden />
        <span className="hidden max-w-[160px] truncate sm:inline">{current?.display_name}</span>
        <span className="rounded bg-surface-2 px-1.5 py-0.5 text-[11px] font-semibold uppercase text-muted">{ROLE_LABEL[role]}</span>
        <ChevronDown className={`h-4 w-4 ${pending ? "animate-pulse" : ""}`} aria-hidden />
        <span className="sr-only">Demo identity menu</span>
      </DD.Trigger>
      <DD.Portal>
        <DD.Content align="end" sideOffset={6} className="z-[70] max-h-[80dvh] w-[300px] overflow-y-auto rounded-xl border border-line bg-surface p-2 shadow-lift">
          <DD.Label className="px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted">Demo identity — not a login</DD.Label>
          <DD.Label className="px-3 pt-2 text-xs font-semibold text-muted">View as</DD.Label>
          {(Object.keys(ROLE_LABEL) as Role[]).map((r) => (
            <DD.Item key={r} className={item} onSelect={() => set({ role: r })}>
              {ROLE_LABEL[r]}
              {r === role && <Check className="h-4 w-4" aria-hidden />}
            </DD.Item>
          ))}
          <DD.Separator className="my-2 h-px bg-line" />
          <DD.Label className="px-3 text-xs font-semibold text-muted">Persona (synthetic)</DD.Label>
          {personas.map((p) => (
            <DD.Item key={p.id} className={item} onSelect={() => set({ account_id: p.id })}>
              <span>
                <span className="block font-medium">{p.display_name}</span>
                <span className="block text-xs text-muted">{p.headline}</span>
              </span>
              {p.id === accountId && <Check className="h-4 w-4" aria-hidden />}
            </DD.Item>
          ))}
        </DD.Content>
      </DD.Portal>
    </DD.Root>
  );
}
