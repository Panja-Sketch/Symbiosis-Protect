import { expect, test, type Browser } from "@playwright/test";
import { asPersona, resetDemo } from "./helpers";

// BUILD_SPEC section 15: the 7-minute demo script, end to end, laptop + phone, driven through the Scenario Director.

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
  "base64",
);

async function phone(browser: Browser) {
  return browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
}

test("full demo script runs end to end in under 8 minutes with no errors", async ({ page, context, browser, request }, info) => {
  test.skip(info.project.name.startsWith("phone"), "drives its own phone context");
  test.setTimeout(8 * 60_000);
  const started = Date.now();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && !/favicon|Failed to load resource/.test(m.text()) && errors.push(m.text()));

  await resetDemo(request);

  // 0. Director: heat wave for the Phoenix metro (October is calm, so the demo injects it; everything is labelled SIMULATED)
  await asPersona(context, "acct-p1");
  await page.goto("/director");
  await page.getByTestId("inject-heat_phoenix").click();
  await expect(page.getByTestId("director-log")).toContainText("Maya Okafor");
  await expect(page.getByTestId("active-injections")).toContainText("SIMULATED");

  // 1. Laptop, Maya: ribbon shows heat days -> condensate task -> Coverage Lens plain-language note
  await page.goto("/");
  await expect(page.locator('[data-testid="ribbon-day"][data-risk="high"]').first()).toBeVisible();
  const card = page.getByTestId("task-card").filter({ hasText: "AC condensate" });
  await card.click();
  const lens = page.getByTestId("coverage-lens");
  await expect(lens).toContainText("Sudden leak vs. slow leak");
  await expect(lens).toContainText("Why now");
  await page.keyboard.press("Escape");

  // 2. Ask: grounded answer with coverage chips and an agent confirmation
  await page.goto("/ask");
  await page.getByTestId("starter").filter({ hasText: "Is water from my AC covered?" }).click();
  await expect(page.getByTestId("citation-chip").first()).toBeVisible();
  await expect(page.getByTestId("answer-text")).toContainText("Your agent confirms final coverage decisions");

  // 3. Phone, same user: complete with photo proof (E1) -> readiness ring updates
  const pctx = await phone(browser);
  await asPersona(pctx, "acct-p1");
  const ph = await pctx.newPage();
  ph.on("pageerror", (e) => errors.push(e.message));
  await ph.goto("/");
  const before = await ph.getByTestId("readiness-count").innerText();
  await ph.getByTestId("task-card").filter({ hasText: "AC condensate" }).click();
  await ph.getByTestId("proof-file").setInputFiles({ name: "condensate.png", mimeType: "image/png", buffer: PNG });
  await ph.getByTestId("proof-submit").click();
  await expect(ph.getByTestId("coverage-lens")).toHaveCount(0);
  await expect(ph.getByTestId("readiness-count")).not.toHaveText(before);
  await pctx.close();

  // 4. Director: thunderstorm + flash flood -> Saguaro Grill roof-drain + wet-floor tasks, flood-exclusion note
  await page.goto("/director");
  await page.getByTestId("inject-storm_flood_valley").click();
  await expect(page.getByTestId("director-log")).toContainText("Saguaro Grill");
  await asPersona(context, "acct-p3");
  await page.goto("/tasks?tab=coming_up");
  const all = (await page.getByTestId("task-card").allInnerTexts()).join("\n") + (await (async () => {
    await page.goto("/tasks");
    return (await page.getByTestId("task-card").allInnerTexts()).join("\n");
  })());
  expect(all).toContain("Clear roof drains");
  expect(all).toContain("Wet-floor response");
  await page.goto("/tasks");
  await page.getByTestId("task-card").filter({ hasText: "Flash-flood readiness" }).click();
  await expect(page.getByTestId("coverage-lens")).toContainText("Flash flooding is usually not included");
  await page.keyboard.press("Escape");

  // 5. Director: freeze warning (Flagstaff) -> Ponderosa sprinkler 40°F task; holiday closure via the demo clock
  await asPersona(context, "acct-p4");
  await page.goto("/director");
  await page.getByTestId("inject-freeze_flagstaff").click();
  await page.goto("/tasks");
  await expect(page.getByTestId("task-card").filter({ hasText: "40°F" }).first()).toBeVisible();
  await page.goto("/director");
  await page.getByRole("button", { name: /Dec 22/ }).click();
  await expect(page.getByTestId("director-clock")).toContainText("December 22");
  await page.goto("/tasks?tab=coming_up");
  await page.goto("/tasks");
  const dec = (await page.getByTestId("task-card").allInnerTexts()).join("\n") + (await (async () => {
    await page.goto("/tasks?tab=coming_up");
    return (await page.getByTestId("task-card").allInnerTexts()).join("\n");
  })());
  expect(dec).toContain("Holiday closure");
  await page.goto("/director");
  await page.getByRole("button", { name: "Back to today" }).click();
  await expect(page.getByTestId("director-clock")).toContainText("Real time");

  // 6. Sense, Mesa Palms: slow leak in 3B -> alert -> "check 2B" task -> report fix -> sensor-verified -> recurrence reopens
  await asPersona(context, "acct-p5");
  await page.goto("/director");
  await page.getByTestId("device-dev-p5-3b").click();
  await page.goto("/sense");
  const dev = page.locator('[data-device="dev-p5-3b"]');
  await expect(dev.getByTestId("case-state")).toHaveText(/alerted/i, { timeout: 45_000 });
  await page.goto("/tasks");
  await expect(page.getByTestId("task-card").filter({ hasText: "check unit 2B below" })).toBeVisible();
  await page.goto("/sense");
  await dev.getByTestId("shutoff").click();
  await dev.getByTestId("report-fix").click();
  await expect(dev.getByTestId("case-state")).toHaveText(/verifying/i);
  await expect(dev.getByTestId("case-state")).toHaveText(/verified/i, { timeout: 100_000 });
  await dev.getByText("Demo controls (SIMULATED)").click();
  await dev.getByTestId("scenario-slow_leak").click();
  await expect(dev.getByTestId("case-state")).toHaveText(/reopened/i, { timeout: 45_000 });

  // 7. Agent view: who is under an active alert + renewal points; Underwriter view: participation, proof mix, export
  await asPersona(context, "acct-p1", "agent");
  await page.goto("/agent");
  expect(Number(await page.getByTestId("alerted-count").innerText())).toBeGreaterThanOrEqual(3);
  await expect(page.locator('[data-persona="P1"]').getByTestId("renewal-points")).toBeVisible();
  await asPersona(context, "acct-p1", "underwriter");
  await page.goto("/underwriter");
  await expect(page.getByTestId("tile-participation")).toContainText("83%");
  await expect(page.getByTestId("tile-proof-mix")).toContainText("E1");
  await page.goto("/client/acct-p5");
  const [dl] = await Promise.all([page.waitForEvent("download"), page.getByTestId("export-zip").click()]);
  expect(dl.suggestedFilename()).toMatch(/\.zip$/);
  await expect(page.getByTestId("export-hash")).toHaveText(/^[0-9a-f]{64}$/);

  await resetDemo(request);
  const seconds = (Date.now() - started) / 1000;
  console.log(`DEMO SCRIPT TOTAL: ${seconds.toFixed(0)}s`);
  expect(seconds).toBeLessThan(8 * 60);
  expect(errors.map((e) => e.slice(0, 300))).toEqual([]);
});
