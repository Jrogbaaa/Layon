import type { PostSnapshot, ProfileSnapshot } from "@/app/lib/types";

export type FormatStats = {
  count: number;
  avgInteractions: number;
  avgEngagementRate: number;
  avgViews: number | null;
};

export function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return `${Math.round(n).toLocaleString()}`;
}

export function engagementRate(posts: PostSnapshot[], followers: number): number {
  if (posts.length === 0 || followers <= 0) return 0;
  const total = posts.reduce((sum, post) => sum + post.likes + post.comments, 0);
  return Math.round((total / posts.length / followers) * 1000) / 10;
}

export function postEngagementRate(post: PostSnapshot, followers: number): number {
  if (followers <= 0) return 0;
  return Math.round(((post.likes + post.comments) / followers) * 1000) / 10;
}

export function formatPerformance(posts: PostSnapshot[], followers: number): Record<string, FormatStats> {
  const groups = new Map<string, PostSnapshot[]>();
  for (const post of posts) {
    const list = groups.get(post.post_type) ?? [];
    list.push(post);
    groups.set(post.post_type, list);
  }

  const result: Record<string, FormatStats> = {};
  for (const [type, typePosts] of groups) {
    const interactions = typePosts.map((p) => p.likes + p.comments);
    const avgInteractions = interactions.reduce((a, b) => a + b, 0) / typePosts.length;
    const avgEngagementRate =
      followers > 0
        ? typePosts.reduce((sum, p) => sum + postEngagementRate(p, followers), 0) / typePosts.length
        : 0;

    const viewPosts = typePosts.filter((p) => p.views != null);
    const avgViews =
      viewPosts.length > 0
        ? viewPosts.reduce((sum, p) => sum + (p.views ?? 0), 0) / viewPosts.length
        : null;

    result[type] = {
      count: typePosts.length,
      avgInteractions: Math.round(avgInteractions),
      avgEngagementRate: Math.round(avgEngagementRate * 10) / 10,
      avgViews: avgViews != null ? Math.round(avgViews) : null,
    };
  }
  return result;
}

export function postingCadence(posts: PostSnapshot[]): number | null {
  if (posts.length < 2) return null;
  const times = posts.map((p) => new Date(p.posted_at).getTime()).sort((a, b) => a - b);
  const spanMs = times[times.length - 1] - times[0];
  const spanDays = spanMs / (1000 * 60 * 60 * 24);
  if (spanDays < 1) return posts.length;
  return Math.round((posts.length / spanDays) * 7 * 10) / 10;
}

export function dailyHistory(history: ProfileSnapshot[]): ProfileSnapshot[] {
  const byDay = new Map<string, ProfileSnapshot>();
  for (const snapshot of history) {
    const day = snapshot.captured_at.slice(0, 10);
    byDay.set(day, snapshot);
  }
  return Array.from(byDay.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, snapshot]) => snapshot);
}

export function followerChange(history: ProfileSnapshot[]): { delta: number; label: string } {
  const daily = dailyHistory(history);
  if (daily.length === 0) return { delta: 0, label: "since last capture" };
  if (daily.length === 1) return { delta: 0, label: "first capture" };
  const latest = daily[daily.length - 1];
  const previous = daily[daily.length - 2];
  return { delta: latest.followers - previous.followers, label: "since yesterday" };
}

export function latestFollowerDelta(history: ProfileSnapshot[]): number {
  return followerChange(history).delta;
}
