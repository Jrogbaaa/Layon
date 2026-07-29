import { expect, test } from "@playwright/test";
import { createClient } from "@supabase/supabase-js";

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
  await expect(page.getByTestId("strategy-panel")).toBeVisible();
  await expect(page.getByText(/Shared context/)).toBeVisible();
});

test("shared strategy panel supports bilingual inline editing without translating authored text", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/strategy-panel?scenario=current");

  const panel = page.getByTestId("strategy-panel");
  await expect(panel.getByRole("heading", { name: "CURRENT DIRECTION" })).toBeVisible();
  await expect(panel.getByText("Grow meaningful conversation without changing the creator's voice.")).toBeVisible();
  await panel.getByRole("button", { name: "Edit strategy" }).click();
  await expect(panel.getByLabel("Current objective")).toHaveValue(
    "Grow meaningful conversation without changing the creator's voice.",
  );
  await expect(panel.getByRole("checkbox")).toHaveCount(4);

  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(panel.getByRole("heading", { name: "DIRECCIÓN ACTUAL" })).toBeVisible();
  await expect(panel.getByLabel("Objetivo actual")).toHaveValue(
    "Grow meaningful conversation without changing the creator's voice.",
  );
  await expect(panel.getByText(/Contexto compartido/)).toBeVisible();
  await panel.getByLabel("Pilares de contenido").fill("one,two,three,four,five,six,seven,eight,nine");
  await panel.getByRole("button", { name: "Guardar y marcar revisada" }).click();
  await expect(panel.getByRole("alert")).toContainText("Use up to 8 content pillars");
});

test("strategy trust strip distinguishes missing and stale evidence", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/strategy-panel?scenario=empty");
  const emptyPanel = page.getByTestId("strategy-panel");
  await expect(emptyPanel.getByText("Not set")).toBeVisible();
  await expect(emptyPanel.getByText(/No current strategy has been set/)).toBeVisible();

  await page.goto("/test-fixtures/strategy-panel?scenario=stale");
  const stalePanel = page.getByTestId("strategy-panel");
  await expect(stalePanel.getByText("Stale")).toBeVisible();
  await expect(stalePanel.getByText("Refresh needed")).toBeVisible();
});

test("every substantive strategy field counts as current strategy", async ({ page }) => {
  await login(page);
  for (const [scenario, evidence] of [
    ["formats", "reel"],
    ["commercial", "Selective partnerships only."],
    ["constraints", "Weekdays only."],
  ]) {
    await page.goto(`/test-fixtures/strategy-panel?scenario=${scenario}`);
    const panel = page.getByTestId("strategy-panel");
    await expect(panel.getByText(evidence, { exact: true })).toBeVisible();
    await expect(panel.getByRole("button", { name: "Edit strategy" })).toBeVisible();
    await expect(panel.getByText(/No current strategy has been set/)).toHaveCount(0);
  }
});

test("recommendation feedback is bilingual and legacy recommendations remain read-only", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/recommendation-feedback");
  await expect(page.getByText("Shared response")).toBeVisible();
  await expect(page.getByPlaceholder("Visible to everyone with dashboard access")).toBeVisible();
  await expect(page.getByRole("option", { name: "Talent declined" })).toHaveCount(1);

  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.getByText("Respuesta compartida")).toBeVisible();
  await expect(page.getByRole("option", { name: "Talento no interesado" })).toHaveCount(1);

  await page.goto("/test-fixtures/recommendation-feedback?scenario=legacy");
  await expect(page.getByRole("heading", { name: "Legacy brief" })).toBeVisible();
  await expect(page.getByText("Shared response")).toHaveCount(0);
});

test("recommendation writes enforce bounded notes and an active session", async ({ page, context }) => {
  await login(page);
  await page.goto("/test-fixtures/recommendation-feedback");
  const note = page.locator('input[name="shared_note"]');
  await note.evaluate((input: HTMLInputElement) => {
    input.removeAttribute("maxlength");
    input.value = "x".repeat(501);
  });
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Shared note must be 500 characters or fewer.")).toBeVisible();

  await note.fill("Valid shared note");
  await page.locator('select[name="decision"]').selectOption("revisit");
  const revisit = page.locator('input[name="revisit_on"]');
  await expect(revisit).toBeVisible();
  await revisit.evaluate((input: HTMLInputElement) => {
    input.type = "text";
    input.value = "2026-02-31";
  });
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Revisit date must be a real calendar date.")).toBeVisible();

  await context.clearCookies();
  await page.reload();
  await expect(page).toHaveURL(/\/login/);
});

