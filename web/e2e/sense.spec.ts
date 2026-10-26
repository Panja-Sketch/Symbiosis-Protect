import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { API, asPersona, noHorizontalScroll, resetDemo } from "./helpers";

test.beforeEach(async ({ request, context }) => {
  await resetDemo(request);
  await asPersona(context, "acct-p5");
});

test("Mesa Palms: slow leak in 3B -> alert -> check 2B task -> fix -> sensor-verified -> recurrence reopens", async ({ page, request }) => {
  test.setTimeout(180_000);
  await page.goto("/sense");
  const card = page.locator('[data-device="dev-p5-3b"]');
  await expect(card).toContainText("SIMULATED");
  await card.getByTestId("connect").click();
  await expect(card.getByTestId("tiles")).toBeVisible();
  await expect(card.getByTestId("tiles")).toContainText("Dry");

  await card.getByText("Demo controls (SIMULATED)").click();
  await card.getByTestId("scenario-slow_leak").click();
  await expect(card.getByTestId("case-state")).toHaveText(/alerted/i, { timeout: 40_000 });
  await expect(card.getByTestId("tiles")).toContainText("WET", { timeout: 20_000 });

  // alert + tasks created for the account
  const alerts = await (await request.get(`${API}/alerts?account_id=acct-p5`)).json();
  expect(alerts.some((a: { kind: string; provenance: string }) => a.kind === "device" && a.provenance === "SIMULATED")).toBe(true);
  const tasks = (await (await request.get(`${API}/accounts/acct-p5/tasks?status=open`)).json()).tasks;
  expect(tasks.map((t: { title: string }) => t.title)).toContain("Leak in 3B — check unit 2B below");

  await card.getByTestId("shutoff").click();
  await expect(card.getByTestId("case-state")).toHaveText(/acting/i);
  await card.getByTestId("report-fix").click();
  await expect(card.getByTestId("case-state")).toHaveText(/verifying/i);
  // never verified instantly: the sensor must show several normal readings first
  await expect(card.getByTestId("case-state")).toHaveText(/verified/i, { timeout: 90_000 });
  await expect(card.getByTestId("manifest-hash")).toHaveText(/^[0-9a-f]{64}$/);

  const done = (await (await request.get(`${API}/accounts/acct-p5/tasks?status=done`)).json()).tasks;
  const sensorTask = done.find((t: { rule_id: string }) => t.rule_id === "az.sense.leak.v1");
  expect(sensorTask.proof[0].level).toBe("E4");

  await card.getByTestId("scenario-slow_leak").click();
  await expect(card.getByTestId("case-state")).toHaveText(/reopened/i, { timeout: 40_000 });
  expect(await noHorizontalScroll(page)).toBe(true);
});

test("sense page is accessible and fits both viewports", async ({ page }) => {
  await page.goto("/sense");
  await page.waitForLoadState("networkidle");
  const res = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
  expect(res.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);
  expect(await noHorizontalScroll(page)).toBe(true);
});
