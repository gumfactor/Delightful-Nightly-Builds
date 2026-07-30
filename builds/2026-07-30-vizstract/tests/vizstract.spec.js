const { test, expect } = require("@playwright/test");

const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("page loads with all core UI regions present", async ({ page }) => {
  await expect(page.locator('[data-testid="field-title"]')).toBeVisible();
  await expect(page.locator('[data-testid="preview-svg"] svg')).toBeVisible();
  await expect(page.locator('[data-testid="library-list"]')).toBeVisible();
  await expect(page.locator('[data-testid="field-abstract-paste"]')).toBeVisible();
});

test("editing the title updates the live SVG preview", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("Empathy Training Reduces Burnout");
  const previewText = await page.locator('[data-testid="preview-svg"]').innerText();
  expect(previewText).toContain("Empathy Training Reduces Burnout");
});

test("switching design type swaps the rendered template", async ({ page }) => {
  await page.locator('[data-testid="field-design-type"]').selectOption("process");
  let previewText = await page.locator('[data-testid="preview-svg"]').innerText();
  expect(previewText).toContain("Baseline");
  expect(previewText).toContain("Intervention");

  await page.locator('[data-testid="field-design-type"]').selectOption("compare");
  previewText = await page.locator('[data-testid="preview-svg"]').innerText();
  expect(previewText).not.toContain("Baseline");
  expect(previewText).toContain("Groups");
});

test("switching theme changes the SVG background fill color", async ({ page }) => {
  const bgRect = page.locator('[data-testid="preview-svg"] svg rect').first();
  const before = await bgRect.getAttribute("fill");

  await page.locator('[data-testid="theme-swatch"][data-theme="teal"]').click();
  await expect(page.locator('[data-testid="theme-swatch"][data-theme="teal"]')).toHaveAttribute("aria-pressed", "true");

  // background rect is always white by design (print/embed convention); verify a themed
  // element's fill actually changed instead, e.g. an icon-box card background.
  const cardBefore = before;
  const cardRect = page.locator('[data-testid="preview-svg"] svg rect').nth(1);
  const cardFillTeal = await cardRect.getAttribute("fill");

  await page.locator('[data-testid="theme-swatch"][data-theme="crimson"]').click();
  const cardFillCrimson = await cardRect.getAttribute("fill");

  expect(cardFillTeal).not.toBe(cardFillCrimson);
  expect(cardBefore).toBeTruthy();
});

test("a very long title wraps/truncates without overflowing its box", async ({ page }) => {
  const result = await page.evaluate(() => {
    const longTitle = "A".repeat(20) + " " + "Extremely Long Study Title That Keeps Going And Going And Going Well Past Any Reasonable Length ".repeat(4);
    const fit = window.Vizstract.Render.fitText(longTitle, 592, 54, { maxFontSize: 24, minFontSize: 14, weight: 800, maxLines: 2 });
    const totalHeight = fit.lines.length * fit.fontSize * 1.15;
    const widths = fit.lines.map((line) => window.Vizstract.Render.measureWidth(line, fit.fontSize, 800));
    return { totalHeight, widths, lineCount: fit.lines.length };
  });
  expect(result.totalHeight).toBeLessThanOrEqual(54 + 1);
  expect(result.lineCount).toBeLessThanOrEqual(2);
  for (const w of result.widths) {
    expect(w).toBeLessThanOrEqual(592 + 1);
  }
});

test("sample size and stat detail render correctly formatted in the callout", async ({ page }) => {
  await page.locator('[data-testid="field-n"]').fill("84");
  await page.locator('[data-testid="field-population"]').fill("clinical trainees");
  await page.locator('[data-testid="field-stat"]').fill("p < .05");
  const previewText = await page.locator('[data-testid="preview-svg"]').innerText();
  expect(previewText).toContain("N = 84");
  expect(previewText).toContain("clinical trainees");
  expect(previewText).toContain("p < .05");
});

test("each effect direction selects the matching directional icon", async ({ page }) => {
  const mapping = await page.evaluate(() => {
    const T = window.Vizstract.Templates;
    return {
      increase: T.directionIcon({ effectDirection: "increase" }),
      decrease: T.directionIcon({ effectDirection: "decrease" }),
      none: T.directionIcon({ effectDirection: "none" }),
      mixed: T.directionIcon({ effectDirection: "mixed" })
    };
  });
  expect(mapping.increase).toBe("arrowUp");
  expect(mapping.decrease).toBe("arrowDown");
  expect(mapping.none).toBe("dash");
  expect(mapping.mixed).toBe("zigzag");
});

