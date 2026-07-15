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
  const firstRow = page.locator('.panel a[href^="/influencer/"]').first();
  await expect(firstRow).toBeVisible();
  await firstRow.click();
  await expect(page).toHaveURL(/\/influencer\//, { timeout: 15_000 });
}

async function openEngagementFixture(page: import("@playwright/test").Page, scenario: string) {
  await page.goto(`/test-fixtures/engagement-chart?scenario=${scenario}`);
  await expect(page.getByRole("heading", { name: new RegExp(`ENGAGEMENT CHART TEST FIXTURE · ${scenario}`, "i") })).toBeVisible();
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
  const markerCount = await markers.count();
  expect(markerCount).toBeGreaterThan(0);

  const firstMarker = markers.first();
  await expect(firstMarker).toHaveAttribute("aria-label", /Published|Publication timing unavailable/);
  await firstMarker.focus();
  await expect(firstMarker).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(firstMarker).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("selected-publication-guide")).toHaveAttribute("stroke", "#e3b04b");
  await expect(page.getByTestId("publication-details")).toBeVisible();
  await expect(page.getByTestId("publication-details")).toContainText(/engagement/);

  const firstPoint = page.getByTestId("engagement-point-0");
  await expect(firstPoint).toHaveAttribute("href", /instagram\.com\/p\//);
  await firstPoint.focus();
  await expect(firstPoint).toBeFocused();
  await expect(firstPoint).toHaveAttribute("data-selected", "true");
  await expect(firstMarker).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("publication-details-link")).toHaveAttribute("href", /instagram\.com\/p\//);

  const persistentMarker = markerCount > 1 ? markers.nth(1) : firstMarker;
  const persistentPoint = markerCount > 1 ? page.getByTestId("engagement-point-1") : firstPoint;
  if (markerCount > 1) {
    await persistentMarker.click();
    await expect(firstMarker).toHaveAttribute("aria-pressed", "false");
  }
  await persistentPoint.hover();
  await expect(persistentPoint).toHaveAttribute("data-selected", "true");
  await expect(persistentMarker).toHaveAttribute("aria-pressed", "true");
  const backLink = page.getByRole("link", { name: "← THE ROSTER" });
  await backLink.hover();
  await expect(persistentMarker).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("publication-details")).toBeVisible();

  await backLink.focus();
  await page.keyboard.press("Escape");
  await expect(page.getByText("Select a point to identify the post and compare its timing with the spike.")).toBeVisible();
  await expect(persistentMarker).toHaveAttribute("aria-pressed", "false");

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByTestId("publication-marker-rail")).toBeVisible();
  await expect(page.getByTestId("publication-marker-overview")).toBeVisible();
  await expect(page.getByTestId("publication-mobile-controls")).toBeVisible();

  await page.getByRole("button", { name: "Select first post" }).click();
  const detailsBox = await page.getByTestId("publication-details").boundingBox();
  expect(detailsBox).not.toBeNull();
  expect(detailsBox?.x ?? 0).toBeGreaterThanOrEqual(0);
  expect((detailsBox?.x ?? 0) + (detailsBox?.width ?? 0)).toBeLessThanOrEqual(390);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();
});

test("engagement chart strictly validates publication timestamps", async ({ page }) => {
  await login(page);
  await openEngagementFixture(page, "mixed");

  const markers = page.getByTestId("publication-marker");
  await expect(markers).toHaveCount(5);
  await expect(markers.nth(0)).toHaveAttribute("data-publication-date", "Mar 1, 2026");
  await expect(markers.nth(1)).toHaveAttribute("data-publication-date", "Mar 1, 2026");
  await expect(markers.nth(1)).toHaveAttribute("aria-label", /same day as previous post/);

  for (const invalidIndex of [2, 3, 4]) {
    await expect(markers.nth(invalidIndex)).toHaveAttribute("aria-label", /Publication timing unavailable/);
  }

  await markers.nth(0).click();
  await expect(page.getByTestId("engagement-point-0")).toHaveAttribute("data-selected", "true");
  await markers.nth(1).click();
  await expect(page.getByTestId("engagement-point-1")).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("engagement-point-0")).toHaveAttribute("data-selected", "false");
  await expect(page.getByTestId("engagement-point-1")).toHaveAttribute(
    "href",
    "https://www.instagram.com/p/fixture-1/",
  );
  await expect(page.getByTestId("publication-details-link")).toHaveAttribute(
    "href",
    "https://www.instagram.com/p/fixture-1/",
  );
});

test("engagement details remain available when every timestamp is invalid", async ({ page }) => {
  await login(page);
  await openEngagementFixture(page, "all-invalid");

  const markers = page.getByTestId("publication-marker");
  await expect(markers).toHaveCount(2);
  await markers.first().focus();
  await expect(page.getByTestId("publication-details")).toContainText("Publication timing unavailable");
  await expect(page.getByTestId("publication-details")).toContainText("engagement");
  await expect(page.getByTestId("selected-publication-guide")).toHaveAttribute("stroke", "#e3b04b");
});

test("engagement chart keeps no-post and one-post states safe", async ({ page }) => {
  await login(page);
  await openEngagementFixture(page, "none");
  await expect(page.getByText("No post engagement data yet.")).toBeVisible();

  await openEngagementFixture(page, "one");
  const marker = page.getByTestId("publication-marker");
  await expect(marker).toHaveCount(1);
  await marker.click();
  await expect(page.getByTestId("publication-details")).toContainText("first plotted post");
});

