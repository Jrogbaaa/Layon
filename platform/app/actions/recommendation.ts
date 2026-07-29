"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getSupabaseClient } from "@/app/lib/supabase";
import { isValidSessionCookieValue, SESSION_COOKIE_NAME } from "@/app/lib/session";
import type { RecommendationDecision } from "@/app/lib/types";

export type RecommendationActionState = { error?: string; success?: boolean } | undefined;

const DECISIONS = new Set<RecommendationDecision>([
  "try",
  "not_relevant",
  "already_planned",
  "talent_declined",
  "revisit",
]);

async function requireSession(): Promise<void> {
  const cookieStore = await cookies();
  const value = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!isValidSessionCookieValue(value)) {
    throw new Error("Your session has expired. Please log in again.");
  }
}

function validDate(value: FormDataEntryValue | null): string | null {
  if (typeof value !== "string" || value === "") return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error("Revisit date must be a valid date.");
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    throw new Error("Revisit date must be a real calendar date.");
  }
  return value;
}

export async function respondToRecommendation(
  recommendationId: number,
  influencerId: number,
  handle: string,
  bulletIndex: number,
  _previousState: RecommendationActionState,
  formData: FormData,
): Promise<RecommendationActionState> {
  try {
    await requireSession();
    if (!Number.isInteger(recommendationId) || recommendationId <= 0) throw new Error("Invalid recommendation.");
    if (!Number.isInteger(influencerId) || influencerId <= 0) throw new Error("Invalid talent.");
    if (!Number.isInteger(bulletIndex) || bulletIndex < 0 || bulletIndex > 20) throw new Error("Invalid recommendation item.");
    if (!/^[A-Za-z0-9._]+$/.test(handle)) throw new Error("Invalid talent handle.");

    const decision = formData.get("decision");
    if (typeof decision !== "string" || !DECISIONS.has(decision as RecommendationDecision)) {
      throw new Error("Choose a valid response.");
    }
    const noteValue = formData.get("shared_note");
    const sharedNote = typeof noteValue === "string" ? noteValue.trim() : "";
    if (sharedNote.length > 500) throw new Error("Shared note must be 500 characters or fewer.");
    const revisitOn = validDate(formData.get("revisit_on"));

    const client = getSupabaseClient();
    const { data: recommendation, error: readError } = await client
      .from("recommendations")
      .select("influencer_id, content")
      .eq("id", recommendationId)
      .maybeSingle();
    if (readError || !recommendation || recommendation.influencer_id !== influencerId) {
      throw new Error("Recommendation not found for this talent.");
    }
    let bullets: unknown[];
    try {
      const parsed = JSON.parse(recommendation.content) as { bullets?: unknown };
      if (!Array.isArray(parsed.bullets)) throw new Error("legacy");
      bullets = parsed.bullets;
    } catch {
      throw new Error("Legacy recommendations are read-only.");
    }
    if (bulletIndex >= bullets.length) throw new Error("Recommendation item not found.");

    const { data: current } = await client
      .from("recommendation_actions")
      .select("experiment_status")
      .eq("recommendation_id", recommendationId)
      .eq("bullet_index", bulletIndex)
      .maybeSingle();
    if (current && ["published", "evaluated"].includes(current.experiment_status)) {
      throw new Error("Use the experiment controls to change an active or evaluated experiment.");
    }

    const { error } = await client.from("recommendation_actions").upsert(
      {
        recommendation_id: recommendationId,
        influencer_id: influencerId,
        bullet_index: bulletIndex,
        decision,
        shared_note: sharedNote,
        revisit_on: revisitOn,
        experiment_status: decision === "try" ? "planned" : null,
        linked_shortcode: null,
        published_at: null,
        review_at: null,
        baseline: null,
        outcome: null,
        evaluated_at: null,
        acknowledged_at: null,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "recommendation_id,bullet_index" },
    );
    if (error) throw new Error("The response could not be saved. Please try again.");

    revalidatePath("/");
    revalidatePath(`/influencer/${handle}`);
    return { success: true };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "The response could not be saved." };
  }
}
