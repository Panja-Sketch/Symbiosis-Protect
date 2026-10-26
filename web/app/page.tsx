const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function apiHealth(): Promise<{ ok: boolean; detail: string }> {
  try {
    const r = await fetch(`${API}/api/v1/healthz`, { cache: "no-store" });
    const j = await r.json();
    return { ok: r.ok, detail: `${j.status} · demo_mode=${j.demo_mode}` };
  } catch {
    return { ok: false, detail: "API unreachable" };
  }
}

export default async function Home() {
  const health = await apiHealth();
  return (
    <main className="mx-auto max-w-xl p-6">
      <h1 className="text-2xl font-semibold">Symbiosis Protect</h1>
      <p className="mt-1 text-sm text-slate-600">Arizona demo · scaffold (Phase 0)</p>
      <p role="status" className="mt-6 text-sm">
        API: <strong>{health.ok ? "healthy" : "down"}</strong> — {health.detail}
      </p>
    </main>
  );
}
