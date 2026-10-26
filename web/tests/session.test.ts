import { describe, expect, it } from "vitest";
import { decodeSession, encodeSession } from "@/lib/session";
import { fmtDate, usd } from "@/lib/utils";

describe("demo session cookie", () => {
  it("round-trips a valid persona and role", () => {
    const v = encodeSession({ account_id: "acct-p4", role: "agent" });
    expect(decodeSession(v)).toEqual({ account_id: "acct-p4", role: "agent" });
  });

  it("falls back to the default persona when tampered or unsigned", () => {
    const v = encodeSession({ account_id: "acct-p4", role: "agent" });
    const [body] = v.split(".");
    expect(decodeSession(`${body}.bad`).account_id).toBe("acct-p1");
    expect(decodeSession("garbage").role).toBe("policyholder");
    expect(decodeSession(undefined).account_id).toBe("acct-p1");
  });

  it("rejects unknown personas even when correctly signed", () => {
    const v = encodeSession({ account_id: "acct-p9", role: "policyholder" });
    expect(decodeSession(v).account_id).toBe("acct-p1");
  });
});

describe("formatting", () => {
  it("formats dollars and dates", () => {
    expect(usd(385000)).toBe("$385,000");
    expect(usd(null)).toBe("—");
    expect(fmtDate("2026-10-25")).toBe("Oct 25");
    expect(fmtDate(null)).toBe("—");
  });
});