test("recommendation action rejects mismatched talent ownership", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/recommendation-action?mode=ownership");
  const form = page.locator('form[data-recommendation-id]').first();
  await form.locator('input[name="shared_note"]').fill("TEMPORARY FEATURE 020 OWNERSHIP CHECK");
  await form.getByRole("button", { name: "Save" }).click();
  await expect(form.getByText("Recommendation not found for this talent.")).toBeVisible();
});

test("recommendation action upserts one row, refreshes current state, and transitions decisions", async ({ page }) => {
  test.setTimeout(90_000);
  const supabaseUrl = process.env.SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_KEY;
  expect(supabaseUrl).toBeTruthy();
  expect(serviceKey).toBeTruthy();
  const client = createClient(supabaseUrl!, serviceKey!, { auth: { persistSession: false } });
  const marker = "TEMPORARY FEATURE 020 ACTION CHECK";
  let recommendationId = 0;

  try {
    await login(page);
    await page.goto("/test-fixtures/recommendation-action");
    let form = page.locator('form[data-recommendation-id]').first();
    recommendationId = Number(await form.getAttribute("data-recommendation-id"));
    expect(recommendationId).toBeGreaterThan(0);
    await form.locator('input[name="shared_note"]').fill(marker);
    await form.getByRole("button", { name: "Save" }).click();
    await expect(form.getByRole("status")).toContainText("planned experiment", { timeout: 45_000 });

    await page.goto(`/test-fixtures/recommendation-action?recommendation=${recommendationId}`);
    form = page.locator(`form[data-recommendation-id="${recommendationId}"]`).first();
    await expect(form.locator('select[name="decision"]')).toHaveValue("try");
    await expect(form.locator('input[name="shared_note"]')).toHaveValue(marker);

    await form.locator('select[name="decision"]').selectOption("not_relevant");
    await form.locator('input[name="shared_note"]').fill(`${marker} TRANSITION`);
    await form.getByRole("button", { name: "Save" }).click();
    await expect(form.getByRole("status")).toContainText("Response saved", { timeout: 45_000 });

    await expect.poll(async () => {
      const { data } = await client
        .from("recommendation_actions")
        .select("decision, experiment_status")
        .eq("recommendation_id", recommendationId)
        .eq("bullet_index", 0);
      return data;
    }).toEqual([{ decision: "not_relevant", experiment_status: null }]);
  } finally {
    if (recommendationId > 0) {
      const { data } = await client
        .from("recommendation_actions")
        .select("id, shared_note")
        .eq("recommendation_id", recommendationId)
        .eq("bullet_index", 0);
      const ids = (data ?? []).filter((row) => row.shared_note.startsWith(marker)).map((row) => row.id);
      if (ids.length) await client.from("recommendation_actions").delete().in("id", ids);
    }
  }
});

test("next action precedence favors warnings over unanswered recommendations and active experiments", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/recommendation-feedback?scenario=warning");
  await expect(page.getByTestId("next-action")).toContainText("Discuss the warning signal");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=active");
  await expect(page.getByTestId("next-action")).toContainText("Plan the chosen experiment");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=recommendation");
  await expect(page.getByTestId("next-action")).toContainText("Respond to the latest recommendation");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=missing");
  await expect(page.getByTestId("next-action")).toContainText("Restore Instagram evidence");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=stale");
  await expect(page.getByTestId("next-action")).toContainText("Refresh Instagram evidence");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=review");
  await expect(page.getByTestId("next-action")).toContainText("Review experiment outcome");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=none");
  await expect(page.getByTestId("next-action")).toContainText("No immediate action");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=acknowledged");
  await expect(page.getByTestId("next-action")).toContainText("No immediate action");

  await page.goto("/test-fixtures/recommendation-feedback?scenario=evaluated-no-outcome");
  await expect(page.getByTestId("next-action")).toContainText("No immediate action");
});

