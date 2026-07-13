import json
import logging
from statistics import median as _median

from google import genai
from google.genai import types

from . import config, metrics

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
TOP_PERFORMERS_COUNT = 4
MAX_ATTEMPTS = 2


def _post_line(post: dict, baseline: float, content_map: dict[str, dict]) -> str:
    engagement = post["likes"] + post["comments"]
    multiple = f"{engagement / baseline:.1f}x median" if baseline > 0 else "n/a"
    content = content_map.get(post["shortcode"])
    summary = content["summary"] if content else (post.get("caption") or "(no caption)")
    views_part = f", {post['views']:,} views" if post.get("views") else ""
    return (
        f"- [{post['shortcode']}] {post['post_type']}, {post['likes']} likes, "
        f"{post['comments']} comments{views_part} ({multiple}) — {summary}"
    )


def build_prompt(
    handle: str,
    computed_metrics: dict,
    posts: list[dict],
    persona: str | None = None,
    highlights: list[dict] | None = None,
    content_map: dict[str, dict] | None = None,
    alltime_top_posts: list[dict] | None = None,
) -> str:
    content_map = content_map or {}
    deduped: dict[str, dict] = {}
    for post in posts:
        existing = deduped.get(post["shortcode"])
        if existing is None or (post["likes"] + post["comments"]) > (existing["likes"] + existing["comments"]):
            deduped[post["shortcode"]] = post

    ranked = sorted(deduped.values(), key=lambda p: p["likes"] + p["comments"], reverse=True)
    baseline = float(_median([p["likes"] + p["comments"] for p in ranked])) if ranked else 0.0

    top_posts = ranked[:TOP_PERFORMERS_COUNT]
    top_section = "\n".join(_post_line(p, baseline, content_map) for p in top_posts)

    weakest_section = ""
    if len(ranked) > TOP_PERFORMERS_COUNT:
        weakest_section = f"\nWeakest recent post for contrast:\n{_post_line(ranked[-1], baseline, content_map)}\n"

    persona_section = (
        f"\nInfluencer persona/brand: {persona}\n"
        "Only suggest formats and trend adaptations that fit this persona — adapt trends "
        "to match their brand rather than forcing an off-brand format.\n"
        if persona
        else ""
    )

    highlight_lines = "\n".join(f"- {h['content']}" for h in (highlights or []))
    highlights_section = (
        f"\nRecent performance highlights (lead with the standout stat when relevant):\n{highlight_lines}\n"
        if highlight_lines
        else ""
    )

    alltime_section = ""
    if alltime_top_posts:
        ceiling = max(p["likes"] + p["comments"] for p in alltime_top_posts)
        alltime_lines = "\n".join(_post_line(p, baseline, content_map) for p in alltime_top_posts)
        alltime_section = f"""
All-time top performing posts (this is what GOOD looks like for @{handle}):
{alltime_lines}
Performance ceiling: @{handle}'s best posts reach ~{ceiling:,} engagement (likes+comments).
The recent 12-post median is {baseline:,.0f}. Judge recent posts against the all-time
ceiling, not just the recent median: only call a recent post "top performing" if it
approaches the all-time numbers. If recent posts sit far below the ceiling, say so
plainly and base recommendations on what the all-time winners did.
"""

    return f"""You are a social media strategist for a talent agency's Instagram influencer.

Influencer: @{handle}
{persona_section}
Metrics (from real scraped data):
- Engagement rate: {computed_metrics['engagement_rate_pct']}%
- Follower change since last snapshot: {computed_metrics['follower_delta']}
- Average engagement by post format: {computed_metrics['format_performance']}
- Average days between posts: {computed_metrics['posting_cadence_days']}
{highlights_section}
{alltime_section}
Recent posts ranked by engagement (last ~12):
{top_section or '(no recent posts)'}
{weakest_section}
The target audience is Spain / Spanish-speaking, not the USA — recommendations should fit
Spanish social media culture and trends, not US ones.

Write 3-5 short, specific, actionable creative recommendations for this influencer's next
posts. Each recommendation must reference the specific top-performing post (by its content,
not just its shortcode) or metric that motivated it — e.g. "Follow up on [post topic], it
performed very well (2.3x median)." Do not give generic advice ("post more often") without
tying it to the data above.

Write every recommendation and its reason in BOTH English and Spanish.

Respond ONLY with JSON in this exact shape, no other text:
{{"bullets": [{{"text": {{"en": "short recommendation in English, max ~20 words", "es": "the same recommendation in Spanish"}}, "reason": {{"en": "the specific stat or content that motivated it, in English", "es": "the same reason in Spanish"}}, "shortcode": "the referenced post's shortcode, or null if none"}}]}}"""


def _validate(parsed: object) -> None:
    if not isinstance(parsed, dict) or "bullets" not in parsed:
        raise ValueError("missing bullets key")
    bullets = parsed["bullets"]
    if not isinstance(bullets, list) or not bullets:
        raise ValueError("bullets must be a non-empty list")
    for bullet in bullets:
        for field in ("text", "reason"):
            value = bullet.get(field) if isinstance(bullet, dict) else None
            if not isinstance(value, dict) or "en" not in value or "es" not in value:
                raise ValueError(f"bullet {field} missing en/es")


def generate_recommendation(
    handle: str,
    profile_snapshots: list[dict],
    posts: list[dict],
    persona: str | None = None,
    highlights: list[dict] | None = None,
    content_map: dict[str, dict] | None = None,
    alltime_top_posts: list[dict] | None = None,
) -> str | None:
    computed_metrics = metrics.compute_metrics(profile_snapshots, posts)
    prompt = build_prompt(
        handle, computed_metrics, posts, persona, highlights, content_map, alltime_top_posts
    )

    client = genai.Client(api_key=config.GOOGLE_API_KEY)

    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        contents = (
            prompt
            if attempt == 0
            else f"{prompt}\n\nYour previous response was invalid ({last_error}). "
            "Respond ONLY with valid JSON matching the exact shape above."
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            parsed = json.loads(response.text)
            _validate(parsed)
            return json.dumps(parsed)
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            logger.warning(
                "Gemini recommendation for %s invalid on attempt %d: %s", handle, attempt + 1, e
            )

    logger.error("Gemini recommendation for %s failed validation twice — not storing", handle)
    return None
