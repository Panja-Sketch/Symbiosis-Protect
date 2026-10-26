import "server-only";
import crypto from "node:crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { Role } from "./types";

// "Demo identity" only: an HMAC-signed cookie choosing persona + role. Not authentication.
export const SESSION_COOKIE = "sp_session";
const secret = () => process.env.SESSION_SECRET ?? "dev-only-change-me";

export interface Session {
  account_id: string;
  role: Role;
}

const DEFAULT: Session = { account_id: "acct-p1", role: "policyholder" };
export const ROLES: Role[] = ["policyholder", "agent", "underwriter"];

function mac(body: string): string {
  return crypto.createHmac("sha256", secret()).update(body).digest("base64url");
}

export function encodeSession(s: Session): string {
  const body = Buffer.from(JSON.stringify(s)).toString("base64url");
  return `${body}.${mac(body)}`;
}

export function decodeSession(value: string | undefined): Session {
  if (!value) return DEFAULT;
  const [body, sig] = value.split(".");
  if (!body || !sig) return DEFAULT;
  const expected = mac(body);
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return DEFAULT;
  try {
    const s = JSON.parse(Buffer.from(body, "base64url").toString());
    if (/^acct-p[1-6]$/.test(s.account_id) && ROLES.includes(s.role)) return s;
  } catch {
    /* fall through */
  }
  return DEFAULT;
}

export function getSession(): Session {
  return decodeSession(cookies().get(SESSION_COOKIE)?.value);
}

export function homeFor(role: Role): string {
  return role === "agent" ? "/agent" : role === "underwriter" ? "/underwriter" : "/";
}

/** Policyholder screens: other roles are sent to their own home. Returns the session for convenience. */
export function policyholderOnly(): Session {
  const s = getSession();
  if (s.role !== "policyholder") redirect(homeFor(s.role));
  return s;
}

/** Agent / underwriter screens. */
export function roleOnly(...roles: Role[]): Session {
  const s = getSession();
  if (!roles.includes(s.role)) redirect(homeFor(s.role));
  return s;
}