test("dense mobile chart uses bounded post navigation and tooltip", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await openEngagementFixture(page, "dense");

  await expect(page.getByTestId("publication-marker-visual")).toHaveCount(30);
  await expect(page.getByTestId("publication-marker").first()).toBeHidden();
  const previousButton = page.getByRole("button", { name: "Previous post" });
  const nextButton = page.getByRole("button", { name: "Select first post" });
  const previousBox = await previousButton.boundingBox();
  const nextBox = await nextButton.boundingBox();
  expect(previousBox).not.toBeNull();
  expect(nextBox).not.toBeNull();
  expect(previousBox?.width ?? 0).toBeGreaterThanOrEqual(44);
  expect(previousBox?.height ?? 0).toBeGreaterThanOrEqual(44);
  expect(nextBox?.width ?? 0).toBeGreaterThanOrEqual(44);
  expect(nextBox?.height ?? 0).toBeGreaterThanOrEqual(44);

  await nextButton.click();
  await expect(page.getByTestId("selected-post-position")).toHaveText("POST 1 / 30");
  await expect(page.getByTestId("publication-marker-visual").nth(0)).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("engagement-point-0")).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("publication-details")).toContainText("Published Jun 1, 2026");
  await expect(page.getByTestId("publication-details")).toContainText("reel");
  await expect(page.getByTestId("publication-details")).toContainText("first plotted post");
  await expect(page.getByTestId("publication-details")).toContainText("1.0K engagement");

  await page.getByRole("button", { name: "Next post" }).click();
  await expect(page.getByTestId("selected-post-position")).toHaveText("POST 2 / 30");
  await expect(page.getByTestId("publication-marker-visual").nth(1)).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("publication-marker-visual").nth(0)).toHaveAttribute("data-selected", "false");
  await expect(page.getByTestId("engagement-point-1")).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("engagement-point-0")).toHaveAttribute("data-selected", "false");
  await expect(page.getByTestId("publication-details")).toContainText("Published Jun 2, 2026");
  await expect(page.getByTestId("publication-details")).toContainText("photo");
  await expect(page.getByTestId("publication-details")).toContainText("1 day after previous post");
  await expect(page.getByTestId("publication-details")).toContainText("1.2K engagement");

  await page.getByTestId("engagement-point-29").hover();
  await page.getByTestId("engagement-point-29").click();
  const tooltip = page.locator(".recharts-tooltip-wrapper");
  await expect(tooltip).toBeVisible();
  await expect(tooltip).toContainText("Jun 30 · photo");
  await expect(tooltip).toContainText("Published Jun 30, 2026 · 1 day after previous post");
  await expect(page.getByTestId("selected-post-position")).toHaveText("POST 30 / 30");
  await expect(page.getByTestId("publication-marker-visual").nth(29)).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("engagement-point-29")).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("publication-details")).toContainText("Published Jun 30, 2026");
  await expect(page.getByTestId("publication-details")).toContainText("photo");
  await expect(page.getByTestId("publication-details")).toContainText("1 day after previous post");
  await expect(page.getByTestId("publication-details")).toContainText("5.3K engagement");
  const tooltipBox = await tooltip.boundingBox();
  expect(tooltipBox).not.toBeNull();
  expect(tooltipBox?.x ?? 0).toBeGreaterThanOrEqual(0);
  expect((tooltipBox?.x ?? 0) + (tooltipBox?.width ?? 0)).toBeLessThanOrEqual(390);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();
});

test("engagement chart visualizes ad posts with badges and outer rings", async ({ page }) => {
  await login(page);
  await openEngagementFixture(page, "dense");

  // Verify that ad dots are visually flagged with data-ad="true"
  const adPoints = page.locator('a[data-ad="true"]');
  await expect(adPoints).not.toHaveCount(0);
  const firstAdPoint = adPoints.first();

  // Hover over the first ad point to trigger the tooltip
  await firstAdPoint.hover();
  const tooltip = page.locator(".recharts-tooltip-wrapper");
  await expect(tooltip).toBeVisible();
  await expect(tooltip).toContainText(/· Paid Media/i);

  // Click the ad point to lock selection details
  await firstAdPoint.click();
  await expect(page.getByTestId("publication-details")).toBeVisible();
  // Selection details should contain the "Paid Media" badge
  await expect(page.getByTestId("publication-details").getByText("Paid Media", { exact: true })).toBeVisible();

  // A non-ad point should be labeled Organic instead
  const organicPoints = page.locator('a[data-ad="false"]');
  await expect(organicPoints).not.toHaveCount(0);
  await organicPoints.first().hover();
  await expect(tooltip).toContainText(/· Organic/i);
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
  await expect(page.locator('.panel a[href^="/influencer/"]').first()).toBeVisible();
});

test("roster index rows render an avatar for each influencer", async ({ page }) => {
  await login(page);

  const firstRow = page.locator('.panel a[href^="/influencer/"]').first();
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
    await expect(page.locator('.panel a[href^="/influencer/"]').first()).toBeVisible();
  }
});

test("silk.jpg static asset can be fetched without authentication", async ({ request }) => {
  const response = await request.get("/silk.jpg");
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("image/jpeg");
});


test("login page password visibility toggle works", async ({ page }) => {
  await page.goto("/login");
  const passwordInput = page.getByLabel("Team password");
  await expect(passwordInput).toHaveAttribute("type", "password");
  
  const toggleBtn = page.getByLabel("Show password");
  await expect(toggleBtn).toBeVisible();
  await toggleBtn.click();
  await expect(passwordInput).toHaveAttribute("type", "text");
  
  const hideBtn = page.getByLabel("Hide password");
  await expect(hideBtn).toBeVisible();
  await hideBtn.click();
  await expect(passwordInput).toHaveAttribute("type", "password");
});
