import Link from "next/link";
import { getRoster } from "@/app/lib/data";
import { formatCount } from "@/app/lib/metrics";
import { HighlightContent } from "@/app/components/HighlightContent";

export const dynamic = "force-dynamic";

export default async function RosterPage() {
  const roster = await getRoster();

  const attentionItems = roster.flatMap(({ influencer, recentHighlights }) =>
    recentHighlights
      .filter((h) => h.metric?.severity === "warning")
      .map((h) => ({ influencer, highlight: h })),
  );

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">Roster</h1>
      <p className="mb-8 text-neutral-400">Instagram performance across the talent roster.</p>

      {attentionItems.length > 0 ? (
        <section className="mb-8 rounded-2xl border border-amber-500/30 bg-amber-500/5 p-6">
          <h2 className="mb-3 text-sm font-medium text-amber-400">Needs attention</h2>
          <ul className="space-y-2">
            {attentionItems.map(({ influencer, highlight }) => (
              <li key={`${influencer.id}-${highlight.captured_at}`} className="text-sm text-neutral-200">
                <Link href={`/influencer/${influencer.handle}`} className="font-medium hover:underline">
                  @{influencer.handle}
                </Link>
                {" — "}
                <HighlightContent content={highlight.content} />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {roster.length === 0 ? (
        <p className="text-neutral-500">
          No influencer data yet. Run the scraper (see <code>scraper/README.md</code>) to populate this page.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {roster.map(({ influencer, latestSnapshot, followerDelta, recentHighlights }) => {
            const hasWarning = recentHighlights.some((h) => h.metric?.severity === "warning");
            const hasGood = recentHighlights.some((h) => h.metric?.severity === "good");

            return (
              <Link
                key={influencer.id}
                href={`/influencer/${influencer.handle}`}
                className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6 transition hover:border-amber-500/60"
              >
                <div className="flex items-center justify-between">
                  <p className="text-lg font-medium">@{influencer.handle}</p>
                  {hasWarning ? (
                    <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-xs text-amber-400">attention</span>
                  ) : hasGood ? (
                    <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-400">breakout</span>
                  ) : null}
                </div>
                {latestSnapshot ? (
                  <>
                    <p className="mt-3 text-3xl font-semibold">{formatCount(latestSnapshot.followers)}</p>
                    <p className="text-sm text-neutral-400">followers</p>
                    <p
                      className={`mt-2 text-sm ${
                        followerDelta > 0
                          ? "text-emerald-400"
                          : followerDelta < 0
                            ? "text-red-400"
                            : "text-neutral-500"
                      }`}
                    >
                      {followerDelta === 0
                        ? "No change since last scrape"
                        : `${followerDelta > 0 ? "+" : ""}${followerDelta.toLocaleString()} since last scrape`}
                    </p>
                  </>
                ) : (
                  <p className="mt-3 text-sm text-neutral-500">No scrape data yet</p>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
