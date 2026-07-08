import { getLatestTrends } from "@/app/lib/data";

export const dynamic = "force-dynamic";

export default async function TrendsPage() {
  const trends = await getLatestTrends(10);

  return (
    <div>
      <h1 className="font-display mb-1 text-2xl font-bold tracking-tight">Trends</h1>
      <p className="mb-8 text-muted">Latest Instagram trend report scrapes, used to ground recommendations.</p>

      {trends.length === 0 ? (
        <p className="text-muted">No trend data yet — check back after the next daily update.</p>
      ) : (
        <div className="space-y-4">
          {trends.map((trend, i) => (
            <div key={`${trend.source_url}-${i}`} className="card p-6">
              <p className="text-xs text-muted">
                {new Date(trend.captured_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
              </p>
              <h2 className="mt-1 text-lg font-semibold">{trend.title || trend.source_url}</h2>
              <a
                href={trend.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-accent-strong hover:underline"
              >
                {trend.source_url}
              </a>
              <p className="mt-3 line-clamp-4 text-sm text-ink">{trend.content_text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