test("experiment panel shows lifecycle, like-for-like evidence, paid separation, and removed pillar warnings", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/experiment-panel");
  const panel = page.getByTestId("experiment-panel");
  await expect(panel.locator('[data-experiment-status="planned"]')).toContainText("Test the craft-led format");
  await expect(panel.locator('[data-experiment-status="planned"] select[name="shortcode"]')).toHaveValue("");
  await expect(panel.locator('[data-experiment-status="published"]')).toContainText("Seven-day review");
  await expect(panel.locator('[data-experiment-status="evaluated"]')).toContainText("+50%");
  await expect(panel.locator('[data-experiment-status="evaluated"]')).toContainText("n=4");
  await expect(panel.locator('[data-experiment-status="evaluated"]')).toContainText("directional");
  await expect(panel.getByText(/does not establish causal lift/)).toBeVisible();
  await expect(panel.getByText("organic", { exact: true })).toBeVisible();
  await expect(panel.getByText("paid", { exact: true })).toBeVisible();
  await expect(panel.getByText(/manual · removed pillar/)).toBeVisible();

  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(panel.getByText(/Evidencia direccional compartida/)).toBeVisible();
  await page.getByRole("button", { name: "ES", exact: true }).click();

  await page.goto("/test-fixtures/experiment-panel?scenario=zero-pillars");
  const zeroPillarPanel = page.getByTestId("experiment-panel");
  await expect(zeroPillarPanel.getByText("POST PILLAR OVERRIDES")).toBeVisible();
  await expect(zeroPillarPanel.getByText(/manual · removed pillar/)).toBeVisible();
  await expect(zeroPillarPanel.getByLabel("Pillar for organic-post").getByRole("option", { name: "Unassigned" })).toHaveCount(1);
});

test("experiment actions reject foreign posts, link at seven days, abandon, and acknowledge", async ({ page }) => {
  test.setTimeout(120_000);
  const client = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!, { auth: { persistSession: false } });
  const marker = "TEMPORARY FEATURE 021 LIFECYCLE CHECK";
  let actionId = 0;

  try {
    await login(page);
    await page.goto("/test-fixtures/recommendation-action");
    const feedbackForm = page.locator('form[data-recommendation-id]').first();
    const recommendationId = Number(await feedbackForm.getAttribute("data-recommendation-id"));
    const influencerId = Number(await feedbackForm.getAttribute("data-influencer-id"));
    await feedbackForm.locator('input[name="shared_note"]').fill(marker);
    await feedbackForm.getByRole("button", { name: "Save" }).click();
    await expect(feedbackForm.getByRole("status")).toContainText("planned experiment", { timeout: 45_000 });

    const { data: actionRows } = await client
      .from("recommendation_actions")
      .select("id")
      .eq("recommendation_id", recommendationId)
      .eq("bullet_index", 0)
      .eq("shared_note", marker);
    actionId = actionRows?.[0]?.id ?? 0;
    expect(actionId).toBeGreaterThan(0);
    const { data: influencer } = await client.from("influencers").select("handle").eq("id", influencerId).single();
    const { data: foreignPosts } = await client.from("post_snapshots").select("shortcode").neq("influencer_id", influencerId).limit(1);
    expect(influencer?.handle).toBeTruthy();
    expect(foreignPosts?.[0]?.shortcode).toBeTruthy();

    await page.goto(`/influencer/${influencer!.handle}`);
    let article = page.locator(`article[data-action-id="${actionId}"]`);
    const linkForm = article.getByTestId("link-experiment-form");
    const postSelect = linkForm.locator('select[name="shortcode"]');
    await postSelect.evaluate((element: HTMLSelectElement, shortcode: string) => {
      element.add(new Option(shortcode, shortcode));
      element.value = shortcode;
    }, foreignPosts![0].shortcode);
    await linkForm.getByRole("button", { name: "Link & start" }).click();
    await expect(linkForm.getByText("That post does not belong to this talent.")).toBeVisible();

    const ownedShortcode = await postSelect.locator("option").nth(1).getAttribute("value");
    expect(ownedShortcode).toBeTruthy();
    await postSelect.selectOption(ownedShortcode!);
    await linkForm.getByRole("button", { name: "Link & start" }).click();
    await expect.poll(async () => {
      const { data } = await client.from("recommendation_actions").select("experiment_status, published_at, review_at").eq("id", actionId).single();
      return data;
    }, { timeout: 45_000 }).toMatchObject({ experiment_status: "published" });
    const { data: linked } = await client.from("recommendation_actions").select("published_at, review_at").eq("id", actionId).single();
    expect(new Date(linked!.review_at).getTime() - new Date(linked!.published_at).getTime()).toBe(7 * 24 * 60 * 60 * 1000);

    await page.reload();
    article = page.locator(`article[data-action-id="${actionId}"]`);
    await article.getByRole("button", { name: "Abandon" }).click();
    await expect.poll(async () => (await client.from("recommendation_actions").select("experiment_status").eq("id", actionId).single()).data?.experiment_status).toBe("abandoned");

    const outcome = {
      target: { interactions: 150, views: 2000, captured_at: "2026-07-27T10:00:00.000Z" },
      baseline: { interactions_median: 100, views_median: 1000, sample_size: 4, cohort: "format_paid", post_type: "reel", paid_status: "organic", pillar: null },
      interaction_delta_pct: 50,
      views_delta_pct: 100,
      confidence: "directional",
      disclaimer: "Directional comparison only; this does not establish causal lift.",
    };
    await client.from("recommendation_actions").update({ experiment_status: "evaluated", baseline: outcome.baseline, outcome, evaluated_at: new Date().toISOString(), acknowledged_at: null }).eq("id", actionId);
    await page.reload();
    article = page.locator(`article[data-action-id="${actionId}"]`);
    await article.getByRole("button", { name: "Acknowledge outcome" }).click();
    await expect.poll(async () => Boolean((await client.from("recommendation_actions").select("acknowledged_at").eq("id", actionId).single()).data?.acknowledged_at)).toBe(true);
  } finally {
    if (actionId > 0) await client.from("recommendation_actions").delete().eq("id", actionId).eq("shared_note", marker);
  }
});

