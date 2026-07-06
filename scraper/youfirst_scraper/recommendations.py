import logging

from google import genai

from . import config, metrics

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"


def build_prompt(handle: str, computed_metrics: dict, posts: list[dict], trends: list[dict]) -> str:
    trend_text = "\n\n".join(
        f"Source: {t['source_url']}\nTitle: {t.get('title') or 'N/A'}\n{t['content_text'][:1500]}"
        for t in trends
    ) or "No trend data available."

    top_captions = "\n".join(f"- {p.get('caption') or '(no caption)'}" for p in posts[:5])

    return f"""You are a social media strategist for a talent agency's Instagram influencer.

Influencer: @{handle}

Metrics (from real scraped data):
- Engagement rate: {computed_metrics['engagement_rate_pct']}%
- Follower change since last snapshot: {computed_metrics['follower_delta']}
- Average engagement by post format: {computed_metrics['format_performance']}
- Average days between posts: {computed_metrics['posting_cadence_days']}

Recent post captions:
{top_captions or '(no recent posts)'}

Current Instagram trend reports:
{trend_text}

Write 3-5 specific, actionable creative recommendations for this influencer's next posts,
in both Spanish and English. Reference the specific metric or trend that motivated each
recommendation. Do not give generic advice ("post more consistently") without tying it to
the data above."""


def generate_recommendation(handle: str, profile_snapshots: list[dict], posts: list[dict], trends: list[dict]) -> str:
    computed_metrics = metrics.compute_metrics(profile_snapshots, posts)
    prompt = build_prompt(handle, computed_metrics, posts, trends)

    client = genai.Client(api_key=config.GOOGLE_API_KEY)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text
