import json
import logging

from google import genai
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
MAX_POSTS = 30


def build_tagging_prompt(pillars: list[str], posts: list[dict], content_map: dict[str, dict]) -> str:
    evidence = []
    seen = set()
    for post in posts:
        shortcode = post["shortcode"]
        if shortcode in seen:
            continue
        seen.add(shortcode)
        content = content_map.get(shortcode) or {}
        evidence.append(
            {
                "shortcode": shortcode,
                "post_type": post.get("post_type"),
                "caption": post.get("caption") or "",
                "summary": content.get("summary") or "",
                "analysis": content.get("analysis") or {},
            }
        )
        if len(evidence) >= MAX_POSTS:
            break
    return f"""Map each stored Instagram post to one active content pillar or null.

Active pillars (use these strings exactly):
{json.dumps(pillars, ensure_ascii=False)}

Stored evidence only; do not infer private facts and do not request external data:
{json.dumps(evidence, ensure_ascii=False, default=str)}

Choose null when the evidence does not clearly fit a pillar. Return every supplied shortcode
exactly once. Respond only as JSON:
{{"tags":[{{"shortcode":"abc","pillar":"exact active pillar or null"}}]}}
"""


def generate_tags(pillars: list[str], posts: list[dict], content_map: dict[str, dict]) -> list[dict] | None:
    prompt = build_tagging_prompt(pillars, posts, content_map)
    supplied = []
    seen = set()
    for post in posts:
        if post["shortcode"] not in seen:
            supplied.append(post["shortcode"])
            seen.add(post["shortcode"])
        if len(supplied) >= MAX_POSTS:
            break
    if not supplied:
        return []

    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    try:
        parsed = json.loads(response.text)
        tags = parsed["tags"]
        if not isinstance(tags, list):
            raise ValueError("tags must be a list")
        by_shortcode = {}
        for tag in tags:
            shortcode = tag.get("shortcode")
            pillar = tag.get("pillar")
            if shortcode not in supplied or shortcode in by_shortcode:
                raise ValueError("invalid or duplicate shortcode")
            if pillar is not None and pillar not in pillars:
                raise ValueError("pillar is not active")
            by_shortcode[shortcode] = {"shortcode": shortcode, "pillar": pillar}
        if set(by_shortcode) != set(supplied):
            raise ValueError("response omitted a shortcode")
        return [by_shortcode[shortcode] for shortcode in supplied]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        logger.warning("Invalid post strategy tagging response: %s", error)
        return None


def tag_influencer(client, db_module, influencer_id: int) -> int:
    strategy = db_module.get_talent_strategy(client, influencer_id)
    if not strategy:
        return 0
    pillars = strategy.get("content_pillars") or []
    existing = db_module.get_post_strategy_tags(client, influencer_id)
    db_module.flag_removed_manual_post_tags(client, influencer_id, pillars, existing)
    manual_shortcodes = {row["shortcode"] for row in existing if row["source"] == "manual"}
    stale_automatic = {
        row["shortcode"]
        for row in existing
        if row["source"] == "automatic" and row.get("strategy_updated_at") != strategy["updated_at"]
    }
    posts = db_module.get_recent_posts(client, influencer_id, limit=MAX_POSTS * 3)
    unique_posts = []
    seen = set()
    for post in posts:
        shortcode = post["shortcode"]
        if shortcode in seen or shortcode in manual_shortcodes:
            continue
        seen.add(shortcode)
        known_current = any(
            row["shortcode"] == shortcode
            and row["source"] == "automatic"
            and row.get("strategy_updated_at") == strategy["updated_at"]
            for row in existing
        )
        if not known_current or shortcode in stale_automatic:
            unique_posts.append(post)
        if len(unique_posts) >= MAX_POSTS:
            break
    if not unique_posts:
        return 0
    tags = (
        [{"shortcode": post["shortcode"], "pillar": None} for post in unique_posts]
        if not pillars
        else generate_tags(pillars, unique_posts, db_module.get_post_content_map(client, influencer_id))
    )
    if tags is None:
        return 0
    db_module.upsert_automatic_post_strategy_tags(
        client, influencer_id, tags, strategy["updated_at"], manual_shortcodes
    )
    return len(tags)
