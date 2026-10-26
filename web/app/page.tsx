import Link from "next/link";
import { HistoryTeaser, ReadinessRing, WeatherCard } from "@/components/home-cards";
import { Provenance } from "@/components/provenance";
import { RiskRibbon } from "@/components/risk-ribbon";
import { TaskList } from "@/components/task-list";
import { apiGet, apiTry } from "@/lib/api";
import { getSession } from "@/lib/session";
import type { AccountResponse, HistoryResponse, Policy, Ribbon, TasksResponse, WeatherAlert, WeatherResponse } from "@/lib/types";

export default async function HomePage() {
  const { account_id } = getSession();
  const acct = await apiGet<AccountResponse>(`/accounts/${account_id}`);
  const loc = acct.locations[0];
  const [tasks, policies, ribbon, weather, alerts, history] = await Promise.all([
    apiGet<TasksResponse>(`/accounts/${account_id}/tasks?status=do_now`),
    apiGet<Policy[]>(`/accounts/${account_id}/policies`),
    apiTry<Ribbon>(`/locations/${loc.id}/risk-ribbon`),
    apiGet<WeatherResponse>(`/locations/${loc.id}/weather`),
    apiGet<{ alerts: WeatherAlert[]; error: string | null }>(`/locations/${loc.id}/alerts`),
    apiTry<HistoryResponse>(`/locations/${loc.id}/history`),
  ]);
  const policy = await apiGet<Policy>(`/policies/${policies[0].id}`);
  const all = await apiGet<TasksResponse>(`/accounts/${account_id}/tasks`);
  const hour = Number(weather.now_local.slice(11, 13));
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const name = acct.type === "person" ? acct.display_name.split(" ")[0] : acct.display_name;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="font-display text-2xl font-semibold md:text-3xl">
            {greeting}, {name}
          </h1>
          <p className="text-sm text-muted">
            {acct.headline} · {loc.city}, AZ
          </p>
        </div>
        <Provenance kind="SYNTHETIC" detail="This persona and policy are invented for the demo." />
      </div>

      {ribbon && <RiskRibbon ribbon={ribbon} />}

      <div className="grid gap-4 lg:grid-cols-12">
        <section aria-labelledby="donow-h" className="space-y-3 lg:col-span-7">
          <div className="flex items-center justify-between">
            <h2 id="donow-h" className="font-display text-lg font-semibold">
              Do now
            </h2>
            <Link href="/tasks" className="inline-flex min-h-[44px] items-center text-sm font-semibold text-accent-text underline underline-offset-2">
              All tasks
            </Link>
          </div>
          <TaskList tasks={tasks.tasks} policy={policy} empty="You are all caught up. New tasks appear when weather or your property details change." />
        </section>
        <div className="space-y-4 lg:col-span-5">
          <WeatherCard weather={weather} alerts={alerts.alerts} alertsError={alerts.error} />
          <ReadinessRing done={all.readiness.done} applicable={all.readiness.applicable} />
          {history && <HistoryTeaser history={history} city={loc.city} />}
        </div>
      </div>
    </div>
  );
}
