import Link from "next/link";
import { getRoster } from "@/app/lib/data";
import { formatCount } from "@/app/lib/metrics";
import { HighlightContent } from "@/app/components/HighlightContent";
import { Avatar } from "@/app/components/Avatar";

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
      <h1 className="font-display mb-1 text-2xl font-bold tracking-tight">Roster</h1>
      <p className="mb-8 text-muted">Instagram performance across the talent roster.</p>

      {attentionItems.length > 0 ? (
        <section className="card mb-8 border-negative/20 p-6">
          <h2 className="mb-3 text-sm font-semibold text-negative">Needs attention</h2>
          <ul className="space-y-2">
            {attentionItems.map(({ influencer, highlight }) => (
              <li key={`${influencer.id}-${highlight.captured_at}`} className="text-sm text-ink">
                <Link href={`/influencer/${influencer.handle}`} className="font-semibold hover:underline">
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
        <p className="text-muted">
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
                className="card p-6 transition hover:-translate-y-0.5 hover:shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar handle={influencer.handle} avatarUrl={influencer.avatar_url} size="sm" />
                    <p className="text-lg font-semibold">@{influencer.handle}</p>
                  </div>
                  {hasWarning ? (
                    <span className="rounded-full bg-negative-soft px-2 py-0.5 text-xs font-medium text-negative">
                      attention
                    </span>
                  ) : hasGood ? (
                    <span className="rounded-full bg-positive-soft px-2 py-0.5 text-xs font-medium text-positive">
                      breakout
                    </span>
                  ) : null}
                </div>
                {latestSnapshot ? (
                  <>
                    <p className="font-display mt-3 text-3xl font-extrabold tracking-tight">
                      {formatCount(latestSnapshot.followers)}
                    </p>
                    <p className="text-sm text-muted">followers</p>
                    <p
                      className={`mt-2 text-sm font-medium ${
                        followerDelta > 0
                          ? "text-positive"
                          : followerDelta < 0
                            ? "text-negative"
                            : "text-muted"
                      }`}
                    >
                      {followerDelta === 0
                        ? "No change since last scrape"
                        : `${followerDelta > 0 ? "+" : ""}${followerDelta.toLocaleString()} since last scrape`}
                    </p>
                  </>
                ) : (
                  <p className="mt-3 text-sm text-muted">No scrape data yet</p>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
