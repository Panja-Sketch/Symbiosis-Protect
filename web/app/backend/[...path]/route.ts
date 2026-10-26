// Same-origin proxy to the API for browser calls (/backend/api/v1/...). Reads API_BASE_URL at runtime, so one web image
// works against any API URL (needed on Cloud Run, where the API URL is known only after the API is deployed).
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

const HOP = new Set(["host", "connection", "content-length", "transfer-encoding", "keep-alive", "upgrade", "te", "trailer", "proxy-authorization"]);

async function forward(req: NextRequest, { params }: { params: { path: string[] } }) {
  const api = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  const url = `${api}/${params.path.join("/")}${req.nextUrl.search}`;
  const headers = new Headers();
  req.headers.forEach((v, k) => {
    if (!HOP.has(k.toLowerCase()) && k.toLowerCase() !== "cookie") headers.set(k, v);
  });
  const hasBody = !["GET", "HEAD"].includes(req.method);
  const upstream = await fetch(url, {
    method: req.method,
    headers,
    body: hasBody ? await req.arrayBuffer() : undefined,
    cache: "no-store",
    redirect: "manual",
  });
  const out = new Headers();
  upstream.headers.forEach((v, k) => {
    if (!["content-encoding", "content-length", "transfer-encoding", "connection"].includes(k.toLowerCase())) out.set(k, v);
  });
  return new Response(upstream.body, { status: upstream.status, headers: out });
}

export { forward as GET, forward as POST, forward as PATCH, forward as PUT, forward as DELETE };
