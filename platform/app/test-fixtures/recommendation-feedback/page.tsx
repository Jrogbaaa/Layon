import { NextActionPanel } from "@/app/components/NextActionPanel";
import { RecommendationContent } from "@/app/components/RecommendationContent";
import { LanguageProvider } from "@/app/components/LanguageProvider";
import { LanguageToggle } from "@/app/components/LanguageToggle";
import { deriveNextAction } from "@/app/lib/next-action";
import { notFound } from "next/navigation";
import type { Recommendation, RecommendationAction } from "@/app/lib/types";

const recommendation: Recommendation = {
  id: 42,
  generated_at: "2026-07-29T00:00:00.000Z",
  model: "fixture",
  content: JSON.stringify({
    bullets: [
      {
        kind: "past_success",
        text: { en: "Build a recurring craft-led reel.", es: "Crea un reel recurrente sobre el oficio." },
        reason: { en: "The format beat the median.", es: "El formato superó la mediana." },
        shortcode: "fixture-post",
      },
    ],
  }),
};

const action: RecommendationAction = {
  id: 1,
  recommendation_id: 42,
  influencer_id: 7,
  bullet_index: 0,
  decision: "revisit",
  shared_note: "Discuss together",
  revisit_on: "2026-08-15",
  experiment_status: null,
  linked_shortcode: null,
  published_at: null,
  review_at: null,
  baseline: null,
  outcome: null,
  evaluated_at: null,
  acknowledged_at: null,
  created_at: "2026-07-29T00:00:00.000Z",
  updated_at: "2026-07-29T00:00:00.000Z",
};

const evaluatedOutcome = {
  target: { interactions: 150, views: 2000, captured_at: "2026-07-27T00:00:00.000Z" },
  baseline: { interactions_median: 100, views_median: 1000, sample_size: 4, cohort: "format_paid" as const, post_type: "reel" as const, paid_status: "organic" as const, pillar: null },
  interaction_delta_pct: 50,
  views_delta_pct: 100,
  confidence: "directional" as const,
  disclaimer: "Directional comparison only; this does not establish causal lift.",
};

export default async function RecommendationFeedbackFixture({
  searchParams,
}: {
  searchParams: Promise<{ scenario?: string }>;
}) {
  const { scenario = "recommendation" } = await searchParams;
  if (process.env.NODE_ENV === "production") notFound();
  const captureAt = scenario === "missing" ? null : scenario === "stale" ? "2020-01-01T00:00:00.000Z" : "2099-01-01T00:00:00.000Z";
  const scenarioActions = scenario === "active"
    ? [{ ...action, decision: "try" as const, experiment_status: "planned" as const }]
    : scenario === "review"
      ? [{ ...action, decision: "try" as const, experiment_status: "evaluated" as const, outcome: evaluatedOutcome }]
      : scenario === "acknowledged"
      ? [{ ...action, decision: "try" as const, experiment_status: "evaluated" as const, acknowledged_at: "2026-07-29T12:00:00.000Z" }]
      : scenario === "evaluated-no-outcome"
        ? [{ ...action, decision: "try" as const, experiment_status: "evaluated" as const }]
      : scenario === "answered" || scenario === "none"
        ? [action]
        : [];
  const nextAction = deriveNextAction({
    latestCaptureAt: captureAt,
    highlights: scenario === "warning" ? [{ content: "Cadence fell sharply.", metric: { severity: "warning" }, captured_at: "2026-07-29T00:00:00.000Z" }] : [],
    recommendation,
    actions: scenarioActions,
  });

  return (
    <LanguageProvider>
      <main className="mx-auto max-w-3xl p-8">
        <div className="mb-4 flex justify-end"><LanguageToggle /></div>
        <NextActionPanel action={nextAction} />
        <section className="panel p-7">
          {scenario === "legacy" ? (
            <RecommendationContent content="## Legacy brief\n\nKeep the proven cadence." />
          ) : (
            <RecommendationContent
              content={recommendation.content}
              recommendationId={recommendation.id}
              influencerId={7}
              handle="fixture_talent"
              actions={scenario === "answered" ? [action] : []}
            />
          )}
        </section>
      </main>
    </LanguageProvider>
  );
}
