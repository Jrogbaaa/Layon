import { notFound } from "next/navigation";
import { LanguageProvider } from "@/app/components/LanguageProvider";
import { RecommendationContent } from "@/app/components/RecommendationContent";
import { getSupabaseClient } from "@/app/lib/supabase";
import type { Recommendation, RecommendationAction } from "@/app/lib/types";

function structured(content: string): boolean {
  try {
    return Array.isArray((JSON.parse(content) as { bullets?: unknown }).bullets);
  } catch {
    return false;
  }
}

export default async function RecommendationActionFixture({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string; recommendation?: string }>;
}) {
  if (process.env.NODE_ENV === "production") notFound();
  const { mode, recommendation: requested } = await searchParams;
  const client = getSupabaseClient();
  const requestedId = Number(requested);
  let recommendation: Recommendation & { influencer_id: number };

  if (Number.isInteger(requestedId) && requestedId > 0) {
    const { data } = await client
      .from("recommendations")
      .select("id, influencer_id, generated_at, model, content")
      .eq("id", requestedId)
      .maybeSingle();
    if (!data || !structured(data.content)) notFound();
    recommendation = data as Recommendation & { influencer_id: number };
  } else {
    const { data: rows } = await client
      .from("recommendations")
      .select("id, influencer_id, generated_at, model, content")
      .order("generated_at", { ascending: false })
      .limit(50);
    const structuredRows = (rows ?? []).filter((row) => structured(row.content));
    const ids = structuredRows.map((row) => row.id);
    const { data: actionRows } = ids.length
      ? await client.from("recommendation_actions").select("recommendation_id, bullet_index").in("recommendation_id", ids)
      : { data: [] };
    const occupied = new Set(
      (actionRows ?? []).filter((row) => row.bullet_index === 0).map((row) => row.recommendation_id),
    );
    const available = structuredRows.find((row) => !occupied.has(row.id));
    if (!available) notFound();
    recommendation = available as Recommendation & { influencer_id: number };
  }

  const { data: influencer } = await client
    .from("influencers")
    .select("handle")
    .eq("id", recommendation.influencer_id)
    .maybeSingle();
  if (!influencer) notFound();

  const { data: actionRows } = await client
    .from("recommendation_actions")
    .select(
      "id, recommendation_id, influencer_id, bullet_index, decision, shared_note, revisit_on, experiment_status, linked_shortcode, published_at, review_at, baseline, outcome, evaluated_at, acknowledged_at, created_at, updated_at",
    )
    .eq("recommendation_id", recommendation.id);

  return (
    <LanguageProvider>
      <main className="mx-auto max-w-3xl p-8">
        <h1 className="font-display mb-6 text-3xl text-ink">Recommendation action fixture</h1>
        <RecommendationContent
          content={recommendation.content}
          recommendationId={recommendation.id}
          influencerId={mode === "ownership" ? recommendation.influencer_id + 999_999 : recommendation.influencer_id}
          handle={influencer.handle}
          actions={(actionRows ?? []) as RecommendationAction[]}
        />
      </main>
    </LanguageProvider>
  );
}