test("manual pillar override survives strategy change and is flagged when removed", async ({ page }) => {
  test.setTimeout(120_000);
  const client = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!, { auth: { persistSession: false } });
  const marker = "TEMPORARY FEATURE 021 STRATEGY CHECK";
  const pillar = "TEMPORARY FEATURE 021 PILLAR";
  let influencerId = 0;
  let shortcode = "";

  try {
    const [{ data: influencers }, { data: strategies }] = await Promise.all([
      client.from("influencers").select("id, handle").eq("active", true).order("id"),
      client.from("talent_strategies").select("influencer_id"),
    ]);
    const occupied = new Set((strategies ?? []).map((row) => row.influencer_id));
    const candidate = (influencers ?? []).find((row) => !occupied.has(row.id));
    test.skip(!candidate, "No talent without a strategy is available for marker-scoped verification.");
    influencerId = candidate!.id;
    const { data: posts } = await client.from("post_snapshots").select("shortcode").eq("influencer_id", influencerId).order("posted_at", { ascending: false }).limit(1);
    shortcode = posts?.[0]?.shortcode ?? "";
    test.skip(!shortcode, "No scraped post is available for pillar override verification.");
    await client.from("talent_strategies").insert({ influencer_id: influencerId, current_objective: marker, content_pillars: [pillar] });

    await login(page);
    await page.goto(`/influencer/${candidate!.handle}`);
    const pillarSelect = page.getByLabel(`Pillar for ${shortcode}`);
    await pillarSelect.selectOption(pillar);
    await pillarSelect.locator("xpath=..").getByRole("button", { name: "Override" }).click();
    await expect.poll(async () => {
      const { data } = await client.from("post_strategy_tags").select("pillar, source, removed_pillar").eq("influencer_id", influencerId).eq("shortcode", shortcode).maybeSingle();
      return data;
    }).toEqual({ pillar, source: "manual", removed_pillar: false });

    const strategyPanel = page.getByTestId("strategy-panel");
    await strategyPanel.getByRole("button", { name: "Edit strategy" }).click();
    await strategyPanel.getByLabel("Content pillars").fill("");
    await strategyPanel.getByRole("button", { name: "Save and mark reviewed" }).click();
    await expect.poll(async () => (await client.from("post_strategy_tags").select("removed_pillar").eq("influencer_id", influencerId).eq("shortcode", shortcode).single()).data?.removed_pillar).toBe(true);

    const clearedPillar = page.getByLabel(`Pillar for ${shortcode}`);
    await clearedPillar.selectOption("");
    await clearedPillar.locator("xpath=..").getByRole("button", { name: "Override" }).click();
    await expect.poll(async () => {
      const { data } = await client.from("post_strategy_tags").select("pillar, removed_pillar").eq("influencer_id", influencerId).eq("shortcode", shortcode).single();
      return data;
    }).toEqual({ pillar: null, removed_pillar: false });

    await strategyPanel.getByRole("button", { name: "Edit strategy" }).click();
    await strategyPanel.getByRole("button", { name: "Save and mark reviewed" }).click();
    await expect.poll(async () => (await client.from("post_strategy_tags").select("removed_pillar").eq("influencer_id", influencerId).eq("shortcode", shortcode).single()).data?.removed_pillar).toBe(false);
  } finally {
    if (influencerId > 0 && shortcode) await client.from("post_strategy_tags").delete().eq("influencer_id", influencerId).eq("shortcode", shortcode).eq("source", "manual");
    if (influencerId > 0) await client.from("talent_strategies").delete().eq("influencer_id", influencerId).eq("current_objective", marker);
  }
});

