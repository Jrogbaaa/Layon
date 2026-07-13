import "server-only";
import { cache } from "react";
import { getSupabaseClient } from "@/app/lib/supabase";
import { latestFollowerDelta } from "@/app/lib/metrics";
import type {
  Highlight,
  Influencer,
  InfluencerDashboard,
  PostSnapshot,
  ProfileSnapshot,
  Recommendation,
  RosterBriefing,
  RosterEntry,
  TopPost,
  TrendHeadlines,
  TrendSnapshot,
} from "@/app/lib/types";

// cache(): the nav tape and the roster page both call this within one request.
export const getRoster = cache(async function getRoster(): Promise<RosterEntry[]> {
  const client = getSupabaseClient();

  const { data: influencers } = await client
    .from("influencers")
    .select("id, handle, display_name, avatar_url")
    .eq("active", true)
    .order("handle");

  if (!influencers) return [];

  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();

  const entries: RosterEntry[] = [];
  for (const influencer of influencers as Influencer[]) {
    const { data: snapshots } = await client
      .from("profile_snapshots")
      .select("followers, following, media_count, bio, captured_at")
      .eq("influencer_id", influencer.id)
      .order("captured_at", { ascending: false })
      .limit(14);

    const rows = (snapshots ?? []) as ProfileSnapshot[];
    const latestSnapshot = rows[0] ?? null;
    const history = [...rows].reverse();
    const followerDelta = latestFollowerDelta(history);

    const { data: recentHighlights } = await client
      .from("highlights")
      .select("content, metric, captured_at")
      .eq("influencer_id", influencer.id)
      .gte("captured_at", sevenDaysAgo)
      .order("captured_at", { ascending: false })
      .limit(5);

    entries.push({
      influencer,
      latestSnapshot,
      followerDelta,
      recentHighlights: (recentHighlights ?? []) as Highlight[],
      history,
    });
  }

  return entries;
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
    .select("shortcode, post_type, likes, comments, views, caption, posted_at, captured_at")
    .eq("influencer_id", influencer.id)
    .order("captured_at", { ascending: false })
    .limit(100);

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
    .select("generated_at, model, content")
    .eq("influencer_id", influencer.id)
    .order("generated_at", { ascending: false })
    .limit(1);

  const { data: topPosts } = await client
    .from("top_posts")
    .select("shortcode, post_type, likes, comments, views, caption, posted_at, engagement")
    .eq("influencer_id", influencer.id)
    .order("engagement", { ascending: false })
    .limit(5);

  return {
    influencer: influencer as Influencer,
    profileHistory: [...(profileHistory ?? [])].reverse() as ProfileSnapshot[],
    recentPosts,
    chartPosts,
    latestRecommendation: ((recommendations ?? [])[0] as Recommendation) ?? null,
    highlights: (highlights ?? []) as Highlight[],
    topPosts: (topPosts ?? []) as TopPost[],
  };
}

export async function getLatestBriefing(): Promise<RosterBriefing | null> {
  const client = getSupabaseClient();

  const { data } = await client
    .from("roster_briefings")
    .select("generated_at, model, content")
    .order("generated_at", { ascending: false })
    .limit(1);

  return ((data ?? [])[0] as RosterBriefing) ?? null;
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
