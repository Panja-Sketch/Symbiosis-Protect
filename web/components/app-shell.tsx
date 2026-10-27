import type { ReactNode } from "react";
import Link from "next/link";
import { Clapperboard } from "lucide-react";
import { Sidebar, TabBar } from "@/components/nav";
import { IdentitySwitcher } from "@/components/identity-switcher";
import { apiTry } from "@/lib/api";
import { getSession } from "@/lib/session";
import type { AlertRow, Persona } from "@/lib/types";

const CARRIER = process.env.CARRIER_NAME || "Symbiosis Protect";

export async function AppShell({ children }: { children: ReactNode }) {
  const session = getSession();
  const [personas, alerts] = await Promise.all([
    apiTry<Persona[]>("/personas"),
    session.role === "policyholder" ? apiTry<AlertRow[]>(`/alerts?account_id=${session.account_id}`) : Promise.resolve(null),
  ]);
  const unread = (alerts ?? []).filter((a) => !a.read_at).length;
  const me = personas?.find((p) => p.id === session.account_id);

  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-[80] focus:rounded focus:bg-surface focus:p-3">
        Skip to content
      </a>
      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-line bg-surface px-4 py-2">
        <div className="flex items-center gap-2">
          <span aria-hidden className="grid h-8 w-8 place-items-center rounded-lg bg-accent-strong font-display text-sm font-bold text-white dark:text-[#06201f]">
            S
          </span>
          <div className="leading-tight">
            <p className="whitespace-nowrap font-display text-base font-semibold">{CARRIER}</p>
            <p className="hidden text-[11px] text-muted sm:block">Arizona demo · synthetic &amp; simulated data labelled on screen</p>
          </div>
        </div>
        {personas && <IdentitySwitcher personas={personas} accountId={session.account_id} role={session.role} />}
      </header>
      <div className="flex flex-1">
        <Sidebar unread={unread} role={session.role} />
        <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 pb-28 pt-4 lg:pb-8">
          {me?.preview_flag && session.role === "policyholder" && (
            <p className="mb-3 rounded-lg border border-amber/50 bg-amber-soft px-3 py-2 text-sm text-amber-text" data-testid="preview-banner">
              <strong>Personal-lines preview (AZ demo data).</strong> This carrier writes commercial and agricultural lines in Arizona; this
              persona is illustrative.
            </p>
          )}
          {children}
        </main>
      </div>
      {process.env.DEMO_MODE !== "false" && (
        <Link
          prefetch={false}
          href="/director"
          className="fixed bottom-20 right-3 z-40 inline-flex min-h-[44px] items-center gap-2 rounded-full border border-line bg-surface px-4 text-sm font-semibold shadow-lift hover:bg-surface-2 lg:bottom-4"
        >
          <Clapperboard className="h-4 w-4" aria-hidden /> Director
        </Link>
      )}
      <TabBar unread={unread} role={session.role} />
    </div>
  );
}
