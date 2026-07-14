import Link from "next/link";
import { getLatestBriefing, getRoster } from "@/app/lib/data";
import { HighlightContent } from "@/app/components/HighlightContent";
import { RosterBriefing } from "@/app/components/RosterBriefing";
import { CountUp } from "@/app/components/CountUp";
import { Reveal } from "@/app/components/Reveal";
import { RosterIndexList } from "@/app/components/RosterIndexList";

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
        <div>
          <RosterIndexList initialRoster={roster} />
          <p className="font-mono mt-5 text-right text-xs text-faint">
            overnight change · last {Math.max(...ranked.map((r) => r.history.length), 0)} captures
          </p>
        </div>
      )}
    </div>
  );
}
