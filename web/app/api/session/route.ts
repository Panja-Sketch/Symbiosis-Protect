import { NextResponse } from "next/server";
import { decodeSession, encodeSession, getSession, ROLES, SESSION_COOKIE } from "@/lib/session";

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const current = getSession();
  const next = decodeSession(
    encodeSession({ account_id: body.account_id ?? current.account_id, role: body.role ?? current.role }),
  );
  if (body.account_id && next.account_id !== body.account_id) {
    return NextResponse.json({ error: "unknown persona" }, { status: 422 });
  }
  if (body.role && !ROLES.includes(body.role)) {
    return NextResponse.json({ error: "unknown role" }, { status: 422 });
  }
  const res = NextResponse.json(next);
  res.cookies.set(SESSION_COOKIE, encodeSession(next), { httpOnly: true, sameSite: "lax", path: "/", maxAge: 60 * 60 * 24 });
  return res;
}
