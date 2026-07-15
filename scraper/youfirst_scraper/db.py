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


def get_analyzed_shortcodes(client: Client, influencer_id: int) -> set[str]:
    result = (
        client.table("post_content")
        .select("shortcode")
        .eq("influencer_id", influencer_id)
        .execute()
    )
    return {row["shortcode"] for row in result.data}


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
        .select("content, generated_at")
        .eq("influencer_id", influencer_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def insert_roster_briefing(client: Client, model: str, content: str) -> None:
    client.table("roster_briefings").insert(
        {
            "model": model,
            "content": content,
        }
    ).execute()


def get_latest_roster_briefing(client: Client) -> dict | None:
    result = (
        client.table("roster_briefings")
        .select("content, generated_at, model")
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
