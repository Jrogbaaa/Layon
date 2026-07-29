import json
from datetime import datetime, timezone

from supabase import Client, create_client

from . import config


def get_client() -> Client:
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def get_or_create_influencer(client: Client, handle: str) -> int:
    existing = client.table("influencers").select("id").eq("handle", handle).execute()
    if existing.data:
        return existing.data[0]["id"]
    created = client.table("influencers").insert({"handle": handle}).execute()
    return created.data[0]["id"]


def delete_influencer_by_handle(client: Client, handle: str) -> bool:
    result = client.table("influencers").delete().eq("handle", handle).execute()
    return bool(result.data)


def upload_avatar(client: Client, handle: str, image_bytes: bytes) -> str:
    path = f"{handle}.jpg"
    client.storage.from_("avatars").upload(
        path,
        image_bytes,
        file_options={"content-type": "image/jpeg", "upsert": "true"},
    )
    return client.storage.from_("avatars").get_public_url(path)


def update_influencer_avatar(client: Client, influencer_id: int, avatar_url: str) -> None:
    client.table("influencers").update({"avatar_url": avatar_url}).eq("id", influencer_id).execute()


def insert_profile_snapshot(client: Client, influencer_id: int, profile: dict) -> None:
    client.table("profile_snapshots").insert(
        {
            "influencer_id": influencer_id,
            "followers": profile["followers"],
            "following": profile["following"],
            "media_count": profile["media_count"],
            "bio": profile.get("bio"),
        }
    ).execute()


def insert_post_snapshots(client: Client, influencer_id: int, posts: list[dict]) -> None:
    if not posts:
        return
    rows = [
        {
            "influencer_id": influencer_id,
            "shortcode": post["shortcode"],
            "post_type": post["post_type"],
            "likes": post["likes"],
            "comments": post["comments"],
            "views": post.get("views"),
            "caption": post.get("caption"),
            "posted_at": post["posted_at"],
            "is_ad": post.get("is_ad", False),
        }
        for post in posts
    ]
    client.table("post_snapshots").insert(rows).execute()


def profile_scraped_today(client: Client, influencer_id: int) -> bool:
    today_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    result = (
        client.table("profile_snapshots")
        .select("id")
        .eq("influencer_id", influencer_id)
        .gte("captured_at", today_start)
        .execute()
    )
    return len(result.data) > 0


def trend_source_scraped_today(client: Client, source_url: str) -> bool:
    today_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    result = (
        client.table("trend_snapshots")
        .select("id")
        .eq("source_url", source_url)
        .gte("captured_at", today_start)
        .execute()
    )
    return len(result.data) > 0


def insert_trend_snapshot(client: Client, source_url: str, title: str | None, content_text: str) -> None:
    client.table("trend_snapshots").insert(
        {
            "source_url": source_url,
            "title": title,
            "content_text": content_text,
        }
    ).execute()


def list_influencers(client: Client) -> list[dict]:
    result = client.table("influencers").select("id, handle, persona").eq("active", True).execute()
    return result.data


