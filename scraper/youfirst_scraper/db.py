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
            "caption": post.get("caption"),
            "posted_at": post["posted_at"],
        }
        for post in posts
    ]
    client.table("post_snapshots").insert(rows).execute()


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
    result = client.table("influencers").select("id, handle").eq("active", True).execute()
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
        .select("shortcode, post_type, likes, comments, caption, posted_at")
        .eq("influencer_id", influencer_id)
        .order("posted_at", desc=True)
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


def insert_recommendation(client: Client, influencer_id: int, model: str, content: str) -> None:
    client.table("recommendations").insert(
        {
            "influencer_id": influencer_id,
            "model": model,
            "content": content,
        }
    ).execute()
