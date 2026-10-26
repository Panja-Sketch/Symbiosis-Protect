import "server-only";

const API = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/** Server-side GET against the FastAPI service (never cached: weather and tasks change). */
export async function apiGet<T>(path: string, role?: string): Promise<T> {
  const r = await fetch(`${API}/api/v1${path}`, { cache: "no-store", headers: role ? { "X-Demo-Role": role } : {} });
  if (!r.ok) throw new ApiError(r.status, `${path} -> ${r.status}`);
  return r.json() as Promise<T>;
}

export async function apiTry<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}
