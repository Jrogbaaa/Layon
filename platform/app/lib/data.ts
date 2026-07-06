import "server-only";
import { getSupabaseClient } from "@/app/lib/supabase";
import type {
  Influencer,
  InfluencerDashboard,
  PostSnapshot,
  ProfileSnapshot,
  Recommendation,
  RosterEntry,
  TrendSnapshot,
} from "@/app/lib/types";

export async function getRoster(): Promise<RosterEntry[]> {
  const client = getSupabaseClient();

  const { data: influencers } = await client
    .from("influencers")
    .select("id, handle, display_name")
    .eq("active", true)
    .order("handle");

  if (!influencers) return [];

  const entries: RosterEntry[] = [];
  for (const influencer of influencers as Influencer[]) {
    const { data: snapshots } = await client
      .from("profile_snapshots")
      .select("followers, following, media_count, bio, captured_at")
      .eq("influencer_id", influencer.id)
      .order("captured_at", { ascending: false })
      .limit(2);

    const rows = (snapshots ?? []) as ProfileSnapshot[];
    const latestSnapshot = rows[0] ?? null;
    const followerDelta = rows.length >= 2 ? rows[0].followers - rows[1].followers : 0;

    entries.push({ influencer, latestSnapshot, followerDelta });
  }

  return entries;
}

export async function getInfluencerDashboard(handle: string): Promise<InfluencerDashboard | null> {
  const client = getSupabaseClient();

  const { data: influencer } = await client
    .from("influencers")
    .select("id, handle, display_name")
    .eq("handle", handle)
    .single();

  if (!influencer) return null;

  const { data: profileHistory } = await client
    .from("profile_snapshots")
    .select("followers, following, media_count, bio, captured_at")
    .eq("influencer_id", influencer.id)
    .order("captured_at", { ascending: true })
    .limit(30);

  const { data: recentPosts } = await client
    .from("post_snapshots")
    .select("shortcode, post_type, likes, comments, caption, posted_at")
    .eq("influencer_id", influencer.id)
    .order("posted_at", { ascending: false })
    .limit(12);

  const { data: recommendations } = await client
    .from("recommendations")
    .select("generated_at, model, content")
    .eq("influencer_id", influencer.id)
    .order("generated_at", { ascending: false })
    .limit(1);

  return {
    influencer: influencer as Influencer,
    profileHistory: (profileHistory ?? []) as ProfileSnapshot[],
    recentPosts: (recentPosts ?? []) as PostSnapshot[],
    latestRecommendation: ((recommendations ?? [])[0] as Recommendation) ?? null,
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
