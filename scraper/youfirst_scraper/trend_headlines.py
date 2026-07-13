import json
import logging

from google import genai
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 2
MAX_CHARS_PER_SOURCE = 4000


def _source_section(snapshot: dict, index: int) -> str:
    title = snapshot.get("title") or snapshot["source_url"]
    text = snapshot["content_text"][:MAX_CHARS_PER_SOURCE]
    return f"Source {index}: {title} ({snapshot['source_url']})\n{text}"


def build_prompt(snapshots: list[dict]) -> str:
    sources_section = "\n\n".join(_source_section(s, i + 1) for i, s in enumerate(snapshots))

    return f"""You are a trends editor for a Spanish talent agency. Below are today's scraped
Spanish social media trend reports, platform creative insights, format statistics, and strategic forecasts for TikTok and Instagram.

{sources_section}

Distill these into 5-8 short, punchy headlines a manager can absorb in ten seconds detailing the key social media trend insights, platform strategies, content formats, or viral tactics.

CRITICAL FILTERS:
- Focus strictly on Spain/Spanish-market social media trends, strategies, and creator tips (the "be all end all").
- STRICTLY EXCLUDE generic news, politics, and global celebrity gossip that is unrelated to social media trends or Spanish influencers.
- Ensure every headline is highly relevant to Spanish talent managers and their influencers (helping them design content for Instagram and TikTok).

Each headline must NAME the specific tactic, format, trend concept, or statistic involved (e.g.
"Carousels outperform Reels for engagement" or "Curiosity Detours driving watch times") — never a generic theme like "short video
keeps growing". Skip items with no named subject. No filler, no numbering. Attribute
each headline to the source_url it came from (use the exact URL given above, or null if
you cannot attribute it to one).

Write every headline in BOTH English and Spanish.

Respond ONLY with JSON in this exact shape, no other text:
{{"headlines": [{{"text": {{"en": "short headline, max ~12 words", "es": "the same headline in Spanish"}}, "source_url": "the source url, or null"}}]}}"""


def _validate(parsed: object) -> None:
    if not isinstance(parsed, dict) or "headlines" not in parsed:
        raise ValueError("missing headlines key")
    headlines = parsed["headlines"]
    if not isinstance(headlines, list) or not headlines:
        raise ValueError("headlines must be a non-empty list")
    for headline in headlines:
        text = headline.get("text") if isinstance(headline, dict) else None
        if not isinstance(text, dict) or "en" not in text or "es" not in text:
            raise ValueError("headline text missing en/es")


def _normalize_source_urls(parsed: dict, known_urls: set[str]) -> None:
    for headline in parsed["headlines"]:
        if headline.get("source_url") not in known_urls:
            headline["source_url"] = None


def generate_headlines(snapshots: list[dict]) -> str | None:
    prompt = build_prompt(snapshots)
    known_urls = {s["source_url"] for s in snapshots}
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
            _normalize_source_urls(parsed, known_urls)
            return json.dumps(parsed)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError, AttributeError) as e:
            last_error = e
            logger.warning("Trend headlines invalid on attempt %d: %s", attempt + 1, e)

    logger.error("Trend headlines failed validation twice — not storing")
    return None
