import { getLatestTrendHeadlines, getLatestTrends } from "@/app/lib/data";
import { TrendHeadlinesList } from "@/app/components/TrendHeadlinesList";
import { LanguageToggle } from "@/app/components/LanguageToggle";

export const dynamic = "force-dynamic";

export default async function TrendsPage() {
  const headlinesRow = await getLatestTrendHeadlines();
  const trends = headlinesRow ? [] : await getLatestTrends(4);

  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold tracking-tight">Trends</h1>
        {headlinesRow ? <LanguageToggle /> : null}
      </div>
      <p className="mb-8 text-muted">
        {headlinesRow
          ? `Distilled from today's Spanish social trend reports · ${new Date(
              headlinesRow.generated_at
            ).toLocaleDateString(undefined, { month: "short", day: "numeric" })}`
          : "Latest Instagram trend report scrapes, used to ground recommendations."}
      </p>

      {headlinesRow ? (
        <TrendHeadlinesList content={headlinesRow.content} />
      ) : trends.length === 0 ? (
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
