import json
import logging
from statistics import median as _median

from google import genai
from google.genai import types

from . import config, metrics

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
TOP_PERFORMERS_COUNT = 4


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

    return f"""You are a social media strategist for a talent agency's Instagram influencer.

Influencer: @{handle}
{persona_section}
Metrics (from real scraped data):
- Engagement rate: {computed_metrics['engagement_rate_pct']}%
- Follower change since last snapshot: {computed_metrics['follower_delta']}
- Average engagement by post format: {computed_metrics['format_performance']}
- Average days between posts: {computed_metrics['posting_cadence_days']}
{highlights_section}
Top performing recent posts (with what the content was actually about):
{top_section or '(no recent posts)'}
{weakest_section}
The target audience is Spain / Spanish-speaking, not the USA — recommendations should fit
Spanish social media culture and trends, not US ones.

Write 3-5 short, specific, actionable creative recommendations for this influencer's next
posts, in Spanish only. Each recommendation must reference the specific top-performing post
(by its content, not just its shortcode) or metric that motivated it — e.g. "Haz un
seguimiento al [tema del post], funcionó muy bien (2.3x la mediana)." Do not give generic
advice ("publica más seguido") without tying it to the data above.

Respond ONLY with JSON in this exact shape, no other text:
{{"bullets": [{{"text": "short recommendation in Spanish, max ~20 words", "reason": "the specific stat or content that motivated it, in Spanish", "shortcode": "the referenced post's shortcode, or null if none"}}]}}"""


def generate_recommendation(
    handle: str,
    profile_snapshots: list[dict],
    posts: list[dict],
    persona: str | None = None,
    highlights: list[dict] | None = None,
    content_map: dict[str, dict] | None = None,
) -> str:
    computed_metrics = metrics.compute_metrics(profile_snapshots, posts)
    prompt = build_prompt(handle, computed_metrics, posts, persona, highlights, content_map)

    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        parsed = json.loads(response.text)
        if not isinstance(parsed, dict) or "bullets" not in parsed:
            raise ValueError("missing bullets key")
        return json.dumps(parsed)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Gemini recommendation for %s was not valid bullet JSON — storing raw text", handle)
        return response.text
