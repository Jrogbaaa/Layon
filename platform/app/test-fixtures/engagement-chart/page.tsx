import { notFound } from "next/navigation";
import { EngagementChart } from "@/app/components/EngagementChart";
import type { PostSnapshot } from "@/app/lib/types";

function post(index: number, postedAt: string): PostSnapshot {
  return {
    shortcode: `fixture-${index}`,
    post_type: index % 2 === 0 ? "reel" : "photo",
    likes: 1_000 + index * 137,
    comments: 40 + index * 11,
    views: null,
    caption: `Fixture post ${index + 1}`,
    posted_at: postedAt,
    is_ad: index % 3 === 0,
  };
}

const fixtures: Record<string, PostSnapshot[]> = {
  dense: Array.from({ length: 30 }, (_, index) =>
    post(index, `2026-06-${String(index + 1).padStart(2, "0")}T12:00:00+02:00`),
  ),
  mixed: [
    post(0, "2026-02-28T23:30:00Z"),
    post(1, "2026-03-01T00:30:00+01:00"),
    post(2, "2026-02-30T12:00:00Z"),
    post(3, "2026-03-02T12:00:00"),
    post(4, "2026-03-03T12:00:00+14:30"),
  ],
  "all-invalid": [
    post(0, "2026-02-30T12:00:00Z"),
    post(1, "2026-03-02T12:00:00"),
  ],
  one: [post(0, "2026-03-01T10:00:00+01:00")],
  none: [],
};

export default async function EngagementChartFixturePage({
  searchParams,
}: {
  searchParams: Promise<{ scenario?: string | string[] }>;
}) {
  if (process.env.NODE_ENV !== "development") notFound();

  const requestedScenario = (await searchParams).scenario;
  const scenario = typeof requestedScenario === "string" ? requestedScenario : "dense";
  const posts = fixtures[scenario] ?? fixtures.dense;

  return (
    <main className="grain min-h-screen bg-canvas px-6 py-10 text-ink">
      <section className="mx-auto w-full max-w-6xl">
        <h1 className="font-mono mb-6 text-xs tracking-widest text-faint">
          ENGAGEMENT CHART TEST FIXTURE · {scenario.toUpperCase()}
        </h1>
        <EngagementChart posts={posts} followers={100_000} />
      </section>
    </main>
  );
}
