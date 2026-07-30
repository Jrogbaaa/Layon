import "server-only";
import { cache } from "react";
import { getSupabaseClient } from "@/app/lib/supabase";
import { latestFollowerDelta } from "@/app/lib/metrics";
import { deriveNextAction } from "@/app/lib/next-action";
import { hasSubstantiveStrategy } from "@/app/lib/freshness";
import type {
  Highlight,
  Influencer,
  InfluencerDashboard,
  PostClassification,
  PillarPerformance,
  PortfolioKpis,
  PostStrategyTag,
  PostSnapshot,
  ProfileSnapshot,
  Recommendation,
  RecommendationAction,
  RosterBriefing,
  RosterEntry,
  TalentStrategy,
  TopPost,
  TrendHeadlines,
  TrendSnapshot,
} from "@/app/lib/types";

type PostClassificationRow = PostClassification & { shortcode: string };

const ACTION_FIELDS =
  "id, recommendation_id, influencer_id, bullet_index, decision, shared_note, revisit_on, experiment_status, linked_shortcode, published_at, review_at, baseline, outcome, evaluated_at, acknowledged_at, created_at, updated_at";

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

// cache(): the nav tape and the roster page both call this within one request.
export const getRoster = cache(async function getRoster(): Promise<RosterEntry[]> {
  const client = getSupabaseClient();

  const { data: influencers } = await client
    .from("influencers")
    .select("id, handle, display_name, avatar_url")
    .eq("active", true)
    .order("handle");

  if (!influencers || influencers.length === 0) return [];
  const influencerIds = (influencers as Influencer[]).map((i) => i.id);

  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();

  // Explicit per-influencer-scaled caps so PostgREST's default max-rows limit
  // (1000) can't silently truncate a bulk .in() query before it reaches every
  // influencer's rows.
  const SNAPSHOT_CAP_PER_INFLUENCER = 14;
  const HIGHLIGHT_CAP_PER_INFLUENCER = 5;
  const RECOMMENDATION_CAP_PER_INFLUENCER = 5;
  const ACTION_CAP_PER_INFLUENCER = 200;

  const [snapshotsRes, highlightsRes, recommendationsRes, actionsRes] = await Promise.all([
    client
      .from("profile_snapshots")
      .select("influencer_id, followers, following, media_count, bio, captured_at")
      .in("influencer_id", influencerIds)
      .order("captured_at", { ascending: false })
      .limit(influencerIds.length * SNAPSHOT_CAP_PER_INFLUENCER),
    client
      .from("highlights")
      .select("influencer_id, content, metric, captured_at")
      .in("influencer_id", influencerIds)
      .gte("captured_at", sevenDaysAgo)
      .order("captured_at", { ascending: false })
      .limit(influencerIds.length * HIGHLIGHT_CAP_PER_INFLUENCER),
    client
      .from("recommendations")
      .select("id, influencer_id, generated_at, model, content")
      .in("influencer_id", influencerIds)
      .order("generated_at", { ascending: false })
      .limit(influencerIds.length * RECOMMENDATION_CAP_PER_INFLUENCER),
    client
      .from("recommendation_actions")
      .select(`influencer_id, ${ACTION_FIELDS}`)
      .in("influencer_id", influencerIds)
      .order("updated_at", { ascending: false })
      .limit(influencerIds.length * ACTION_CAP_PER_INFLUENCER),
  ]);

  const snapshotsByInfluencer = new Map<number, ProfileSnapshot[]>();
  for (const row of snapshotsRes.data ?? []) {
    const id = row.influencer_id as number;
    const list = snapshotsByInfluencer.get(id) ?? [];
    if (list.length < SNAPSHOT_CAP_PER_INFLUENCER) list.push(row as ProfileSnapshot);
    snapshotsByInfluencer.set(id, list);
  }

  const highlightsByInfluencer = new Map<number, Highlight[]>();
  for (const row of highlightsRes.data ?? []) {
    const id = row.influencer_id as number;
    const list = highlightsByInfluencer.get(id) ?? [];
    if (list.length < HIGHLIGHT_CAP_PER_INFLUENCER) list.push(row as Highlight);
    highlightsByInfluencer.set(id, list);
  }

  const latestRecByInfluencer = new Map<number, Recommendation>();
  for (const row of recommendationsRes.data ?? []) {
    const id = row.influencer_id as number;
    if (!latestRecByInfluencer.has(id)) {
      latestRecByInfluencer.set(id, row as Recommendation);
    }
  }

  const actionsByInfluencer = new Map<number, RecommendationAction[]>();
  for (const row of actionsRes.data ?? []) {
    const id = row.influencer_id as number;
    const list = actionsByInfluencer.get(id) ?? [];
    list.push(row as RecommendationAction);
    actionsByInfluencer.set(id, list);
  }

  return (influencers as Influencer[]).map((influencer) => {
    const rows = snapshotsByInfluencer.get(influencer.id) ?? [];
    const latestSnapshot = rows[0] ?? null;
    const history = [...rows].reverse();
    const followerDelta = latestFollowerDelta(history);
    const highlights = highlightsByInfluencer.get(influencer.id) ?? [];
    const latestRecommendation = latestRecByInfluencer.get(influencer.id) ?? null;
    const recommendationActions = actionsByInfluencer.get(influencer.id) ?? [];

    return {
      influencer,
      latestSnapshot,
      followerDelta,
      recentHighlights: highlights,
      history,
      nextAction: deriveNextAction({
        latestCaptureAt: latestSnapshot?.captured_at ?? null,
        highlights,
        recommendation: latestRecommendation,
        actions: recommendationActions,
      }),
    };
  });
});