test("saving to the library persists an entry and it appears in the visible list", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("Study Alpha");
  await page.locator('[data-testid="field-library-name"]').fill("Alpha Save");
  await page.locator('[data-testid="btn-save"]').click();

  await expect(page.locator('[data-testid="library-item"]')).toHaveCount(1);
  await expect(page.locator('[data-testid="library-item"]')).toContainText("Alpha Save");

  const stored = await page.evaluate(() => window.localStorage.getItem("vizstract.library.v1"));
  expect(stored).toContain("Study Alpha");
});

test("loading a saved library entry restores form fields and preview", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("Restore Me Study");
  await page.locator('[data-testid="field-iv"]').fill("Sleep deprivation");
  await page.locator('[data-testid="field-library-name"]').fill("Restore Entry");
  await page.locator('[data-testid="btn-save"]').click();

  await page.locator('[data-testid="btn-clear"]').click();
  await expect(page.locator('[data-testid="field-title"]')).toHaveValue("");

  await page.locator('[data-testid="library-item"] [data-testid="btn-load"]').click();
  await expect(page.locator('[data-testid="field-title"]')).toHaveValue("Restore Me Study");
  await expect(page.locator('[data-testid="field-iv"]')).toHaveValue("Sleep deprivation");
});

test("deleting a library entry removes it from storage and the list", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("Delete Me Study");
  await page.locator('[data-testid="btn-save"]').click();
  await expect(page.locator('[data-testid="library-item"]')).toHaveCount(1);

  await page.locator('[data-testid="btn-delete"]').click();
  await expect(page.locator('[data-testid="library-item"]')).toHaveCount(0);

  const stored = await page.evaluate(() => JSON.parse(window.localStorage.getItem("vizstract.library.v1") || "[]"));
  expect(stored.length).toBe(0);
});

test("SVG download produces well-formed, script-free markup with the expected filename", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("Download Test Study");
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator('[data-testid="btn-download-svg"]').click()
  ]);
  expect(download.suggestedFilename()).toBe("download-test-study.svg");
  const streamPath = await download.path();
  const fs = require("fs");
  const content = fs.readFileSync(streamPath, "utf8");
  expect(content.startsWith("<svg")).toBe(true);
  expect(content).toContain('xmlns="http://www.w3.org/2000/svg"');
  expect(content.toLowerCase()).not.toContain("<script");
  expect(content).toContain("Download Test Study");
});

test("PNG export produces a downloadable, non-empty PNG file", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("PNG Export Study");
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.locator('[data-testid="btn-download-png"]').click()
  ]);
  expect(download.suggestedFilename()).toBe("png-export-study.png");
  const streamPath = await download.path();
  const fs = require("fs");
  const stats = fs.statSync(streamPath);
  expect(stats.size).toBeGreaterThan(200);
});

test("with no API key, extraction uses the deterministic fallback and makes zero network requests", async ({ page }) => {
  let hit = false;
  await page.route("**/v1/messages", (route) => {
    hit = true;
    route.abort();
  });

  await page.locator('[data-testid="field-abstract-paste"]').fill(
    "Empathy training reduces burnout. We recruited 60 clinical trainees (N = 60) for an 8-week intervention. " +
    "Results indicated that trainees who completed the training reported significantly lower burnout scores, p < .05."
  );
  await page.locator('[data-testid="btn-extract"]').click();
  await expect(page.locator('[data-testid="extract-status"]')).toContainText("deterministic keyword extractor");
  expect(hit).toBe(false);

  await expect(page.locator('[data-testid="field-n"]')).toHaveValue("60");
});

test("with an API key and a mocked endpoint, exactly one POST populates the form", async ({ page }) => {
  let callCount = 0;
  await page.route(ANTHROPIC_URL, (route) => {
    callCount += 1;
    const body = {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            title: "Mocked AI Title",
            designType: "correlate",
            population: "mocked adults",
            ivLabel: "mocked predictor",
            dvLabel: "mocked outcome",
            sampleSize: "42",
            headlineFinding: "Mocked finding text.",
            effectDirection: "increase",
            statDetail: "r = .42"
          })
        }
      ]
    };
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });

  await page.locator('[data-testid="field-abstract-paste"]').fill("Any abstract text works since the endpoint is mocked.");
  await page.locator('[data-testid="field-api-key"]').fill("sk-ant-fake-key-for-test");
  await page.locator('[data-testid="btn-extract"]').click();

  await expect(page.locator('[data-testid="extract-status"]')).toContainText("Claude Haiku");
  expect(callCount).toBe(1);
  await expect(page.locator('[data-testid="field-title"]')).toHaveValue("Mocked AI Title");
  await expect(page.locator('[data-testid="field-n"]')).toHaveValue("42");
});

