import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { asPersona, inject, noHorizontalScroll, resetDemo } from "./helpers";

const PAGES = ["/", "/tasks", "/tasks?tab=coming_up", "/tasks?tab=done", "/coverage", "/place", "/alerts", "/ask", "/sense", "/settings", "/more"];

test.beforeEach(async ({ request, context }) => {
  await resetDemo(request);
  await asPersona(context, "acct-p1");
});

test("layout adapts: tab bar on phone, sidebar on laptop, no horizontal scroll", async ({ page }, info) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Maya");
  const phone = info.project.name.startsWith("phone");
  const nav = page.getByRole("navigation", { name: "Primary" });
  await expect(nav.filter({ visible: true })).toHaveCount(1);
  if (phone) {
    await expect(nav.filter({ visible: true }).getByRole("link")).toHaveCount(5);
  } else {
    await expect(nav.filter({ visible: true }).getByRole("link")).toHaveCount(8);
  }
  expect(await noHorizontalScroll(page)).toBe(true);
});

test("home shows ribbon, at most 3 do-now tasks, readiness, weather and provenance pills", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("ribbon-day")).toHaveCount(7);
  const n = await page.getByTestId("task-card").count();
  expect(n).toBeGreaterThanOrEqual(3);
  expect(n).toBeLessThanOrEqual(3);
  await expect(page.getByTestId("readiness-count")).toContainText(/\d+ of \d+/);
  await expect(page.getByText("Weather & alerts")).toBeVisible();
  for (const kind of ["SYNTHETIC"]) await expect(page.getByText(kind, { exact: true }).first()).toBeVisible();
  await expect(page.getByTestId("preview-banner")).toContainText("Personal-lines preview");
});

for (const path of PAGES) {
  test(`axe: no WCAG 2.2 AA violations on ${path}`, async ({ page }) => {
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const res = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
    expect(res.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);
    expect(await noHorizontalScroll(page)).toBe(true);
  });
}

test("heat scenario drives a SIMULATED condensate task; Coverage Lens explains it; completing updates readiness", async ({ page, request }) => {
  await inject(request, "heat_phoenix");
  await page.goto("/");
  const ribbonHigh = page.locator('[data-testid="ribbon-day"][data-risk="high"]');
  await expect(ribbonHigh.first()).toBeVisible();
  const card = page.getByTestId("task-card").filter({ hasText: "AC condensate" });
  await expect(card).toBeVisible();
  await expect(card).toContainText("SIMULATED");
  await card.click();
  const lens = page.getByTestId("coverage-lens");
  await expect(lens).toContainText("What could happen");
  await expect(lens).toContainText("What your policy says");
  await expect(lens).toContainText("Sudden leak vs. slow leak");
  await expect(lens.getByTestId("coverage-chip").first()).toBeVisible();
  await expect(lens).toContainText("Why now");
  await expect(lens).toContainText("114");
  const before = await page.getByTestId("readiness-count").innerText();
  await lens.getByRole("button", { name: "I did this" }).click();
  await expect(page.getByTestId("coverage-lens")).toHaveCount(0);
  await expect(page.getByTestId("readiness-count")).not.toHaveText(before);
  await page.goto("/tasks?tab=done");
  await expect(page.getByTestId("task-card").filter({ hasText: "AC condensate" })).toBeVisible();
});

test("alerts page lists the scenario alert and marks it read", async ({ page, request }) => {
  await inject(request, "heat_phoenix");
  await page.goto("/alerts");
  const row = page.getByTestId("alert-row").filter({ hasText: "Extreme Heat Warning" });
  await expect(row).toBeVisible();
  await expect(row).toContainText("SIMULATED");
  await row.getByRole("button", { name: "Mark read" }).click();
  await expect(row.getByRole("button", { name: "Mark read" })).toHaveCount(0);
});

test("persona switcher changes the whole app to Saguaro Grill", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("identity-switcher").click();
  await page.getByRole("menuitem", { name: /Saguaro Grill/ }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Saguaro Grill");
  await expect(page.getByTestId("preview-banner")).toHaveCount(0);
});

test("coverage page shows limits, present and missing endorsements", async ({ page }) => {
  await page.goto("/coverage");
  await expect(page.getByTestId("coverage-card").first()).toContainText("Limit");
  await expect(page.getByTestId("endorsement").filter({ hasText: "Not on your policy" }).first()).toBeVisible();
  await expect(page.getByTestId("endorsement").filter({ hasText: "On your policy" }).first()).toBeVisible();
  await expect(page.getByText("Your agent confirms final coverage decisions.")).toBeVisible();
});

test("my place: editing the water heater year updates the equipment list", async ({ page }) => {
  await page.goto("/place");
  const row = page.getByTestId("asset-row").filter({ hasText: "Water heater" });
  await expect(row).toContainText("Age unknown");
  await row.getByRole("button", { name: /Edit Water heater/ }).click();
  await row.getByLabel("Install year").fill("2024");
  await row.getByRole("button", { name: "Save" }).click();
  await expect(page.getByTestId("asset-row").filter({ hasText: "Water heater" })).toContainText("Installed 2024");
  await expect(page.getByRole("heading", { name: "Local history" })).toBeVisible();
});
