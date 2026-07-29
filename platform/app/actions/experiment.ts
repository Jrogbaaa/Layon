"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getSupabaseClient } from "@/app/lib/supabase";
import { isValidSessionCookieValue, SESSION_COOKIE_NAME } from "@/app/lib/session";

export type ExperimentActionState = { error?: string; success?: boolean } | undefined;

async function requireSession(): Promise<void> {
  const cookieStore = await cookies();
  if (!isValidSessionCookieValue(cookieStore.get(SESSION_COOKIE_NAME)?.value)) {
    throw new Error("Your session has expired. Please log in again.");
  }
}

function validateIdentity(actionId: number, influencerId: number, handle: string): void {
  if (!Number.isInteger(actionId) || actionId <= 0) throw new Error("Invalid experiment.");
  if (!Number.isInteger(influencerId) || influencerId <= 0) throw new Error("Invalid talent.");
  if (!/^[A-Za-z0-9._]+$/.test(handle)) throw new Error("Invalid talent handle.");
}

function refresh(handle: string): void {
  revalidatePath("/");
  revalidatePath(`/influencer/${handle}`);
}

export async function linkExperiment(
  actionId: number,
  influencerId: number,
  handle: string,
  _previousState: ExperimentActionState,
  formData: FormData,
): Promise<ExperimentActionState> {
  void _previousState;
  try {
    await requireSession();
    validateIdentity(actionId, influencerId, handle);
    const shortcodeValue = formData.get("shortcode");
    const shortcode = typeof shortcodeValue === "string" ? shortcodeValue.trim() : "";
    if (!/^[A-Za-z0-9_-]{3,30}$/.test(shortcode)) throw new Error("Choose a valid scraped post.");

    const client = getSupabaseClient();
    const { data: action } = await client
      .from("recommendation_actions")
      .select("id, experiment_status, decision")
      .eq("id", actionId)
      .eq("influencer_id", influencerId)
      .maybeSingle();
    if (!action || action.decision !== "try" || action.experiment_status !== "planned") {
      throw new Error("Only a planned experiment can be linked.");
    }

    const { data: posts } = await client
      .from("post_snapshots")
      .select("posted_at")
      .eq("influencer_id", influencerId)
      .eq("shortcode", shortcode)
      .order("captured_at", { ascending: false })
      .limit(1);
    const publishedAt = posts?.[0]?.posted_at;
    if (!publishedAt) throw new Error("That post does not belong to this talent.");
    const published = new Date(publishedAt);
    if (Number.isNaN(published.getTime())) throw new Error("The stored publication date is invalid.");
    const reviewAt = new Date(published.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const now = new Date().toISOString();

    const { data: updated, error } = await client
      .from("recommendation_actions")
      .update({
        experiment_status: "published",
        linked_shortcode: shortcode,
        published_at: published.toISOString(),
        review_at: reviewAt,
        baseline: null,
        outcome: null,
        evaluated_at: null,
        acknowledged_at: null,
        updated_at: now,
      })
      .eq("id", actionId)
      .eq("influencer_id", influencerId)
      .eq("experiment_status", "planned")
      .select("id");
    if (error || !updated?.length) throw new Error("The experiment could not be linked.");
    refresh(handle);
    return { success: true };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "The experiment could not be linked." };
  }
}

export async function abandonExperiment(
  actionId: number,
  influencerId: number,
  handle: string,
  _previousState: ExperimentActionState,
  _formData: FormData,
): Promise<ExperimentActionState> {
  void _previousState;
  void _formData;
  try {
    await requireSession();
    validateIdentity(actionId, influencerId, handle);
    const client = getSupabaseClient();
    const { data: action } = await client
      .from("recommendation_actions")
      .select("experiment_status")
      .eq("id", actionId)
      .eq("influencer_id", influencerId)
      .maybeSingle();
    if (!action || !["planned", "published"].includes(action.experiment_status)) {
      throw new Error("Only an active experiment can be abandoned.");
    }
    const { error } = await client
      .from("recommendation_actions")
      .update({ experiment_status: "abandoned", updated_at: new Date().toISOString() })
      .eq("id", actionId)
      .eq("influencer_id", influencerId)
      .in("experiment_status", ["planned", "published"]);
    if (error) throw new Error("The experiment could not be abandoned.");
    refresh(handle);
    return { success: true };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "The experiment could not be abandoned." };
  }
}

export async function acknowledgeOutcome(
  actionId: number,
  influencerId: number,
  handle: string,
  _previousState: ExperimentActionState,
  _formData: FormData,
): Promise<ExperimentActionState> {
  void _previousState;
  void _formData;
  try {
    await requireSession();
    validateIdentity(actionId, influencerId, handle);
    const { data, error } = await getSupabaseClient()
      .from("recommendation_actions")
      .update({ acknowledged_at: new Date().toISOString(), updated_at: new Date().toISOString() })
      .eq("id", actionId)
      .eq("influencer_id", influencerId)
      .eq("experiment_status", "evaluated")
      .not("outcome", "is", null)
      .is("acknowledged_at", null)
      .select("id");
    if (error || !data?.length) throw new Error("Only an unacknowledged outcome can be acknowledged.");
    refresh(handle);
    return { success: true };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "The outcome could not be acknowledged." };
  }
}

export async function overridePostPillar(
  influencerId: number,
  handle: string,
  shortcode: string,
  _previousState: ExperimentActionState,
  formData: FormData,
): Promise<ExperimentActionState> {
  try {
    await requireSession();
    validateIdentity(1, influencerId, handle);
    if (!/^[A-Za-z0-9_-]{3,30}$/.test(shortcode)) throw new Error("Invalid post.");
    const pillarValue = formData.get("pillar");
    const pillar = typeof pillarValue === "string" && pillarValue !== "" ? pillarValue : null;
    if (pillar && pillar.length > 80) throw new Error("Pillar is too long.");

    const client = getSupabaseClient();
    const [{ data: postRows }, { data: strategy }] = await Promise.all([
      client.from("post_snapshots").select("shortcode").eq("influencer_id", influencerId).eq("shortcode", shortcode).limit(1),
      client.from("talent_strategies").select("content_pillars, updated_at").eq("influencer_id", influencerId).maybeSingle(),
    ]);
    if (!postRows?.length) throw new Error("That post does not belong to this talent.");
    const activePillars = (strategy?.content_pillars ?? []) as string[];
    if (pillar && !activePillars.includes(pillar)) throw new Error("Choose an active strategy pillar.");
    const now = new Date().toISOString();
    const { error } = await client.from("post_strategy_tags").upsert(
      {
        influencer_id: influencerId,
        shortcode,
        pillar,
        source: "manual",
        strategy_updated_at: strategy?.updated_at ?? null,
        removed_pillar: false,
        tagged_at: now,
        updated_at: now,
      },
      { onConflict: "influencer_id,shortcode" },
    );
    if (error) throw new Error("The pillar override could not be saved.");
    refresh(handle);
    return { success: true };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "The pillar override could not be saved." };
  }
}