test("weekly review renders every portfolio section bilingually with period and KPI health", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/weekly-review");
  await expect(page.getByTestId("weekly-review")).toContainText("2026-07-27 → 2026-08-02");
  await expect(page.getByTestId("weekly-review").getByText("Discuss the active experiment").first()).toBeVisible();
  await expect(page.getByText("Craft reel beat its baseline")).toBeVisible();
  await expect(page.getByText("Strategy review is overdue")).toBeVisible();
  await page.getByText("Experiments, strategy health & conversations").click();
  await expect(page.getByText("Agree the next craft test")).toBeVisible();
  const health = page.getByTestId("portfolio-health");
  await expect(health).toContainText("60%");
  await expect(health).toContainText("7");
  await expect(health).toContainText("75%");

  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.getByTestId("weekly-review").getByText("Revisar el experimento activo").first()).toBeVisible();
  await expect(health).toContainText("Cobertura estratégica");
});

test("legacy briefing still renders and empty KPI denominators use em dash", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/weekly-review?scenario=legacy");
  await expect(page.getByText("Legacy summary")).toBeVisible();
  await expect(page.getByTestId("weekly-review")).toHaveCount(0);

  await page.goto("/test-fixtures/weekly-review?scenario=empty");
  const health = page.getByTestId("portfolio-health");
  await expect(health).toContainText("0/0");
  await expect(health).toContainText("no evaluated outcomes");
  await expect(health.getByText("—")).toHaveCount(2);

  await page.goto("/test-fixtures/weekly-review?scenario=malformed");
  await expect(page.getByTestId("weekly-review")).toHaveCount(0);
  await expect(page.getByTestId("portfolio-health")).toBeVisible();
});

test("roster defaults to attention priority and retains existing sorts", async ({ page }) => {
  await login(page);
  await page.goto("/test-fixtures/roster-priority");
  const rows = page.locator("ol > li");
  await expect(rows.nth(0)).toContainText("data_missing");
  await expect(rows.nth(1)).toContainText("recommendation_due");
  await expect(rows.nth(2)).toContainText("large_no_action");

  await page.locator("select").selectOption("audience");
  await expect(rows.nth(0)).toContainText("large_no_action");
  await page.locator("select").selectOption("name");
  await expect(rows.nth(0)).toContainText("data_missing");
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

test("list views keep organic posts unbadged", async ({ page }) => {
  await login(page);

  await openFirstInfluencer(page);

  const recentPostsSection = page
    .getByRole("heading", { name: "THE LOG · RECENT POSTS" })
    .locator("xpath=..");
  const greatestHitsSection = page
    .getByRole("heading", { name: "GREATEST HITS · ALL-TIME" })
    .locator("xpath=..");

  await expect(recentPostsSection.getByText("Organic", { exact: true })).toHaveCount(0);
  await expect(greatestHitsSection.getByText("Organic", { exact: true })).toHaveCount(0);
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