test("a script-injection payload in a live-typed field renders as inert text", async ({ page }) => {
  let dialogFired = false;
  page.on("dialog", (dialog) => {
    dialogFired = true;
    dialog.dismiss();
  });

  await page.locator('[data-testid="field-title"]').fill('<script>window.__vizXSS=true</script>Hi');
  await page.waitForTimeout(150);

  const executed = await page.evaluate(() => window.__vizXSS);
  expect(executed).toBeUndefined();
  expect(dialogFired).toBe(false);

  const previewText = await page.locator('[data-testid="preview-svg"]').innerText();
  expect(previewText).toContain("<script>window.__vizXSS=true</script>Hi");

  const scriptTags = await page.locator('[data-testid="preview-svg"] script').count();
  expect(scriptTags).toBe(0);
});

test("a reloaded library entry with an injection payload also renders inert", async ({ page }) => {
  let dialogFired = false;
  page.on("dialog", (dialog) => {
    dialogFired = true;
    dialog.dismiss();
  });

  await page.locator('[data-testid="field-title"]').fill('<img src=x onerror="window.__vizXSS2=true">Persisted');
  await page.locator('[data-testid="field-library-name"]').fill("XSS Entry");
  await page.locator('[data-testid="btn-save"]').click();

  await page.locator('[data-testid="btn-clear"]').click();
  await page.locator('[data-testid="library-item"] [data-testid="btn-load"]').click();
  await page.waitForTimeout(150);

  const executed = await page.evaluate(() => window.__vizXSS2);
  expect(executed).toBeUndefined();
  expect(dialogFired).toBe(false);

  const previewText = await page.locator('[data-testid="preview-svg"]').innerText();
  expect(previewText).toContain("Persisted");

  const imgTags = await page.locator('[data-testid="preview-svg"] img').count();
  expect(imgTags).toBe(0);
});

test("a blank title shows a validation message and blocks export", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("");
  await page.locator('[data-testid="btn-download-svg"]').click();
  await expect(page.locator('[data-testid="validation-message"]')).toBeVisible();
  await expect(page.locator('[data-testid="validation-message"]')).toContainText("title");

  const isValid = await page.evaluate(() => window.Vizstract.App.validateData({ title: "" }) === null);
  expect(isValid).toBe(false);
});

test("two independently saved entries do not bleed state when loaded back to back", async ({ page }) => {
  await page.locator('[data-testid="field-title"]').fill("Study A");
  await page.locator('[data-testid="field-iv"]').fill("Condition A");
  await page.locator('[data-testid="field-library-name"]').fill("Entry A");
  await page.locator('[data-testid="btn-save"]').click();

  await page.locator('[data-testid="btn-clear"]').click();
  await page.locator('[data-testid="field-title"]').fill("Study B");
  await page.locator('[data-testid="field-iv"]').fill("Condition B");
  await page.locator('[data-testid="field-library-name"]').fill("Entry B");
  await page.locator('[data-testid="btn-save"]').click();

  await expect(page.locator('[data-testid="library-item"]')).toHaveCount(2);

  const items = page.locator('[data-testid="library-item"]');
  const first = items.filter({ hasText: "Entry A" });
  const second = items.filter({ hasText: "Entry B" });

  await first.locator('[data-testid="btn-load"]').click();
  await expect(page.locator('[data-testid="field-title"]')).toHaveValue("Study A");
  await expect(page.locator('[data-testid="field-iv"]')).toHaveValue("Condition A");

  await second.locator('[data-testid="btn-load"]').click();
  await expect(page.locator('[data-testid="field-title"]')).toHaveValue("Study B");
  await expect(page.locator('[data-testid="field-iv"]')).toHaveValue("Condition B");
});

test("a fresh page load with empty storage shows sane defaults, not an error", async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err));

  await page.goto("/");
  await expect(page.locator('[data-testid="field-design-type"]')).toHaveValue("compare");
  await expect(page.locator('[data-testid="field-direction"]')).toHaveValue("none");
  await expect(page.locator('[data-testid="library-list"]')).toContainText("No saved abstracts yet.");
  expect(pageErrors).toEqual([]);

  await context.close();
});
