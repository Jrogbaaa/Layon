import Link from "next/link";
import { ViewTransition } from "react";
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
import { CountUp } from "@/app/components/CountUp";
import { Reveal } from "@/app/components/Reveal";

export default async function InfluencerPage({ params }: { params: Promise<{ handle: string }> }) {
  const { handle } = await params;
  const dashboard = await getInfluencerDashboard(handle);

  if (!dashboard) {
    notFound();
  }

  const { influencer, profileHistory, recentPosts, latestRecommendation, highlights, topPosts } = dashboard;
  const latestSnapshot = profileHistory[profileHistory.length - 1] ?? null;
  const followers = latestSnapshot?.followers ?? 0;
  const rate = followers > 0 ? engagementRate(recentPosts, followers) : 0;
  const change = followerChange(profileHistory);
  const cadence = postingCadence(recentPosts);
  const formatBreakdown = formatPerformance(recentPosts, followers);
  // Deltas below ~0.01% of the audience are noise — keep alarm colors meaningful.
  const changeMeaningful = Math.abs(change.delta) >= Math.max(5, followers * 0.0001);
  const maxFormatRate = Math.max(...Object.values(formatBreakdown).map((s) => s.avgEngagementRate), 0);

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
      <Link
        href="/"
        className="font-mono mb-10 inline-block text-xs tracking-widest text-faint transition-colors hover:text-ink"
      >
        ← THE ROSTER
      </Link>

      {/* Star hero */}
      <div className="flex flex-wrap items-center gap-6">
        <span className="rounded-full bg-gradient-to-br from-accent via-garnet to-accent-deep p-[2px]">
          <span className="block rounded-full bg-canvas p-[3px]">
            <ViewTransition name={`avatar-${influencer.handle}`}>
              <Avatar handle={influencer.handle} avatarUrl={influencer.avatar_url} size="lg" />
            </ViewTransition>
          </span>
        </span>
        <div>
          <h1 className="display-hero text-4xl text-ink [overflow-wrap:anywhere] sm:text-6xl">
            {influencer.display_name ?? `@${influencer.handle}`}
          </h1>
          <p className="font-mono mt-2 text-sm text-faint">
            {influencer.display_name ? `@${influencer.handle} · Instagram` : "Instagram"}
          </p>
        </div>
      </div>

      {/* Stat band */}
      <dl className="mt-10 mb-14 grid grid-cols-2 gap-y-8 border-y border-border-faint py-6 sm:grid-cols-4 sm:divide-x sm:divide-border-faint">
        <div className="sm:pr-8">
          <dt className="text-xs text-faint">Followers</dt>
          <dd className="font-mono mt-2 text-3xl text-ink">
            {followers > 0 ? <CountUp value={followers} /> : "—"}
          </dd>
        </div>
        <div className="sm:px-8">
          <dt className="text-xs text-faint">Change · {change.label}</dt>
          <dd
            className={`font-mono tnum mt-2 text-3xl ${
              changeMeaningful && change.delta > 0
                ? "text-positive"
                : changeMeaningful && change.delta < 0
                  ? "text-negative"
                  : "text-ink"
            }`}
          >
            {change.delta > 0 ? "+" : ""}
            {change.delta.toLocaleString("en-US")}
          </dd>
        </div>
        <div className="sm:px-8">
          <dt className="text-xs text-faint">Engagement rate</dt>
          <dd className="font-mono tnum mt-2 text-3xl text-ink">{rate}%</dd>
          <dd className="mt-1 text-xs text-faint">avg per post, % of followers</dd>
        </div>
        <div className="sm:pl-8">
          <dt className="text-xs text-faint">Cadence</dt>
          <dd className="font-mono tnum mt-2 text-3xl text-ink">
            {cadence != null ? `${cadence}/wk` : "—"}
          </dd>
          <dd className="mt-1 text-xs text-faint">
            {cadence != null ? `across ${recentPosts.length} tracked posts` : "need 2+ posts"}
          </dd>
        </div>
      </dl>

      <Reveal as="section" className="mb-14">
        <h2 className="font-mono mb-6 text-xs tracking-widest text-faint">TRAJECTORY · FOLLOWERS</h2>
        <FollowerChart history={profileHistory} />
      </Reveal>

      <div className="mb-14 grid gap-14 lg:grid-cols-[5fr_7fr]">
        <Reveal as="section">
          <h2 className="font-mono mb-6 text-xs tracking-widest text-faint">BY FORMAT</h2>
          {Object.keys(formatBreakdown).length === 0 ? (
            <p className="text-sm text-muted">No post data yet.</p>
          ) : (
            <ul className="space-y-6">
              {Object.entries(formatBreakdown)
                .sort(([, a], [, b]) => b.avgEngagementRate - a.avgEngagementRate)
                .map(([type, stats]) => (
                  <li key={type}>
                    <div className="flex items-baseline justify-between gap-4">
                      <span className="text-sm font-medium capitalize text-ink">{type}</span>
                      <span className="font-mono tnum text-sm text-ink">
                        {stats.avgEngagementRate}%
                      </span>
                    </div>
                    <div className="mt-2 h-1 overflow-hidden rounded-full bg-surface-2">
                      <div
                        className="h-full rounded-full bg-accent"
                        style={{
                          width: `${maxFormatRate > 0 ? Math.max((stats.avgEngagementRate / maxFormatRate) * 100, 2) : 2}%`,
                        }}
                      />
                    </div>
                    <p className="font-mono mt-2 text-xs text-faint">
                      {formatCount(stats.avgInteractions)} avg interactions
                      {stats.avgViews != null ? ` · ${formatCount(stats.avgViews)} avg views` : ""} ·{" "}
                      {stats.count} posts
                    </p>
                  </li>
                ))}
            </ul>
          )}
        </Reveal>

        <Reveal as="section" delay={80}>
          <h2 className="font-mono mb-6 text-xs tracking-widest text-accent">GREATEST HITS · ALL-TIME</h2>
          {topPosts.length === 0 ? (
            <p className="text-sm text-muted">No post history yet — appears after the next scrape.</p>
          ) : (
            <ol className="divide-y divide-border-faint">
              {topPosts.map((post, i) => (
                <li key={post.shortcode} className="flex items-baseline gap-5 py-4 first:pt-0 last:pb-0">
                  <span className="font-mono text-xs text-accent" aria-hidden>
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-ink">
                      <span className="capitalize">{post.post_type}</span>
                      <span className="text-faint">
                        {" · "}
                        {new Date(post.posted_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </span>
                    </p>
                    <p className="font-mono mt-1 text-xs text-muted">
                      {post.likes.toLocaleString("en-US")} likes · {post.comments.toLocaleString("en-US")}{" "}
                      comments
                      {post.views != null ? ` · ${formatCount(post.views)} views` : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono tnum text-xl text-ink">{formatCount(post.engagement)}</p>
                    <a
                      href={`https://www.instagram.com/p/${post.shortcode}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-accent hover:text-accent-bright"
                    >
                      View →
                    </a>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </Reveal>
      </div>

      <Reveal as="section" className="panel mb-14 p-7 sm:p-9">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="font-mono text-xs tracking-widest text-accent">
            THE BRIEF · CREATIVE RECOMMENDATIONS
          </h2>
          {latestRecommendation ? <LanguageToggle /> : null}
        </div>
        {latestRecommendation ? (
          <>
            <RecommendationContent content={latestRecommendation.content} />
            <p className="font-mono mt-6 text-xs text-faint">
              Updated{" "}
              {new Date(latestRecommendation.generated_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              })}
            </p>
          </>
        ) : (
          <p className="text-sm text-muted">
            No recommendation generated yet — check back after the next daily update.
          </p>
        )}
      </Reveal>

      <Reveal as="section" className="mb-14">
        <h2 className="font-mono mb-6 text-xs tracking-widest text-faint">THE LOG · RECENT POSTS</h2>
        <RecentPostsTable posts={recentPosts} followers={followers} />
      </Reveal>

      <Reveal as="section">
        <h2 className="font-mono mb-6 text-xs tracking-widest text-faint">SIGNALS</h2>
        {dedupedHighlights.length === 0 ? (
          <p className="text-sm text-muted">
            No standout highlights yet — growth-over-time insights need a few days of daily captures.
          </p>
        ) : (
          <ul className="space-y-3">
            {dedupedHighlights.map((highlight) => (
              <li
                key={`${highlight.captured_at}-${highlight.content.slice(0, 24)}`}
                className="flex gap-3 text-sm leading-relaxed text-ink"
              >
                <span aria-hidden className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-accent/60" />
                <p className="max-w-[75ch]">
                  <HighlightContent content={highlight.content} />
                </p>
              </li>
            ))}
          </ul>
        )}
      </Reveal>
    </div>
  );
}
