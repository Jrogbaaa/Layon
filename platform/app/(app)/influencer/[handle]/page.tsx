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
import { HighlightContent } from "@/app/components/HighlightContent";
import { RecentPostsTable } from "@/app/components/RecentPostsTable";
import { RecommendationContent } from "@/app/components/RecommendationContent";

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

  return (
    <div>
      <Link href="/" className="mb-4 inline-block text-sm text-neutral-400 hover:text-neutral-200">
        ← Roster
      </Link>

      <h1 className="mb-8 text-2xl font-semibold">
        @{influencer.handle}
        {influencer.display_name ? (
          <span className="ml-2 text-lg font-normal text-neutral-400">{influencer.display_name}</span>
        ) : null}
      </h1>

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

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Follower growth</h2>
        <FollowerChart history={profileHistory} />
      </section>

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Performance by format</h2>
        {Object.keys(formatBreakdown).length === 0 ? (
          <p className="text-sm text-neutral-500">No post data yet.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(formatBreakdown).map(([type, stats]) => (
              <div key={type} className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                <p className="text-sm capitalize text-neutral-400">{type}</p>
                <p className="mt-1 text-2xl font-semibold">{stats.avgEngagementRate}%</p>
                <p className="text-xs text-neutral-500">avg engagement rate</p>
                <p className="mt-3 text-sm text-neutral-300">
                  {formatCount(stats.avgInteractions)} avg interactions
                </p>
                {stats.avgViews != null ? (
                  <p className="text-sm text-neutral-400">{formatCount(stats.avgViews)} avg views</p>
                ) : null}
                <p className="mt-2 text-xs text-neutral-500">based on {stats.count} posts</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Recent posts</h2>
        <RecentPostsTable posts={recentPosts} followers={followers} />
      </section>

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Highlights</h2>
        {highlights.length === 0 ? (
          <p className="text-sm text-neutral-500">
            No standout highlights yet — growth-over-time insights need a few days of daily captures.
          </p>
        ) : (
          <ul className="space-y-3">
            {highlights.map((highlight) => (
              <li
                key={`${highlight.captured_at}-${highlight.content.slice(0, 24)}`}
                className="rounded-xl border border-neutral-800 bg-neutral-950 px-4 py-3 text-sm leading-relaxed text-neutral-200"
              >
                <HighlightContent content={highlight.content} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Creative recommendations</h2>
        {latestRecommendation ? (
          <>
            <p className="mb-3 text-xs text-neutral-500">
              Generated {new Date(latestRecommendation.generated_at).toLocaleString()} ·{" "}
              {latestRecommendation.model}
            </p>
            <RecommendationContent content={latestRecommendation.content} />
          </>
        ) : (
          <p className="text-sm text-neutral-500">
            No recommendation generated yet — needs at least one daily scrape run.
          </p>
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
    tone === "positive" ? "text-emerald-400" : tone === "negative" ? "text-red-400" : "text-neutral-50";

  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
      <p className="text-xs text-neutral-400">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${toneClass}`}>{value}</p>
      {subtext ? <p className="mt-1 text-xs text-neutral-500">{subtext}</p> : null}
    </div>
  );
}
