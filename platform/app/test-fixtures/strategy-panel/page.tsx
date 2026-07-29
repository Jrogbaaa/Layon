import { notFound } from "next/navigation";
import { StrategyPanel } from "@/app/components/StrategyPanel";
import { LanguageProvider } from "@/app/components/LanguageProvider";
import { LanguageToggle } from "@/app/components/LanguageToggle";
import type { Influencer, TalentStrategy } from "@/app/lib/types";

const influencer: Influencer = {
  id: 1,
  handle: "fixture_talent",
  display_name: "Fixture Talent",
  avatar_url: null,
};

const strategy: TalentStrategy = {
  influencer_id: 1,
  current_objective: "Grow meaningful conversation without changing the creator's voice.",
  horizon: "2099-12-31",
  target_audience: "Spanish-speaking viewers interested in culture and everyday humor.",
  content_pillars: ["Behind the scenes", "Observational humor"],
  development_formats: ["reel", "carousel"],
  tone: "Warm, precise, and self-aware.",
  guardrails: "No private family stories.",
  commercial_direction: "Keep product work clearly separated from organic storytelling.",
  posting_constraints: "No more than three planned posts per week.",
  updated_at: "2026-07-29T08:00:00.000Z",
  reviewed_at: "2026-07-29T08:00:00.000Z",
};

export default async function StrategyPanelFixture({
  searchParams,
}: {
  searchParams: Promise<{ scenario?: string }>;
}) {
  if (process.env.NODE_ENV === "production") notFound();
  const { scenario = "current" } = await searchParams;
  const isEmpty = scenario === "empty";
  const isStale = scenario === "stale";

  return (
    <LanguageProvider>
      <div>
        <div className="flex items-center justify-between">
          <h1 className="display-hero text-4xl text-ink">Strategy panel fixture</h1>
          <LanguageToggle />
        </div>
        <StrategyPanel
          influencer={influencer}
          strategy={isEmpty ? null : strategy}
          latestCaptureAt={isStale ? "2020-01-01T00:00:00.000Z" : new Date().toISOString()}
          recommendationGeneratedAt={isStale ? "2026-07-01T00:00:00.000Z" : "2099-01-01T00:00:00.000Z"}
        />
      </div>
    </LanguageProvider>
  );
}
