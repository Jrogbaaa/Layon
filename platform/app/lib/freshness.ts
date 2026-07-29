import type { TalentStrategy } from "@/app/lib/types";

export type FreshnessStatus = "current" | "stale" | "missing";

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

type StrategyContent = Pick<
  TalentStrategy,
  | "current_objective"
  | "target_audience"
  | "content_pillars"
  | "development_formats"
  | "tone"
  | "guardrails"
  | "commercial_direction"
  | "posting_constraints"
>;

export function hasSubstantiveStrategy(strategy: StrategyContent | null | undefined): boolean {
  return Boolean(
    strategy
      && (
        strategy.current_objective
        || strategy.target_audience
        || strategy.content_pillars.length
        || strategy.development_formats.length
        || strategy.tone
        || strategy.guardrails
        || strategy.commercial_direction
        || strategy.posting_constraints
      ),
  );
}

export function getCaptureFreshness(
  capturedAt: string | null | undefined,
  now = new Date(),
): FreshnessStatus {
  if (!capturedAt) return "missing";
  const captured = new Date(capturedAt);
  if (Number.isNaN(captured.getTime())) return "missing";
  return now.getTime() - captured.getTime() > 36 * HOUR_MS ? "stale" : "current";
}

export function isStrategyReviewStale(
  reviewedAt: string | null | undefined,
  now = new Date(),
): boolean {
  if (!reviewedAt) return true;
  const reviewed = new Date(reviewedAt);
  if (Number.isNaN(reviewed.getTime())) return true;
  return now.getTime() - reviewed.getTime() > 90 * DAY_MS;
}

export function isStrategyHorizonExpired(
  horizon: string | null | undefined,
  now = new Date(),
): boolean {
  if (!horizon) return false;
  const todayInMadrid = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Madrid",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
  return horizon < todayInMadrid;
}

export function isRecommendationOlderThanStrategy(
  recommendationGeneratedAt: string | null | undefined,
  strategyUpdatedAt: string | null | undefined,
): boolean {
  if (!recommendationGeneratedAt || !strategyUpdatedAt) return false;
  const recommendationTime = new Date(recommendationGeneratedAt).getTime();
  const strategyTime = new Date(strategyUpdatedAt).getTime();
  if (Number.isNaN(recommendationTime) || Number.isNaN(strategyTime)) return false;
  return recommendationTime < strategyTime;
}
