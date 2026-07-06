import { notFound } from "next/navigation";
import { getInfluencerDashboard } from "@/app/lib/data";
import { engagementRate, formatPerformance, latestFollowerDelta } from "@/app/lib/metrics";
import { FollowerChart } from "@/app/components/FollowerChart";

export default async function InfluencerPage({ params }: { params: Promise<{ handle: string }> }) {
  const { handle } = await params;
  const dashboard = await getInfluencerDashboard(handle);

  if (!dashboard) {
    notFound();
  }

  const { influencer, profileHistory, recentPosts, latestRecommendation } = dashboard;
  const latestSnapshot = profileHistory[profileHistory.length - 1] ?? null;
  const rate = latestSnapshot ? engagementRate(recentPosts, latestSnapshot.followers) : 0;
  const delta = latestFollowerDelta(profileHistory);
  const formatBreakdown = formatPerformance(recentPosts);

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold">@{influencer.handle}</h1>
      <p className="mb-8 text-neutral-400">{latestSnapshot?.bio || "No bio available."}</p>

      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Followers" value={latestSnapshot ? latestSnapshot.followers.toLocaleString() : "—"} />
        <Stat
          label="Change"
          value={`${delta > 0 ? "+" : ""}${delta}`}
          tone={delta > 0 ? "positive" : delta < 0 ? "negative" : "neutral"}
        />
        <Stat label="Engagement rate" value={`${rate}%`} />
        <Stat label="Posts tracked" value={`${recentPosts.length}`} />
      </div>

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Follower growth</h2>
        <FollowerChart history={profileHistory} />
      </section>

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Performance by format</h2>
        {Object.keys(formatBreakdown).length === 0 ? (
          <p className="text-sm text-neutral-500">No post data yet.</p>
        ) : (
          <div className="flex flex-wrap gap-6">
            {Object.entries(formatBreakdown).map(([type, avg]) => (
              <div key={type}>
                <p className="text-sm text-neutral-400 capitalize">{type}</p>
                <p className="text-xl font-semibold">{avg}</p>
                <p className="text-xs text-neutral-500">avg engagement</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="mb-4 text-lg font-medium">Creative recommendations</h2>
        {latestRecommendation ? (
          <>
            <p className="mb-3 text-xs text-neutral-500">
              Generated {new Date(latestRecommendation.generated_at).toLocaleString()} · {latestRecommendation.model}
            </p>
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-200">
              {latestRecommendation.content}
            </div>
          </>
        ) : (
          <p className="text-sm text-neutral-500">
            No recommendation generated yet — needs at least one daily scrape run.
          </p>
        )}
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "positive" | "negative" | "neutral";
}) {
  const toneClass =
    tone === "positive" ? "text-emerald-400" : tone === "negative" ? "text-red-400" : "text-neutral-50";

  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
      <p className="text-xs text-neutral-400">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}
