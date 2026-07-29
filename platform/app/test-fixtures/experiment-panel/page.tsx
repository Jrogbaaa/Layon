import { notFound } from "next/navigation";
import { ExperimentPanel } from "@/app/components/ExperimentPanel";
import { LanguageProvider } from "@/app/components/LanguageProvider";
import { LanguageToggle } from "@/app/components/LanguageToggle";
import type { RecommendationAction } from "@/app/lib/types";

const influencer = { id: 7, handle: "fixture_talent", display_name: "Fixture Talent", avatar_url: null };
const posts = [
  { shortcode: "organic-post", post_type: "reel" as const, likes: 120, comments: 30, views: 2000, caption: "Craft", posted_at: "2026-07-20T10:00:00.000Z", is_ad: false },
  { shortcode: "paid-post", post_type: "reel" as const, likes: 80, comments: 20, views: 1500, caption: "Partner", posted_at: "2026-07-18T10:00:00.000Z", is_ad: true },
];

function action(id: number, status: RecommendationAction["experiment_status"]): RecommendationAction {
  const evaluated = status === "evaluated";
  return {
    id,
    recommendation_id: 42,
    influencer_id: 7,
    bullet_index: id,
    decision: "try",
    shared_note: id === 1 ? "Test the craft-led format" : "",
    revisit_on: null,
    experiment_status: status,
    linked_shortcode: status === "planned" ? null : "organic-post",
    published_at: status === "planned" ? null : "2026-07-20T10:00:00.000Z",
    review_at: status === "planned" ? null : "2026-07-27T10:00:00.000Z",
    baseline: evaluated ? { interactions_median: 100, views_median: 1000, sample_size: 4, cohort: "format_paid_pillar", post_type: "reel", paid_status: "organic", pillar: "craft" } : null,
    outcome: evaluated ? { target: { interactions: 150, views: 2000, captured_at: "2026-07-27T10:00:00.000Z" }, baseline: { interactions_median: 100, views_median: 1000, sample_size: 4, cohort: "format_paid_pillar", post_type: "reel", paid_status: "organic", pillar: "craft" }, interaction_delta_pct: 50, views_delta_pct: 100, confidence: "directional", disclaimer: "Directional comparison only; this does not establish causal lift." } : null,
    evaluated_at: evaluated ? "2026-07-27T10:00:00.000Z" : null,
    acknowledged_at: null,
    created_at: "2026-07-20T00:00:00.000Z",
    updated_at: "2026-07-27T10:00:00.000Z",
  };
}

export default async function ExperimentPanelFixture({ searchParams }: { searchParams: Promise<{ scenario?: string }> }) {
  if (process.env.NODE_ENV === "production") notFound();
  const { scenario } = await searchParams;
  return (
    <LanguageProvider>
      <main className="mx-auto max-w-5xl p-8">
        <div className="mb-4 flex justify-end"><LanguageToggle /></div>
        <ExperimentPanel
          influencer={influencer}
          actions={[action(1, "planned"), action(2, "published"), action(3, "evaluated")]}
          posts={posts}
          tags={[
            { id: 1, influencer_id: 7, shortcode: "organic-post", pillar: "removed pillar", source: "manual", strategy_updated_at: "old", removed_pillar: true, tagged_at: "2026-07-20T00:00:00.000Z", updated_at: "2026-07-20T00:00:00.000Z" },
            { id: 2, influencer_id: 7, shortcode: "paid-post", pillar: "craft", source: "automatic", strategy_updated_at: "current", removed_pillar: false, tagged_at: "2026-07-20T00:00:00.000Z", updated_at: "2026-07-20T00:00:00.000Z" },
          ]}
          pillars={scenario === "zero-pillars" ? [] : ["craft", "race"]}
          performance={[
            { pillar: "craft", paidStatus: "organic", interactionsMedian: 100, viewsMedian: 1000, sampleSize: 4, confidence: "directional" },
            { pillar: "craft", paidStatus: "paid", interactionsMedian: 70, viewsMedian: 800, sampleSize: 2, confidence: "insufficient" },
          ]}
        />
      </main>
    </LanguageProvider>
  );
}
