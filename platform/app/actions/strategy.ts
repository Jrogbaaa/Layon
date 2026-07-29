"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { getSupabaseClient } from "@/app/lib/supabase";
import { isValidSessionCookieValue, SESSION_COOKIE_NAME } from "@/app/lib/session";

export type StrategyActionState = { error?: string; success?: boolean } | undefined;

const LIMITS = {
  current_objective: 500,
  target_audience: 500,
  tone: 1000,
  guardrails: 1000,
  commercial_direction: 500,
  posting_constraints: 1000,
} as const;

const ALLOWED_FORMATS = new Set(["photo", "video", "reel", "carousel"]);

function textField(formData: FormData, name: keyof typeof LIMITS): string {
  const value = formData.get(name);
  if (typeof value !== "string") return "";
  const trimmed = value.trim();
  if (trimmed.length > LIMITS[name]) {
    throw new Error(`${name.replaceAll("_", " ")} is too long.`);
  }
  return trimmed;
}

function pillarsField(formData: FormData): string[] {
  const value = formData.get("content_pillars");
  if (typeof value !== "string") return [];
  const pillars = value
    .split(",")
    .map((pillar) => pillar.trim())
    .filter(Boolean);
  if (pillars.length > 8 || pillars.some((pillar) => pillar.length > 80)) {
    throw new Error("Use up to 8 content pillars, each 80 characters or fewer.");
  }
  return [...new Set(pillars)];
}

function horizonField(formData: FormData): string | null {
  const value = formData.get("horizon");
  if (typeof value !== "string" || value === "") return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error("Horizon must be a valid date.");
  return value;
}

async function requireSession(): Promise<void> {
  const cookieStore = await cookies();
  const value = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!isValidSessionCookieValue(value)) {
    throw new Error("Your session has expired. Please log in again.");
  }
}

export async function saveTalentStrategy(
  influencerId: number,
  handle: string,
  _previousState: StrategyActionState,
  formData: FormData,
): Promise<StrategyActionState> {
  try {
    await requireSession();
    if (!Number.isInteger(influencerId) || influencerId <= 0) throw new Error("Invalid talent.");
    if (!/^[A-Za-z0-9._]+$/.test(handle)) throw new Error("Invalid talent handle.");

    const formats = formData
      .getAll("development_formats")
      .filter((value): value is string => typeof value === "string");
    if (formats.some((format) => !ALLOWED_FORMATS.has(format))) {
      throw new Error("Invalid development format.");
    }

    const now = new Date().toISOString();
    const pillars = pillarsField(formData);
    const client = getSupabaseClient();
    const { error } = await client.from("talent_strategies").upsert({
      influencer_id: influencerId,
      current_objective: textField(formData, "current_objective"),
      horizon: horizonField(formData),
      target_audience: textField(formData, "target_audience"),
      content_pillars: pillars,
      development_formats: [...new Set(formats)],
      tone: textField(formData, "tone"),
      guardrails: textField(formData, "guardrails"),
      commercial_direction: textField(formData, "commercial_direction"),
      posting_constraints: textField(formData, "posting_constraints"),
      updated_at: now,
      reviewed_at: now,
    });
    if (error) throw new Error("The strategy could not be saved. Please try again.");

    const { data: manualTags } = await client
      .from("post_strategy_tags")
      .select("shortcode, pillar, removed_pillar")
      .eq("influencer_id", influencerId)
      .eq("source", "manual");
    for (const tag of manualTags ?? []) {
      const removed = Boolean(tag.pillar) && !pillars.includes(tag.pillar);
      if (tag.removed_pillar !== removed) {
        await client
          .from("post_strategy_tags")
          .update({ removed_pillar: removed, updated_at: now })
          .eq("influencer_id", influencerId)
          .eq("shortcode", tag.shortcode)
          .eq("source", "manual");
      }
    }

    revalidatePath("/");
    revalidatePath(`/influencer/${handle}`);
    return { success: true };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "The strategy could not be saved." };
  }
}