export async function getInfluencerDashboard(handle: string): Promise<InfluencerDashboard | null> {
  const client = getSupabaseClient();

  const { data: influencer } = await client
    .from("influencers")
    .select("id, handle, display_name, avatar_url")
    .eq("handle", handle)
    .single();

  if (!influencer) return null;

  const { data: profileHistory } = await client
    .from("profile_snapshots")
    .select("followers, following, media_count, bio, captured_at")
    .eq("influencer_id", influencer.id)
    .order("captured_at", { ascending: false })
    .limit(30);

  const { data: rawPosts } = await client
    .from("post_snapshots")
    .select("shortcode, post_type, likes, comments, views, caption, posted_at, captured_at, is_ad")
    .eq("influencer_id", influencer.id)
    .order("captured_at", { ascending: false })
    .limit(100);

  let rawClassifications: unknown[] = [];
  try {
    const { data } = await client
      .from("post_classifications")
      .select("shortcode, status, decision_code, evidence, classifier_version, input_hash, classified_at")
      .eq("influencer_id", influencer.id)
      .order("classified_at", { ascending: false });
    rawClassifications = data ?? [];
  } catch {
    rawClassifications = [];
  }

  const classificationByShortcode = new Map(
    (rawClassifications as PostClassificationRow[]).map((row) => [row.shortcode, row] as const),
  );

  const latestByShortcode = new Map<string, PostSnapshot>();
  for (const row of rawPosts ?? []) {
    const post = row as PostSnapshot & { captured_at: string };
    if (!latestByShortcode.has(post.shortcode)) {
      latestByShortcode.set(post.shortcode, {
        shortcode: post.shortcode,
        post_type: post.post_type,
        likes: post.likes,
        comments: post.comments,
        views: post.views,
        caption: post.caption,
        posted_at: post.posted_at,
        is_ad: post.is_ad,
        classification: classificationByShortcode.get(post.shortcode) ?? null,
      });
    }
  }

  const sortedByDateDesc = Array.from(latestByShortcode.values())
    .sort((a, b) => new Date(b.posted_at).getTime() - new Date(a.posted_at).getTime());

  const recentPosts = sortedByDateDesc.slice(0, 12);
  const chartPosts = sortedByDateDesc.slice(0, 30).reverse();

  const { data: highlights } = await client
    .from("highlights")
    .select("content, metric, captured_at")
    .eq("influencer_id", influencer.id)
    .order("captured_at", { ascending: false })
    .limit(5);

  const { data: recommendations } = await client
    .from("recommendations")
    .select("id, generated_at, model, content")
    .eq("influencer_id", influencer.id)
    .order("generated_at", { ascending: false })
    .limit(1);
  const latestRecommendation = ((recommendations ?? [])[0] as Recommendation) ?? null;

  const { data: actionRows } = await client
    .from("recommendation_actions")
    .select(ACTION_FIELDS)
    .eq("influencer_id", influencer.id)
    .order("updated_at", { ascending: false });
  const recommendationActions = (actionRows ?? []) as RecommendationAction[];

  const { data: tagRows } = await client
    .from("post_strategy_tags")
    .select(
      "id, influencer_id, shortcode, pillar, source, strategy_updated_at, removed_pillar, tagged_at, updated_at",
    )
    .eq("influencer_id", influencer.id)
    .order("updated_at", { ascending: false });
  const postStrategyTags = (tagRows ?? []) as PostStrategyTag[];

  const { data: strategy } = await client
    .from("talent_strategies")
    .select(
      "influencer_id, current_objective, horizon, target_audience, content_pillars, development_formats, tone, guardrails, commercial_direction, posting_constraints, updated_at, reviewed_at",
    )
    .eq("influencer_id", influencer.id)
    .maybeSingle();

  const { data: topPosts } = await client
    .from("top_posts")
    .select("shortcode, post_type, likes, comments, views, caption, posted_at, engagement, is_ad")
    .eq("influencer_id", influencer.id)
    .order("engagement", { ascending: false })
    .limit(5);

  const topPostsWithClassification = (topPosts ?? []).map((post) => ({
    ...post,
    classification: classificationByShortcode.get(post.shortcode) ?? null,
  }));

  const postByShortcode = new Map(sortedByDateDesc.slice(0, 30).map((post) => [post.shortcode, post] as const));
  const performanceGroups = new Map<string, { pillar: string; paidStatus: PostClassification["status"]; interactions: number[]; views: number[] }>();
  for (const tag of postStrategyTags) {
    if (!tag.pillar) continue;
    const post = postByShortcode.get(tag.shortcode);
    if (!post) continue;
    const paidStatus = post.classification?.status ?? (post.is_ad ? "paid" : "organic");
    const key = `${tag.pillar}\u0000${paidStatus}`;
    const group = performanceGroups.get(key) ?? { pillar: tag.pillar, paidStatus, interactions: [], views: [] };
    group.interactions.push(post.likes + post.comments);
    if (post.views != null) group.views.push(post.views);
    performanceGroups.set(key, group);
  }
  const pillarPerformance: PillarPerformance[] = Array.from(performanceGroups.values()).map((group) => ({
    pillar: group.pillar,
    paidStatus: group.paidStatus,
    interactionsMedian: median(group.interactions),
    viewsMedian: group.views.length ? median(group.views) : null,
    sampleSize: group.interactions.length,
    confidence: group.interactions.length < 3 ? "insufficient" : group.interactions.length <= 5 ? "directional" : "strong",
  }));

  return {
    influencer: influencer as Influencer,
    profileHistory: [...(profileHistory ?? [])].reverse() as ProfileSnapshot[],
    recentPosts,
    chartPosts,
    latestRecommendation,
    recommendationActions,
    nextAction: deriveNextAction({
      latestCaptureAt: ((profileHistory ?? [])[0] as ProfileSnapshot | undefined)?.captured_at ?? null,
      highlights: (highlights ?? []) as Highlight[],
      recommendation: latestRecommendation,
      actions: recommendationActions,
    }),
    postStrategyTags,
    pillarPerformance,
    strategy: (strategy as TalentStrategy | null) ?? null,
    highlights: (highlights ?? []) as Highlight[],
    topPosts: topPostsWithClassification as TopPost[],
  };
}

