import json
import logging

from google import genai
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 2


def _status_line(status: dict) -> str:
    return (
        f"- @{status['handle']}: {status['followers']:,} followers, "
        f"{status['engagement_rate_pct']}% engagement rate, "
        f"{status['follower_delta']:+d} followers since last snapshot"
    )


def _pattern_line(pattern: dict) -> str:
    handles = ", ".join(f"@{h}" for h in pattern["handles"])
    evidence = "; ".join(
        f"@{e['handle']} +{e['pct']:.0f}% ({e['engagement']:.0f} vs median {e['median_engagement']:.0f})"
        for e in pattern["evidence"]
    )
    return f"- {pattern['attribute']}=\"{pattern['value']}\" outperformed for {handles}: {evidence}"


def build_prompt(pattern_facts: dict, recommendations_by_handle: dict[str, str] | None = None) -> str:
    statuses = pattern_facts.get("statuses", [])
    patterns = pattern_facts.get("patterns", [])
    recommendations_by_handle = recommendations_by_handle or {}

    status_section = "\n".join(_status_line(s) for s in statuses) or "(no influencers with data yet)"
    pattern_section = (
        "\n".join(_pattern_line(p) for p in patterns)
        or "(no cross-influencer content pattern found yet — fewer than 2 influencers share a standout topic/format/hook)"
    )
    rec_lines = "\n".join(f"- @{handle}: {text}" for handle, text in recommendations_by_handle.items())
    rec_section = f"\nExisting per-influencer recommendations (for context, don't just repeat them):\n{rec_lines}\n" if rec_lines else ""

    return f"""You are a talent-agency social media analyst producing a roster-wide weekly
briefing. You must narrate ONLY the facts given below — do not invent patterns, numbers,
or influencers not listed.

Roster status:
{status_section}

Cross-influencer content patterns (same topic/format/hook outperforming for 2+ influencers):
{pattern_section}
{rec_section}
Write a short briefing with:
1. A 2-3 sentence summary of the roster's overall state this week.
2. For each cross-influencer pattern above, a one-sentence finding that names the
   influencers and the stat that proves it.
3. One specific, prioritized next action per influencer with data (do not invent an
   action for an influencer with no data).

Write every piece of text in BOTH English and Spanish.

Respond ONLY with JSON in this exact shape, no other text:
{{"summary": {{"en": "...", "es": "..."}}, "patterns": [{{"finding": {{"en": "...", "es": "..."}}, "evidence": "the stat that proves it", "handles": ["handle1", "handle2"]}}], "actions": [{{"handle": "...", "action": {{"en": "...", "es": "..."}}, "reason": {{"en": "...", "es": "..."}}, "shortcode": "referenced post's shortcode, or null"}}]}}"""


def _validate(parsed: object) -> None:
    if not isinstance(parsed, dict):
        raise ValueError("response is not a JSON object")
    for key in ("summary", "patterns", "actions"):
        if key not in parsed:
            raise ValueError(f"missing {key} key")

    summary = parsed["summary"]
    if not isinstance(summary, dict) or "en" not in summary or "es" not in summary:
        raise ValueError("summary missing en/es")

    if not isinstance(parsed["patterns"], list):
        raise ValueError("patterns must be a list")
    for pattern in parsed["patterns"]:
        finding = pattern.get("finding") if isinstance(pattern, dict) else None
        if not isinstance(finding, dict) or "en" not in finding or "es" not in finding:
            raise ValueError("pattern finding missing en/es")
        handles = pattern.get("handles") if isinstance(pattern, dict) else None
        if not isinstance(handles, list) or not all(isinstance(h, str) for h in handles):
            raise ValueError("pattern handles must be a list of strings")

    if not isinstance(parsed["actions"], list):
        raise ValueError("actions must be a list")
    for action in parsed["actions"]:
        if not isinstance(action, dict) or not isinstance(action.get("handle"), str):
            raise ValueError("action missing string handle")
        for field in ("action", "reason"):
            value = action.get(field)
            if not isinstance(value, dict) or "en" not in value or "es" not in value:
                raise ValueError(f"action {field} missing en/es")


def _strip_at(handle: str) -> str:
    return handle.lstrip("@")


def _normalize_handles(parsed: dict) -> None:
    """Gemini sometimes includes a leading '@' on handles despite the prompt using
    plain handles — strip it so links to /influencer/<handle> resolve correctly."""
    for pattern in parsed["patterns"]:
        pattern["handles"] = [_strip_at(h) for h in pattern["handles"]]
    for action in parsed["actions"]:
        action["handle"] = _strip_at(action["handle"])


def generate_briefing(pattern_facts: dict, recommendations_by_handle: dict[str, str] | None = None) -> str | None:
    prompt = build_prompt(pattern_facts, recommendations_by_handle)
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
            _normalize_handles(parsed)
            return json.dumps(parsed)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError, AttributeError) as e:
            last_error = e
            logger.warning("Roster briefing invalid on attempt %d: %s", attempt + 1, e)

    logger.error("Roster briefing failed validation twice — not storing")
    return None