def get_profile_snapshots(client: Client, influencer_id: int, limit: int = 30) -> list[dict]:
    result = (
        client.table("profile_snapshots")
        .select("followers, following, media_count, bio, captured_at")
        .eq("influencer_id", influencer_id)
        .order("captured_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data))


def get_recent_posts(client: Client, influencer_id: int, limit: int = 12) -> list[dict]:
    result = (
        client.table("post_snapshots")
        .select("shortcode, post_type, likes, comments, views, caption, posted_at, is_ad")
        .eq("influencer_id", influencer_id)
        .order("posted_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_all_post_snapshots(client: Client, influencer_id: int, limit: int = 500) -> list[dict]:
    result = (
        client.table("post_snapshots")
        .select("shortcode, post_type, likes, comments, views, caption, posted_at, captured_at, is_ad")
        .eq("influencer_id", influencer_id)
        .order("captured_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data


def insert_highlights(client: Client, influencer_id: int, highlights: list[dict]) -> None:
    if not highlights:
        return
    rows = [
        {
            "influencer_id": influencer_id,
            "content": highlight["content"],
            "metric": highlight["metric"],
        }
        for highlight in highlights
    ]
    client.table("highlights").insert(rows).execute()


def get_latest_highlights(client: Client, influencer_id: int, limit: int = 5) -> list[dict]:
    result = (
        client.table("highlights")
        .select("content, metric, captured_at")
        .eq("influencer_id", influencer_id)
        .order("captured_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_latest_trend_snapshots(client: Client, limit: int = 2) -> list[dict]:
    result = (
        client.table("trend_snapshots")
        .select("source_url, title, content_text, captured_at")
        .order("captured_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_top_posts(client: Client, influencer_id: int, limit: int = 5) -> list[dict]:
    result = (
        client.table("top_posts")
        .select("shortcode, post_type, likes, comments, views, caption, posted_at, engagement, is_ad")
        .eq("influencer_id", influencer_id)
        .order("engagement", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_post_classifications(client: Client, influencer_id: int) -> dict[str, dict]:
    result = (
        client.table("post_classifications")
        .select(
            "shortcode, status, decision_code, evidence, classifier_version, input_hash, classified_at"
        )
        .eq("influencer_id", influencer_id)
        .execute()
    )
    return {row["shortcode"]: row for row in result.data}


def upsert_post_classifications(client: Client, influencer_id: int, classifications: list[dict]) -> None:
    if not classifications:
        return
    rows = [
        {
            "influencer_id": influencer_id,
            "shortcode": row["shortcode"],
            "status": row["classification"]["status"],
            "decision_code": row["classification"]["decision_code"],
            "evidence": row["classification"]["evidence"],
            "classifier_version": row["classification"]["classifier_version"],
            "input_hash": row["classification"]["input_hash"],
            "classified_at": row["classification"]["classified_at"],
        }
        for row in classifications
    ]
    client.table("post_classifications").upsert(rows, on_conflict="influencer_id,shortcode").execute()


def get_analyzed_shortcodes(client: Client, influencer_id: int) -> set[str]:
    result = (
        client.table("post_content")
        .select("shortcode")
        .eq("influencer_id", influencer_id)
        .execute()
    )
    return {row["shortcode"] for row in result.data}


def get_ad_flags(client: Client, influencer_id: int, shortcodes: list[str]) -> dict[str, bool]:
    """Stored is_ad values for the given shortcodes, so already-classified posts can be
    reused rather than re-sent to Gemini. Snapshot rows of the same shortcode agree."""
    if not shortcodes:
        return {}
    result = (
        client.table("post_snapshots")
        .select("shortcode, is_ad")
        .eq("influencer_id", influencer_id)
        .in_("shortcode", shortcodes)
        .execute()
    )
    return {row["shortcode"]: row["is_ad"] for row in result.data}


def insert_post_content(client: Client, influencer_id: int, analyzed: list[dict]) -> None:
    if not analyzed:
        return
    rows = [
        {
            "influencer_id": influencer_id,
            "shortcode": item["shortcode"],
            "summary": item["summary"],
            "analysis": item["analysis"],
        }
        for item in analyzed
    ]
    client.table("post_content").insert(rows).execute()


def get_post_content_map(client: Client, influencer_id: int) -> dict[str, dict]:
    result = (
        client.table("post_content")
        .select("shortcode, summary, analysis")
        .eq("influencer_id", influencer_id)
        .execute()
    )
    return {row["shortcode"]: row for row in result.data}


def insert_recommendation(client: Client, influencer_id: int, model: str, content: str) -> None:
    client.table("recommendations").insert(
        {
            "influencer_id": influencer_id,
            "model": model,
            "content": content,
        }
    ).execute()


def get_latest_recommendation(client: Client, influencer_id: int) -> dict | None:
    result = (
        client.table("recommendations")
        .select("id, content, generated_at")
        .eq("influencer_id", influencer_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_talent_strategy(client: Client, influencer_id: int) -> dict | None:
    result = (
        client.table("talent_strategies")
        .select(
            "current_objective, horizon, target_audience, content_pillars, development_formats, "
            "tone, guardrails, commercial_direction, posting_constraints, updated_at, reviewed_at"
        )
        .eq("influencer_id", influencer_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def _with_recommendation_context(rows: list[dict]) -> list[dict]:
    enriched = []
    for source in rows:
        row = dict(source)
        recommendation = row.pop("recommendations", None)
        if isinstance(recommendation, list):
            recommendation = recommendation[0] if recommendation else None
        content = recommendation.get("content") if isinstance(recommendation, dict) else None
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            bullets = parsed.get("bullets", []) if isinstance(parsed, dict) else []
            index = row.get("bullet_index")
            bullet = bullets[index] if isinstance(index, int) and 0 <= index < len(bullets) else None
        except (json.JSONDecodeError, TypeError):
            bullet = None
        if isinstance(bullet, dict):
            row["recommendation_text"] = bullet.get("text")
            row["recommendation_shortcode"] = bullet.get("shortcode")
        enriched.append(row)
    return enriched


def get_recent_recommendation_actions(client: Client, influencer_id: int, limit: int = 10) -> list[dict]:
    result = (
        client.table("recommendation_actions")
        .select(
            "recommendation_id, bullet_index, decision, shared_note, revisit_on, "
            "experiment_status, linked_shortcode, updated_at, recommendations(content)"
        )
        .eq("influencer_id", influencer_id)
        .order("updated_at", desc=True)
        .limit(min(max(limit, 0), 10))
        .execute()
    )
    return _with_recommendation_context(result.data)


def get_recent_evaluated_experiments(client: Client, influencer_id: int, limit: int = 5) -> list[dict]:
    result = (
        client.table("recommendation_actions")
        .select(
            "recommendation_id, bullet_index, decision, shared_note, linked_shortcode, outcome, "
            "baseline, evaluated_at, updated_at, recommendations(content)"
        )
        .eq("influencer_id", influencer_id)
        .eq("experiment_status", "evaluated")
        .order("updated_at", desc=True)
        .limit(min(max(limit, 0), 5))
        .execute()
    )
    return _with_recommendation_context(result.data)


def get_due_experiments(client: Client, now_iso: str) -> list[dict]:
    result = (
        client.table("recommendation_actions")
        .select("id, influencer_id, linked_shortcode, published_at, review_at")
        .eq("experiment_status", "published")
        .lte("review_at", now_iso)
        .is_("evaluated_at", "null")
        .execute()
    )
    return result.data


def get_experiment_post_snapshots(client: Client, influencer_id: int) -> list[dict]:
    result = (
        client.table("post_snapshots")
        .select("shortcode, post_type, likes, comments, views, posted_at, captured_at, is_ad")
        .eq("influencer_id", influencer_id)
        .execute()
    )
    return result.data


def get_post_strategy_tags(client: Client, influencer_id: int) -> list[dict]:
    result = (
        client.table("post_strategy_tags")
        .select("shortcode, pillar, source, strategy_updated_at, removed_pillar")
        .eq("influencer_id", influencer_id)
        .execute()
    )
    return result.data


def flag_removed_manual_post_tags(
    client: Client, influencer_id: int, active_pillars: list[str], existing: list[dict] | None = None
) -> None:
    rows = existing if existing is not None else get_post_strategy_tags(client, influencer_id)
    for row in rows:
        if row["source"] != "manual":
            continue
        removed = manual_pillar_removed(row.get("pillar"), active_pillars)
        if bool(row.get("removed_pillar")) != removed:
            (
                client.table("post_strategy_tags")
                .update({"removed_pillar": removed, "updated_at": datetime.now(timezone.utc).isoformat()})
                .eq("influencer_id", influencer_id)
                .eq("shortcode", row["shortcode"])
                .eq("source", "manual")
                .execute()
            )


def manual_pillar_removed(pillar: str | None, active_pillars: list[str]) -> bool:
    return pillar is not None and pillar not in active_pillars


def upsert_automatic_post_strategy_tags(
    client: Client,
    influencer_id: int,
    tags: list[dict],
    strategy_updated_at: str,
    manual_shortcodes: set[str] | None = None,
) -> None:
    manual_shortcodes = manual_shortcodes or set()
    rows = [
        {
            "influencer_id": influencer_id,
            "shortcode": tag["shortcode"],
            "pillar": tag.get("pillar"),
            "source": "automatic",
            "strategy_updated_at": strategy_updated_at,
            "removed_pillar": False,
            "tagged_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for tag in tags
        if tag["shortcode"] not in manual_shortcodes
    ]
    if rows:
        client.table("post_strategy_tags").upsert(
            rows, on_conflict="influencer_id,shortcode"
        ).execute()


def mark_experiment_evaluated(
    client: Client, action_id: int, outcome: dict, evaluated_at: str
) -> bool:
    result = (
        client.table("recommendation_actions")
        .update(
            {
                "experiment_status": "evaluated",
                "baseline": outcome["baseline"],
                "outcome": outcome,
                "evaluated_at": evaluated_at,
                "updated_at": evaluated_at,
            }
        )
        .eq("id", action_id)
        .eq("experiment_status", "published")
        .is_("evaluated_at", "null")
        .execute()
    )
    return bool(result.data)


def weekly_review_exists(client: Client, period_start: str) -> bool:
    result = (
        client.table("roster_briefings")
        .select("id")
        .eq("period_start", period_start)
        .limit(1)
        .execute()
    )
    return bool(result.data)


def get_weekly_review_actions(client: Client, influencer_id: int) -> list[dict]:
    result = (
        client.table("recommendation_actions")
        .select(
            "recommendation_id, bullet_index, decision, experiment_status, linked_shortcode, "
            "review_at, outcome, evaluated_at, acknowledged_at"
        )
        .eq("influencer_id", influencer_id)
        .execute()
    )
    return result.data


def insert_roster_briefing(
    client: Client,
    model: str,
    content: str,
    period_start: str | None = None,
    period_end: str | None = None,
) -> None:
    row = {"model": model, "content": content}
    if period_start is not None:
        row["period_start"] = period_start
    if period_end is not None:
        row["period_end"] = period_end
    client.table("roster_briefings").insert(row).execute()


def get_latest_roster_briefing(client: Client) -> dict | None:
    result = (
        client.table("roster_briefings")
        .select("content, generated_at, model, period_start, period_end")
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def insert_trend_headlines(client: Client, model: str, content: str) -> None:
    client.table("trend_headlines").insert(
        {
            "model": model,
            "content": content,
        }
    ).execute()


def get_latest_trend_headlines(client: Client) -> dict | None:
    result = (
        client.table("trend_headlines")
        .select("content, generated_at, model")
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
