import type { PostSnapshot, ProfileSnapshot } from "@/app/lib/types";

export function engagementRate(posts: PostSnapshot[], followers: number): number {
  if (posts.length === 0 || followers <= 0) return 0;
  const total = posts.reduce((sum, post) => sum + post.likes + post.comments, 0);
  return Math.round((total / posts.length / followers) * 1000) / 10;
}

export function formatPerformance(posts: PostSnapshot[]): Record<string, number> {
  const totals = new Map<string, number[]>();
  for (const post of posts) {
    const values = totals.get(post.post_type) ?? [];
    values.push(post.likes + post.comments);
    totals.set(post.post_type, values);
  }
  const result: Record<string, number> = {};
  for (const [type, values] of totals) {
    result[type] = Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 10) / 10;
  }
  return result;
}

export function latestFollowerDelta(history: ProfileSnapshot[]): number {
  if (history.length < 2) return 0;
  return history[history.length - 1].followers - history[0].followers;
}
