import Link from "next/link";
import { notFound } from "next/navigation";
import { getInfluencerDashboard } from "@/app/lib/data";
import {
  engagementRate,
  followerChange,
  formatCount,
  formatPerformance,
  postingCadence,
} from "@/app/lib/metrics";
import { FollowerChart } from "@/app/components/FollowerChart";
import { Avatar } from "@/app/components/Avatar";
import { HighlightContent } from "@/app/components/HighlightContent";
import { RecentPostsTable } from "@/app/components/RecentPostsTable";
import { RecommendationContent } from "@/app/components/RecommendationContent";
import { LanguageToggle } from "@/app/components/LanguageToggle";

export default async function InfluencerPage({ params }: { params: Promise<{ handle: string }> }) {
  const { handle } = await params;
  const dashboard = await getInfluencerDashboard(handle);

  if (!dashboard) {
    notFound();
  }

  const { influencer, profileHistory, recentPosts, latestRecommendation, highlights } = dashboard;
  const latestSnapshot = profileHistory[profileHistory.length - 1] ?? null;
  const followers = latestSnapshot?.followers ?? 0;
  const rate = followers > 0 ? engagementRate(recentPosts, followers) : 0;
  const change = followerChange(profileHistory);
  const cadence = postingCadence(recentPosts);
  const formatBreakdown = formatPerformance(recentPosts, followers);

  // Repeated daily captures can surface the same post/reel spike more than once;
  // keep only the most recent mention per referenced post. If two distinct
  // highlights reference the same shortcode on the same captured_at, the
  // query has no tie-break, so which one wins is non-deterministic — rare
  // enough not to warrant a secondary sort key.
  const seenShortcodes = new Set<string>();
  const dedupedHighlights = highlights.filter((highlight) => {
    const shortcode = highlight.content.match(/(?:post|reel)\s+([A-Za-z0-9_-]+)/)?.[1];
    if (!shortcode) return true;
    if (seenShortcodes.has(shortcode)) return false;
    seenShortcodes.add(shortcode);
    return true;
  });

  return (
    <div>
      <Link href="/" className="mb-4 inline-block text-sm text-muted hover:text-ink">
        ← Roster
      </Link>

      <div className="mb-8 flex items-center gap-4">
        <Avatar handle={influencer.handle} avatarUrl={influencer.avatar_url} size="lg" />
        <h1 className="font-display text-2xl font-bold tracking-tight">
          @{influencer.handle}
          {influencer.display_name ? (
            <span className="ml-2 text-lg font-normal text-muted">{influencer.display_name}</span>
          ) : null}
        </h1>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Followers" value={followers > 0 ? followers.toLocaleString() : "—"} />
        <Stat
          label={`Change (${change.label})`}
          value={`${change.delta > 0 ? "+" : ""}${change.delta.toLocaleString()}`}
          tone={change.delta > 0 ? "positive" : change.delta < 0 ? "negative" : "neutral"}
        />
        <Stat label="Engagement rate" value={`${rate}%`} subtext="avg per post, % of followers" />
        <Stat
          label="Posting cadence"
          value={cadence != null ? `${cadence}/wk` : "—"}
          subtext={cadence != null ? `based on ${recentPosts.length} tracked posts` : "need 2+ posts"}
        />
      </div>

      <section className="card mb-8 p-6">
        <h2 className="mb-4 text-lg font-semibold">Follower growth</h2>
        <FollowerChart history={profileHistory} />
      </section>

      <section className="card mb-8 p-6">
        <h2 className="mb-4 text-lg font-semibold">Performance by format</h2>
        {Object.keys(formatBreakdown).length === 0 ? (
          <p className="text-sm text-muted">No post data yet.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(formatBreakdown).map(([type, stats]) => (
              <div key={type} className="rounded-xl border border-border bg-canvas p-4">
                <p className="text-sm capitalize text-muted">{type}</p>
                <p className="font-display mt-1 text-2xl font-bold">{stats.avgEngagementRate}%</p>
                <p className="text-xs text-muted">avg engagement rate</p>
                <p className="mt-3 text-sm text-ink">
                  {formatCount(stats.avgInteractions)} avg interactions
                </p>
                {stats.avgViews != null ? (
                  <p className="text-sm text-muted">{formatCount(stats.avgViews)} avg views</p>
                ) : null}
                <p className="mt-2 text-xs text-muted">based on {stats.count} posts</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card mb-8 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Creative recommendations</h2>
          {latestRecommendation ? <LanguageToggle /> : null}
        </div>
        {latestRecommendation ? (
          <>
            <p className="mb-3 text-xs text-muted">
              Updated{" "}
              {new Date(latestRecommendation.generated_at).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })}
            </p>
            <RecommendationContent content={latestRecommendation.content} />
          </>
        ) : (
          <p className="text-sm text-muted">
            No recommendation generated yet — check back after the next daily update.
          </p>
        )}
      </section>

      <section className="card mb-8 p-6">
        <h2 className="mb-4 text-lg font-semibold">Recent posts</h2>
        <RecentPostsTable posts={recentPosts} followers={followers} />
      </section>

      <section className="card p-6">
        <h2 className="mb-4 text-lg font-semibold">Highlights</h2>
        {dedupedHighlights.length === 0 ? (
          <p className="text-sm text-muted">
            No standout highlights yet — growth-over-time insights need a few days of daily captures.
          </p>
        ) : (
          <ul className="space-y-3">
            {dedupedHighlights.map((highlight) => (
              <li
                key={`${highlight.captured_at}-${highlight.content.slice(0, 24)}`}
                className="rounded-xl border border-border bg-canvas px-4 py-3 text-sm leading-relaxed text-ink"
              >
                <HighlightContent content={highlight.content} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  subtext,
  tone = "neutral",
}: {
  label: string;
  value: string;
  subtext?: string;
  tone?: "positive" | "negative" | "neutral";
}) {
  const toneClass =
    tone === "positive" ? "text-positive" : tone === "negative" ? "text-negative" : "text-ink";

  return (
    <div className="card p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted">{label}</p>
      <p className={`font-display mt-1 text-xl font-bold ${toneClass}`}>{value}</p>
      {subtext ? <p className="mt-1 text-xs text-muted">{subtext}</p> : null}
    </div>
  );
}