export async function getLatestBriefing(): Promise<RosterBriefing | null> {
  const client = getSupabaseClient();

  const { data } = await client
    .from("roster_briefings")
    .select("generated_at, model, content, period_start, period_end")
    .order("generated_at", { ascending: false })
    .limit(1);

  return ((data ?? [])[0] as RosterBriefing) ?? null;
}

export async function getPortfolioKpis(): Promise<PortfolioKpis> {
  const client = getSupabaseClient();
  const { data: influencerRows } = await client.from("influencers").select("id").eq("active", true);
  const influencerIds = (influencerRows ?? []).map((row) => row.id as number);
  if (!influencerIds.length) {
    return { rosterSize: 0, strategyProfiles: 0, unresolvedRecommendations: 0, activeExperiments: 0, evaluatedExperiments: 0, experimentHits: 0, experimentHitRate: null };
  }

  const [{ data: strategies }, { data: recommendationRows }, { data: actionRows }] = await Promise.all([
    client
      .from("talent_strategies")
      .select("influencer_id, current_objective, target_audience, content_pillars, development_formats, tone, guardrails, commercial_direction, posting_constraints")
      .in("influencer_id", influencerIds),
    client
      .from("recommendations")
      .select("id, influencer_id, content, generated_at")
      .in("influencer_id", influencerIds)
      .order("generated_at", { ascending: false }),
    client
      .from("recommendation_actions")
      .select("recommendation_id, influencer_id, bullet_index, experiment_status, outcome")
      .in("influencer_id", influencerIds),
  ]);

  const strategyProfiles = (strategies ?? []).filter(hasSubstantiveStrategy).length;

  const latestByInfluencer = new Map<number, { id: number; content: string }>();
  for (const row of recommendationRows ?? []) {
    if (!latestByInfluencer.has(row.influencer_id)) latestByInfluencer.set(row.influencer_id, row);
  }
  const answeredByRecommendation = new Map<number, Set<number>>();
  for (const action of actionRows ?? []) {
    const indices = answeredByRecommendation.get(action.recommendation_id) ?? new Set<number>();
    indices.add(action.bullet_index);
    answeredByRecommendation.set(action.recommendation_id, indices);
  }
  let unresolvedRecommendations = 0;
  for (const recommendation of latestByInfluencer.values()) {
    try {
      const parsed = typeof recommendation.content === "string" ? JSON.parse(recommendation.content) : recommendation.content;
      if (!Array.isArray(parsed?.bullets)) continue;
      const answered = answeredByRecommendation.get(recommendation.id) ?? new Set<number>();
      unresolvedRecommendations += parsed.bullets.filter((_: unknown, index: number) => !answered.has(index)).length;
    } catch {
      // Legacy prose has no stable bullets and is not counted as unresolved work.
    }
  }

  const activeExperiments = (actionRows ?? []).filter((action) =>
    action.experiment_status === "planned" || action.experiment_status === "published",
  ).length;
  const evaluated = (actionRows ?? []).filter((action) => {
    const outcome = action.outcome as { interaction_delta_pct?: unknown } | null;
    return action.experiment_status === "evaluated" && typeof outcome?.interaction_delta_pct === "number";
  });
  const experimentHits = evaluated.filter((action) => {
    const outcome = action.outcome as { interaction_delta_pct: number; confidence?: string };
    return outcome.interaction_delta_pct > 0 && (outcome.confidence === "directional" || outcome.confidence === "strong");
  }).length;

  return {
    rosterSize: influencerIds.length,
    strategyProfiles,
    unresolvedRecommendations,
    activeExperiments,
    evaluatedExperiments: evaluated.length,
    experimentHits,
    experimentHitRate: evaluated.length ? Math.round((experimentHits / evaluated.length) * 100) : null,
  };
}

export async function getLatestTrends(limit = 2): Promise<TrendSnapshot[]> {
  const client = getSupabaseClient();

  const { data } = await client
    .from("trend_snapshots")
    .select("source_url, title, content_text, captured_at")
    .order("captured_at", { ascending: false })
    .limit(limit);

  return (data ?? []) as TrendSnapshot[];
}

export async function getLatestTrendHeadlines(): Promise<TrendHeadlines | null> {
  const client = getSupabaseClient();

  const { data } = await client
    .from("trend_headlines")
    .select("generated_at, model, content")
    .order("generated_at", { ascending: false })
    .limit(1);

  return ((data ?? [])[0] as TrendHeadlines) ?? null;
}
