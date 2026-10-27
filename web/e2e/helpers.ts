import type { APIRequestContext, BrowserContext, Page } from "@playwright/test";
import { createHmac } from "node:crypto";

export const API = `${process.env.API_URL ?? "http://127.0.0.1:8000"}/api/v1`;
const BASE = process.env.BASE_URL ?? "http://localhost:3100";

export async function resetDemo(request: APIRequestContext) {
  const r = await request.post(`${API}/director/reset`);
  if (!r.ok()) throw new Error(`reset failed ${r.status()}`);
}

export async function inject(request: APIRequestContext, kind: string) {
  const r = await request.post(`${API}/director/inject`, { data: { kind } });
  if (!r.ok()) throw new Error(`inject ${kind} failed ${r.status()}`);
}

/** Sets the signed demo-identity cookie (same algorithm as lib/session.ts) so tests can pick a persona. */
export async function asPersona(context: BrowserContext, accountId: string, role = "policyholder") {
  const body = Buffer.from(JSON.stringify({ account_id: accountId, role })).toString("base64url");
  const sig = createHmac("sha256", process.env.SESSION_SECRET ?? "dev-only-change-me").update(body).digest("base64url");
  await context.addCookies([{ name: "sp_session", value: `${body}.${sig}`, domain: new URL(BASE).hostname, path: "/", secure: BASE.startsWith("https") }]);
}

export async function noHorizontalScroll(page: Page) {
  const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  return over <= 1;
}
