import { expect, test } from "@playwright/test";

const password = process.env.SITE_PASSWORD ?? "LAYCC";

async function login(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByLabel("Team password").fill(password);
  await page.getByRole("button", { name: "Enter" }).click();
  await expect(page).toHaveURL(/\/$/, { timeout: 15_000 });
  await expect(page.getByRole("heading", { name: "The Roster", exact: true })).toBeVisible({ timeout: 15_000 });
}

async function openFirstInfluencer(page: import("@playwright/test").Page) {
  const firstRow = page.locator('ol.panel a[href^="/influencer/"]').first();
  await expect(firstRow).toBeVisible();
  await firstRow.click();
  await expect(page).toHaveURL(/\/influencer\//, { timeout: 15_000 });
}

test("unauthenticated visit redirects to login", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Look After You" })).toBeVisible();
});

test("login grants access to roster", async ({ page }) => {
  await login(page);
  await expect(
    page.getByText("Instagram performance across the talent roster, watched nightly."),
  ).toBeVisible();
});

test("influencer page shows overhauled dashboard sections", async ({ page }) => {
  await login(page);

  await openFirstInfluencer(page);

  await expect(page.getByRole("link", { name: "← THE ROSTER" })).toBeVisible();
  await expect(page.getByText("No bio available.")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "BY FORMAT" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /THE LOG/ })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "ENG." })).toBeVisible();
});

test("influencer engagement chart exposes publication timing markers", async ({ page }) => {
  await login(page);

  await openFirstInfluencer(page);

  await expect(page.getByRole("heading", { name: "TRAJECTORY · POST ENGAGEMENT" })).toBeVisible();

  const markers = page.getByTestId("publication-marker");
  await expect(markers.first()).toBeVisible();
  expect(await markers.count()).toBeGreaterThan(0);

  const firstMarker = markers.first();
  await expect(firstMarker).toHaveAttribute("aria-label", /Published|Publication timing unavailable/);
  await firstMarker.focus();
  await expect(firstMarker).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(firstMarker).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("selected-publication-guide")).toHaveAttribute("stroke", "#e3b04b");
  await expect(page.getByTestId("publication-details")).toBeVisible();
  await expect(page.getByTestId("publication-details")).toContainText(/engagement/);

  const secondMarker = markers.nth(1);
  const firstPoint = page.getByTestId("engagement-point-0");
  const secondPoint = page.getByTestId("engagement-point-1");
  await secondMarker.click();
  await expect(secondMarker).toHaveAttribute("aria-pressed", "true");
  await expect(firstMarker).toHaveAttribute("aria-pressed", "false");
  await expect(secondPoint).toHaveAttribute("aria-pressed", "true");

  await firstPoint.focus();
  await expect(firstPoint).toBeFocused();
  await expect(firstPoint).toHaveAttribute("aria-pressed", "true");
  await expect(firstMarker).toHaveAttribute("aria-pressed", "true");

  await secondPoint.hover();
  await expect(secondPoint).toHaveAttribute("aria-pressed", "true");
  await expect(secondMarker).toHaveAttribute("aria-pressed", "true");
  const backLink = page.getByRole("link", { name: "← THE ROSTER" });
  await backLink.hover();
  await expect(secondMarker).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("publication-details")).toBeVisible();

  await backLink.focus();
  await page.keyboard.press("Escape");
  await expect(page.getByText("Select a point to identify the post and compare its timing with the spike.")).toBeVisible();
  await expect(secondMarker).toHaveAttribute("aria-pressed", "false");

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByTestId("publication-marker-rail")).toBeVisible();
  await expect(firstMarker).toBeVisible();

  await firstMarker.focus();
  const detailsBox = await page.getByTestId("publication-details").boundingBox();
  expect(detailsBox).not.toBeNull();
  expect(detailsBox?.x ?? 0).toBeGreaterThanOrEqual(0);
  expect((detailsBox?.x ?? 0) + (detailsBox?.width ?? 0)).toBeLessThanOrEqual(390);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();

  await firstPoint.hover();
  const tooltipBox = await page.locator(".recharts-tooltip-wrapper").boundingBox();
  if (tooltipBox) {
    expect(tooltipBox.x).toBeGreaterThanOrEqual(0);
    expect(tooltipBox.x + tooltipBox.width).toBeLessThanOrEqual(390);
  }
});

test("influencer page renders creative recommendations section", async ({ page }) => {
  await login(page);

  await openFirstInfluencer(page);

  await expect(page.getByRole("heading", { name: /THE BRIEF/ })).toBeVisible();
});

test("influencer page renders top performing posts with Instagram links when present", async ({ page }) => {
  await login(page);

  await openFirstInfluencer(page);

  const heading = page.getByRole("heading", { name: /GREATEST HITS/ });
  await expect(heading).toBeVisible();

  const firstLink = page.getByRole("link", { name: "View →" }).first();
  if (await firstLink.isVisible().catch(() => false)) {
    await expect(firstLink).toHaveAttribute("href", /instagram\.com\/p\//);
  }
});

test("influencer detail page renders an avatar next to the handle", async ({ page }) => {
  await login(page);

  await openFirstInfluencer(page);
  await expect(page.getByRole("link", { name: "← THE ROSTER" })).toBeVisible();

  await expect(page.locator("main img, main div.rounded-full").first()).toBeVisible();
});

test("roster page loads without crashing when highlight data exists", async ({ page }) => {
  await login(page);

  await expect(page.getByRole("heading", { name: "The Roster", exact: true })).toBeVisible();
  // Watchlist is conditional on live warning-severity highlights existing;
  // just confirm the page renders index rows regardless.
  await expect(page.locator('ol.panel a[href^="/influencer/"]').first()).toBeVisible();
});

test("roster index rows render an avatar for each influencer", async ({ page }) => {
  await login(page);

  const firstRow = page.locator('ol.panel a[href^="/influencer/"]').first();
  await expect(firstRow.locator("img, div.rounded-full").first()).toBeVisible();
});

test("roster page renders roster-wide briefing and toggles language when present", async ({ page }) => {
  await login(page);

  await expect(page.getByRole("heading", { name: "The Roster", exact: true })).toBeVisible();

  const briefingHeading = page.getByRole("heading", { name: /THE DISPATCH/ });
  if (await briefingHeading.isVisible().catch(() => false)) {
    const toggle = page.getByRole("button", { name: /^(EN|ES)$/ });
    await expect(toggle).toBeVisible();
    const before = await toggle.textContent();
    await toggle.click();
    await expect(toggle).not.toHaveText(before ?? "");
  } else {
    // Briefing is generated by the scraper's daily run — absent on a fresh DB is fine.
    await expect(page.locator('ol.panel a[href^="/influencer/"]').first()).toBeVisible();
  }
});

test("silk.jpg static asset can be fetched without authentication", async ({ request }) => {
  const response = await request.get("/silk.jpg");
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("image/jpeg");
});
