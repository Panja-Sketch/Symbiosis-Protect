import { notFound } from "next/navigation";
import { DirectorPanel } from "@/components/director-panel";
import { apiGet } from "@/lib/api";
import type { Persona } from "@/lib/types";

export default async function DirectorPage() {
  if (process.env.DEMO_MODE === "false") notFound();
  const personas = await apiGet<Persona[]>("/personas");
  const names = Object.fromEntries(personas.map((p) => [p.id, p.display_name]));
  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-display text-2xl font-semibold md:text-3xl">Scenario Director</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Demo control panel. Everything injected here is labelled <strong>SIMULATED</strong> wherever it appears, so a calm-weather day never passes for
          a real event.
        </p>
      </div>
      <DirectorPanel names={names} />
    </div>
  );
}
