import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { API, asPersona, inject, noHorizontalScroll, resetDemo } from "./helpers";

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
  "base64",
);

test.beforeEach(async ({ request }) => {
  await resetDemo(request);
});

for (const [role, path] of [
  ["agent", "/agent"],
  ["underwriter", "/underwriter"],
  ["underwriter", "/client/acct-p1"],
  ["agent", "/client/acct-p4"],
  ["policyholder", "/settings"],
] as const) {
  test(`axe + no horizontal scroll: ${role} ${path}`, async ({ page, context }) => {
    await asPersona(context, "acct-p1", role);
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const res = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
    expect(res.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`)).toEqual([]);
    expect(await noHorizontalScroll(page)).toBe(true);
  });
}

test("role switcher moves between policyholder, agent and underwriter views and guards the other screens", async ({ page, context }) => {
  await asPersona(context, "acct-p1");
  await page.goto("/");
  await page.getByTestId("identity-switcher").click();
  await Promise.all([page.waitForResponse("**/api/session"), page.getByRole("menuitem", { name: "Underwriter" }).click()]);
  await page.goto("/");
  await expect(page).toHaveURL(/\/underwriter$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Portfolio");
  await page.goto("/tasks");
  await expect(page).toHaveURL(/\/underwriter$/);
  await page.getByTestId("identity-switcher").click();
  await Promise.all([page.waitForResponse("**/api/session"), page.getByRole("menuitem", { name: "Agent" }).click()]);
  await page.goto("/underwriter");
  await expect(page).toHaveURL(/\/agent$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("My book");
  await expect(page.getByTestId("client-card")).toHaveCount(6);
});

test("consistency: Maya's shared photo proof appears for the underwriter with the same SHA-256, then privacy toggle hides it", async ({ page, context, request }) => {
  const { createHash } = await import("node:crypto");
  const expected = createHash("sha256").update(PNG).digest("hex");
  await asPersona(context, "acct-p1");
  await page.goto("/");
  await page.getByTestId("task-card").filter({ hasText: "washer hoses" }).click();
  const lens = page.getByTestId("coverage-lens");
  await expect(lens.getByTestId("share-task")).toBeChecked();
  await lens.getByTestId("proof-file").setInputFiles({ name: "hoses.png", mimeType: "image/png", buffer: PNG });
  await lens.getByTestId("proof-submit").click();
  await expect(page.getByTestId("coverage-lens")).toHaveCount(0);

  await asPersona(context, "acct-p1", "underwriter");
  await page.goto("/client/acct-p1");
  await expect(page.getByText(expected)).toBeVisible();
  await page.goto("/underwriter");
  await expect(page.getByTestId("tile-proof-mix")).toContainText("E1");

  const tasks = (await (await request.get(`${API}/accounts/acct-p1/tasks?status=done`)).json()).tasks;
  const id = tasks.find((t: { rule_id: string }) => t.rule_id.includes("hose_age")).id;
  await request.patch(`${API}/tasks/${id}/visibility`, { data: { visibility: "private" } });
  await page.goto("/client/acct-p1");
  await expect(page.getByText(expected)).toHaveCount(0);
});

test("privacy: Luis keeps tasks private by default; sharing one task from the app makes only that task visible to the underwriter", async ({ page, context }) => {
  await asPersona(context, "acct-p2", "underwriter");
  await page.goto("/client/acct-p2");
  await expect(page.getByTestId("no-shared-tasks")).toBeVisible();
  await expect(page.getByTestId("shared-task")).toHaveCount(0);

  await asPersona(context, "acct-p2");
  await page.goto("/tasks");
  await page.getByTestId("task-card").first().click();
  const toggle = page.getByTestId("share-task");
  await expect(toggle).not.toBeChecked();
  await toggle.click();
  await expect(page.getByText("They can see this task")).toBeVisible();
  await expect(toggle).toBeChecked();

  await asPersona(context, "acct-p2", "underwriter");
  await page.goto("/client/acct-p2");
  await expect(page.getByTestId("shared-task")).toHaveCount(1);
});

test("insurer-issued recommendation reaches the policyholder, is labelled, and bypasses the Do-now cap", async ({ page, context }) => {
  await asPersona(context, "acct-p1", "underwriter");
  await page.goto("/client/acct-p1");
  const form = page.getByTestId("issue-form");
  await form.getByLabel("Recommendation title").fill("Install a leak sensor at the water heater");
  await form.getByLabel("Why (shown to the policyholder)").fill("Risk control recommends early leak detection near the water heater.");
  await form.getByLabel("Steps (one per line)").fill("Place the sensor in the drain pan\nTest it with a damp cloth");
  await form.getByRole("button", { name: "Issue recommendation" }).click();
  await expect(page.getByText("Issued.")).toBeVisible();

  await asPersona(context, "acct-p1");
  await page.goto("/");
  const cards = page.getByTestId("task-card");
  await expect(cards).toHaveCount(4);
  const issued = cards.filter({ hasText: "Install a leak sensor" });
  await expect(issued).toContainText("From insurer");
  await issued.click();
  await expect(page.getByText("Issued by your insurer; it is visible to them.")).toBeVisible();
});

test("underwriter exports an evidence package and sees its manifest hash", async ({ page, context }) => {
  await asPersona(context, "acct-p5", "underwriter");
  await page.goto("/client/acct-p5");
  const [download] = await Promise.all([page.waitForEvent("download"), page.getByTestId("export-zip").click()]);
  expect(download.suggestedFilename()).toMatch(/^evidence_pol-p5_pkg-.*\.zip$/);
  await expect(page.getByTestId("export-hash")).toHaveText(/^[0-9a-f]{64}$/);
  await expect(page.getByTestId("export-result")).toContainText("shared only");
  await page.reload();
  await expect(page.getByTestId("package-list")).toContainText("underwriter");
});

test("agent book flags clients under an active alert and shows renewal talking points", async ({ page, context, request }) => {
  await inject(request, "heat_phoenix");
  await asPersona(context, "acct-p1", "agent");
  await page.goto("/agent");
  await expect(page.getByTestId("alerted-count")).toHaveText("3");
  const maya = page.locator('[data-persona="P1"]');
  await expect(maya.getByTestId("exposure-alert")).toContainText("Extreme Heat Warning");
  await expect(maya.getByTestId("exposure-alert")).toContainText("SIMULATED");
  await expect(maya.getByTestId("renewal-points")).toContainText("Water backup");
  await expect(page.locator('[data-persona="P4"]').getByTestId("exposure-alert")).toHaveCount(0);
  await asPersona(context, "acct-p1", "underwriter");
  await page.goto("/underwriter");
  await expect(page.getByTestId("county-alerts")).toContainText("Maricopa County");
});
