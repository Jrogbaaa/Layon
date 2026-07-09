import Link from "next/link";
import { ViewTransition } from "react";
import { getLatestBriefing, getRoster } from "@/app/lib/data";
import { HighlightContent } from "@/app/components/HighlightContent";
import { Avatar } from "@/app/components/Avatar";
import { RosterBriefing } from "@/app/components/RosterBriefing";
import { CountUp } from "@/app/components/CountUp";
import { Sparkline } from "@/app/components/Sparkline";
import { Reveal } from "@/app/components/Reveal";

export const dynamic = "force-dynamic";

export default async function RosterPage() {
  const [roster, briefing] = await Promise.all([getRoster(), getLatestBriefing()]);

  const ranked = [...roster].sort(
    (a, b) => (b.latestSnapshot?.followers ?? 0) - (a.latestSnapshot?.followers ?? 0),
  );

  const totalFollowers = roster.reduce((sum, r) => sum + (r.latestSnapshot?.followers ?? 0), 0);
  const netDelta = roster.reduce((sum, r) => sum + r.followerDelta, 0);
  const risers = roster.filter((r) => r.followerDelta > 0).length;
  const fallers = roster.filter((r) => r.followerDelta < 0).length;

  const attentionItems = roster.flatMap(({ influencer, recentHighlights }) =>
    recentHighlights
      .filter((h) => h.metric?.severity === "warning")
      .map((h) => ({ influencer, highlight: h })),
  );

  return (
    <div>
      {/* Masthead */}
      <div className="flex flex-wrap items-end justify-between gap-x-12 gap-y-6">
        <div>
          <h1 className="display-hero text-6xl text-ink sm:text-7xl">The Roster</h1>
          <p className="mt-3 max-w-md text-muted">
            Instagram performance across the talent roster, watched nightly.
          </p>
        </div>

        <dl className="font-mono flex gap-10 pb-1 text-sm">
          <div>
            <dt className="text-xs text-faint">Audience</dt>
            <dd className="mt-1 text-2xl text-ink">
              <CountUp value={totalFollowers} format="compact" />
            </dd>
          </div>
          <div>
            <dt className="text-xs text-faint">Overnight</dt>
            <dd
              className={`tnum mt-1 text-2xl ${
                netDelta > 0 ? "text-positive" : netDelta < 0 ? "text-negative" : "text-ink"
              }`}
            >
              {netDelta > 0 ? "+" : ""}
              {netDelta.toLocaleString("en-US")}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-faint">Moving</dt>
            <dd className="mt-1 text-2xl text-ink">
              <span className="text-positive">{risers}▲</span>{" "}
              <span className="text-negative">{fallers}▼</span>
            </dd>
          </div>
        </dl>
      </div>

      <hr className="rule-gold mt-8 mb-10" />

      <div
        className={`grid gap-x-16 gap-y-12 ${
          briefing && attentionItems.length > 0 ? "lg:grid-cols-[7fr_5fr]" : ""
        }`}
      >
        {briefing ? (
          <Reveal>
            <RosterBriefing content={briefing.content} generatedAt={briefing.generated_at} />
          </Reveal>
        ) : null}

        {attentionItems.length > 0 ? (
          <Reveal as="section" delay={80} className="mb-12">
            <h2 className="font-mono mb-5 text-xs tracking-widest text-negative">WATCHLIST</h2>
            <ul className="space-y-4">
              {attentionItems.map(({ influencer, highlight }) => (
                <li
                  key={`${influencer.id}-${highlight.captured_at}`}
                  className="flex gap-3 text-sm leading-relaxed text-ink"
                >
                  <span aria-hidden className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-negative" />
                  <p className="max-w-[75ch]">
                    <Link
                      href={`/influencer/${influencer.handle}`}
                      className="font-semibold text-ink hover:text-accent"
                    >
                      @{influencer.handle}
                    </Link>
                    {" — "}
                    <HighlightContent content={highlight.content} />
                  </p>
                </li>
              ))}
            </ul>
          </Reveal>
        ) : null}
      </div>

      {/* The index */}
      {roster.length === 0 ? (
        <p className="text-muted">
          No influencer data yet — it will appear after the next daily update.
        </p>
      ) : (
        <section>
          <h2 className="font-mono mb-4 text-xs tracking-widest text-faint">
            TONIGHT&apos;S INDEX · BY AUDIENCE
          </h2>
          <ol className="panel divide-y divide-border-faint overflow-hidden">
            {ranked.map(({ influencer, latestSnapshot, followerDelta, recentHighlights, history }, i) => {
              const hasWarning = recentHighlights.some((h) => h.metric?.severity === "warning");
              const hasGood = recentHighlights.some((h) => h.metric?.severity === "good");
              const followers = latestSnapshot?.followers ?? 0;
              // Deltas below ~0.01% of the audience are noise — keep alarm colors meaningful.
              const meaningful = Math.abs(followerDelta) >= Math.max(5, followers * 0.0001);
              const sparkValues = history.map((h) => h.followers);
              const sparkTone =
                meaningful && followerDelta > 0
                  ? ("positive" as const)
                  : meaningful && followerDelta < 0
                    ? ("negative" as const)
                    : ("neutral" as const);

              return (
                <Reveal as="li" key={influencer.id} delay={Math.min(i * 40, 240)}>
                  <Link
                    href={`/influencer/${influencer.handle}`}
                    className="group grid grid-cols-[2rem_auto_1fr] items-center gap-x-4 px-5 py-4 transition-colors hover:bg-surface-2 sm:grid-cols-[2.5rem_3rem_minmax(0,1fr)_8rem_9rem_8.5rem] sm:px-7"
                  >
                    <span className="font-mono text-sm text-faint" aria-hidden>
                      {String(i + 1).padStart(2, "0")}
                    </span>

                    <ViewTransition name={`avatar-${influencer.handle}`}>
                      <Avatar handle={influencer.handle} avatarUrl={influencer.avatar_url} size="sm" />
                    </ViewTransition>

                    <span className="min-w-0">
                      <span className="font-display block truncate text-xl text-ink transition-colors group-hover:text-accent">
                        {influencer.display_name ?? `@${influencer.handle}`}
                      </span>
                      <span className="mt-0.5 flex items-center gap-2 text-xs text-faint">
                        {influencer.display_name ? `@${influencer.handle}` : "Instagram"}
                        {hasWarning ? (
                          <span className="inline-flex items-center gap-1 text-negative">
                            <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-negative" />
                            attention
                          </span>
                        ) : hasGood ? (
                          <span className="inline-flex items-center gap-1 text-positive">
                            <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-positive" />
                            breakout
                          </span>
                        ) : null}
                      </span>
                    </span>

                    <span className="font-mono tnum col-start-3 row-start-2 text-right text-sm text-ink sm:col-start-4 sm:row-start-1 sm:text-base">
                      {followers > 0 ? followers.toLocaleString("en-US") : "—"}
                    </span>

                    <span
                      className={`font-mono tnum hidden text-right text-sm sm:block ${
                        meaningful && followerDelta > 0
                          ? "text-positive"
                          : meaningful && followerDelta < 0
                            ? "text-negative"
                            : "text-faint"
                      }`}
                    >
                      {latestSnapshot
                        ? followerDelta === 0
                          ? "±0"
                          : `${followerDelta > 0 ? "+" : ""}${followerDelta.toLocaleString("en-US")}`
                        : ""}
                    </span>

                    <span className="hidden justify-end sm:flex">
                      <Sparkline values={sparkValues} tone={sparkTone} />
                    </span>
                  </Link>
                </Reveal>
              );
            })}
          </ol>
          <p className="font-mono mt-3 text-right text-xs text-faint">
            overnight change · last {Math.max(...ranked.map((r) => r.history.length), 0)} captures
          </p>
        </section>
      )}
    </div>
  );
}
