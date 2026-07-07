import { expect, test } from "@playwright/test";

const password = process.env.SITE_PASSWORD ?? "LAYCC";

async function login(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Enter" }).click();
  await expect(page.getByRole("heading", { name: "Roster" })).toBeVisible();
}

test("unauthenticated visit redirects to login", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "You First Gersh" })).toBeVisible();
});

test("login grants access to roster", async ({ page }) => {
  await login(page);
  await expect(page.getByText("Instagram performance across the talent roster.")).toBeVisible();
});

test("influencer page shows overhauled dashboard sections", async ({ page }) => {
  await login(page);

  const firstCard = page.locator('a[href^="/influencer/"]').first();
  await expect(firstCard).toBeVisible();
  await firstCard.click();

  await expect(page.getByRole("link", { name: "← Roster" })).toBeVisible();
  await expect(page.getByText("No bio available.")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Performance by format" })).toBeVisible();
  await expect(page.getByText(/based on \d+ posts/).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recent posts" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Eng. rate" })).toBeVisible();
});

test("influencer page renders creative recommendations section", async ({ page }) => {
  await login(page);

  const firstCard = page.locator('a[href^="/influencer/"]').first();
  await firstCard.click();

  await expect(page.getByRole("heading", { name: "Creative recommendations" })).toBeVisible();
});

test("influencer detail page renders an avatar next to the handle", async ({ page }) => {
  await login(page);

  const firstCard = page.locator('a[href^="/influencer/"]').first();
  await firstCard.click();
  await expect(page.getByRole("link", { name: "← Roster" })).toBeVisible();

  await expect(page.locator("h1 img, h1 + * img, main div.rounded-full").first()).toBeVisible();
});

test("roster page loads without crashing when highlight data exists", async ({ page }) => {
  await login(page);

  await expect(page.getByRole("heading", { name: "Roster" })).toBeVisible();
  // Attention strip is conditional on live warning-severity highlights existing;
  // just confirm the page renders roster cards regardless.
  await expect(page.locator('a[href^="/influencer/"]').first()).toBeVisible();
});

test("roster cards render an avatar for each influencer", async ({ page }) => {
  await login(page);

  const firstCard = page.locator('a[href^="/influencer/"]').first();
  await expect(firstCard.locator("img, div.rounded-full").first()).toBeVisible();
});
