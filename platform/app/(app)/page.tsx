import Link from "next/link";
import { getRoster } from "@/app/lib/data";

export const dynamic = "force-dynamic";

function formatFollowers(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return `${n}`;
}

export default async function RosterPage() {
  const roster = await getRoster();

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">Roster</h1>
      <p className="mb-8 text-neutral-400">Instagram performance across the talent roster.</p>

      {roster.length === 0 ? (
        <p className="text-neutral-500">
          No influencer data yet. Run the scraper (see <code>scraper/README.md</code>) to populate this page.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {roster.map(({ influencer, latestSnapshot, followerDelta }) => (
            <Link
              key={influencer.id}
              href={`/influencer/${influencer.handle}`}
              className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6 transition hover:border-amber-500/60"
            >
              <p className="text-lg font-medium">@{influencer.handle}</p>
              {latestSnapshot ? (
                <>
                  <p className="mt-3 text-3xl font-semibold">{formatFollowers(latestSnapshot.followers)}</p>
                  <p className="text-sm text-neutral-400">followers</p>
                  <p
                    className={`mt-2 text-sm ${
                      followerDelta > 0 ? "text-emerald-400" : followerDelta < 0 ? "text-red-400" : "text-neutral-500"
                    }`}
                  >
                    {followerDelta > 0 ? "+" : ""}
                    {followerDelta} since last scrape
                  </p>
                </>
              ) : (
                <p className="mt-3 text-sm text-neutral-500">No scrape data yet</p>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
