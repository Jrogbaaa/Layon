import { getLatestTrendHeadlines, getLatestTrends } from "@/app/lib/data";
import { parseTrendHeadlines } from "@/app/lib/trends";
import { TrendHeadlinesList } from "@/app/components/TrendHeadlinesList";
import { LanguageToggle } from "@/app/components/LanguageToggle";

export const dynamic = "force-dynamic";

export default async function TrendsPage() {
  const headlinesRow = await getLatestTrendHeadlines();
  const headlines = headlinesRow ? parseTrendHeadlines(headlinesRow.content) : null;
  const trends = headlines ? [] : await getLatestTrends(4);

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <h1 className="display-hero text-6xl text-ink sm:text-7xl">The Wire</h1>
          <p className="mt-3 max-w-md text-muted">
            {headlines
              ? "What moved the Spanish social landscape today, distilled to headlines."
              : "Latest Instagram trend report scrapes, used to ground recommendations."}
          </p>
        </div>
        {headlinesRow && headlines ? (
          <div className="flex items-center gap-4 pb-1">
            <span className="font-mono text-xs text-faint">
              {new Date(headlinesRow.generated_at)
                .toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })
                .toUpperCase()}
            </span>
            <LanguageToggle />
          </div>
        ) : null}
      </div>

      <hr className="rule-gold mt-8 mb-12" />

      {headlines ? (
        <TrendHeadlinesList headlines={headlines} />
      ) : trends.length === 0 ? (
        <p className="text-muted">No trend data yet — check back after the next daily update.</p>
      ) : (
        <div className="space-y-10">
          {trends.map((trend, i) => (
            <article key={`${trend.source_url}-${i}`} className="max-w-3xl">
              <p className="font-mono text-xs text-faint">
                {new Date(trend.captured_at)
                  .toLocaleDateString("en-US", { month: "short", day: "numeric" })
                  .toUpperCase()}
              </p>
              <h2 className="font-display mt-2 text-2xl text-ink">{trend.title || trend.source_url}</h2>
              <p className="mt-3 line-clamp-4 max-w-prose text-sm leading-relaxed text-muted">
                {trend.content_text}
              </p>
              <a
                href={trend.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-xs text-accent hover:text-accent-bright"
              >
                Source →
              </a>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
