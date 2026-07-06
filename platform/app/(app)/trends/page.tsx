import { getLatestTrends } from "@/app/lib/data";

export const dynamic = "force-dynamic";

export default async function TrendsPage() {
  const trends = await getLatestTrends(10);

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">Trends</h1>
      <p className="mb-8 text-neutral-400">Latest Instagram trend report scrapes, used to ground recommendations.</p>

      {trends.length === 0 ? (
        <p className="text-neutral-500">No trend data yet — run the scraper to populate this page.</p>
      ) : (
        <div className="space-y-4">
          {trends.map((trend, i) => (
            <div key={`${trend.source_url}-${i}`} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
              <p className="text-xs text-neutral-500">{new Date(trend.captured_at).toLocaleString()}</p>
              <h2 className="mt-1 text-lg font-medium">{trend.title || trend.source_url}</h2>
              <a
                href={trend.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-amber-500 hover:underline"
              >
                {trend.source_url}
              </a>
              <p className="mt-3 line-clamp-4 text-sm text-neutral-300">{trend.content_text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
