import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { asPersona, inject, noHorizontalScroll, resetDemo } from "./helpers";

const PAGES = ["/", "/tasks", "/tasks?tab=coming_up", "/tasks?tab=done", "/tasks?tab=evidence", "/coverage", "/place", "/alerts", "/ask", "/sense", "/settings", "/more"];

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
  await lens.getByText("One tap").click();
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

test("photo proof: stored with hash, location, appears in Evidence, re-downloads identically", async ({ page, request, context }) => {
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
    "base64",
  );
  const { createHash } = await import("node:crypto");
  const expected = createHash("sha256").update(png).digest("hex");
  await context.grantPermissions(["geolocation"]);
  await context.setGeolocation({ latitude: 33.3062, longitude: -111.8413 });
  await inject(request, "heat_phoenix");
  await page.goto("/");
  await page.getByTestId("task-card").filter({ hasText: "AC condensate" }).click();
  const lens = page.getByTestId("coverage-lens");
  await expect(lens.getByLabel(/Photo/)).toBeChecked();
  await lens.getByTestId("proof-file").setInputFiles({ name: "condensate.png", mimeType: "image/png", buffer: png });
  await lens.getByTestId("proof-submit").click();
  await expect(page.getByTestId("coverage-lens")).toHaveCount(0);
  await page.goto("/tasks?tab=evidence");
  const row = page.getByTestId("evidence-row").filter({ hasText: "AC condensate" });
  await expect(row.getByTestId("evidence-hash")).toHaveText(expected);
  await expect(row).toContainText("33.3062");
  await expect(row).toContainText("E1");
  const href = await row.getByRole("link", { name: /Download/ }).getAttribute("href");
  const res = await request.get(`http://localhost:3100${href}`);
  expect(res.status()).toBe(200);
  expect(createHash("sha256").update(await res.body()).digest("hex")).toBe(expected);
  expect(res.headers()["x-content-sha256"]).toBe(expected);
});

test("photo proof without location permission is still accepted and says so", async ({ page, request }) => {
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
    "base64",
  );
  await inject(request, "heat_phoenix");
  await page.goto("/");
  await page.getByTestId("task-card").filter({ hasText: "AC condensate" }).click();
  await page.getByTestId("proof-submit").click();
  await expect(page.getByRole("alert")).toContainText("photo first");
  await page.getByTestId("proof-file").setInputFiles({ name: "x.png", mimeType: "image/png", buffer: png });
  await page.getByTestId("proof-submit").click();
  await page.goto("/tasks?tab=evidence");
  await expect(page.getByTestId("evidence-row").first()).toContainText("location not shared");
});

test("ask: starter question returns a grounded answer with citation chips that open the coverage card", async ({ page }) => {
  await page.goto("/ask");
  await page.getByTestId("starter").filter({ hasText: "Is water from my AC covered?" }).click();
  const ans = page.getByTestId("answer");
  await expect(ans).toBeVisible();
  await expect(ans.getByTestId("answer-text")).toContainText("Your policy summary");
  await expect(ans.getByTestId("answer-text")).toContainText("Your agent confirms final coverage decisions");
  await expect(ans.getByTestId("handoff")).toContainText("Dana Whitfield");
  const chip = ans.getByTestId("citation-chip").first();
  await expect(chip).toContainText("Sudden water leaks");
  await chip.click();
  await expect(page).toHaveURL(/\/coverage#HO_WATER_SUDDEN/);
  await expect(page.locator("#HO_WATER_SUDDEN")).toBeVisible();
});

test("ask: unknown topic is refused and handed to the agent; claim decision is not promised", async ({ page }) => {
  await page.goto("/ask");
  await page.getByLabel("Your question about your coverage").fill("Do you cover my dog's vet bills?");
  await page.getByRole("button", { name: "Send question" }).click();
  await expect(page.getByTestId("answer-text")).toContainText("could not find that in your policy summary");
  await expect(page.getByTestId("handoff")).toContainText("Talk to your agent about this");
  await page.getByLabel("Your question about your coverage").fill("Will my claim be paid if a hose bursts?");
  await page.getByRole("button", { name: "Send question" }).click();
  const last = page.getByTestId("answer-text").last();
  await expect(last).toContainText("I cannot");
  await expect(last).not.toContainText(/you are covered|will be paid|guaranteed/i);
});
