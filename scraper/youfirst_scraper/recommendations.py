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
    trend_items: list[str] | None = None,
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

    trends_section = ""
    if trend_items:
        trend_lines = "\n".join(f"- {t}" for t in trend_items)
        trends_section = f"""
What's trending in Spain today (scraped today — the ONLY trends you may reference):
{trend_lines}
If a recommendation ties into a trend, NAME the specific show, event, person, or moment
from this list in the recommendation text itself. Never write a vague placeholder like
"a currently trending Spanish TV show" or "a viral moment". If none of these trends fit
the persona, base the recommendation on the performance data instead of inventing a trend.
"""

    return f"""You are an emotionally intelligent creative strategist for @{handle}, an Instagram influencer.

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
Spanish social media culture, not US ones.
{trends_section}
INSTRUCTIONS:
Generate 2-4 short, specific, actionable creative recommendations for this influencer's next posts.

Recommendations are strictly limited to exactly two types of bullets:
1. Past success re-expressed with emotional intelligence (kind: "past_success"):
   - Grounded in a specific post that worked (either recent or all-time).
   - Propose a fresh creative expression of the underlying mechanism (theme, format, tone, pacing, visual hook, authenticity signals).
   - NEVER recommend copying the exact event/topic or literal repetition (e.g. do NOT say "do another sad story" or "do that post again").
   - Classify the referenced post's mechanism (e.g. why it worked based on format, emotional register - arousal level/valence, and authenticity) and explain this in the "reason" field.
2. Trend-tied idea (kind: "trend"):
   - Propose an idea tied into a specific Spanish trend from the list provided (if trend_items is present).
   - You must NAME the specific show, event, person, or moment from the trend list in the recommendation text itself.
   - ONLY recommend this if the trend fits the influencer's persona, tier, and style.
   - If no trends fit the persona, skip the trend bullet entirely. Do not force-fit or invent a trend.

EMOTIONAL INTELLIGENCE & APPROPRIATENESS GUARDRAIL:
- Sensitive, raw, or vulnerable content (e.g., posts about grief, illness, recovery, breakups, personal struggle, or sensitive family milestones) may be noted in the data as evidence that the audience values authenticity.
- However, you must NEVER recommend tactical repetition or cloning of these personal experiences/emotions.
- Tactical repetition of intimacy damages creator credibility (Leite et al. 2013), and sadness is a low-arousal emotion which does not sustain virality (Berger & Milkman 2012). Do not advise repeating these personal events/emotions.

ACHIEVABILITY FILTER:
- Every recommendation must be immediately executable using formats and content types the influencer has already demonstrated in their posting history.
- Do not suggest low-fi sketches or comedic acting if the influencer is a professional athlete or premium presenter.
- Respect their persona boundaries:
  - @cristipedroche is a high-profile presenter who won't do comedy sketches, low-fi meme trends, or TikTok dances.
  - @ferminaldeguer_54 is an athlete who won't do sketches or TikTok dances.
  - @antonlofer, @dante_caro, and @mariavalero are sketch creators where comedic acting/sketches are fair game.

Write every recommendation and its reason in BOTH English and Spanish.

Respond ONLY with JSON in this exact shape, no other text:
{{"bullets": [{{"kind": "past_success", "text": {{"en": "short recommendation in English, max ~20 words", "es": "the same recommendation in Spanish"}}, "reason": {{"en": "the specific stat/content mechanism that motivated it, in English", "es": "the same reason in Spanish"}}, "shortcode": "referenced post's shortcode, or null if trend"}}]}}"""


def _validate(parsed: object) -> None:
    if not isinstance(parsed, dict) or "bullets" not in parsed:
        raise ValueError("missing bullets key")
    bullets = parsed["bullets"]
    if not isinstance(bullets, list) or not bullets:
        raise ValueError("bullets must be a non-empty list")
    for bullet in bullets:
        if not isinstance(bullet, dict):
            raise ValueError("bullet must be a dictionary")
        kind = bullet.get("kind")
        if kind not in ("past_success", "trend"):
            raise ValueError(f"invalid or missing bullet kind: {kind}")
        for field in ("text", "reason"):
            value = bullet.get(field)
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
    trend_items: list[str] | None = None,
) -> str | None:
    computed_metrics = metrics.compute_metrics(profile_snapshots, posts)
    prompt = build_prompt(
        handle,
        computed_metrics,
        posts,
        persona,
        highlights,
        content_map,
        alltime_top_posts,
        trend_items,
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
